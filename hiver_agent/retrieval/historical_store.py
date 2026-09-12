"""Local TF-IDF and Nearest Neighbors retrieval store for historical AppleSupport responses."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
import pickle
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.neighbors import NearestNeighbors
from hiver_agent.schema import RetrievedEvidence


class HistoricalResponseRetriever:
    """Retrieves top-k historical AppleSupport interactions similar to an incoming customer query.
    
    Index is built strictly on the training partition of the dataset.
    """

    def __init__(self, max_features: int = 20000, ngram_range: Tuple[int, int] = (1, 2)):
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            sublinear_tf=True,
            strip_accents="unicode",
        )
        self.nn_index = NearestNeighbors(metric="cosine", algorithm="brute")
        self.corpus_customer: List[str] = []
        self.corpus_apple: List[str] = []
        self.is_indexed: bool = False

    def build_index(
        self,
        customer_texts: List[str],
        apple_responses: List[str],
    ) -> "HistoricalResponseRetriever":
        """Index training corpus of customer queries and their official historical responses."""
        if len(customer_texts) != len(apple_responses):
            raise ValueError("customer_texts and apple_responses must have identical lengths.")

        # Clean empty entries
        valid_pairs = [
            (c, a) for c, a in zip(customer_texts, apple_responses)
            if isinstance(c, str) and isinstance(a, str) and len(c.strip()) > 0 and len(a.strip()) > 0
        ]

        self.corpus_customer = [p[0] for p in valid_pairs]
        self.corpus_apple = [p[1] for p in valid_pairs]

        # Fit TF-IDF matrix on customer queries
        tfidf_matrix = self.vectorizer.fit_transform(self.corpus_customer)
        self.nn_index.fit(tfidf_matrix)
        self.is_indexed = True
        return self

    def retrieve(self, query: str, top_k: int = 3) -> List[RetrievedEvidence]:
        """Retrieve top-k most similar historical examples with similarity score."""
        if not self.is_indexed:
            raise RuntimeError("Index has not been built. Call build_index() or load().")

        if not isinstance(query, str) or not query.strip():
            return []

        query_vec = self.vectorizer.transform([query])
        distances, indices = self.nn_index.kneighbors(query_vec, n_neighbors=min(top_k, len(self.corpus_customer)))

        results: List[RetrievedEvidence] = []
        for dist, idx in zip(distances[0], indices[0]):
            sim_score = max(0.0, 1.0 - float(dist))
            results.append(
                RetrievedEvidence(
                    customer_query=self.corpus_customer[idx],
                    historical_response=self.corpus_apple[idx],
                    similarity_score=round(sim_score, 4),
                )
            )

        return results

    def save(self, path: Union[str, Path]) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump(
                {
                    "vectorizer": self.vectorizer,
                    "nn_index": self.nn_index,
                    "corpus_customer": self.corpus_customer,
                    "corpus_apple": self.corpus_apple,
                    "is_indexed": self.is_indexed,
                },
                f,
            )

    def load(self, path: Union[str, Path]) -> "HistoricalResponseRetriever":
        path = Path(path)
        with open(path, "rb") as f:
            data = pickle.load(f)
            self.vectorizer = data["vectorizer"]
            self.nn_index = data["nn_index"]
            self.corpus_customer = data["corpus_customer"]
            self.corpus_apple = data["corpus_apple"]
            self.is_indexed = data["is_indexed"]
        return self
