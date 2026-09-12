"""Statistical validation tools comparing LLM Judge outputs against human ratings."""
from typing import Any, Dict, List, Optional, Sequence, Tuple
import numpy as np
from sklearn.metrics import cohen_kappa_score, accuracy_score, f1_score, precision_score, recall_score
from scipy.stats import spearmanr


def compute_rating_agreement(
    human_scores: Sequence[float],
    judge_scores: Sequence[float],
) -> Dict[str, Any]:
    """Compute agreement metrics between human and judge numerical ratings (1-5 scale)."""
    h = np.array(human_scores, dtype=float)
    j = np.array(judge_scores, dtype=float)

    if len(h) == 0 or len(j) == 0:
        return {}

    # Exact agreement
    exact_match = float(np.mean(np.round(h) == np.round(j)))

    # Agreement within +/- 1
    within_one = float(np.mean(np.abs(h - j) <= 1.0 + 1e-5))

    # Quadratic Weighted Cohen's Kappa
    try:
        h_int = np.clip(np.round(h).astype(int), 1, 5)
        j_int = np.clip(np.round(j).astype(int), 1, 5)
        kappa_weighted = float(cohen_kappa_score(h_int, j_int, weights="quadratic"))
    except Exception:
        kappa_weighted = 0.0

    # Spearman rank correlation
    try:
        corr, p_val = spearmanr(h, j)
        spearman_corr = float(corr) if not np.isnan(corr) else 0.0
    except Exception:
        spearman_corr = 0.0

    # Mean Absolute Error
    mae = float(np.mean(np.abs(h - j)))

    return {
        "sample_count": len(h),
        "exact_agreement_pct": round(exact_match * 100, 2),
        "agreement_within_1_pct": round(within_one * 100, 2),
        "quadratic_weighted_kappa": round(kappa_weighted, 4),
        "spearman_correlation": round(spearman_corr, 4),
        "mean_absolute_error": round(mae, 4),
    }


def compute_critical_error_agreement(
    human_critical: Sequence[bool],
    judge_critical: Sequence[bool],
) -> Dict[str, Any]:
    """Compute binary classification agreement on critical error detection."""
    h = np.array(human_critical, dtype=bool)
    j = np.array(judge_critical, dtype=bool)

    if len(h) == 0:
        return {}

    acc = accuracy_score(h, j)
    prec = precision_score(h, j, zero_division=0)
    rec = recall_score(h, j, zero_division=0)
    f1 = f1_score(h, j, zero_division=0)

    try:
        kappa = cohen_kappa_score(h, j)
    except Exception:
        kappa = 0.0

    return {
        "sample_count": len(h),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "cohen_kappa": round(float(kappa), 4),
    }
