from typing import Dict

from src.forexgenerator.forexgenerator import FOREXGenerator


def create_default_forex_generators() -> Dict[str, FOREXGenerator]:
    starting_values = {
        "AUDJPY": 81.44,
        "AUDUSD": 0.77,
        "CADJPY": 87.36,
        "EURAUD": 1.54,
        "EURCAD": 1.48,
        "EURGBP": 0.85,
        "EURJPY": 129.38,
        "EURUSD": 1.18,
        "GBPAUD": 1.8,
        "GBPCHF": 1.29,
        "GBPJPY": 151.47,
        "GBPNZD": 1.96,
        "GBPUSD": 1.38,
        "NZDUSD": 0.71,
        "USDCAD": 1.25,
        "USDCHF": 0.94,
        "USDJPY": 109.93,
    }
    return {
        symbol: FOREXGenerator(value, currency_pair=symbol)
        for symbol, value in starting_values.items()
    }