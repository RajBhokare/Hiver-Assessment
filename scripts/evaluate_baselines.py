import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np
from hiver_agent.baselines.majority_baseline import MajorityIntentBaseline, TrivialEscalationStrategy
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline
from src.data.labeler import apply_labels
from src.utils.seed import set_seed
from src.utils.logger import get_logger

logger = get_logger("evaluate_baselines")


def main():
    set_seed(42)

    # 1. Load splits
    train_path = Path("data/splits/train.csv")
    test_path = Path("data/splits/test.csv")

    if not train_path.exists() or not test_path.exists():
        raise FileNotFoundError("Train or Test splits missing! Please ensure 'make prepare' was run.")

    logger.info("Loading training and testing datasets...")
    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    # 2. Apply deterministic frozen taxonomy labels
    df_train_labeled = apply_labels(df_train, text_col="clean_customer_text")
    df_test_labeled = apply_labels(df_test, text_col="clean_customer_text")

    X_train = df_train_labeled["clean_customer_text"].fillna("").tolist()
    y_train = df_train_labeled["intent"].tolist()

    X_test = df_test_labeled["clean_customer_text"].fillna("").tolist()
    y_test = df_test_labeled["intent"].tolist()

    logger.info(f"Training samples: {len(X_train):,} | Test samples: {len(X_test):,}")

    metrics_dir = Path("artifacts/metrics")
    metrics_dir.mkdir(parents=True, exist_ok=True)
    models_dir = Path("artifacts/models")
    models_dir.mkdir(parents=True, exist_ok=True)

    # ---------------------------------------------------------
    # BASELINE 1: Majority Class Intent + Trivial Escalation
    # ---------------------------------------------------------
    logger.info("--- Fitting Baseline 1: Majority Class ---")
    maj_baseline = MajorityIntentBaseline()
    maj_baseline.fit(X_train, y_train)

    logger.info(f"Majority intent identified from train set: '{maj_baseline.majority_intent}' ({maj_baseline.majority_probability:.2%})")

    # Evaluate Baseline 1 on Test
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, classification_report, confusion_matrix
    y_pred_maj = maj_baseline.predict(X_test)
    classes = sorted(list(set(y_test)))

    maj_metrics = {
        "model_name": "Baseline_1_Majority_Class",
        "sample_count": len(y_test),
        "majority_class": maj_baseline.majority_intent,
        "classes": classes,
        "accuracy": round(float(accuracy_score(y_test, y_pred_maj)), 4),
        "macro_precision": round(float(precision_score(y_test, y_pred_maj, average="macro", zero_division=0)), 4),
        "macro_recall": round(float(recall_score(y_test, y_pred_maj, average="macro", zero_division=0)), 4),
        "macro_f1": round(float(f1_score(y_test, y_pred_maj, average="macro", zero_division=0)), 4),
        "weighted_f1": round(float(f1_score(y_test, y_pred_maj, average="weighted", zero_division=0)), 4),
        "per_class_f1": {
            cls: round(float(classification_report(y_test, y_pred_maj, output_dict=True, zero_division=0).get(cls, {}).get("f1-score", 0.0)), 4)
            for cls in classes
        },
        "confusion_matrix": confusion_matrix(y_test, y_pred_maj, labels=classes).tolist(),
    }

    with open(metrics_dir / "baseline1_majority_metrics.json", "w", encoding="utf-8") as f:
        json.dump(maj_metrics, f, indent=2)

    logger.info(f"Baseline 1 Metrics: Accuracy={maj_metrics['accuracy']} | Macro-F1={maj_metrics['macro_f1']}")

    # ---------------------------------------------------------
    # BASELINE 2: TF-IDF -> Logistic Regression
    # ---------------------------------------------------------
    logger.info("--- Fitting Baseline 2: TF-IDF -> Logistic Regression ---")
    tfidf_baseline = TFIDFLogisticBaseline(max_features=15000, ngram_range=(1, 2), random_state=42)
    # Strictly fit ONLY on training texts
    tfidf_baseline.fit(X_train, y_train)

    # Save model checkpoint
    tfidf_baseline.save(models_dir / "tfidf_logistic_intent.pkl")

    # Evaluate Baseline 2 on Test
    logger.info("Evaluating Baseline 2 on held-out test split...")
    tfidf_metrics = tfidf_baseline.evaluate(X_test, y_test)
    tfidf_metrics["model_name"] = "Baseline_2_TFIDF_LogisticRegression"

    with open(metrics_dir / "baseline2_tfidf_logistic_metrics.json", "w", encoding="utf-8") as f:
        json.dump(tfidf_metrics, f, indent=2)

    logger.info(f"Baseline 2 Metrics: Accuracy={tfidf_metrics['accuracy']} | Macro-F1={tfidf_metrics['macro_f1']}")


if __name__ == "__main__":
    main()
