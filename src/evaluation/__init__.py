"""Evaluation suite package."""
from src.evaluation.metrics import calculate_intent_metrics, calculate_escalation_metrics
from src.evaluation.judge import ResponseQualityJudge
from src.evaluation.evaluator import ComprehensiveEvaluator


def calculate_metrics(y_true, y_pred):
    """Backwards-compatible wrapper for general classification metric calculation."""
    classes = sorted(list(set(y_true).union(set(y_pred))))
    res = calculate_intent_metrics(y_true, y_pred, classes)
    return {
        "sample_count": res["sample_count"],
        "accuracy": res["accuracy"],
        "precision_macro": res["macro_precision"],
        "recall_macro": res["macro_recall"],
        "f1_macro": res["macro_f1"],
        "f1_weighted": res["weighted_f1"],
        "per_class_report": res["per_intent"],
        "confusion_matrix": res["confusion_matrix"],
    }


__all__ = [
    "calculate_intent_metrics",
    "calculate_escalation_metrics",
    "calculate_metrics",
    "ResponseQualityJudge",
    "ComprehensiveEvaluator",
]
