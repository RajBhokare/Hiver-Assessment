"""Tests ensuring strict zero data leakage between train/val/test splits."""
import pandas as pd
from src.data.split import DataSplitter


def test_zero_leakage_split():
    # Create sample dataframe with unique IDs
    data = {
        "id": list(range(100)),
        "text": [f"Sample query {i}" for i in range(100)],
        "label": ["A" if i % 2 == 0 else "B" for i in range(100)],
    }
    df = pd.DataFrame(data)

    splitter = DataSplitter(train_size=0.70, val_size=0.15, test_size=0.15, seed=42)
    train_df, val_df, test_df = splitter.split(df, stratify_col="label")

    # Assert correct sizes
    assert len(train_df) == 70
    assert len(val_df) == 15
    assert len(test_df) == 15

    # Assert zero overlap across raw IDs
    train_ids = set(train_df["id"])
    val_ids = set(val_df["id"])
    test_ids = set(test_df["id"])

    assert train_ids.isdisjoint(val_ids), "Train and Val IDs must be mutually exclusive"
    assert train_ids.isdisjoint(test_ids), "Train and Test IDs must be mutually exclusive"
    assert val_ids.isdisjoint(test_ids), "Val and Test IDs must be mutually exclusive"
