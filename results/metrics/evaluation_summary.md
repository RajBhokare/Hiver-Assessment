# Benchmark Evaluation Summary & Safety Audit

**Evaluation Split**: Held-out Evaluation Set

## 1. Executive Summary Table

| Category | Model / Configuration | Primary Metric | Primary Score | Secondary Metric | Secondary Score | Safety / Error Rate |
| --- | --- | --- | --- | --- | --- | --- |
| Intent Classification | majority_baseline | Macro F1 | 0.051 | Accuracy | 0.39 | N/A |
| Intent Classification | tfidf_logistic_baseline | Macro F1 | 0.9308 | Accuracy | 0.955 | N/A |
| Intent Classification | final_agent | Macro F1 | 0.9308 | Accuracy | 0.955 | N/A |
| Escalation & Safety | trivial_escalation_strategy | Escalation F1 | 0.5385 | Escalation Precision | 0.525 | False Auto-Handling Rate: 44.7% |
| Escalation & Safety | final_agent_escalation_policy | Escalation F1 | 0.605 | Escalation Precision | 0.4444 | False Auto-Handling Rate: 5.3% |
| Reply Quality & Ablation | Ablation_A_No_Retrieval | Overall Mean Score (1-5) | 4.678 | % High Quality (>=4.0) | 100.0 | Critical Error Rate: 0.0% |
| Reply Quality & Ablation | Ablation_B_With_Retrieval_No_Escalation | Overall Mean Score (1-5) | 4.583 | % High Quality (>=4.0) | 81.0 | Critical Error Rate: 19.0% |
| Reply Quality & Ablation | Ablation_C_Full_Agent | Overall Mean Score (1-5) | 4.673 | % High Quality (>=4.0) | 99.0 | Critical Error Rate: 1.0% |


---

## 2. Intent Classification Benchmark

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **majority_baseline** | 0.3900 | 0.0355 | 0.0909 | 0.0510 | 0.2188 |
| **tfidf_logistic_baseline** | 0.9550 | 0.9432 | 0.9338 | 0.9308 | 0.9546 |
| **final_agent** | 0.9550 | 0.9432 | 0.9338 | 0.9308 | 0.9546 |


---

## 3. Escalation & Safety Metrics (False Auto-Handling Rate)

| Strategy / Model | Precision | Recall | F1 | False Auto-Handling Rate (Safety Risk) | False Escalation Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **trivial_escalation_strategy** | 0.5250 | 0.5526 | 0.5385 | **44.74%** | 11.73% |
| **final_agent_escalation_policy** | 0.4444 | 0.9474 | 0.6050 | **5.26%** | 27.78% |


---

## 4. Reply Quality & Ablation Study

| Configuration | Correctness | Grounding | Actionability | Brand Consistency | Safety | Conciseness | Overall Mean (1-5) | % >= 4.0 | Critical Error Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ablation_A_No_Retrieval** | 4.66 | 5.00 | 3.94 | 4.46 | 5.00 | 5.00 | **4.68** | 100.0% | **0.0%** |
| **Ablation_B_With_Retrieval_No_Escalation** | 4.66 | 5.00 | 3.94 | 4.46 | 4.43 | 5.00 | **4.58** | 81.0% | **19.0%** |
| **Ablation_C_Full_Agent** | 4.66 | 5.00 | 3.94 | 4.46 | 4.97 | 5.00 | **4.67** | 99.0% | **1.0%** |

