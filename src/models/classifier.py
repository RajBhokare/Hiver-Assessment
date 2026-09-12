"""Abstract / general classifier interface for candidate models."""
from abc import ABC, abstractmethod
from typing import Any, List


class TextClassifier(ABC):
    """Base interface for all classification models to guarantee consistent API."""

    @abstractmethod
    def fit(self, texts: List[str], labels: List[Any]) -> "TextClassifier":
        pass

    @abstractmethod
    def predict(self, texts: List[str]) -> List[Any]:
        pass

    @abstractmethod
    def predict_proba(self, texts: List[str]) -> Any:
        pass
