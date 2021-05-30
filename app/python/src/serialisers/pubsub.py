import json
from typing import Dict, Any, Tuple

import apache_beam as beam


def parse_pubsub_topic_or_subscription_str(
    topic_or_subscription: str,
) -> Tuple[str, str]:
    if "topic" in topic_or_subscription:
        return topic_or_subscription, None
    else:
        return None, topic_or_subscription


class PubSubSerialiser:
    def __init__(self, timestamp_key: str):
        self._timestamp_key = timestamp_key

    def to_json(
        self,
        pubsub_payload: bytes,
        timestamp=beam.DoFn.TimestampParam,
    ) -> Dict[str, Any]:
        payload_string = pubsub_payload.decode("utf-8")
        json_message = json.loads(payload_string)
        json_message[self._timestamp_key] = timestamp.to_rfc3339()
        return json_message

    def from_json(
        self,
        json_message: Dict[str, Any],
    ) -> bytes:
        if self._timestamp_key in json_message:
            del json_message[self._timestamp_key]
        payload_string = json.dumps(json_message)
        return str.encode(payload_string, "utf-8")
