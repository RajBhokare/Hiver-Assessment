# Annotation Guide: Apple Support Customer Intent & Escalation

This guide establishes the rules and disambiguation standards for human annotators labeling the held-out golden set (`data/golden/golden_unlabelled.jsonl`).

---

## 1. Annotation Objective

For each tweet in `golden_unlabelled.jsonl`, fill in the following fields:
1. `intent` (string): Primary customer intent from the 11 candidate classes.
2. `requires_escalation` (boolean: `true` or `false`): Whether this query requires direct human tier-2 routing or DM intervention rather than a static self-serve answer.
3. `ambiguity_notes` (string / optional): Explanations if the query contains multiple overlapping intents or vague wording.
4. `annotator_id` (string): Your assigned annotator initials or ID.

---

## 2. Intent Taxonomy & Classification Rules

### Class 1: `software_update_os_issues`
* **Definition**: Inquiries or complaints regarding iOS/macOS system updates, installation failures, post-update bugs, or update eligibility.
* **Inclusion Criteria**: Explicit mention of iOS versions (e.g. "iOS 11.1"), update installation errors, boot loop during update, or general glitches attributed directly to a new OS version.
* **Exclusion Criteria**: If the user mentions an issue caused by an update that is exclusively about battery drain without other OS symptoms, prioritize `battery_power_charging`. If exclusively an app crash, prioritize `app_performance_crash`.
* **Example**: *"My phone won't finish downloading iOS 11.0.2 update, keeps saying error occurred."*

### Class 2: `battery_power_charging`
* **Definition**: Battery degradation, rapid percentage drops, failure to hold charge, cable/charging port issues, and device overheating.
* **Inclusion Criteria**: Keywords: battery, drain, dying fast, percentage jumping, overheating, won't charge, charger cable.
* **Exclusion Criteria**: Physical broken battery replacement inquiries at Genius Bar (`hardware_repair_store_service`).
* **Example**: *"Battery drops from 80% to 20% in 15 minutes while doing nothing. Phone gets burning hot."*

### Class 3: `app_performance_crash`
* **Definition**: Application crashes, UI freezing, lagging, unresponsive keyboards, or general software sluggishness.
* **Inclusion Criteria**: Specific apps closing automatically, keyboard typing glitches (e.g., 'I' autocomplete bug), lag when opening apps.
* **Exclusion Criteria**: Hardware touchscreen unresponsive (`screen_display_touch`).
* **Example**: *"The keyboard keeps freezing whenever I try to reply to WhatsApp or Notes."*

### Class 4: `apple_id_account_security`
* **Definition**: Apple ID credentials, passwords, 2-factor authentication (2FA), verification codes, account lockouts, or account merging.
* **Inclusion Criteria**: Forgotten Apple ID password, locked out of account, not receiving verification SMS, security questions.
* **Exclusion Criteria**: iCloud storage space full (`icloud_storage_backup`).
* **Example**: *"Locked out of my Apple ID because I changed my phone number and can't get verification code."*

### Class 5: `icloud_storage_backup`
* **Definition**: iCloud backup/sync failures, storage full warnings, photo syncing issues, or mystery "Other" system storage consuming disk space.
* **Inclusion Criteria**: "Storage almost full", photos not downloading from iCloud, backup failing to complete, space calculation issues.
* **Exclusion Criteria**: Inquiries about monthly iCloud payment/pricing (`billing_subscription_refund`).
* **Example**: *"I pay for 200GB iCloud but my iPhone still says storage full and won't backup photos."*

### Class 6: `audio_call_accessory`
* **Definition**: Audio hardware/software problems: AirPods, headphones, lightning dongles, microphones, speakers, and phone call volume.
* **Inclusion Criteria**: Microphone not picking up voice, call recipient can't hear, AirPods disconnecting audio, static from speaker.
* **Exclusion Criteria**: Cellular network drops during calls (`network_connectivity`).
* **Example**: *"During phone calls I can hear them but they can't hear me unless I put it on speaker."*

### Class 7: `screen_display_touch`
* **Definition**: Display hardware and touch sensors, flickering screens, black screen of death, unresponsive touch digitizer, Face ID / Touch ID sensors.
* **Inclusion Criteria**: Screen touch not responding, vertical lines on display, screen goes black during startup, Touch ID / Face ID failure.
* **Exclusion Criteria**: Physical screen repair pricing or appointments (`hardware_repair_store_service`).
* **Example**: *"The bottom half of my screen doesn't register any touches after the drop."*

