import time
import json
from typing import Callable

from absl import logging
from apache_beam.options.pipeline_options import PipelineOptions
from google.cloud import pubsub_v1

from src.forexgenerator.utils import create_default_forex_generators


def setup_parser(parser):
    parser.add_argument(
        "--output_prices_topic",
        required=True,
        help=(
            "PubSub topic to publish the generated prices to. A string in the form of "
            "'projects/<PROJECT>/topics/<TOPIC>'."
        ),
    )
    parser.add_argument(
        "--tick_hz",
        default=10,
        type=int,
        help=(
            "Rate to which to tick the price generator. Note that due to in-built gap "
            "generation, the number of prices output per second will be less than the "
            "tick rate."
        ),
    )
    parser.add_argument(
        "--timestamp_key",
        default="timestamp",
        help="Key under which timestamp is included in output PubSub metadata.",
    )


def run_pipeline(
    pipeline_options: PipelineOptions,
    output_prices_topic: str,
    tick_hz: int,
    timestamp_key: str,
):
    pubsub_publisher = pubsub_v1.PublisherClient()

    def _publish_price(
        symbol: str, price: float, timestamp: int, done_callback: Callable
    ):
        tick_data = {"symbol": symbol, "value": price}
        encoded_tick_data = json.dumps(tick_data).encode("utf-8")
        tick_metadata = {
            "symbol": symbol,
            f"{timestamp_key}": str(round(timestamp * 1000)),
        }
        future = pubsub_publisher.publish(
            output_prices_topic, encoded_tick_data, **tick_metadata
        )

        def _done_callback_wrapper(complete_future):
            done_callback(symbol, price, timestamp)

        future.add_done_callback(_done_callback_wrapper)
        return future

    generators = create_default_forex_generators()
    while True:
        timestamp = time.time()
        # Generate next spot prices for each currency pair
        for symbol, generator in generators.items():
            price = generator.next()

            # If there is no price (due to simulated gaps), we don't publish anything
            if price is None:
                if logging.level_debug:
                    logging.debug(f"{symbol} $ None  {timestamp}")
            else:

                def log_done(symbol: str, price: float, timestamp: int):
                    if logging.level_debug:
                        logging.debug(f"{symbol} ${price} {timestamp}")

                _publish_price(symbol, price, timestamp, log_done)

        # Wait until next tick
        time.sleep(1 / tick_hz)
