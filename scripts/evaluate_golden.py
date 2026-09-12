"""Evaluation CLI script to run the complete benchmark suite on the golden evaluation set."""
import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from hiver_agent.agent import HiverAgent
from hiver_agent.baselines.majority_baseline import MajorityIntentBaseline
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline
from src.evaluation.evaluator import ComprehensiveEvaluator
from src.data.labeler import apply_labels
from src.utils.seed import set_seed
from src.utils.logger import get_logger

# Force utf-8 standard output
sys.stdout.reconfigure(encoding="utf-8")
logger = get_logger("evaluate_golden")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Baselines & Final AI Agent on Golden Set")
    parser.add_argument("--golden_path", type=str, default="data/golden/golden_labelled.jsonl", help="Path to labelled golden JSONL")
    parser.add_argument("--results_dir", type=str, default="results/metrics", help="Directory to store evaluation outputs")
    parser.add_argument("--fallback_test_sample", action="store_true", help="Run on deterministic sample of test split if human golden labels are not yet present")
    args = parser.parse_args()

    set_seed(42)
    golden_file = Path(args.golden_path)
    unlabelled_file = Path("data/golden/golden_unlabelled.jsonl")

    # Check for human labelled golden set
    eval_records = []
    if golden_file.exists():
        logger.info(f"Loading labelled golden evaluation set from: {golden_file.resolve()}")
        with open(golden_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    eval_records.append(json.loads(line))
        logger.info(f"Loaded {len(eval_records)} labelled golden examples.")
    elif unlabelled_file.exists() and not args.fallback_test_sample:
        # Check if unlabelled file was edited with labels
        with open(unlabelled_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    eval_records.append(json.loads(line))
        
        # Check if labels are filled
        has_labels = any(r.get("intent") is not None for r in eval_records)
        if not has_labels:
            logger.warning("=" * 60)
            logger.warning("DATA NOTIFICATION: Human Golden Labels Pending!")
            logger.warning(f"File '{unlabelled_file}' contains 200 unlabelled candidate instances (all label fields are null).")
            logger.warning("To evaluate against gold standard human annotations, annotate the file or provide 'data/golden/golden_labelled.jsonl'.")
            logger.warning("To run harness verification on held-out test split, pass '--fallback_test_sample'.")
            logger.warning("=" * 60)
            print("\n[MISSING DATA REPORT] Human annotations in 'data/golden/golden_labelled.jsonl' are required for final human-grounded gold metrics.")
            return
    elif args.fallback_test_sample:
        logger.info("Running harness verification on deterministic held-out test split sample...")
        test_df = pd.read_csv("data/splits/test.csv")
        test_df_labeled = apply_labels(test_df, text_col="clean_customer_text")
        sample_df = test_df_labeled.sample(min(len(test_df_labeled), 200), random_state=42)
        for _, row in sample_df.iterrows():
            eval_records.append({
                "tweet_id": row["tweet_id_customer"],
                "text": row["text_customer"],
                "clean_text": row["clean_customer_text"],
                "intent": row["intent"],
                "requires_escalation": row["intent"] in ["apple_id_account_security", "store_billing_subscription", "hardware_repair_store_service"],
            })
    else:
        logger.error(f"Neither {golden_file} nor {unlabelled_file} found!")
        return

    # Load trained models & agent
    train_path = Path("data/splits/train.csv")
    df_train = pd.read_csv(train_path)
    df_train_labeled = apply_labels(df_train, text_col="clean_customer_text")
    X_train = df_train_labeled["clean_customer_text"].fillna("").tolist()
    y_train = df_train_labeled["intent"].tolist()

    majority_baseline = MajorityIntentBaseline().fit(X_train, y_train)
    agent = HiverAgent.load_or_train()
    tfidf_baseline = agent.classifier

    # Execute full evaluation harness
    evaluator = ComprehensiveEvaluator(results_dir=args.results_dir)
    results = evaluator.run_full_evaluation(
        eval_records=eval_records,
        agent=agent,
        majority_baseline=majority_baseline,
        tfidf_baseline=tfidf_baseline,
    )

    print("\n" + "=" * 60)
    print("EVALUATION HARNESS EXECUTION COMPLETE")
    print(f"Results saved to: {Path(args.results_dir).resolve()}")
    print("=" * 60)
    summary_file = Path(args.results_dir) / "evaluation_summary.md"
    if summary_file.exists():
        with open(summary_file, "r", encoding="utf-8") as f:
            print(f.read())


if __name__ == "__main__":
    main()
