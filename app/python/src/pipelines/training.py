import os
import datetime

from absl import logging
from google.cloud import bigquery
from apache_beam.options.pipeline_options import (
    PipelineOptions,
    GoogleCloudOptions,
    SetupOptions,
)
import tfx.components as default_components
from tfx.orchestration.pipeline import Pipeline
from tfx.orchestration.beam.beam_dag_runner import BeamDagRunner
from tfx.dsl.components.base.executor_spec import ExecutorClassSpec
from tfx.components.trainer.executor import GenericExecutor
from tfx.proto.trainer_pb2 import EvalArgs, TrainArgs
from tfx.proto.example_gen_pb2 import Input
from tfx.proto.pusher_pb2 import PushDestination
from tfx.extensions.google_cloud_ai_platform.pusher import (
    executor as ai_platform_pusher_executor,
)
from ml_metadata.proto import metadata_store_pb2

from src.tfx_components.bigquery_window_gen import BigQueryExampleWithSlidingWindowGen


def setup_parser(parser):
    parser.add_argument(
        "--tfx_root_dir", required=True, help=("Root directory for TFX files and data.")
    )
    parser.add_argument(
        "--tfx_metadata_sql_database",
        required=True,
        help=("SQL database name for TFX metadata store."),
    )
    parser.add_argument(
        "--tfx_metadata_sql_username",
        required=True,
        help=("SQL user name for TFX metadata store database."),
    )
    parser.add_argument(
        "--symbol", default="GBPAUD", help=("Forex symbol to train ML model on.")
    )
    parser.add_argument(
        "--window_length",
        default=60,
        type=int,
        help="Length of window to input into model inference.",
    )
    parser.add_argument(
        "--num_train_steps",
        default=2700,
        type=int,
        help="Number of steps to run with training dataset",
    )
    parser.add_argument(
        "--num_eval_steps",
        default=2700,
        type=int,
        help="Number of steps to run with evaluation dataset",
    ),
    parser.add_argument(
        "--ai_platform_model_region",
        default="us-east1",
        help="Region to deploy ai platform model to",
    ),
    parser.add_argument(
        "--rsi_lower_threshold", default=30, type=float, help="Lower RSI threshold"
    ),
    parser.add_argument(
        "--rsi_upper_threshold", default=70, type=float, help="Upper RSI threshold"
    )


