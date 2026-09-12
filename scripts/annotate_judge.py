"""Interactive Human Annotation CLI for the 25 Judge Validation Set Examples.

Usage:
    python scripts/annotate_judge.py
"""
import json
import sys
from pathlib import Path

# Force UTF-8 standard output
sys.stdout.reconfigure(encoding="utf-8")


def get_score(prompt: str, min_val: float = 1.0, max_val: float = 5.0) -> float:
    while True:
        val = input(f"{prompt} (1-5, default 5): ").strip()
        if not val:
            return 5.0
        if val.lower() in ["q", "quit"]:
            raise KeyboardInterrupt
        try:
            score = float(val)
            if min_val <= score <= max_val:
                return score
        except ValueError:
            pass
        print(f"Please enter a number between {min_val} and {max_val}.")


def main():
    unlabelled_path = Path("data/judge_validation/judge_annotation_unlabelled.jsonl")
    labelled_path = Path("data/judge_validation/judge_annotation_labelled.jsonl")

    if not unlabelled_path.exists():
        print(f"Error: {unlabelled_path} not found!")
        return

    # Load records
    with open(unlabelled_path, "r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    # Filter strictly to the 25 Validation instances
    validation_records = [r for r in records if r.get("split") == "validation"]

    # Load existing labelled if resuming
    labelled_dict = {}
    if labelled_path.exists():
        with open(labelled_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    labelled_dict[item["id"]] = item

    print("=" * 70)
    print("  HIVER LLM JUDGE VALIDATION — HUMAN GRADING INTERFACE")
    print("=" * 70)
    print(f"Total Validation instances to grade: {len(validation_records)}")
    print(f"Already completed: {len(labelled_dict)} / {len(validation_records)}")
    print("Type 'q' or 'quit' at any prompt to save and exit.")
    print("=" * 70 + "\n")

    annotator_id = input("Enter your Annotator ID (e.g. human_judge_1): ").strip() or "human_judge_1"

    for idx, item in enumerate(validation_records, 1):
        item_id = item["id"]
        if item_id in labelled_dict and labelled_dict[item_id]["human_evaluation"].get("overall_score") is not None:
            continue

        print(f"\n[{idx}/{len(validation_records)}] Validation Example: {item_id}")
        print("=" * 70)
        print(f"Customer Tweet   : \"{item.get('customer_message')}\"")
        print(f"Predicted Intent : {item.get('predicted_intent')} (Confidence: {item.get('intent_confidence'):.2%})")
        print(f"Auto-Handle      : {item.get('auto_handle')}")
        if not item.get('auto_handle'):
            print(f"Escalation Reason: {item.get('escalation_reason')}")
        print(f"Draft Reply      : \"{item.get('draft_reply')}\"")
        print("-" * 70)

        try:
            correctness = get_score("1. Correctness (1=incorrect / 5=perfect troubleshooting)")
            grounding = get_score("2. Grounding (1=hallucinated / 5=supported Apple path)")
            actionability = get_score("3. Actionability (1=vague / 5=clear next steps)")
            brand = get_score("4. Brand Consistency (1=toxic / 5=polite empathetic AppleSupport)")
            safety = get_score("5. Safety (1=fabricated refund/action / 5=zero fabrication)")
            conciseness = get_score("6. Conciseness (1=exceeds 280 chars / 5=compact)")

            overall = round((correctness + grounding + actionability + brand + safety + conciseness) / 6.0, 2)
            print(f"-> Calculated Overall Mean Score: {overall} / 5.0")

            crit_choice = input("Has Critical Error? [y/n] (1=fabricated claim / unsafe auto-handle / toxic): ").strip().lower()
            critical_error = crit_choice in ["y", "yes", "true", "1"]
            crit_reason = input("Critical Error Reason (optional): ").strip() or None if critical_error else None

        except KeyboardInterrupt:
            print(f"\nProgress saved to {labelled_path}. Completed {len(labelled_dict)} items.")
            return

        # Record
        labeled_item = dict(item)
        labeled_item["human_evaluation"] = {
            "correctness": correctness,
            "grounding": grounding,
            "actionability": actionability,
            "brand_consistency": brand,
            "safety": safety,
            "conciseness": conciseness,
            "overall_score": overall,
            "critical_error": critical_error,
            "critical_error_reason": crit_reason,
            "annotator_id": annotator_id,
        }

        labelled_dict[item_id] = labeled_item

        # Autosave immediately to disk
        with open(labelled_path, "w", encoding="utf-8") as f:
            for saved_item in labelled_dict.values():
                f.write(json.dumps(saved_item, ensure_ascii=False) + "\n")

        print(f"-> Saved {item_id}: Overall Score = {overall} | Critical Error = {critical_error}")

    print("\n" + "=" * 70)
    print(f"ALL 25 JUDGE VALIDATION EXAMPLES GRADED AND SAVED TO: {labelled_path.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
