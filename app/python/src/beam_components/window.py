from typing import Iterable, List, Dict, Text, Any

import apache_beam as beam


@beam.ptransform_fn
@beam.typehints.with_input_types(Dict[Text, Any])
@beam.typehints.with_output_types(List[Dict[Text, Any]])
def window_elements(
    pipeline: beam.Pipeline,
    window_length: int,
    drop_irregular_windows: bool = True,
    sort_windows_by: str = "timestamp",
):
    def _sort_windows(window: Iterable[Dict[Text, Any]]) -> List[Dict[Text, Any]]:
        sorted_window = sorted(window, key=lambda e: e[sort_windows_by])
        return sorted_window

    windowed_elements = (
        pipeline
        | "AddConstantKey" >> beam.Map(lambda item: (0, item))
        | "WithSlidingWindow"
        >> beam.WindowInto(
            beam.transforms.window.SlidingWindows(window_length, 1),
            trigger=beam.transforms.trigger.AfterCount(window_length),
            accumulation_mode=beam.transforms.trigger.AccumulationMode.DISCARDING,
        )
        | "CombineWindow" >> beam.GroupByKey()
        | "GetValues" >> beam.Values()
    )
    if drop_irregular_windows:
        windowed_elements = windowed_elements | "EnforceWindowLengths" >> beam.Filter(
            lambda w: len(w) == window_length
        ).with_output_types(List[Dict[Text, Any]])
    if sort_windows_by is not None:
        windowed_elements = windowed_elements | "Sort" >> beam.Map(
            _sort_windows
        ).with_output_types(List[Dict[Text, Any]])
    return windowed_elements
