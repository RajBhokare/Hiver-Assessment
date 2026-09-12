"""Data Exploration (EDA) script.
Inspects raw or processed datasets, class distributions, and missing values.
"""
from pathlib import Path
import sys
import pandas as pd
from src.config import load_config
from src.utils.logger import get_logger

logger = get_logger("explore")


def explore_data() -> None:
    config = load_config()
    raw_dir = Path(config.paths.raw_data_dir)
    data_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.parquet"))

    if not data_files:
        logger.warning(f"No raw data files found in '{raw_dir}'. Place raw dataset files there to explore.")
        return

    for file_path in data_files:
        logger.info(f"--- Exploring {file_path.name} ---")
        if file_path.suffix == ".csv":
            df = pd.read_csv(file_path)
        elif file_path.suffix in [".json", ".jsonl"]:
            df = pd.read_json(file_path, lines=(file_path.suffix == ".jsonl"))
        elif file_path.suffix == ".parquet":
            df = pd.read_parquet(file_path)
        else:
            continue

        logger.info(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        logger.info(f"Columns: {list(df.columns)}")
        logger.info(f"Missing values:\n{df.isnull().sum()}")

        label_col = config.data.label_column
        if label_col in df.columns:
            logger.info(f"Class distribution for '{label_col}':\n{df[label_col].value_counts(normalize=True)}")


if __name__ == "__main__":
    explore_data()
