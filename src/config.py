"""Configuration loader and schema validation."""
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml
from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    name: str = "hiver-assessment"
    seed: int = 42
    version: str = "0.1.0"


class PathsConfig(BaseModel):
    raw_data_dir: Path = Path("data/raw")
    processed_data_dir: Path = Path("data/processed")
    splits_dir: Path = Path("data/splits")
    models_dir: Path = Path("artifacts/models")
    metrics_dir: Path = Path("artifacts/metrics")
    logs_dir: Path = Path("artifacts/logs")


class DataConfig(BaseModel):
    train_split: float = 0.70
    val_split: float = 0.15
    test_split: float = 0.15
    stratify: bool = True
    text_column: str = "text"
    label_column: str = "label"


class BaselineModelConfig(BaseModel):
    name: str = "heuristic_tfidf_baseline"
    max_features: int = 5000
    ngram_range: List[int] = Field(default_factory=lambda: [1, 2])


class ModelConfig(BaseModel):
    baseline: BaselineModelConfig = Field(default_factory=BaselineModelConfig)


class EvaluationConfig(BaseModel):
    metrics: List[str] = Field(
        default_factory=lambda: [
            "accuracy",
            "precision_macro",
            "recall_macro",
            "f1_macro",
            "f1_weighted",
        ]
    )
    confusion_matrix: bool = True
    per_class_report: bool = True


class AppConfig(BaseModel):
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    model: ModelConfig = Field(default_factory=ModelConfig)
    evaluation: EvaluationConfig = Field(default_factory=EvaluationConfig)


def load_config(config_path: Optional[str] = None) -> AppConfig:
    """Load configuration from a YAML file or return defaults."""
    if config_path is None:
        default_path = Path("configs/default_config.yaml")
        if default_path.exists():
            config_path = str(default_path)

    if config_path and Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            raw_cfg = yaml.safe_load(f) or {}
        return AppConfig(**raw_cfg)

    return AppConfig()
