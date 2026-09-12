"""Evaluation metrics module for Intent Classification and Safety/Escalation decisions."""
from typing import Any, Dict, List, Sequence, Tuple
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


def calculate_metrics(y_true, y_pred):
    """Backwards compatible metrics helper."""
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


def calculate_intent_metrics(y_true: Sequence[str], y_pred: Sequence[str], classes: Sequence[str]) -> Dict[str, Any]:
    """Compute comprehensive intent classification metrics."""
    y_true_list = list(y_true)
    y_pred_list = list(y_pred)
    classes_list = sorted(list(classes))

    acc = float(accuracy_score(y_true_list, y_pred_list))
    prec_macro = float(precision_score(y_true_list, y_pred_list, labels=classes_list, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true_list, y_pred_list, labels=classes_list, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_true_list, y_pred_list, labels=classes_list, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_true_list, y_pred_list, labels=classes_list, average="weighted", zero_division=0))

    report = classification_report(y_true_list, y_pred_list, labels=classes_list, output_dict=True, zero_division=0)
    
    per_intent = {}
    for cls_name in classes_list:
        cls_stat = report.get(cls_name, {})
        per_intent[cls_name] = {
            "precision": round(float(cls_stat.get("precision", 0.0)), 4),
            "recall": round(float(cls_stat.get("recall", 0.0)), 4),
            "f1_score": round(float(cls_stat.get("f1-score", 0.0)), 4),
            "support": int(cls_stat.get("support", 0)),
        }

    conf_mat = confusion_matrix(y_true_list, y_pred_list, labels=classes_list).tolist()

    return {
        "sample_count": len(y_true_list),
        "classes": classes_list,
        "accuracy": round(acc, 4),
        "macro_precision": round(prec_macro, 4),
        "macro_recall": round(rec_macro, 4),
        "macro_f1": round(f1_macro, 4),
        "weighted_f1": round(f1_weighted, 4),
        "per_intent": per_intent,
        "confusion_matrix": conf_mat,
    }


def calculate_escalation_metrics(
    y_true_escalate: Sequence[bool],
    y_pred_escalate: Sequence[bool],
) -> Dict[str, Any]:
    """Compute escalation and safety metrics.
    
    Positive Class = Escalation Required (True).
    Negative Class = Auto-Handle Safe (False).
    
    False Auto-Handling Rate (Safety Risk):
      Proportion of truly risky queries (y_true=True) that the agent falsely auto-handled (y_pred=False).
      FN / (TP + FN) = 1 - Recall.
      
    False Escalation Rate (Operational Inefficiency):
      Proportion of routine queries (y_true=False) that the agent unnecessarily escalated (y_pred=True).
      FP / (TN + FP).
    """
    y_true_arr = np.array(y_true_escalate, dtype=bool)
    y_pred_arr = np.array(y_pred_escalate, dtype=bool)

    tp = int(np.sum((y_true_arr == True) & (y_pred_arr == True)))
    fp = int(np.sum((y_true_arr == False) & (y_pred_arr == True)))
    fn = int(np.sum((y_true_arr == True) & (y_pred_arr == False)))
    tn = int(np.sum((y_true_arr == False) & (y_pred_arr == False)))

    total_pos = tp + fn  # Total truly requiring escalation
    total_neg = tn + fp  # Total safe for auto-handling

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / total_pos if total_pos > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    accuracy = (tp + tn) / len(y_true_arr) if len(y_true_arr) > 0 else 0.0

    # Safety-critical rate
    false_auto_handling_rate = fn / total_pos if total_pos > 0 else 0.0
    # Inefficiency rate
    false_escalation_rate = fp / total_neg if total_neg > 0 else 0.0

    return {
        "sample_count": len(y_true_arr),
        "true_escalations": total_pos,
        "true_auto_handles": total_neg,
        "true_positives_tp": tp,
        "false_positives_fp": fp,
        "false_negatives_fn": fn,
        "true_negatives_tn": tn,
        "accuracy": round(float(accuracy), 4),
        "precision": round(float(precision), 4),
        "recall": round(float(recall), 4),
        "f1_score": round(float(f1), 4),
        "false_auto_handling_rate": round(float(false_auto_handling_rate), 4),
        "false_escalation_rate": round(float(false_escalation_rate), 4),
    }
