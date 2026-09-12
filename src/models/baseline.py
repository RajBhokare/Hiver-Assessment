"""Lightweight, transparent baseline model (TF-IDF + Logistic Regression)."""
from pathlib import Path
from typing import Any, List, Optional, Union
import pickle
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


class BaselineClassifier:
    """Baseline TF-IDF Logistic Regression classifier."""

    def __init__(self, max_features: int = 5000, ngram_range: tuple = (1, 2), random_state: int = 42):
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.random_state = random_state
        self.pipeline: Pipeline = Pipeline(
            [
                ("tfidf", TfidfVectorizer(max_features=self.max_features, ngram_range=self.ngram_range)),
                (
                    "clf",
                    LogisticRegression(
                        random_state=self.random_state,
                        max_iter=1000,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        self.is_fitted: bool = False

    def fit(self, texts: List[str], labels: List[Any]) -> "BaselineClassifier":
        self.pipeline.fit(texts, labels)
        self.is_fitted = True
        return self

    def predict(self, texts: List[str]) -> List[Any]:
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet. Call fit() before predict().")
        return self.pipeline.predict(texts)

    def predict_proba(self, texts: List[str]):
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet. Call fit() before predict_proba().")
        return self.pipeline.predict_proba(texts)

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(self.pipeline, f)

    def load(self, path: Union[str, Path]) -> "BaselineClassifier":
        path = Path(path)
        with open(path, "rb") as f:
            self.pipeline = pickle.load(f)
        self.is_fitted = True
        return self
