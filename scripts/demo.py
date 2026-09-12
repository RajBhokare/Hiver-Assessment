"""Interactive or CLI demo script for inference."""
from pathlib import Path
import sys
from src.config import load_config
from src.models.baseline import BaselineClassifier
from src.utils.logger import get_logger

logger = get_logger("demo")


def run_demo() -> None:
    config = load_config()
    model_path = Path(config.paths.models_dir) / "baseline_model.pkl"

    if not model_path.exists():
        logger.warning("No trained model found. Please run 'make baseline' before running the demo.")
        return

    model = BaselineClassifier()
    model.load(model_path)

    sample_texts = [
        "Please help me reset my account password as soon as possible.",
        "When will my order #12345 be delivered?",
        "I would like to request a refund for my recent transaction.",
    ]

    logger.info("Running sample demo inferences:")
    for text in sample_texts:
        pred = model.predict([text])[0]
        logger.info(f"Input : '{text}'")
        logger.info(f"Output: Predicted Class = {pred}\n")


if __name__ == "__main__":
    run_demo()
