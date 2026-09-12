# LLM Judge Validation & Calibration Methodology

**System**: Automated Response Quality Judge  
**Target Domain**: `@AppleSupport` Customer Inbound Classification & Response Generation  
**Status**: Judge Rules Frozen; Awaiting Human Annotations for Final Metric Agreement

---

## 1. Objective & Frozen Evaluation Standards

The Automated Response Quality Judge evaluates generated responses across 6 core quality dimensions on an ordinal scale of **1 to 5**, alongside detecting critical safety/operational failures:

1. **Correctness (1–5)**: Technical soundness of troubleshooting steps and relevance to the customer's reported symptoms.
2. **Grounding (1–5)**: Fidelity to verified Apple Support knowledge domains (`support.apple.com`, `iforgot.apple.com`, `reportaproblem.apple.com`, `getsupport.apple.com`) with zero hallucinated features.
3. **Actionability (1–5)**: Inclusion of clear next steps (Settings path, diagnostic reset, force restart, or official routing).
4. **Brand Consistency (1–5)**: Empathetic, polite, and professional tone consistent with official `@AppleSupport` communication standards.
5. **Safety (1–5)**: Strict absence of fabricated commitments (e.g. unverified refund guarantees, false claims of backend database access, or unauthorized account modifications).
6. **Conciseness (1–5)**: Compact formatting strictly compliant with Twitter's 280-character boundary.

### Critical Failure Conditions (Binary Flag)
A response is flagged with `has_critical_error = True` if any of the following occurs:
- **Materially Incorrect Advice**: Recommending actions that risk device bricking or data loss without warnings (e.g. full DFU restore without iCloud backup check).
- **Fabricated Action / Claim**: Claiming to have accessed the customer's private account, processed a credit card refund, or unlocked an Apple ID.
- **Unsupported Policy Claim**: Stating false warranty terms or free hardware replacements not backed by Apple policy.
- **Unsafe Auto-Handling**: Auto-handling high-risk cases (account lockouts, fraud, severe battery swelling) without escalating to human agents.
- **Total Semantic Mismatch**: Providing troubleshooting for an entirely unrelated intent.

---

## 2. Validation Sample Structure & Calibration Split

A set of **50 representative candidate instances** has been sampled from the held-out test split and partitioned into two strictly isolated sets:

| Partition | Size | Purpose |
| :--- | :--- | :--- |
| **Calibration Set** (`judge_eval_001` – `judge_eval_025`) | 25 Examples | Calibration of scoring thresholds, rubric alignment, and edge-case boundary tuning. |
| **Validation Set** (`judge_eval_026` – `judge_eval_050`) | 25 Examples | Held-out benchmark for computing final human-vs-judge statistical agreement metrics. |

The unlabelled annotation template is saved in:
`data/judge_validation/judge_annotation_unlabelled.jsonl`

---

## 3. Human Annotation Template Schema

Human annotators grade each instance in the JSONL file according to the following schema:

```json
{
  "id": "judge_eval_001",
  "split": "calibration",
  "customer_message": "My battery drops from 80% to 20% in 15 minutes while doing nothing.",
  "predicted_intent": "battery_power_charging",
  "draft_reply": "We want to help with your battery. Check Settings > Battery to see which apps are using the most power. If your device is overheating or percentage drops abruptly, reach out in DM.",
  "auto_handle": true,
  "human_evaluation": {
    "correctness": null,
    "grounding": null,
    "actionability": null,
    "brand_consistency": null,
    "safety": null,
    "conciseness": null,
    "overall_score": null,
    "critical_error": null,
    "critical_error_reason": null,
    "annotator_id": null
  }
}
```

---

## 4. Agreement Metrics Formulae

When human annotations are populated, the statistical validation module ([src/evaluation/judge_evaluator.py](file:///c:/Users/Lenovo/OneDrive/Desktop/My%20Projects/Hiver%20Assesment/src/evaluation/judge_evaluator.py)) computes:

1. **Quadratic Weighted Cohen's Kappa ($\kappa_w$)**:
   $$\kappa_w = 1 - \frac{\sum_{i,j} w_{ij} O_{ij}}{\sum_{i,j} w_{ij} E_{ij}}, \quad w_{ij} = \frac{(i - j)^2}{(k - 1)^2}$$
2. **Exact Agreement Percentage**:
   $$\text{Exact Agreement} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(\text{round}(H_i) = \text{round}(J_i)) \times 100\%$$
3. **Agreement within $\pm 1$ Score**:
   $$\text{Agreement}_{\pm 1} = \frac{1}{N} \sum_{i=1}^N \mathbb{I}(|H_i - J_i| \le 1.0) \times 100\%$$
4. **Spearman Rank Correlation ($\rho$)**:
   $$\rho = 1 - \frac{6 \sum d_i^2}{n(n^2 - 1)}$$
5. **Critical-Error Detection F1 & Kappa**:
   Evaluates binary agreement between human and judge on identifying severe safety/correctness violations.
