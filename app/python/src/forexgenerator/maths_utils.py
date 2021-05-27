"""
Space holder for function templates used in the project
"""
import pandas as pd


def z_score(data: pd.Series) -> float:
    """Calculate z-score z = (x-mean) / std for last item in series.

    For use in rolling window consider:
    series['rolling_z_score'] = series['quantity'].rolling(60).apply(zscore)

    Args:
        data (pd.Series):  data to normalise

    Returns:
        pd.Series: z-score of last item in series
    """
    new = (data.values[-1] - data.mean(axis=0)) / data.std(ddof=0, axis=0)

    return new
