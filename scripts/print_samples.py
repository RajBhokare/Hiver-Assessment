import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

with open("artifacts/intent_discovery_stats.json", "r", encoding="utf-8") as f:
    stats = json.load(f)

for k, examples in stats["intent_examples"].items():
    print(f"\n==================== INTENT: {k} (Total Matches: {stats['intent_counts'][k]:,}) ====================")
    for i, ex in enumerate(examples[:3], 1):
        print(f"[{i}] Customer: {ex['clean_text']}")
        print(f"    Apple Support: {ex['apple_reply']}")
