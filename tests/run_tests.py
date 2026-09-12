"""Python unittest-based test runner for the test suite."""
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tests.test_agent import (
    test_schema_serialization,
    test_majority_baseline,
    test_trivial_escalation_strategy,
    test_tfidf_logistic_baseline_fit_and_eval,
    test_grounded_generator_safety_and_length,
    test_agent_end_to_end,
)
from tests.test_metrics import test_calculate_metrics_perfect_score, test_calculate_metrics_partial_score
from tests.test_data_leakage import test_zero_leakage_split

def run_all():
    tests = [
        ("test_calculate_metrics_perfect_score", test_calculate_metrics_perfect_score),
        ("test_calculate_metrics_partial_score", test_calculate_metrics_partial_score),
        ("test_zero_leakage_split", test_zero_leakage_split),
        ("test_schema_serialization", test_schema_serialization),
        ("test_majority_baseline", test_majority_baseline),
        ("test_trivial_escalation_strategy", test_trivial_escalation_strategy),
        ("test_tfidf_logistic_baseline_fit_and_eval", test_tfidf_logistic_baseline_fit_and_eval),
        ("test_grounded_generator_safety_and_length", test_grounded_generator_safety_and_length),
        ("test_agent_end_to_end", test_agent_end_to_end),
    ]

    print(f"Running {len(tests)} test cases...")
    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            raise e

    print(f"\nAll {passed}/{len(tests)} tests passed successfully!")

if __name__ == "__main__":
    run_all()
