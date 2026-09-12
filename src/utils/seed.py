"""Reproducibility seed management."""
import os
import random
import numpy as np


def set_seed(seed: int = 42) -> None:
    """Set random seeds across Python standard library and numpy for deterministic runs."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    np.random.seed(seed)
