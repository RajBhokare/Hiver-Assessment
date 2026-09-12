"""Data loader implementation supporting CSV, JSON, and Parquet."""
from pathlib import Path
from typing import Union
import pandas as pd


class DataLoader:
    """Handles loading datasets with consistent encoding and type preservation."""

    @staticmethod
    def load(file_path: Union[str, Path]) -> pd.DataFrame:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found at: {path.resolve()}")

        suffix = path.suffix.lower()
        if suffix == ".csv":
            return pd.read_csv(path, encoding="utf-8")
        elif suffix in [".json", ".jsonl"]:
            return pd.read_json(path, lines=(suffix == ".jsonl"))
        elif suffix == ".parquet":
            return pd.read_parquet(path)
        else:
            raise ValueError(f"Unsupported file format: {suffix}. Supported: .csv, .json, .jsonl, .parquet")