def run_pipeline(
    pipeline_options: PipelineOptions,
    tfx_root_dir: str,
    tfx_metadata_sql_database: str,
    tfx_metadata_sql_username: str,
    symbol: str,
    window_length: int,
    num_train_steps: int,
    num_eval_steps: int,
    ai_platform_model_region: str,
    rsi_lower_threshold: float,
    rsi_upper_threshold: float,
):
    # TODO: is this needed?
    pipeline_options.view_as(SetupOptions).save_main_session = False

    gcp_project_id = pipeline_options.view_as(GoogleCloudOptions).project
    pipeline_name = pipeline_options.view_as(GoogleCloudOptions).job_name

    metadata_connection_config = metadata_store_pb2.ConnectionConfig()
    metadata_connection_config.mysql.host = "127.0.0.1"
    metadata_connection_config.mysql.port = 3306
    metadata_connection_config.mysql.database = tfx_metadata_sql_database
    metadata_connection_config.mysql.user = tfx_metadata_sql_username

    pipeline_root = os.path.join(tfx_root_dir, pipeline_name, "pipelines")
    serving_path = os.path.join(tfx_root_dir, pipeline_name, "serving_files")

    feature_metrics = [
        "LOG_RTN",
        "SIMPLE_MOVING_AVERAGE",
        "EXPONENTIAL_MOVING_AVERAGE",
        "STANDARD_DEVIATION",
    ]

    eval_datetime_end = datetime.datetime.today()
    eval_datetime_start = eval_datetime_end - datetime.timedelta(hours=2)
    train_datetime_end = eval_datetime_start
    train_datetime_start = train_datetime_end - datetime.timedelta(days=1)

    def _build_data_query_str(start_time, end_time):
        return f"""
			SELECT {', '.join(feature_metrics)}, timestamp
			FROM {gcp_project_id}.forex.metrics WHERE symbol = '{symbol}'
			AND (RELATIVE_STRENGTH_INDICATOR > {rsi_upper_threshold} OR RELATIVE_STRENGTH_INDICATOR < {rsi_lower_threshold})
			AND timestamp
				BETWEEN TIMESTAMP('{start_time.strftime('%Y-%m-%d %H:%M:%S')}')
				AND TIMESTAMP('{end_time.strftime('%Y-%m-%d %H:%M:%S')}')
			ORDER BY timestamp
		"""

    train_data_query_str = _build_data_query_str(
        train_datetime_start, train_datetime_end
    )
    eval_data_query_str = _build_data_query_str(eval_datetime_start, eval_datetime_end)

    # We check to make sure there is enough data to warrant a retraining run before kicking off our TFX pipeline:
    def count_at_least(query, required_count):
        client = bigquery.Client()
        check_query = client.query(f"SELECT COUNT (*) AS count FROM ({query})")
        check_count = next(check_query.result().__iter__())["count"]
        return check_count >= required_count

    if not count_at_least(train_data_query_str, 500) or not count_at_least(
        eval_data_query_str, 100
    ):
        logging.error("Not enough data accumulated in BQ to warrant retraining yet")
        return

        # Generate training samples from windowed BQ rows
    example_gen = BigQueryExampleWithSlidingWindowGen(
        window_length=window_length,
        bq_timestamp_attribute="timestamp",
        drop_irregular_windows=True,
        input_config=Input(
            splits=[
                Input.Split(name="train", pattern=train_data_query_str),
                Input.Split(name="eval", pattern=eval_data_query_str),
            ]
        ),
    )

    # Computes statistics over data for visualization and example validation.
    statistics_gen = default_components.StatisticsGen(
        examples=example_gen.outputs["examples"],
    )
    # Generates schema based on statistics files.
    schema_gen = default_components.SchemaGen(
        statistics=statistics_gen.outputs["statistics"],
        infer_feature_shape=True,
    )
    # Performs anomaly detection based on statistics and data schema.
    example_validator = default_components.ExampleValidator(
        statistics=statistics_gen.outputs["statistics"],
        schema=schema_gen.outputs["schema"],
    )

    # Apply pre-processing transform
    transform = default_components.Transform(
        examples=example_gen.outputs["examples"],
        schema=schema_gen.outputs["schema"],
        module_file=os.path.abspath("./src/tfx_components/transformer.py"),
        custom_config={"feature_columns": feature_metrics},
    )

    # Trains the model
    trainer = default_components.Trainer(
        examples=transform.outputs["transformed_examples"],
        transform_graph=transform.outputs["transform_graph"],
        module_file=os.path.abspath("./src/tfx_components/trainer.py"),
        custom_executor_spec=ExecutorClassSpec(GenericExecutor),
        schema=schema_gen.outputs["schema"],
        custom_config={
            "input_features": feature_metrics,
            "window_size": window_length,
            "outer_units": 8 * len(feature_metrics),
            "inner_units": 4 * len(feature_metrics),
            "batch_size": 32,
        },
        train_args=TrainArgs(num_steps=num_train_steps),
        eval_args=EvalArgs(num_steps=num_eval_steps),
    )

    # Pushes the trained model ai platform
    pusher = default_components.Pusher(
        model=trainer.outputs["model"],
        # model_blessing=evaluator.outputs['blessing'],
        push_destination=PushDestination(
            filesystem=PushDestination.Filesystem(base_directory=serving_path)
        ),
        custom_executor_spec=ExecutorClassSpec(ai_platform_pusher_executor.Executor),
        custom_config={
            ai_platform_pusher_executor.SERVING_ARGS_KEY: {
                "model_name": f"autoencoder{symbol}",
                "project_id": gcp_project_id,
                "regions": [ai_platform_model_region],
            }
        },
    )

    tfx_pipeline = Pipeline(
        pipeline_name=pipeline_name,
        pipeline_root=pipeline_root,
        metadata_connection_config=metadata_connection_config,
        components=[
            example_gen,
            statistics_gen,
            schema_gen,
            example_validator,
            transform,
            trainer,
            pusher,
        ],
        enable_cache=False,
    )

    BeamDagRunner().run(tfx_pipeline)
