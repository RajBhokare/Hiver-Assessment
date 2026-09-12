"""Deterministic text preprocessing and normalization."""
import re
from typing import List, Union


class TextPreprocessor:
    """Standardizes input texts for NLP / classification pipelines without data leakage."""

    def __init__(self, lower: bool = True, strip_html: bool = True, remove_extra_whitespace: bool = True):
        self.lower = lower
        self.strip_html = strip_html
        self.remove_extra_whitespace = remove_extra_whitespace

    def clean_text(self, text: Union[str, float, None]) -> str:
        if text is None or not isinstance(text, str):
            return ""

        cleaned = text
        if self.strip_html:
            cleaned = re.sub(r"<[^>]+>", " ", cleaned)
        if self.lower:
            cleaned = cleaned.lower()
        if self.remove_extra_whitespace:
            cleaned = re.sub(r"\s+", " ", cleaned).strip()

        return cleaned

    def transform(self, texts: List[str]) -> List[str]:
        return [self.clean_text(t) for t in texts]
