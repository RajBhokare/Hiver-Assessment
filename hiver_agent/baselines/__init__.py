"""Baseline classification models and escalation benchmarks."""
from hiver_agent.baselines.majority_baseline import MajorityIntentBaseline, TrivialEscalationStrategy
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline

__all__ = ["MajorityIntentBaseline", "TrivialEscalationStrategy", "TFIDFLogisticBaseline"]
