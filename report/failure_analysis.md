# Failure Mode Analysis & Safety Audit

**System**: `@AppleSupport` Customer Intent Classification & Grounded Agent  
**Dataset**: Twitter Customer Support Real Evaluation Set (`twcs.csv`)  
**Date**: September 2026

---

## Executive Summary

To safeguard customer trust, device safety, and operational efficiency, we performed an in-depth failure analysis on real customer interactions from the held-out test split. We prioritized **high-severity safety and legal risks** (e.g. false auto-handling on safety hazards or account lockouts) over purely cosmetic or stylistic variations.

---

## 1. Failure Mode 1: Critical Physical Safety Hazard (Thermal Event / Fire)

* **Real Customer Message** (Tweet ID `1805403`):
  > *"So my iPhone charging cable just melted and started on fire while on my desk. @115858 @AppleSupport"*
* **Expected Result**:
  - `intent`: `battery_power_charging`
  - `auto_handle`: `False` (Mandatory Emergency Escalation)
  - `risk_flags`: `["safety_hardware_hazard"]`
  - `draft_reply`: Immediate safety protocol advising the user to disconnect power safely and routing to priority safety specialists in DM.
* **Actual Naive Baseline Result**:
  - Naive baseline classified as general charging inquiry and attempted to auto-suggest standard battery troubleshooting: *"Check Settings > Battery to see which apps are using power."*
* **Failure Category**: **Unsafe Auto-Handling / Physical Safety Hazard**
* **Severity**: **CRITICAL (High Safety & Liability Risk)**
* **Why it Failed**:
  - Pure keyword matching on `"charging cable"` without semantic hazard prioritization treated the message as routine accessory guidance rather than an active fire hazard.
* **Proposed Fix**:
  - Implement a dedicated **Zero-Tolerance Safety Filter** regex and classifier layer intercepting keywords like `melted`, `fire`, `exploded`, `smoke`, `swollen`, `shock`, and `burned` before any self-serve response generation. Force immediate human priority escalation with `auto_handle = False`.

---

## 2. Failure Mode 2: Multi-Tier Escalation & Executive Complaint

* **Real Customer Message** (Tweet ID `101304`):
  > *"how do I go about raising a high level complaint please? 4 senior techs couldn’t help fix my problem, now my e mails are being unanswered, want a refund for a product that’s not fit for purpose, have tried everything to fix, thanks."*
* **Expected Result**:
  - `intent`: `store_billing_subscription` / `general_complaint_feedback`
  - `auto_handle`: `False` (Route directly to Senior Customer Relations / Tier-2 Escalation)
  - `escalation_reason`: Customer has exhausted 4 technical support tiers and requests financial refund/formal complaint.
* **Actual Naive Baseline Result**:
  - Auto-handled by suggesting the self-serve `reportaproblem.apple.com` webpage, completely ignoring the prior 4 failed technician interactions.
* **Failure Category**: **Tone-Deaf Auto-Handling / Repeat Failure Blindness**
* **Severity**: **HIGH (Severe Brand Reputation & Churn Risk)**
* **Why it Failed**:
  - Standard intent matching lacks conversation history memory and does not parse multi-attempt metadata (e.g., *"4 senior techs couldn't fix"*).
* **Proposed Fix**:
  - Integrate a **Prior Contact & Frustration Detector** that searches for phrases indicating repeated failed attempts (`"tried everything"`, `"techs couldn't help"`, `"unanswered emails"`, `"senior tech"`). Force immediate Tier-2 human handoff.

---

## 3. Failure Mode 3: Authentication Deadlock / 2FA Recovery Loop

* **Real Customer Message** (Tweet ID `1715358`):
  > *"Hi, So if someone loses his iPhone and two-factor authentication is turned on, there's no way to use Find my iPhone !"*
* **Expected Result**:
  - `intent`: `apple_id_account_security`
  - `auto_handle`: `False`
  - `escalation_reason`: Two-factor authentication deadlock on lost device requiring identity verification.
  - `draft_reply`: Clarify that `icloud.com/find` can be accessed without a 2FA prompt on trusted browsers, but direct account recovery requires secure account support.
* **Actual Naive Result**:
  - Agent matched `apple_id_account_security` but retrieved generic password reset links (`iforgot.apple.com`), which itself requires the lost 2FA device, aggravating customer frustration.
* **Failure Category**: **Misleading Self-Serve Guidance / Authentication Circularity**
* **Severity**: **HIGH (Account Access Lockout)**
* **Why it Failed**:
  - Generic retrieval matched general "two-factor" documents without recognizing the specific sub-scenario of losing the single trusted 2FA hardware key.
* **Proposed Fix**:
  - Sub-intent clustering within `apple_id_account_security` specifically distinguishing `2fa_lost_device` to provide the dedicated `icloud.com/find` direct access instructions while flagging for human agent follow-up.

---

## 4. Failure Mode 4: Impending Legal Threat / Regulatory Complaint

* **Real Customer Message** (Tweet ID `249171`):
  > *"I paid for a product. I should not have to fight to obtain that product I paid for. You don't help soon. A lawyer will call."*
* **Expected Result**:
  - `intent`: `general_complaint_feedback` / `store_billing_subscription`
  - `auto_handle`: `False`
  - `risk_flags`: `["legal_threat_escalation"]`
  - `escalation_reason`: Explicit legal threat requiring corporate legal / executive relations compliance handling.
* **Actual Naive Baseline Result**:
  - Naive model treated query as generic complaint and produced automated empathy response.
* **Failure Category**: **Legal Compliance Risk / Wrong Escalation Protocol**
* **Severity**: **HIGH (Legal & Regulatory Exposure)**
* **Why it Failed**:
  - Lack of legal trigger detection in standard NLP intent models.
* **Proposed Fix**:
  - Strict compliance filter detecting legal terminology (`"lawyer"`, `"attorney"`, `"lawsuit"`, `"sue"`, `"small claims"`, `"subpoena"`). Any match immediately sets `auto_handle = False` and routes to Specialized Support / Legal Desk.

---

## 5. Failure Mode 5: Entangled Multi-Intent Query (Physical Damage vs Sensor Failure)

* **Real Customer Message** (Tweet ID `98840`):
  > *"I’ve had a iPhone X for two wks now within the first 3 Days I’ve dropped it twice and cracked the screen protector, At night the camera cannot read my face and I am forced to manually type my passcode. Does this happen to all people of color @115858 ?"*
* **Expected Result**:
  - `intent`: `screen_display_touch` (Face ID TrueDepth Camera issue) with secondary context of physical drop.
  - `auto_handle`: `False` (High sensitivity query involving demographic fairness question and potential hardware damage).
  - `risk_flags`: `["hardware_damage", "sensitive_brand_inquiry"]`
* **Actual Naive Baseline Result**:
  - Single-label classifier predicted `screen_display_touch` and provided a generic force-restart script.
* **Failure Category**: **Ambiguous Intent Entanglement & Sensitive Brand Risk**
* **Severity**: **MEDIUM-HIGH (Customer Sensitivity & Hardware Misdiagnosis)**
* **Why it Failed**:
  - The query combines physical drop damage, Face ID biometric failure, and a sensitive customer fairness question. Standard single-label classifiers collapse all nuances into one technical category.
* **Proposed Fix**:
  - Multi-intent / multi-aspect tagging in the agent pipeline. When a sensitive brand inquiry or multiple conflicting root causes are detected in a single message, prevent automated replies and escalate to human specialists.
