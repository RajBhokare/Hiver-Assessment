"""Interactive Human Annotation CLI for the 200 Golden Evaluation Set Examples.

Usage:
    python scripts/annotate_golden.py
"""
import json
import sys
from pathlib import Path

# Force UTF-8 standard output
sys.stdout.reconfigure(encoding="utf-8")

INTENTS = [
    ("1", "ios_update_issue", "OS upgrade errors, update verification failure, bootloops"),
    ("2", "app_performance_crash", "App crashing, keyboard typing lag, UI freezing, sluggishness"),
    ("3", "battery_power_charging", "Rapid drain, percentage jumping, charging port fault, overheating"),
    ("4", "apple_id_account_security", "Password reset, 2FA code missing, locked account, security questions"),
    ("5", "screen_display_touch", "Display lines, black screen, touch digitizer unresponsive"),
    ("6", "general_complaint_feedback", "Sarcasm, non-technical venting, switching threats, brand sentiment"),
    ("7", "network_connectivity", "Wi-Fi dropping, Bluetooth pairing failure, 'No Service' cellular"),
    ("8", "icloud_storage_backup", "iCloud sync failure, 'Storage Almost Full' warning, photo backup"),
    ("9", "store_billing_subscription", "In-app charges, subscription cancellation, refund requests"),
    ("10", "audio_call_accessory", "Low call volume, mic failure, AirPods disconnection, crackling"),
    ("11", "hardware_repair_store_service", "Genius Bar booking, cracked glass repair quote, AppleCare warranty"),
]

INTENT_MAP = {k: name for k, name, _ in INTENTS}


def main():
    unlabelled_path = Path("data/golden/golden_unlabelled.jsonl")
    labelled_path = Path("data/golden/golden_labelled.jsonl")

    if not unlabelled_path.exists():
        print(f"Error: {unlabelled_path} not found!")
        return

    # Load unlabelled
    with open(unlabelled_path, "r", encoding="utf-8") as f:
        unlabelled_records = [json.loads(line) for line in f if line.strip()]

    # Load existing labelled if resuming
    labelled_dict = {}
    if labelled_path.exists():
        with open(labelled_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    labelled_dict[item["id"]] = item

    print("=" * 70)
    print("  HIVER GOLDEN EVALUATION SET — HUMAN ANNOTATOR INTERFACE")
    print("=" * 70)
    print(f"Total instances to annotate: {len(unlabelled_records)}")
    print(f"Already completed: {len(labelled_dict)} / {len(unlabelled_records)}")
    print("Type 'q' or 'quit' at any prompt to save and exit.")
    print("=" * 70 + "\n")

    annotator_id = input("Enter your Annotator ID/Initials (e.g. annotator_1): ").strip() or "annotator_1"

    for idx, item in enumerate(unlabelled_records, 1):
        item_id = item["id"]
        if item_id in labelled_dict and labelled_dict[item_id].get("intent") is not None:
            continue

        print(f"\n[{idx}/{len(unlabelled_records)}] Example ID: {item_id} (Tweet ID: {item.get('tweet_id')})")
        print("-" * 70)
        print(f"Customer Tweet:\n\"{item.get('text')}\"")
        print("-" * 70)

        # Show Intent Options
        print("Select Primary Intent:")
        for key, name, desc in INTENTS:
            print(f"  [{key:>2}] {name:32s} - {desc}")

        while True:
            choice = input("\nEnter Intent Number (1-11) or 'q': ").strip()
            if choice.lower() in ["q", "quit"]:
                print(f"\nProgress saved to {labelled_path}. Completed {len(labelled_dict)} items.")
                return
            if choice in INTENT_MAP:
                selected_intent = INTENT_MAP[choice]
                break
            print("Invalid selection! Please enter a number between 1 and 11.")

        # Escalation
        while True:
            esc_choice = input("Requires Human Escalation? [y/n] (y=Mandatory Escalation / n=Auto-handle): ").strip().lower()
            if esc_choice in ["q", "quit"]:
                print(f"\nProgress saved to {labelled_path}. Completed {len(labelled_dict)} items.")
                return
            if esc_choice in ["y", "yes", "true", "1"]:
                requires_escalation = True
                break
            elif esc_choice in ["n", "no", "false", "0"]:
                requires_escalation = False
                break
            print("Please enter 'y' or 'n'.")

        notes = input("Ambiguity notes (optional, press Enter to skip): ").strip() or None

        # Record
        labeled_item = dict(item)
        labeled_item["intent"] = selected_intent
        labeled_item["requires_escalation"] = requires_escalation
        labeled_item["ambiguity_notes"] = notes
        labeled_item["annotator_id"] = annotator_id

        labelled_dict[item_id] = labeled_item

        # Autosave immediately to disk
        with open(labelled_path, "w", encoding="utf-8") as f:
            for saved_item in labelled_dict.values():
                f.write(json.dumps(saved_item, ensure_ascii=False) + "\n")

        print(f"-> Saved {item_id}: [{selected_intent}] | Escalation: {requires_escalation}")

    print("\n" + "=" * 70)
    print(f"ALL 200 GOLDEN EXAMPLES ANNOTATED AND SAVED TO: {labelled_path.resolve()}")
    print("=" * 70)


if __name__ == "__main__":
    main()
