"""Comprehensive evaluation runner for Baselines, Final AI Agent, and Ablation Suite."""
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union
import json
import pandas as pd
import numpy as np

from hiver_agent.baselines.majority_baseline import MajorityIntentBaseline, TrivialEscalationStrategy
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline
from hiver_agent.retrieval.historical_store import HistoricalResponseRetriever
from hiver_agent.generation.grounded_generator import GroundedResponseGenerator
from hiver_agent.agent import HiverAgent
from src.evaluation.metrics import calculate_intent_metrics, calculate_escalation_metrics
from src.evaluation.judge import ResponseQualityJudge
from src.utils.logger import get_logger

logger = get_logger("evaluation_harness")


class ComprehensiveEvaluator:
    """Evaluates all candidate systems and ablations on a unified evaluation set."""

    def __init__(self, results_dir: Union[str, Path] = "results/metrics"):
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        self.judge = ResponseQualityJudge()

    def run_full_evaluation(
        self,
        eval_records: List[Dict[str, Any]],
        agent: HiverAgent,
        majority_baseline: MajorityIntentBaseline,
        tfidf_baseline: TFIDFLogisticBaseline,
    ) -> Dict[str, Any]:
        """Execute evaluation across Intent Classification, Escalation Safety, Reply Quality, and Ablations."""
        n_samples = len(eval_records)
        logger.info(f"Starting evaluation across {n_samples:,} held-out evaluation instances...")

        # Extract texts, gold labels, and ground truth escalation flags
        queries = [r.get("text", "") or r.get("clean_text", "") for r in eval_records]
        gold_intents = [r.get("intent") for r in eval_records]
        gold_escalates = [r.get("requires_escalation") for r in eval_records]

        has_gold_intents = all(g is not None for g in gold_intents)
        has_gold_escalates = all(e is not None for e in gold_escalates)

        # Get unique classes
        if has_gold_intents:
            classes = sorted(list(set(gold_intents)))
        else:
            classes = sorted(list(tfidf_baseline.pipeline.classes_))

        # -------------------------------------------------------------
        # 1. EVALUATE INTENT CLASSIFICATION
        # -------------------------------------------------------------
        intent_results = {}
        if has_gold_intents:
            logger.info("Computing Intent Classification Metrics...")
            # Majority Baseline
            maj_preds = majority_baseline.predict(queries)
            intent_results["majority_baseline"] = calculate_intent_metrics(gold_intents, maj_preds, classes)

            # TF-IDF Logistic Regression Baseline
            tfidf_preds = tfidf_baseline.predict(queries)
            intent_results["tfidf_logistic_baseline"] = calculate_intent_metrics(gold_intents, tfidf_preds, classes)

            # Final AI Agent (same intent model, verified)
            agent_decisions = [agent.respond(q) for q in queries]
            agent_intents = [d.intent for d in agent_decisions]
            intent_results["final_agent"] = calculate_intent_metrics(gold_intents, agent_intents, classes)

        # -------------------------------------------------------------
        # 2. EVALUATE ESCALATION & SAFETY METRICS
        # -------------------------------------------------------------
        escalation_results = {}
        trivial_strategy = TrivialEscalationStrategy(mode="keyword_rule_trivial")

        # Predictions for escalation: True = Escalate, False = Auto-handle
        maj_escalate_preds = [not trivial_strategy.decide(q)[0] for q in queries]
        agent_decisions = agent_decisions if 'agent_decisions' in locals() else [agent.respond(q) for q in queries]
        agent_escalate_preds = [not d.auto_handle for d in agent_decisions]

        if has_gold_escalates:
            logger.info("Computing Escalation & Safety Metrics (False Auto-Handling Rate)...")
            escalation_results["trivial_escalation_strategy"] = calculate_escalation_metrics(gold_escalates, maj_escalate_preds)
            escalation_results["final_agent_escalation_policy"] = calculate_escalation_metrics(gold_escalates, agent_escalate_preds)

        # -------------------------------------------------------------
        # 3. ABLATION STUDY
        # -------------------------------------------------------------
        logger.info("Running Ablation Experiments (A: No Retrieval, B: No Escalation Policy, C: Full Agent)...")
        # Ablation A: LLM without retrieval
        ablation_a_records = []
        generator_no_retrieval = GroundedResponseGenerator()
        for i, q in enumerate(queries):
            intent, conf = tfidf_baseline.predict_with_confidence(q)
            dec = generator_no_retrieval.process(
                customer_message=q,
                predicted_intent=intent,
                intent_confidence=conf,
                evidence=[],  # Zero retrieval context
            )
            ablation_a_records.append({
                "text": q,
                "predicted_intent": dec.intent,
                "draft_reply": dec.draft_reply,
                "auto_handle": dec.auto_handle,
                "gold_intent": gold_intents[i] if has_gold_intents else None,
                "gold_escalate": gold_escalates[i] if has_gold_escalates else None,
            })

        # Ablation B: LLM + Retrieval (Naive Auto-Handle, No Escalation Filtering)
        ablation_b_records = []
        for i, q in enumerate(queries):
            intent, conf = tfidf_baseline.predict_with_confidence(q)
            ev = agent.retriever.retrieve(q, top_k=3)
            # Naively auto-handle everything without escalation safety triggers
            draft = generator_no_retrieval.generate_draft(q, intent, ev, auto_handle=True)
            ablation_b_records.append({
                "text": q,
                "predicted_intent": intent,
                "draft_reply": draft,
                "auto_handle": True,  # Naive 100% auto-handle
                "gold_intent": gold_intents[i] if has_gold_intents else None,
                "gold_escalate": gold_escalates[i] if has_gold_escalates else None,
            })

        # Ablation C: Full Agent (LLM + Retrieval + Escalation Policy)
        ablation_c_records = []
        for i, (q, dec) in enumerate(zip(queries, agent_decisions)):
            ablation_c_records.append({
                "text": q,
                "predicted_intent": dec.intent,
                "draft_reply": dec.draft_reply,
                "auto_handle": dec.auto_handle,
                "gold_intent": gold_intents[i] if has_gold_intents else None,
                "gold_escalate": gold_escalates[i] if has_gold_escalates else None,
            })

        ablation_results = {
            "Ablation_A_No_Retrieval": self.judge.evaluate_batch(ablation_a_records),
            "Ablation_B_With_Retrieval_No_Escalation": self.judge.evaluate_batch(ablation_b_records),
            "Ablation_C_Full_Agent": self.judge.evaluate_batch(ablation_c_records),
        }

        # -------------------------------------------------------------
        # 4. PERSIST ALL OUTPUT ARTIFACTS
        # -------------------------------------------------------------
        logger.info(f"Writing evaluation metrics to {self.results_dir.resolve()}...")

        # JSON Artifacts
        with open(self.results_dir / "intent_metrics.json", "w", encoding="utf-8") as f:
            json.dump(intent_results, f, indent=2)

        with open(self.results_dir / "escalation_metrics.json", "w", encoding="utf-8") as f:
            json.dump(escalation_results, f, indent=2)

        with open(self.results_dir / "reply_quality_metrics.json", "w", encoding="utf-8") as f:
            json.dump(ablation_results["Ablation_C_Full_Agent"], f, indent=2)

        with open(self.results_dir / "ablation_metrics.json", "w", encoding="utf-8") as f:
            json.dump(ablation_results, f, indent=2)

        # Confusion Matrices JSON
        conf_matrices = {
            name: {
                "classes": res.get("classes", []),
                "matrix": res.get("confusion_matrix", [])
            }
            for name, res in intent_results.items()
        }
        with open(self.results_dir / "confusion_matrices.json", "w", encoding="utf-8") as f:
            json.dump(conf_matrices, f, indent=2)

        # Generate Summary CSV
        summary_rows = []
        # Intent metrics summary
        for model_name, res in intent_results.items():
            summary_rows.append({
                "Category": "Intent Classification",
                "Model / Configuration": model_name,
                "Primary Metric": "Macro F1",
                "Primary Score": res.get("macro_f1"),
                "Secondary Metric": "Accuracy",
                "Secondary Score": res.get("accuracy"),
                "Safety / Error Rate": "N/A",
            })
        # Escalation metrics summary
        for model_name, res in escalation_results.items():
            summary_rows.append({
                "Category": "Escalation & Safety",
                "Model / Configuration": model_name,
                "Primary Metric": "Escalation F1",
                "Primary Score": res.get("f1_score"),
                "Secondary Metric": "Escalation Precision",
                "Secondary Score": res.get("precision"),
                "Safety / Error Rate": f"False Auto-Handling Rate: {res.get('false_auto_handling_rate')*100:.1f}%",
            })
        # Quality & Ablation summary
        for config_name, res in ablation_results.items():
            mean_sc = res.get("mean_scores", {}).get("overall_mean")
            crit_rate = res.get("critical_error_rate_pct")
            summary_rows.append({
                "Category": "Reply Quality & Ablation",
                "Model / Configuration": config_name,
                "Primary Metric": "Overall Mean Score (1-5)",
                "Primary Score": mean_sc,
                "Secondary Metric": "% High Quality (>=4.0)",
                "Secondary Score": res.get("pct_high_quality_ge_4"),
                "Safety / Error Rate": f"Critical Error Rate: {crit_rate:.1f}%",
            })

        df_summary = pd.DataFrame(summary_rows)
        df_summary.to_csv(self.results_dir / "evaluation_summary.csv", index=False)

        # Generate Markdown Summary
        self._write_markdown_summary(intent_results, escalation_results, ablation_results, df_summary)

        return {
            "intent_metrics": intent_results,
            "escalation_metrics": escalation_results,
            "ablation_metrics": ablation_results,
        }

    def _write_markdown_summary(
        self,
        intent_results: Dict[str, Any],
        escalation_results: Dict[str, Any],
        ablation_results: Dict[str, Any],
        df_summary: pd.DataFrame,
    ) -> None:
        """Render comprehensive markdown report."""
        md_path = self.results_dir / "evaluation_summary.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Benchmark Evaluation Summary & Safety Audit\n\n")
            f.write("**Evaluation Split**: Held-out Evaluation Set\n\n")
            f.write("## 1. Executive Summary Table\n\n")
            
            # Format dataframe manually to avoid tabulate dependency
            cols = list(df_summary.columns)
            f.write("| " + " | ".join(cols) + " |\n")
            f.write("| " + " | ".join(["---"] * len(cols)) + " |\n")
            for _, row in df_summary.iterrows():
                f.write("| " + " | ".join(str(row[c]) for c in cols) + " |\n")
                
            f.write("\n\n---\n\n")

            f.write("## 2. Intent Classification Benchmark\n\n")
            f.write("| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for name, res in intent_results.items():
                f.write(
                    f"| **{name}** | {res.get('accuracy', 0):.4f} | {res.get('macro_precision', 0):.4f} | "
                    f"{res.get('macro_recall', 0):.4f} | {res.get('macro_f1', 0):.4f} | {res.get('weighted_f1', 0):.4f} |\n"
                )
            f.write("\n\n---\n\n")

            f.write("## 3. Escalation & Safety Metrics (False Auto-Handling Rate)\n\n")
            f.write("| Strategy / Model | Precision | Recall | F1 | False Auto-Handling Rate (Safety Risk) | False Escalation Rate |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for name, res in escalation_results.items():
                f.write(
                    f"| **{name}** | {res.get('precision', 0):.4f} | {res.get('recall', 0):.4f} | "
                    f"{res.get('f1_score', 0):.4f} | **{res.get('false_auto_handling_rate', 0)*100:.2f}%** | "
                    f"{res.get('false_escalation_rate', 0)*100:.2f}% |\n"
                )
            f.write("\n\n---\n\n")

            f.write("## 4. Reply Quality & Ablation Study\n\n")
            f.write("| Configuration | Correctness | Grounding | Actionability | Brand Consistency | Safety | Conciseness | Overall Mean (1-5) | % >= 4.0 | Critical Error Rate |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n")
            for name, res in ablation_results.items():
                m = res.get("mean_scores", {})
                f.write(
                    f"| **{name}** | {m.get('correctness', 0):.2f} | {m.get('grounding', 0):.2f} | {m.get('actionability', 0):.2f} | "
                    f"{m.get('brand_consistency', 0):.2f} | {m.get('safety', 0):.2f} | {m.get('conciseness', 0):.2f} | "
                    f"**{m.get('overall_mean', 0):.2f}** | {res.get('pct_high_quality_ge_4', 0):.1f}% | **{res.get('critical_error_rate_pct', 0):.1f}%** |\n"
                )
            f.write("\n")