### Class 8: `network_connectivity`
* **Definition**: Wi-Fi, Bluetooth, Cellular data, SIM card, and "No Service" network connectivity issues.
* **Inclusion Criteria**: Wi-Fi dropping frequently, Bluetooth failing to pair with car/headphones, "No Service" error, cellular data slow.
* **Exclusion Criteria**: Account billing hold by telecom carrier.
* **Example**: *"My iPhone 8 keeps disconnecting from my home Wi-Fi every 5 minutes."*

### Class 9: `billing_subscription_refund`
* **Definition**: App Store billing, unwanted recurring subscriptions, unauthorized charges, in-app purchases, and refund requests.
* **Inclusion Criteria**: Unrecognized credit card charge, refund request, subscription cancellation, receipt issues.
* **Exclusion Criteria**: Hardware repair cost estimates (`hardware_repair_store_service`).
* **Example**: *"I was charged $9.99 for an app subscription I cancelled last week. How do I get a refund?"*

### Class 10: `hardware_repair_store_service`
* **Definition**: Apple Store visits, Genius Bar appointments, repair estimates, warranty/AppleCare+ claims, and physical device damage.
* **Inclusion Criteria**: Genius Bar scheduling, repair quote requests, broken glass replacement, trade-in program questions.
* **Exclusion Criteria**: General software troubleshooting.
* **Example**: *"How much does Apple charge to replace the back glass on an iPhone X without AppleCare?"*

### Class 11: `general_complaint_feedback`
* **Definition**: Broad negative sentiment, non-technical rants, brand feedback, or switching threats without a distinct resolvable technical problem.
* **Inclusion Criteria**: "Worst customer service ever", "I hate Apple", "Never buying iPhone again", general sarcasm or rage venting.
* **Exclusion Criteria**: If the tweet contains a specific actionable issue despite the angry tone, label by the specific issue intent.
* **Example**: *"Your products are completely useless now. Switching to Android next week."*

---

## 3. Escalation Labeling (`requires_escalation`)

Set `requires_escalation = true` if the message satisfies ANY of the following:
1. **Severe Frustration / Legal / Threat**: Customer threatens legal action, chargeback, or public complaint.
2. **Account Security & Identity**: Locked Apple ID, stolen account, 2FA deadlock requiring manual identity verification.
3. **Financial / Unauthorized Charges**: Unrecognized transactions or disputed refunds requiring access to user account billing records.
4. **Physical Safety & Hardware Danger**: Swollen batteries, smoking devices, burning chargers, extreme overheating.
5. **Multiple Failed Attempts**: Customer explicitly states they tried all self-help steps or already visited a store without resolution.

Set `requires_escalation = false` for:
- Routine troubleshooting questions solvable via documentation or simple instructions (e.g. "how do I update iOS", "how to force restart").
- Simple factual inquiries (e.g. "is the iOS update free?").

---

## 4. Multi-Intent & Ambiguity Disambiguation Rules

When a tweet contains elements of multiple intents, follow this priority hierarchy:
1. **Primary Root Cause over Consequence**: If a customer says *"Updated to iOS 11 and now my battery drains in 1 hour"*, if the main complaint is the battery behavior, label `battery_power_charging` and add a note in `ambiguity_notes: "triggered by iOS 11 update"`.
2. **Actionable Technical Issue over General Anger**: If a customer writes *"Apple is trash, fix the Wifi dropping"*, label `network_connectivity` and mark `requires_escalation: false` (or `true` if extremely toxic).
3. **Hardware over Software**: If hardware digitizer or physical screen glass is visibly damaged, label `hardware_repair_store_service` or `screen_display_touch` rather than `app_performance_crash`.

---

## 5. JSONL Annotation Format

Each line in `data/golden/golden_unlabelled.jsonl` should be updated to look like:
```json
{
  "id": "gold_001",
  "tweet_id": "345497",
  "conversation_id": "345497",
  "author_id": "198218",
  "created_at": "Sun Oct 08 00:33:55 +0000 2017",
  "text": "Yo @116602 the app isn’t even opening half the time since the iOS 11 updates. @AppleSupport",
  "clean_text": "Yo the app isn’t even opening half the time since the iOS 11 updates.",
  "is_conversation_starter": true,
  "intent": "app_performance_crash",
  "requires_escalation": false,
  "ambiguity_notes": "Mentioned iOS 11 update but core failure is third-party app not opening.",
  "annotator_id": "annotator_1"
}
```
