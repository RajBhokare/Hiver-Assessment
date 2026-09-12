"""Model evaluation script: evaluates saved models against test splits."""
from pathlib import Path
import json
from src.config import load_config
from src.data.loader import DataLoader
from src.models.baseline import BaselineClassifier
from src.evaluation.evaluator import ModelEvaluator
from src.utils.logger import get_logger

logger = get_logger("evaluate")


def run_evaluation() -> None:
    config = load_config()
    test_path = Path(config.paths.splits_dir) / "test.csv"
    model_path = Path(config.paths.models_dir) / "baseline_model.pkl"

    if not test_path.exists():
        logger.error(f"Test split not found at {test_path}. Run 'make prepare' first.")
        return

    if not model_path.exists():
        logger.error(f"Model checkpoint not found at {model_path}. Run 'make baseline' first.")
        return

    df_test = DataLoader.load(test_path)
    text_col = config.data.text_column
    label_col = config.data.label_column

    X_test = df_test[text_col].fillna("").tolist()
    y_test = df_test[label_col].tolist()

    logger.info(f"Loading baseline model from {model_path}...")
    model = BaselineClassifier()
    model.load(model_path)

    logger.info(f"Generating predictions for {len(X_test)} test instances...")
    y_pred = model.predict(X_test)

    evaluator = ModelEvaluator(metrics_dir=config.paths.metrics_dir)
    metrics = evaluator.evaluate_predictions(y_test, y_pred, experiment_name="baseline_test")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    run_evaluation()
