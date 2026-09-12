"""Baseline model training script."""
from pathlib import Path
import pandas as pd
from src.config import load_config
from src.data.loader import DataLoader
from src.models.baseline import BaselineClassifier
from src.utils.seed import set_seed
from src.utils.logger import get_logger

logger = get_logger("train_baseline")


def train_baseline() -> None:
    config = load_config()
    set_seed(config.project.seed)

    train_path = Path(config.paths.splits_dir) / "train.csv"
    if not train_path.exists():
        logger.error(f"Train split not found at {train_path}. Run 'make prepare' first.")
        return

    df_train = DataLoader.load(train_path)
    text_col = config.data.text_column
    label_col = config.data.label_column

    X_train = df_train[text_col].fillna("").tolist()
    y_train = df_train[label_col].tolist()

    logger.info(f"Training BaselineClassifier on {len(X_train)} samples...")
    model = BaselineClassifier(
        max_features=config.model.baseline.max_features,
        ngram_range=tuple(config.model.baseline.ngram_range),
        random_state=config.project.seed,
    )
    model.fit(X_train, y_train)

    model_out = Path(config.paths.models_dir) / "baseline_model.pkl"
    model.save(model_out)
    logger.info(f"Baseline model successfully saved to: {model_out.resolve()}")


if __name__ == "__main__":
    train_baseline()
