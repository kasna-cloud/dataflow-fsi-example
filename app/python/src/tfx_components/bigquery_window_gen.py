from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import ast
import distutils
from typing import Optional, Text, List, Dict, Any, Union
from absl import logging

from tfx import types
from tfx.components.example_gen import component, base_example_gen_executor
from tfx.extensions.google_cloud_big_query import utils
from tfx.dsl.components.base import executor_spec
from tfx.proto import example_gen_pb2
import apache_beam as beam
import tensorflow as tf
from google.cloud import bigquery

from src.beam_components.window import window_elements
from src.serialisers.tfexample import TFExampleSerialiser, TFSequenceExampleSerialiser


class _BigQueryConverter(object):
    def __init__(
        self,
        query: Text,
        use_sequenceexample: bool = False,
        project_id: Optional[Text] = None
    ):
        client = bigquery.Client(project=project_id)
        # Dummy query to get the type information for each field.
        query_job = client.query('SELECT * FROM ({}) LIMIT 0'.format(query))
        results = query_job.result()
        schema = {f.name: f.field_type for f in results.schema}
        if use_sequenceexample:
            self._serialiser = TFSequenceExampleSerialiser(schema)
        else:
            self._serialiser = TFExampleSerialiser(schema)

    def Convert(self, window: List[Dict[Text, Any]]) -> Union[tf.train.Example, tf.train.SequenceExample]:
        return self._serialiser.from_json(window)


class _BigQueryTimestampParser(beam.DoFn):
    def __init__(self, timestamp_column):
        super().__init__()
        self._timestamp_column = timestamp_column

    def process(self, big_query_item):
        # Extract the numeric Unix seconds-since-epoch timestamp to be
        # associated with the current log entry.
        timestamp = big_query_item[self._timestamp_column]
        # Wrap and emit the current entry and new timestamp in a
        # TimestampedValue.
        yield beam.window.TimestampedValue(big_query_item, timestamp.timestamp())


@beam.ptransform_fn
@beam.typehints.with_input_types(beam.Pipeline)
def _BigQueryToExampleWithSlidingWindow(
        pipeline: beam.Pipeline,
        exec_properties: Dict[Text, Any],
        split_pattern: Text
) -> beam.pvalue.PCollection:
    # TODO: retrieve the window_length property better:
    custom_config = ast.literal_eval(exec_properties.get('custom_config'))
    window_length = int(custom_config['window_length'])
    bq_timestamp_attribute = custom_config['bq_timestamp_attribute']
    drop_irregular_windows = bool(distutils.util.strtobool(custom_config['drop_irregular_windows']))
    use_sequenceexample = bool(distutils.util.strtobool(custom_config['use_sequenceexample']))

    beam_pipeline_args = exec_properties['_beam_pipeline_args']
    pipeline_options = beam.options.pipeline_options.PipelineOptions(beam_pipeline_args)
    # Try to parse the GCP project ID from the beam pipeline options.
    project = pipeline_options.view_as(beam.options.pipeline_options.GoogleCloudOptions).project
    if isinstance(project, beam.options.value_provider.ValueProvider):
        project = project.get()
    converter = _BigQueryConverter(split_pattern, use_sequenceexample, project)

    if drop_irregular_windows:
        logging.warning("ExampleGen will silently drop windows with irregular lengths")
    windowed_rows = (pipeline
        | "QueryTable" >> utils.ReadFromBigQuery(query=split_pattern)
        | "ParseTimestamp" >> beam.ParDo(_BigQueryTimestampParser(bq_timestamp_attribute))
        | "WindowElements" >> window_elements(
            window_length=window_length,
            drop_irregular_windows=drop_irregular_windows,
            sort_windows_by=bq_timestamp_attribute,
        )
    )
    if use_sequenceexample:
        logging.warning("ExampleGen will output tf.train.SequenceExample")
        return (windowed_rows
            | "MapToTFSequenceExample" >> beam.Map(converter.Convert).with_output_types(
                tf.train.SequenceExample
            )
        )
    else:
        logging.warning("ExampleGen will output tf.train.Example")
        return (windowed_rows
            | "MapToTFExample" >> beam.Map(converter.Convert).with_output_types(
                tf.train.Example)
            )


class Executor(base_example_gen_executor.BaseExampleGenExecutor):
    """TFX BigQueryExampleGen executor extended with sliding window."""

    def GetInputSourceToExamplePTransform(self) -> beam.PTransform:
        """Returns PTransform for BigQuery to TF examples."""
        return _BigQueryToExampleWithSlidingWindow


class BigQueryExampleWithSlidingWindowGen(component.QueryBasedExampleGen):
    """UNOfficial TFX BigQueryExampleGen component with sliding windows.
    The BigQuery examplegen component takes a query, and generates train
    and eval examples for downsteam components.
    """

    EXECUTOR_SPEC = executor_spec.ExecutorClassSpec(Executor)

    def __init__(self,
                 window_length: int,
                 bq_timestamp_attribute: str,
                 drop_irregular_windows: bool = True,
                 use_sequenceexample: bool = False,
                 input_config: Optional[example_gen_pb2.Input] = None,
                 output_config: Optional[example_gen_pb2.Output] = None,
                 example_artifacts: Optional[types.Channel] = None,
                 instance_name: Optional[Text] = None):
        """Constructs a BigQueryExampleGen component.
        Args:
            query: BigQuery sql string, query result will be treated as a single
                split, can be overwritten by input_config.
            input_config: An example_gen_pb2.Input instance with Split.pattern as
                BigQuery sql string. If set, it overwrites the 'query' arg, and allows
                different queries per split. If any field is provided as a
                RuntimeParameter, input_config should be constructed as a dict with the
                same field names as Input proto message.
            output_config: An example_gen_pb2.Output instance, providing output
                configuration. If unset, default splits will be 'train' and 'eval' with
                size 2:1. If any field is provided as a RuntimeParameter,
                input_config should be constructed as a dict with the same field names
                as Output proto message.
            example_artifacts: Optional channel of 'ExamplesPath' for output train and
                eval examples.
            instance_name: Optional unique instance name. Necessary if multiple
                BigQueryExampleGen components are declared in the same pipeline.
        Raises:
            RuntimeError: Only one of query and input_config should be set.
        """
        super(BigQueryExampleWithSlidingWindowGen, self).__init__(
            input_config=input_config,
            custom_config={
                'window_length': str(window_length),
                'bq_timestamp_attribute': str(bq_timestamp_attribute),
                'drop_irregular_windows': str(drop_irregular_windows),
                'use_sequenceexample': str(use_sequenceexample),
            },
            output_config=output_config,
            example_artifacts=example_artifacts,
            instance_name=instance_name,
        )
