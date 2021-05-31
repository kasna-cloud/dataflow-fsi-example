from typing import Dict, Any

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions

from src.serialisers.pubsub import (
    PubSubSerialiser,
    parse_pubsub_topic_or_subscription_str,
)


def setup_parser(parser):
    parser.add_argument(
        "--mappings",
        required=True,
        nargs="+",
        help=(
            "String mapping of in the form of <label>::<input_pubsub>::<output_bigquery>, where "
            "<label> is used to label the pipeline steps, "
            "<input_pubsub> is either PubSub topic of the form 'projects/<PROJECT>/topics/<TOPIC>' "
            "or a PubSub subscription of the form 'projects/<PROJECT>/subscriptions/<SUBSCRIPTION>', "
            "and <output_bigquery> is a BigQuery table of the form '<PROJECT>:<DATASET>.<TABLE>'."
        ),
    )
    parser.add_argument(
        "--timestamp_key",
        default="timestamp",
        help="Key under which timestamp is included in input PubSub metadata, and added to output BigQuery Table.",
    )


def run_pipeline(
    pipeline_options: PipelineOptions,
    mappings,
    timestamp_key,
):
    pipeline_options.view_as(StandardOptions).streaming = True

    with beam.Pipeline(options=pipeline_options) as pipeline:
        for mapping in mappings:
            label, input_ps, output_bq = mapping.split("::")
            input_topic, input_subscription = parse_pubsub_topic_or_subscription_str(
                input_ps
            )
            pubsub_serialiser = PubSubSerialiser(timestamp_key)
            (
                pipeline
                | f"Read from Pubsub ({label})"
                >> beam.io.ReadFromPubSub(
                    topic=input_topic,
                    subscription=input_subscription,
                    timestamp_attribute=timestamp_key,
                )
                | f"Deserialise Json ({label})" >> beam.Map(pubsub_serialiser.to_json)
                | f"Write to BigQuery ({label})"
                >> beam.io.WriteToBigQuery(
                    table=output_bq,
                    method="STREAMING_INSERTS",
                )
            )
