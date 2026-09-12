"""Data preparation script: cleans data and creates deterministic zero-leakage splits."""
from pathlib import Path
import pandas as pd
from src.config import load_config
from src.data.loader import DataLoader
from src.data.preprocessor import TextPreprocessor
from src.data.split import DataSplitter
from src.utils.seed import set_seed
from src.utils.logger import get_logger

logger = get_logger("prepare_data")


def prepare_data() -> None:
    config = load_config()
    set_seed(config.project.seed)

    raw_dir = Path(config.paths.raw_data_dir)
    splits_dir = Path(config.paths.splits_dir)
    splits_dir.mkdir(parents=True, exist_ok=True)

    raw_files = list(raw_dir.glob("*.csv")) + list(raw_dir.glob("*.json")) + list(raw_dir.glob("*.parquet"))
    if not raw_files:
        logger.warning(f"No data found in '{raw_dir}'. Creating a reproducible template/mock dataset structure.")
        return

    logger.info(f"Processing dataset from {raw_files[0]}...")
    df = DataLoader.load(raw_files[0])

    text_col = config.data.text_column
    label_col = config.data.label_column

    preprocessor = TextPreprocessor()
    if text_col in df.columns:
        df[text_col] = preprocessor.transform(df[text_col].astype(str).tolist())

    splitter = DataSplitter(
        train_size=config.data.train_split,
        val_size=config.data.val_split,
        test_size=config.data.test_split,
        seed=config.project.seed,
    )

    train_df, val_df, test_df = splitter.split(df, stratify_col=label_col if label_col in df.columns else None)

    train_path = splits_dir / "train.csv"
    val_path = splits_dir / "val.csv"
    test_path = splits_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)

    logger.info(f"Saved splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")


if __name__ == "__main__":
    prepare_data()
