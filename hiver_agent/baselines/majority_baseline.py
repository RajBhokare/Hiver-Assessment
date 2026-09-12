"""Baseline 1: Trivial Majority-Class Intent Classifier & Documented Trivial Escalation Strategy."""
from collections import Counter
from typing import List, Tuple, Dict, Any, Sequence
import numpy as np


class MajorityIntentBaseline:
    """Trivial baseline that always predicts the most frequent intent in the training set.
    
    Serves as the lower performance floor for accuracy and macro-F1 benchmarking.
    """

    def __init__(self):
        self.majority_intent: str = "ios_update_issue"
        self.majority_probability: float = 1.0
        self.classes_: List[str] = []

    def fit(self, texts: Sequence[str], labels: Sequence[str]) -> "MajorityIntentBaseline":
        """Compute the empirical majority class strictly from training data."""
        counter = Counter(labels)
        self.majority_intent, most_common_count = counter.most_common(1)[0]
        self.majority_probability = most_common_count / max(len(labels), 1)
        self.classes_ = sorted(list(counter.keys()))
        return self

    def predict(self, texts: Sequence[str]) -> List[str]:
        return [self.majority_intent for _ in texts]

    def predict_proba(self, texts: Sequence[str]) -> np.ndarray:
        probas = np.zeros((len(texts), len(self.classes_)))
        if self.majority_intent in self.classes_:
            maj_idx = self.classes_.index(self.majority_intent)
            probas[:, maj_idx] = 1.0
        return probas


class TrivialEscalationStrategy:
    """Documented Trivial Escalation Strategy: Heuristic Keyword & Safety Floor.
    
    DOCUMENTATION & RATIONALE:
    In a high-volume customer support channel like Twitter, a trivial escalation strategy
    must act as a baseline benchmark against more nuanced LLM/ML decision systems.
    
    Two trivial strategies are provided:
    1. 'always_escalate' (Conservative / Zero-Automation Baseline):
       Routes 100% of tickets to human agents (Auto-handle rate = 0%, Precision = 100% safety, Recall = 100% escalations).
    2. 'keyword_rule_trivial' (Simple Rule Baseline):
       Escalates if explicit high-risk keywords (e.g., 'charge', 'refund', 'lawsuit', 'stolen', 'hacked', 'burn', 'dm')
       are present, or if the text exceeds 180 characters (indicating complex, multi-issue problems).
    """

    HIGH_RISK_KEYWORDS = {
        "charge", "charged", "refund", "refunds", "stolen", "hacked", "lockout",
        "locked", "fraud", "lawyer", "lawsuit", "smoke", "swollen", "fire", "exploded",
        "overheating", "genius bar", "repair cost", "dm me", "private message"
    }

    def __init__(self, mode: str = "keyword_rule_trivial"):
        if mode not in ["always_escalate", "never_escalate", "keyword_rule_trivial"]:
            raise ValueError(f"Unknown trivial escalation mode: {mode}")
        self.mode = mode

    def decide(self, text: str) -> Tuple[bool, str, List[str]]:
        """Determine escalation.
        
        Returns:
            (auto_handle: bool, escalation_reason: str, risk_flags: List[str])
        """
        if not isinstance(text, str):
            return False, "Invalid input payload", ["invalid_input"]

        if self.mode == "always_escalate":
            return False, "Trivial baseline policy: escalate all tickets to human agent.", ["policy_always_escalate"]
            
        if self.mode == "never_escalate":
            return True, "", []

        # keyword_rule_trivial
        text_lower = text.lower()
        matched_flags = [kw for kw in self.HIGH_RISK_KEYWORDS if kw in text_lower]
        
        if matched_flags:
            return (
                False,
                f"Trivial safety trigger: matched high-risk keyword(s): {', '.join(matched_flags)}",
                [f"keyword:{kw}" for kw in matched_flags]
            )
            
        if len(text) > 200:
            return (
                False,
                "Trivial complexity trigger: message length exceeds 200 characters.",
                ["length_complexity"]
            )

        return True, "", []
