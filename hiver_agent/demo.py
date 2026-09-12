"""CLI Demo for Hiver Customer Support Agent.

Usage:
    python -m hiver_agent.demo --message "My battery drops from 80% to 20% in 15 minutes"
    python -m hiver_agent.demo --interactive
"""
import argparse
import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hiver_agent.agent import HiverAgent

# Force utf-8 encoding for standard output
sys.stdout.reconfigure(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Hiver Agent CLI Demo for AppleSupport")
    parser.add_argument("--message", type=str, help="Customer support message to evaluate")
    parser.add_argument("--interactive", action="store_true", help="Launch interactive chat session")
    parser.add_argument("--json", action="store_true", help="Output raw JSON format only")
    args = parser.parse_args()

    # Initialize agent
    print("Initializing Hiver Agent (loading/training models on training data)...", file=sys.stderr)
    agent = HiverAgent.load_or_train()

    if args.message:
        decision = agent.respond(args.message)
        if args.json:
            print(decision.model_dump_json(indent=2))
        else:
            print("\n" + "=" * 60)
            print("HIVER AGENT DECISION REPORT")
            print("=" * 60)
            print(f"Customer Message    : {args.message}")
            print(f"Predicted Intent    : {decision.intent} (Confidence: {decision.intent_confidence:.2%})")
            print(f"Auto-Handle Status  : {'[AUTO-HANDLE]' if decision.auto_handle else '[ESCALATE TO HUMAN AGENT]'}")
            if not decision.auto_handle:
                print(f"Escalation Reason   : {decision.escalation_reason}")
                print(f"Risk Flags          : {', '.join(decision.risk_flags)}")
            print(f"Draft Reply (<280)  : {decision.draft_reply}")
            print("-" * 60)
            print("Top Retrieved Historical Evidence:")
            for i, ev in enumerate(decision.retrieved_evidence, 1):
                print(f"  [{i}] (Sim: {ev.similarity_score:.3f}) Customer : {ev.customer_query[:70]}...")
                print(f"      Official Reply: {ev.historical_response[:80]}...")
            print("=" * 60 + "\n")
            print("Structured Output (Pydantic JSON):")
            print(decision.model_dump_json(indent=2))
            
    elif args.interactive:
        print("\n=== Hiver Agent Interactive Console (type 'exit' to quit) ===")
        while True:
            try:
                msg = input("\nEnter Customer Tweet: ").strip()
                if not msg or msg.lower() in ["exit", "quit"]:
                    break
                decision = agent.respond(msg)
                print(f"\n[Intent]    : {decision.intent} ({decision.intent_confidence:.2%})")
                print(f"[Action]    : {'AUTO-REPLY' if decision.auto_handle else 'ESCALATE'}")
                if not decision.auto_handle:
                    print(f"[Reason]    : {decision.escalation_reason}")
                print(f"[Draft (<280)]: {decision.draft_reply}\n")
            except (KeyboardInterrupt, EOFError):
                break
    else:
        # Default sample run
        sample = "My phone died while updating to iOS 11 and now it won't turn back on!"
        print(f"No --message provided. Running on sample query:\n'{sample}'\n")
        decision = agent.respond(sample)
        print(decision.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
