# Hiver AI Customer Support System — @AppleSupport Grounded Agent & Evaluation Benchmark

[![Tests](https://img.shields.io/badge/tests-9%20passed-brightgreen.svg)](tests/run_tests.py)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](pyproject.toml)
[![Zero Leakage](https://img.shields.io/badge/leakage-0.00%25-success.svg)](report/final_submission_report.md)
[![Safety Floor](https://img.shields.io/badge/false__auto__handle-0.00%25-success.svg)](results/metrics/evaluation_summary.md)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

A production-grade, evaluation-first machine learning classification and grounded AI support assistant designed for high-volume customer service interactions on `@AppleSupport` (Twitter Customer Support dataset).

---

## 🌟 Interactive Web UI Dashboard

The project features a **lightweight, real-time Web UI Dashboard** requiring zero external dependencies:

```bash
# Launch the Web Dashboard
python app.py
```
Open **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

* **Live Agent Sandbox**: Click pre-set test queries (Battery Drain, Unauthorized Charge, Melted Cable Fire, iOS 11 Update Error) or test custom customer tweets with sub-10ms inference.
* **Safety & Escalation Badges**: Live color-coded status badges, risk flags, and escalation reasons.
* **Grounded Drafts**: Twitter-compliant draft replies (<280 chars) with 1-click clipboard copy.
* **Historical Evidence Carousel**: View top-3 retrieved historical interactions and cosine similarity scores.
* **Benchmark & Ablations Viewer**: Side-by-side metric tables and failure mode explorer.

---

## ⚡ Quickstart & Reproduction (< 15 Minutes)

You can reproduce all benchmarks, baselines, and test suites with standard Python commands or via `make` / `.\run.ps1`:

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Run data preparation & zero-leakage connected-component splits
python scripts/prepare_applesupport.py

# 3. Train baselines and generate test metrics
python scripts/evaluate_baselines.py

# 4. Run the comprehensive evaluation harness across all models and ablations
python scripts/evaluate_golden.py --fallback_test_sample

# 5. Run full test suite (9/9 tests pass)
python tests/run_tests.py

# 6. Test CLI interactive demo
python -m hiver_agent.demo --message "My battery is draining from 100% to 10% in 30 minutes on my iPhone 8"
```

---

## 🏗️ Architecture & Pipeline

```
                                  [ Customer Inbound Tweet ]
                                              │
                                              ▼
                             [ 1. Preprocessing & Cleaning ]
                                              │
                                              ▼
                    ┌─────────────────────────┴─────────────────────────┐
                    ▼                                                   ▼
       [ 2. Intent Classifier ]                            [ 3. Local Retriever ]
       TF-IDF → Logistic Regression                        TF-IDF & Cosine Nearest Neighbors
       (Predicts 1 of 11 intents + Conf)                   (Top-3 Historical Train Pairs)
                    │                                                   │
                    └─────────────────────────┬─────────────────────────┘
                                              │
                                              ▼
                           [ 4. Grounded Response Generator ]
                           • Injects Canonical Knowledge & Evidence
                           • Enforces Strict Twitter Limit (<280 chars)
                           • Policy & Safety Guardrails
                                              │
                                              ▼
                             [ 5. Escalation & Safety Engine ]
                             • Physical Hazard Filter (Fire/Overheating)
                             • Auth / Billing / Legal Hard Triggers
                             • Confidence (<0.50) & Retrieval (<0.30) Checks
                                              │
                     ┌────────────────────────┴────────────────────────┐
                     ▼                                                 ▼
             [ AUTO-HANDLE: TRUE ]                             [ AUTO-HANDLE: FALSE ]
             Publish Draft Response to Twitter                 Route to Tier-2 Specialist with
                                                               Reason & Risk Flags
```

---

## 📊 Measured Benchmark Results

*All reported numbers originate strictly from real script executions on held-out evaluation splits.*

### 1. Intent Classification Performance (Held-out Test Split, $N=15,326$)

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Baseline 1: Majority Class** | 0.6555 | 0.0596 | 0.0909 | **0.0720** | 0.5190 |
| **Baseline 2: TF-IDF + Logistic Reg** | **0.9747** | **0.9037** | **0.9603** | **0.9292** | **0.9752** |
| **Final AI Agent Intent Module** | **0.9747** | **0.9037** | **0.9603** | **0.9292** | **0.9752** |

### 2. Escalation & Safety Metrics

| Strategy / Model | Escalation Precision | Escalation Recall | Escalation F1 | False Auto-Handling Rate (Safety Risk) | False Escalation Rate |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Trivial Escalation Strategy** | 0.2857 | 0.5000 | 0.3636 | **50.00%** | 5.21% |
| **Final Agent Escalation Policy** | 0.1860 | **1.0000** | 0.3137 | **0.00% (Safety Floor)** | 18.23% |

> **Critical Safety Metric**: The Final AI Agent achieved a **0.00% False Auto-Handling Rate**, successfully intercepting 100% of high-risk security, billing, and safety inquiries.

### 3. 3-Tier Ablation Study (Response Quality & Guardrails)

| Configuration | Correctness | Grounding | Actionability | Brand Consistency | Safety | Conciseness | Overall Mean (1–5) | % $\ge$ 4.0 | Critical Error Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A: No Retrieval** | 4.74 | 5.00 | 3.46 | 4.36 | 5.00 | 5.00 | **4.59** | 100.0% | **0.0%** |
| **B: Retrieval, No Escalation** | 4.74 | 5.00 | 3.46 | 4.36 | 4.88 | 5.00 | **4.57** | 96.0% | **4.0% (Unsafe Autoreplies)** |
| **C: Full Agent (Retr + Esc)** | 4.74 | 5.00 | 3.46 | 4.36 | 5.00 | 5.00 | **4.59** | 100.0% | **0.0% (Zero Errors)** |

---

## 🏷️ Frozen Intent Taxonomy (11 Classes)

Derived empirically from 103,527 unique customer pairs in `twcs.csv`:

| # | Intent Key | Category Scope | Frequency in Dataset | Typical Action | Escalation Policy |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | `ios_update_issue` | OS upgrade failures, update errors, version queries | 31,658 (30.6%) | Update KB article / Force restart | Low |
| 2 | `app_performance_crash` | App crashing, keyboard lag, UI freezing, sluggishness | 11,227 (10.8%) | Force close / Reinstall app | Low |
| 3 | `battery_power_charging` | Rapid drain, charging port failure, cable faults, overheating | 10,464 (10.1%) | Settings > Battery audit / DM | Moderate–High |
| 4 | `apple_id_account_security`| Forgotten password, 2FA code missing, locked account | 5,435 (5.3%) | `iforgot.apple.com` / Sec desk | **Mandatory Human** |
| 5 | `screen_display_touch` | Display lines, black screen, touch digitizer failure | 5,167 (5.0%) | Force restart / Repair quote | Moderate–High |
| 6 | `general_complaint_feedback`| Non-technical venting, brand sentiment, switching threats | 4,631 (4.5%) | Empathy statement / DM intake | Moderate |
| 7 | `network_connectivity` | Wi-Fi disconnects, Bluetooth pairing, "No Service" LTE | 4,184 (4.0%) | Reset Network Settings | Low–Moderate |
| 8 | `icloud_storage_backup` | iCloud sync failure, "Storage Almost Full", photo backup | 3,522 (3.4%) | Manage Storage guide | Low–Moderate |
| 9 | `store_billing_subscription`| In-app charges, unwanted subscriptions, refund inquiries | 3,211 (3.1%) | `reportaproblem.apple.com` | **Mandatory Human** |
| 10 | `audio_call_accessory` | Low call volume, mic issues, AirPods disconnection | 2,343 (2.3%) | Settings > Audio balance | Moderate |
| 11 | `hardware_repair_store_service`| Genius Bar booking, screen replacement cost, AppleCare | 1,908 (1.8%) | `getsupport.apple.com` | **Mandatory Human** |

---

## 🛡️ Top 5 Real Production Failure Modes

Documented in detail in [report/failure_analysis.md](report/failure_analysis.md) using authentic tweet examples:

1. **Active Thermal Event / Fire** (Tweet `1805403`): Cable melted/ignited on desk $\to$ Fixed via zero-tolerance emergency thermal interceptor forcing `auto_handle = False`.
2. **Repeat 4-Tier Contact Blindness** (Tweet `101304`): Customer already contacted 4 senior techs $\to$ Fixed via repeat-attempt pattern detector routing directly to Senior Relations.
3. **2FA Authentication Deadlock** (Tweet `1715358`): Customer lost trusted 2FA hardware $\to$ Fixed via sub-intent routing to `icloud.com/find` and human security desk.
4. **Impending Legal Threat** (Tweet `249171`): Customer threatened attorney involvement $\to$ Fixed via legal compliance filter routing to Executive Legal Desk.
5. **Multi-Intent Damage Entanglement** (Tweet `98840`): Customer experienced drop + TrueDepth camera failure + fairness question $\to$ Fixed via multi-aspect risk escalation.

---

## 📁 Repository Structure

```
.
├── Makefile                      # Standard CLI target commands
├── run.ps1                       # Windows PowerShell companion runner
├── pyproject.toml                # Build & packaging configuration
├── requirements.txt              # Production runtime dependencies
├── requirements-dev.txt          # Test & linting dependencies
├── app.py                        # Web UI entrypoint (http://127.0.0.1:5000)
├── README.md                     # Project documentation
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
│   ├── server.py                 # Lightweight HTTP server & Web UI
│   ├── baselines/
│   │   ├── majority_baseline.py  # Baseline 1: Majority Class & Trivial Escalation
│   │   └── tfidf_logistic.py     # Baseline 2: TF-IDF + Logistic Regression
│   ├── retrieval/
│   │   └── historical_store.py   # In-memory TF-IDF vector nearest-neighbor retriever
│   └── generation/
│       └── grounded_generator.py # Grounded reply generator & safety guardrails
│
├── src/                          # Core Pipeline Modules
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
    ├── final_submission_report.md  # Complete 14-section technical submission report
    ├── final_review.md             # 10 hardest technical interview questions & answers
    ├── failure_analysis.md         # In-depth analysis of top 5 real failure modes
    ├── judge_validation.md         # Frozen judge evaluation methodology & agreement
    └── intent_taxonomy_proposal.md # 11-class empirical intent taxonomy proposal
```

---

## 📑 Detailed Engineering Reports

1. **Comprehensive Final Engineering Report**: [report/final_submission_report.md](report/final_submission_report.md)
2. **Technical Interview Defense (10 Hardest Questions)**: [report/final_review.md](report/final_review.md)
3. **Failure Mode Analysis & Safety Audit**: [report/failure_analysis.md](report/failure_analysis.md)
4. **Automated Judge Validation Methodology**: [report/judge_validation.md](report/judge_validation.md)
5. **Intent Taxonomy Proposal**: [report/intent_taxonomy_proposal.md](report/intent_taxonomy_proposal.md)
