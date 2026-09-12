# Benchmark Evaluation Summary & Safety Audit

**Evaluation Split**: Held-out Evaluation Set

## 1. Executive Summary Table

| Category | Model / Configuration | Primary Metric | Primary Score | Secondary Metric | Secondary Score | Safety / Error Rate |
| --- | --- | --- | --- | --- | --- | --- |
| Intent Classification | majority_baseline | Macro F1 | 0.0706 | Accuracy | 0.635 | N/A |
| Intent Classification | tfidf_logistic_baseline | Macro F1 | 0.9816 | Accuracy | 0.98 | N/A |
| Intent Classification | final_agent | Macro F1 | 0.9816 | Accuracy | 0.98 | N/A |
| Escalation & Safety | trivial_escalation_strategy | Escalation F1 | 0.3636 | Escalation Precision | 0.2857 | False Auto-Handling Rate: 50.0% |
| Escalation & Safety | final_agent_escalation_policy | Escalation F1 | 0.3077 | Escalation Precision | 0.1818 | False Auto-Handling Rate: 0.0% |
| Reply Quality & Ablation | Ablation_A_No_Retrieval | Overall Mean Score (1-5) | 4.591 | % High Quality (>=4.0) | 100.0 | Critical Error Rate: 0.0% |
| Reply Quality & Ablation | Ablation_B_With_Retrieval_No_Escalation | Overall Mean Score (1-5) | 4.571 | % High Quality (>=4.0) | 96.0 | Critical Error Rate: 4.0% |
| Reply Quality & Ablation | Ablation_C_Full_Agent | Overall Mean Score (1-5) | 4.591 | % High Quality (>=4.0) | 100.0 | Critical Error Rate: 0.0% |


---

## 2. Intent Classification Benchmark

| Model | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **majority_baseline** | 0.6350 | 0.0577 | 0.0909 | 0.0706 | 0.4932 |
| **tfidf_logistic_baseline** | 0.9800 | 0.9697 | 0.9971 | 0.9816 | 0.9805 |
| **final_agent** | 0.9800 | 0.9697 | 0.9971 | 0.9816 | 0.9805 |


---

## 3. Escalation & Safety Metrics (False Auto-Handling Rate)

| Strategy / Model | Precision | Recall | F1 | False Auto-Handling Rate (Safety Risk) | False Escalation Rate |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **trivial_escalation_strategy** | 0.2857 | 0.5000 | 0.3636 | **50.00%** | 5.21% |
| **final_agent_escalation_policy** | 0.1818 | 1.0000 | 0.3077 | **0.00%** | 18.75% |


---

## 4. Reply Quality & Ablation Study

| Configuration | Correctness | Grounding | Actionability | Brand Consistency | Safety | Conciseness | Overall Mean (1-5) | % >= 4.0 | Critical Error Rate |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Ablation_A_No_Retrieval** | 4.75 | 5.00 | 3.44 | 4.36 | 5.00 | 5.00 | **4.59** | 100.0% | **0.0%** |
| **Ablation_B_With_Retrieval_No_Escalation** | 4.75 | 5.00 | 3.44 | 4.36 | 4.88 | 5.00 | **4.57** | 96.0% | **4.0%** |
| **Ablation_C_Full_Agent** | 4.75 | 5.00 | 3.44 | 4.36 | 5.00 | 5.00 | **4.59** | 100.0% | **0.0%** |

