"""Deterministic dataset splitting with zero train/test leakage guarantees."""
from typing import Tuple, Optional
import pandas as pd
from sklearn.model_selection import train_test_split


class DataSplitter:
    """Splits data into train, val, test with strict seed determinism and no data overlap."""

    def __init__(self, train_size: float = 0.70, val_size: float = 0.15, test_size: float = 0.15, seed: int = 42):
        if not abs((train_size + val_size + test_size) - 1.0) < 1e-5:
            raise ValueError(f"Split sizes must sum to 1.0, got: train={train_size}, val={val_size}, test={test_size}")
        self.train_size = train_size
        self.val_size = val_size
        self.test_size = test_size
        self.seed = seed

    def split(
        self, df: pd.DataFrame, stratify_col: Optional[str] = None
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Perform 3-way split deterministically."""
        strat = df[stratify_col] if (stratify_col and stratify_col in df.columns) else None

        # First split: train vs temp (val + test)
        temp_size = self.val_size + self.test_size
        train_df, temp_df = train_test_split(
            df,
            train_size=self.train_size,
            test_size=temp_size,
            random_state=self.seed,
            stratify=strat,
        )

        # Second split: val vs test from temp
        temp_strat = temp_df[stratify_col] if (stratify_col and stratify_col in temp_df.columns) else None
        relative_test_size = self.test_size / temp_size

        val_df, test_df = train_test_split(
            temp_df,
            test_size=relative_test_size,
            random_state=self.seed,
            stratify=temp_strat,
        )

        # Validate no index overlap
        train_idx = set(train_df.index)
        val_idx = set(val_df.index)
        test_idx = set(test_df.index)

        assert train_idx.isdisjoint(val_idx), "Data leakage error: train and val indices overlap!"
        assert train_idx.isdisjoint(test_idx), "Data leakage error: train and test indices overlap!"
        assert val_idx.isdisjoint(test_idx), "Data leakage error: val and test indices overlap!"

        return train_df.reset_index(drop=True), val_df.reset_index(drop=True), test_df.reset_index(drop=True)
