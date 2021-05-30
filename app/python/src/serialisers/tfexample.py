import datetime
import distutils
from typing import Optional, Text, List, Dict, Any, Tuple

from absl import logging
import tensorflow as tf


def _validate_schema(schema: Dict[str, str]) -> None:
    serialisable_types = [
        "BOOLEAN",
        "INTEGER",
        "FLOAT",
        "TIMESTAMP",
        "STRING",
    ]
    for key, _type in schema.items():
        if _type not in serialisable_types:
            raise RuntimeError(
                f"Unable to serialise {key} with type {_type} into a TFExample compatible type"
            )


def _parse_schema_from_data(data: Dict[Text, Any]) -> Dict[str, str]:
    schema = {}
    for key, value in data.items():
        if isinstance(value, bool):
            schema[key] = "BOOLEAN"
        elif isinstance(value, int):
            schema[key] = "INTEGER"
        elif isinstance(value, float):
            schema[key] = "FLOAT"
        elif isinstance(value, datetime.datetime):
            schema[key] = "TIMESTAMP"
        elif isinstance(value, str):
            schema[key] = "STRING"
        else:
            raise RuntimeError(
                f"Unable to serialise {key} with value {value} into a TFExample compatible type"
            )
        logging.warning(f"Inferred {key} as type '{schema[key]}'")
    return schema


class TFExampleSerialiser:
    def __init__(self, schema: Dict[str, str] = None):
        if schema is not None:
            _validate_schema(schema)
            self._schema = schema
        else:
            self._schema = None

    def from_json(self, window: List[Dict[Text, Any]]) -> tf.train.Example:
        if self._schema is None:
            self._schema = _parse_schema_from_data(window[0])

        flattened_features = {}
        for feature_label, feature_type in self._schema.items():
            feature_values = [el[feature_label] for el in window]

            if feature_type in ("INTEGER", "BOOLEAN"):
                feature = tf.train.Feature(
                    int64_list=tf.train.Int64List(value=[val for val in feature_values])
                )
            elif feature_type == "FLOAT":
                feature = tf.train.Feature(
                    float_list=tf.train.FloatList(value=[val for val in feature_values])
                )
            elif feature_type == "TIMESTAMP":
                feature = tf.train.Feature(
                    int64_list=tf.train.Int64List(
                        value=[int(val.timestamp()) for val in feature_values]
                    )
                )
            elif feature_type == "STRING":
                feature = tf.train.Feature(
                    bytes_list=tf.train.BytesList(
                        value=[tf.compat.as_bytes(val) for val in feature_values]
                    )
                )

            flattened_features[feature_label] = feature

        return tf.train.Example(features=tf.train.Features(feature=flattened_features))


class TFSequenceExampleSerialiser:
    def __init__(self, schema: Dict[str, str] = None):
        if schema is not None:
            _validate_schema(schema)
            self._schema = schema
        else:
            self._schema = None

    def from_json(self, window: List[Dict[Text, Any]]) -> tf.train.SequenceExample:
        if self._schema is None:
            self._schema = _parse_schema_from_data(window[0])

        flattened_features = {}
        for feature_label, feature_type in self._type_map.items():
            feature_values = [el[feature_label] for el in window]

            if feature_type in ("INTEGER", "BOOLEAN"):
                feature_list = tf.train.FeatureList(
                    feature=[
                        tf.train.Feature(int64_list=tf.train.Int64List(value=[val]))
                        for val in feature_values
                    ]
                )
            elif feature_type == "FLOAT":
                feature_list = tf.train.FeatureList(
                    feature=[
                        tf.train.Feature(float_list=tf.train.FloatList(value=[val]))
                        for val in feature_values
                    ]
                )
            elif feature_type == "TIMESTAMP":
                feature_list = tf.train.FeatureList(
                    feature=[
                        tf.train.Feature(
                            int64_list=tf.train.Int64List(value=[int(val.timestamp())])
                        )
                        for val in feature_values
                    ]
                )
            elif feature_type == "STRING":
                feature_list = tf.train.FeatureList(
                    feature=[
                        tf.train.Feature(
                            bytes_list=tf.train.BytesList(
                                value=[tf.compat.as_bytes(val)]
                            )
                        )
                        for val in feature_values
                    ]
                )

            flattened_features[feature_label] = feature_list

        return tf.train.SequenceExample(
            feature_lists=tf.train.FeatureLists(feature_list=flattened_features)
        )
