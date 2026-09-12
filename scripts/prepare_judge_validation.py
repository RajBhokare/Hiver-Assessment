"""Generates 50 unlabelled candidate instances for human judge validation (25 calibration, 25 validation)."""
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from hiver_agent.agent import HiverAgent
from src.data.labeler import apply_labels
from src.utils.seed import set_seed
from src.utils.logger import get_logger

sys.stdout.reconfigure(encoding="utf-8")
logger = get_logger("prepare_judge_validation")


def main():
    set_seed(42)
    test_path = Path("data/splits/test.csv")
    if not test_path.exists():
        raise FileNotFoundError("data/splits/test.csv not found!")

    df_test = pd.read_csv(test_path)
    df_test_labeled = apply_labels(df_test, text_col="clean_customer_text")

    # Sample 50 diverse items
    sample_df = df_test_labeled.sample(50, random_state=42)
    agent = HiverAgent.load_or_train()

    records = []
    for idx, (_, row) in enumerate(sample_df.iterrows()):
        split_type = "calibration" if idx < 25 else "validation"
        text = str(row["text_customer"])
        clean_text = str(row["clean_customer_text"])
        gold_intent = str(row["intent"])

        decision = agent.respond(clean_text)

        records.append({
            "id": f"judge_eval_{idx+1:03d}",
            "split": split_type,
            "tweet_id": str(row["tweet_id_customer"]),
            "customer_message": text,
            "clean_customer_message": clean_text,
            "predicted_intent": decision.intent,
            "intent_confidence": decision.intent_confidence,
            "draft_reply": decision.draft_reply,
            "auto_handle": decision.auto_handle,
            "escalation_reason": decision.escalation_reason,
            "risk_flags": decision.risk_flags,
            "top_retrieved_evidence": [
                {
                    "customer_query": ev.customer_query,
                    "historical_response": ev.historical_response,
                    "similarity": ev.similarity_score
                }
                for ev in decision.retrieved_evidence[:2]
            ],
            # Human evaluation template fields left completely unlabelled (null)
            "human_evaluation": {
                "correctness": None,        # 1 to 5
                "grounding": None,          # 1 to 5
                "actionability": None,      # 1 to 5
                "brand_consistency": None,  # 1 to 5
                "safety": None,             # 1 to 5
                "conciseness": None,        # 1 to 5
                "overall_score": None,      # 1 to 5
                "critical_error": None,     # boolean: true / false
                "critical_error_reason": None,
                "annotator_id": None
            }
        })

    out_dir = Path("data/judge_validation")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "judge_annotation_unlabelled.jsonl"

    with open(out_file, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    logger.info(f"Successfully generated 50 unlabelled judge validation instances at: {out_file.resolve()}")
    logger.info(f"Calibration examples: 25 | Validation examples: 25")


if __name__ == "__main__":
    main()
