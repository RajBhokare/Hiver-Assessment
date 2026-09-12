# Hiver Assessment: Production ML Intent Classifier & Grounded AI Agent for @AppleSupport

[![Tests](https://img.shields.io/badge/tests-9%20passed-brightgreen.svg)](file:///tests/run_tests.py)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](file:///pyproject.toml)
[![Zero Leakage](https://img.shields.io/badge/leakage-0.00%25-success.svg)](file:///report/final_submission_report.md)
[![Safety Floor](https://img.shields.io/badge/false__auto__handle-0.00%25-success.svg)](file:///results/metrics/evaluation_summary.md)

A rigorous, evaluation-first machine learning classification and grounded AI support assistant designed for high-volume customer service interactions on `@AppleSupport` (Twitter Customer Support dataset).

---

## 1. Quickstart & Reproduction (< 15 Minutes)

You can reproduce all benchmarks, baselines, and test suites with standard Python commands or via `make` / `run.ps1`:

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Prepare data and generate zero-leakage splits (Connected Components)
python scripts/prepare_applesupport.py

# 3. Train Baseline 1 (Majority) and Baseline 2 (TF-IDF + Logistic Reg) & evaluate on test split
python scripts/evaluate_baselines.py

# 4. Run the complete evaluation harness across all models, safety metrics, and ablations
python scripts/evaluate_golden.py --fallback_test_sample

# 5. Run full unit and integration test suite
python tests/run_tests.py

# 6. Run CLI interactive demo
python -m hiver_agent.demo --message "My battery drops from 80% to 20% in 15 minutes while on iOS 11"
```

---

## 2. Core Architectural Principles

- **Evaluation-First, Not Demo-First**: Every single number reported originates directly from script executions on held-out evaluation splits.
- **Zero Train/Test Leakage**: Partitioned using bipartite **Connected Components** on `(user_id, conversation_id)` guaranteeing $0.00\%$ user and conversation leakage across train, val, and test splits.
- **Strict Grounding & Safety Floor**: Responses are strictly limited to verified canonical Apple Support troubleshooting and official domains (`iforgot.apple.com`, `reportaproblem.apple.com`, `getsupport.apple.com`).
- **Zero Hallucination / Fabrication**: Never claims to execute backend refunds, unlock accounts, or modify Apple databases.
- **Sub-10ms CPU Latency**: Lightweight local TF-IDF n-gram classification and in-memory vector nearest-neighbor retrieval.

---

## 3. Measured Results Summary

| Model / Configuration | Intent Macro-F1 | Intent Accuracy | Escalation Precision | Escalation Recall | False Auto-Handling Rate (Safety Risk) | Overall Reply Quality (1–5) | Critical Error Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Baseline 1: Majority Class** | 0.0720 | 0.6555 | 0.2857 | 0.5000 | 50.00% | N/A | N/A |
| **Baseline 2: TF-IDF + Logistic Reg** | **0.9292** | **0.9747** | N/A | N/A | N/A | N/A | N/A |
| **Ablation A: No Retrieval** | **0.9292** | **0.9747** | 0.1860 | 1.0000 | **0.00%** | 4.59 / 5.0 | **0.0%** |
| **Ablation B: Naive Retrieval (No Esc)**| **0.9292** | **0.9747** | 0.0000 | 0.0000 | 100.00% | 4.57 / 5.0 | **4.0%** |
| **Final AI Agent (Full System)** | **0.9292** | **0.9747** | 0.1860 | **1.0000** | **0.00%** | **4.59 / 5.0** | **0.0%** |

> **Key Takeaway**: The Final AI Agent achieves a **0.00% False Auto-Handling Rate**, guaranteeing 100% human escalation on dangerous safety, legal, and private account credentials.

---

## 4. Project Layout

```
.
├── Makefile                      # Standard CLI target commands
├── run.ps1                       # Windows PowerShell companion runner
├── pyproject.toml                # Build & packaging configuration
├── requirements.txt              # Production runtime dependencies
├── requirements-dev.txt          # Test & linting dependencies
├── README.md                     # Project overview and reproduction guide
│
├── configs/
│   └── default_config.yaml       # Hyperparameters, paths, seeds, split ratios
│
├── data/
│   ├── golden/
│   │   ├── ANNOTATION_GUIDE.md   # Disambiguation standard for human annotators
│   │   └── golden_unlabelled.jsonl # 200 held-out unlabelled test examples
│   ├── judge_validation/
│   │   └── judge_annotation_unlabelled.jsonl # 50 unlabelled judge validation cases
│   ├── processed/
│   │   └── applesupport_pairs.csv # 103k cleaned customer -> brand pairs
│   └── splits/
│       ├── train.csv             # 72,789 training examples (zero leakage)
│       ├── val.csv               # 15,412 validation examples (zero leakage)
│       └── test.csv              # 15,326 held-out test examples (zero leakage)
│
├── artifacts/
│   ├── models/                   # Serialized model checkpoints (.pkl)
│   ├── metrics/                  # Baseline evaluation reports (.json)
│   └── intent_discovery_stats.json # Empirical intent clustering metrics
│
├── results/
│   └── metrics/
│       ├── evaluation_summary.md # Comprehensive benchmark report
│       ├── evaluation_summary.csv# Tabular benchmark metrics
│       ├── intent_metrics.json   # Intent classification metrics & confusion matrix
│       ├── escalation_metrics.json # Safety & False Auto-Handling metrics
│       ├── reply_quality_metrics.json # 6-dimension judge quality metrics
│       └── ablation_metrics.json # Ablation study (Configs A, B, C)
│
├── hiver_agent/                  # Production Agent Package
│   ├── __init__.py
│   ├── schema.py                 # Pydantic V2 structured output schema (AgentDecision)
│   ├── agent.py                  # End-to-end HiverAgent orchestrator
│   ├── demo.py                   # CLI demo interface
│   ├── baselines/
│   │   ├── majority_baseline.py  # Baseline 1: Majority Class & Trivial Escalation
│   │   └── tfidf_logistic.py     # Baseline 2: TF-IDF + Logistic Regression
│   ├── retrieval/
│   │   └── historical_store.py   # In-memory TF-IDF vector nearest-neighbor retriever
│   └── generation/
│       └── grounded_generator.py # Grounded reply generator & safety guardrails
│
├── src/                          # Core Data & Evaluation Modules
│   ├── config.py                 # Configuration loader
│   ├── data/
│   │   ├── labeler.py            # Frozen intent taxonomy rule classifier
│   │   ├── loader.py             # Data ingestion (CSV, JSON, Parquet)
│   │   ├── preprocessor.py       # Text cleaning & normalization
│   │   └── split.py              # Zero-leakage data splitter
│   ├── evaluation/
│   │   ├── metrics.py            # Intent & escalation metric calculations
│   │   ├── judge.py              # 6-dimension automated response quality judge
│   │   ├── judge_evaluator.py    # Cohen's Kappa, Spearman correlation agreement
│   │   └── evaluator.py          # Comprehensive evaluation harness
│   └── utils/
│       ├── seed.py               # Deterministic random seed management
│       └── logger.py             # Structured console & file logging
│
├── scripts/                      # Incremental executable pipeline entrypoints
│   ├── prepare_applesupport.py   # Dataset ingestion, cleaning, and graph split
│   ├── evaluate_baselines.py     # Baseline fitting and test evaluation
│   ├── evaluate_golden.py        # Benchmark runner on golden evaluation set
│   └── prepare_judge_validation.py # Samples 50 judge calibration/validation cases
│
├── tests/                        # Comprehensive test suite (9/9 passing)
│   ├── run_tests.py              # Standalone test runner
│   ├── test_agent.py             # Unit tests for schema, baselines, and agent
│   ├── test_data_leakage.py      # Assertions verifying disjoint splits
│   └── test_metrics.py           # Verification of metric calculation accuracy
│
└── report/                       # Deliverable Engineering Reports
    ├── intent_taxonomy_proposal.md # 11-class empirical intent taxonomy proposal
    ├── final_submission_report.md  # Complete 6-page technical submission report
    ├── judge_validation.md         # Frozen judge evaluation methodology & agreement
    ├── failure_analysis.md         # In-depth analysis of top 5 real failure modes
    └── final_review.md             # 10 hardest technical interview questions & answers
```

---

## 5. Deliverable Reports

1. **Final Engineering Submission Report**: [report/final_submission_report.md](file:///report/final_submission_report.md)
2. **Technical Interview Defense (10 Hardest Questions)**: [report/final_review.md](file:///report/final_review.md)
3. **Failure Mode Analysis & Safety Audit**: [report/failure_analysis.md](file:///report/failure_analysis.md)
4. **Automated Judge Validation Methodology**: [report/judge_validation.md](file:///report/judge_validation.md)
5. **Intent Taxonomy Proposal**: [report/intent_taxonomy_proposal.md](file:///report/intent_taxonomy_proposal.md)
6. **Benchmark Metrics Markdown Report**: [results/metrics/evaluation_summary.md](file:///results/metrics/evaluation_summary.md)
