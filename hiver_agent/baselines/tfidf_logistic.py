"""Baseline 2: TF-IDF Vectorizer -> Logistic Regression Intent Classifier."""
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union, Any
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix,
)


class TFIDFLogisticBaseline:
    """Standard TF-IDF + Logistic Regression Intent Classifier.
    
    Preprocessing and vocabulary extraction are strictly fit on training data only.
    """

    def __init__(
        self,
        max_features: int = 10000,
        ngram_range: Tuple[int, int] = (1, 2),
        C: float = 1.0,
        random_state: int = 42,
    ):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.C = C
        self.random_state = random_state
        
        self.pipeline = Pipeline(
            [
                (
                    "tfidf",
                    TfidfVectorizer(
                        max_features=self.max_features,
                        ngram_range=self.ngram_range,
                        sublinear_tf=True,
                        strip_accents="unicode",
                    ),
                ),
                (
                    "clf",
                    LogisticRegression(
                        C=self.C,
                        random_state=self.random_state,
                        max_iter=1000,
                        class_weight="balanced",
                        solver="lbfgs",
                    ),
                ),
            ]
        )
        self.is_fitted: bool = False

    def fit(self, texts: Sequence[str], labels: Sequence[str]) -> "TFIDFLogisticBaseline":
        """Fit vectorizer and classifier strictly on training data."""
        self.pipeline.fit(texts, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: Sequence[str]) -> List[str]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predict().")
        return list(self.pipeline.predict(texts))

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted. Call fit() before predict_proba().")
        return self.pipeline.predict_proba(texts)

    def predict_with_confidence(self, text: str) -> Tuple[str, float]:
        """Predict intent and maximum class probability."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted.")
        probas = self.pipeline.predict_proba([text])[0]
        classes = self.pipeline.classes_
        max_idx = int(np.argmax(probas))
        return str(classes[max_idx]), float(probas[max_idx])

    def evaluate(self, texts: Sequence[str], labels: Sequence[str]) -> Dict[str, Any]:
        """Compute evaluation metrics: accuracy, macro precision, recall, F1, per-class F1, confusion matrix."""
        y_true = list(labels)
        y_pred = self.predict(texts)
        classes = sorted(list(set(y_true)))

        acc = float(accuracy_score(y_true, y_pred))
        prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
        rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
        f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))
        f1_weighted = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))
        
        report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
        per_class_f1 = {cls: report[cls]["f1-score"] for cls in classes if cls in report}
        conf_mat = confusion_matrix(y_true, y_pred, labels=classes).tolist()

        return {
            "sample_count": len(y_true),
            "classes": classes,
            "accuracy": round(acc, 4),
            "macro_precision": round(prec_macro, 4),
            "macro_recall": round(rec_macro, 4),
            "macro_f1": round(f1_macro, 4),
            "weighted_f1": round(f1_weighted, 4),
            "per_class_f1": {k: round(v, 4) for k, v in per_class_f1.items()},
            "confusion_matrix": conf_mat,
            "full_classification_report": report,
        }

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.pipeline, f)

    def load(self, path: Union[str, Path]) -> "TFIDFLogisticBaseline":
        path = Path(path)
        with open(path, "rb") as f:
            self.pipeline = pickle.load(f)
        self.is_fitted = True
        return self
