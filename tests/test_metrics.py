"""Unit tests for metric calculation logic."""
from src.evaluation.metrics import calculate_metrics


def test_calculate_metrics_perfect_score():
    y_true = ["billing", "tech_support", "billing", "general"]
    y_pred = ["billing", "tech_support", "billing", "general"]

    metrics = calculate_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 1.0
    assert metrics["precision_macro"] == 1.0
    assert metrics["recall_macro"] == 1.0
    assert metrics["f1_macro"] == 1.0
    assert metrics["sample_count"] == 4


def test_calculate_metrics_partial_score():
    y_true = [0, 1, 0, 1]
    y_pred = [0, 0, 0, 1]

    metrics = calculate_metrics(y_true, y_pred)
    assert metrics["accuracy"] == 0.75
    assert metrics["sample_count"] == 4
    assert "confusion_matrix" in metrics
    assert "per_class_report" in metrics
