from typing import Tuple, List, Dict, Text, Any

from absl import logging
import apache_beam as beam
from tfx_bsl.beam.run_inference import RunInferenceImpl
from tfx_bsl.public.proto.model_spec_pb2 import (
    InferenceSpecType,
    AIPlatformPredictionModelSpec,
)
import tensorflow as tf

from src.serialisers.tfexample import TFExampleSerialiser


@beam.ptransform_fn
@beam.typehints.with_input_types(Dict[Text, Any])
@beam.typehints.with_output_types(List[Dict[Text, Any]])
def run_windowed_inference(
    input_elements: beam.Pipeline,
    ai_platform_project_id: str,
    ai_platform_model_name: int,
    window_length: int,
    input_schema: Dict[str, str] = None,
):
    """Run AI Platform inference for model and parse output as a window of elements."""
    tfexample_serialiser = TFExampleSerialiser(input_schema)

    def _use_timestamp_as_key(element, timestamp=beam.DoFn.TimestampParam):
        return (timestamp.to_utc_datetime().timestamp(), element)

    def _parse_prediction_log(prediction_log):
        response_output = prediction_log.predict_log.response.outputs

        features_by_type = {}
        for combined_name, tensor in response_output.items():
            output_type, feature_name = combined_name.split("::")

            if output_type not in features_by_type:
                features_by_type[output_type] = {}

            features_by_type[output_type][feature_name] = tf.make_ndarray(
                tensor
            ).flatten()

        parsed_outputs = {}
        for output_type, list_per_feature in features_by_type.items():
            for length in [len(values) for values in list_per_feature.values()]:
                if length != window_length:
                    raise ValueError(
                        "Prediction output features do not have the same window length!"
                    )

            parsed_outputs[output_type] = [
                {f: vs[i] for f, vs in list_per_feature.items()}
                for i in range(window_length)
            ]

        return parsed_outputs

    def _parse_key_as_timestamp(key, value):
        return beam.window.TimestampedValue(value, key)

    return (
        input_elements
        | "AddInputKeys" >> beam.Map(_use_timestamp_as_key)
        | "ToTFExample"
        >> beam.MapTuple(
            lambda k, v: (k, tfexample_serialiser.from_json(v))
        ).with_output_types(Tuple[float, tf.train.Example])
        | "RunInference"
        >> RunInferenceImpl(
            InferenceSpecType(
                ai_platform_prediction_model_spec=AIPlatformPredictionModelSpec(
                    project_id=ai_platform_project_id,
                    model_name=ai_platform_model_name,
                )
            )
        )
        | "ParsePredictionLog"
        >> beam.MapTuple(lambda k, v: (k, _parse_prediction_log(v)))
        | "RewriteTimestamp" >> beam.MapTuple(_parse_key_as_timestamp)
    )
