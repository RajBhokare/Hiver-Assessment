# Intent Taxonomy Proposal & Data Preparation Report: AppleSupport

**Brand**: `@AppleSupport`  
**Dataset**: Twitter Customer Support (`twcs.csv`)  
**Date**: September 2026  
**Status**: Proposal for Review (Awaiting Approval)

---

## 1. Dataset Inspection & Structural Representation

The raw `twcs.csv` dataset contains **2,811,774** customer support tweets spanning major global brands.

### Schema Representation

| Column Name | Data Type | Representation & Semantics |
| :--- | :--- | :--- |
| `tweet_id` | `string` / `int` | Unique identifier for each tweet. |
| `author_id` | `string` | Anonymized user ID (e.g. `115854`) or official brand handle (`AppleSupport`). |
| `inbound` | `boolean` | Direction indicator: `True` indicates customer-to-brand message; `False` indicates brand outbound response. |
| `created_at` | `string` | Timestamp in standard Twitter format (`Tue Oct 31 22:10:47 +0000 2017`). |
| `text` | `string` | Raw tweet text content, including `@` handles, URLs, emojis, and HTML entities. |
| `response_tweet_id` | `string` | Comma-separated ID(s) of tweets that responded directly to this tweet (or `NaN` if unanswered). |
| `in_response_to_tweet_id` | `string` | ID of the parent tweet that this tweet is replying to (or `NaN` for root conversation starters). |

---

## 2. Conversation Filtering & Turn Reconstruction

### Filtering `@AppleSupport` Conversations

To isolate the AppleSupport ecosystem:
1. **Outbound Brand Tweets**: Filtered `author_id == 'AppleSupport'` yielding **106,860** official responses.
2. **Inbound Customer Tweets**: Filtered inbound tweets mentioning `@AppleSupport` or targeted by AppleSupport responses, yielding **126,113** candidate customer messages.
3. **Turn Pairing**: Matched each customer tweet directly to the corresponding initial AppleSupport response via `in_response_to_tweet_id`, establishing **106,646** raw pairs.

### Conversation Thread Tracing
We traced conversation parent links (`in_response_to_tweet_id`) recursively to discover each thread's root tweet:
- **Unique Conversation Threads (Roots)**: **80,710**
- **Direct Conversation Starters** (`in_response_to_tweet_id` is null): **74,632** (70.0%)
- **Multi-Turn Follow-Ups**: **32,014** (30.0%)

---

## 3. Data Cleaning, Filtering Decisions & Deduplication

Every filtering step was recorded with strict counts:

| Pipeline Step | Rule Applied | Count Removed | Remaining Total |
| :--- | :--- | :--- | :--- |
| **Raw Matched Pairs** | Initial Customer $\rightarrow$ AppleSupport pairs | - | 106,646 |
| **Handle / URL Stripping** | Removed `@handles`, URLs (`https://...`), and HTML entity decodes | - | 106,646 |
| **Short Text Filter** | Dropped messages with $<5$ characters of clean text (e.g., only handles/screenshots) | 1,499 | 105,147 |
| **User Duplicate Filter** | Dropped identical clean text queries from the same user ID (spammed retries) | 58 | 105,089 |
| **Global Duplicate Filter** | Dropped identical text copypastas across distinct users to avoid viral skew | 1,562 | **103,527** |

---

## 4. Zero-Leakage Dataset Splitting Design

### Prevention of Conversation & User Leakage via Connected Components

In customer support interactions, a customer may participate in multiple conversation threads, and multiple customers may reply within the same shared root thread. Splitting naively by rows or solely by user ID or conversation ID can create subtle train/test leakage.

To achieve **mathematically verified zero leakage**:
1. We constructed an undirected bipartite graph between `user_id` and `conversation_id`.
2. Computed **72,808** isolated **Connected Components**.
3. Partitioned the connected components deterministically using fixed random seed (`42`) into **70% Train / 15% Validation / 15% Test**.

### Split Statistics

| Split | Number of Pairs | Unique Users | Unique Conversations | User Overlap with Test | Conv Overlap with Test |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Train** | **72,789** (70.3%) | 53,038 | 55,832 | **0 (0.0%)** | **0 (0.0%)** |
| **Validation** | **15,412** (14.9%) | 11,189 | 11,959 | **0 (0.0%)** | **0 (0.0%)** |
| **Test** | **15,326** (14.8%) | 11,231 | 11,920 | **0 (0.0%)** | **0 (0.0%)** |

All cross-split disjointness assertions passed:
- `set(train_df['author_id']).isdisjoint(set(test_df['author_id'])) == True`
- `set(train_df['conversation_id']).isdisjoint(set(test_df['conversation_id'])) == True`

---

## 5. Proposed Intent Taxonomy (11 Core Intents)

Based on empirical clustering and frequency analysis over 103,527 real customer queries, we propose the following 11 intents:

```
                                 [ Customer Inquiries ]
                                           |
         +---------------------------------+---------------------------------+
         |                                 |                                 |
 [System & Software]              [Account & Storage]               [Hardware & Service]
  • ios_update_issue               • apple_id_account_security       • screen_display_touch
  • app_performance_crash          • icloud_storage_backup           • audio_call_accessory
  • battery_power_charging         • store_billing_subscription      • hardware_repair_store_service
  • network_connectivity                                             • general_complaint_feedback
```

---

### Intent 1: `ios_update_issue`
* **Definition**: Inquiries or issues regarding iOS/macOS system updates, installation errors, version verification, and software update regressions.
* **Inclusion Criteria**: Explicit mention of iOS/macOS versions, update download/installation failures, boot loops during updates.
* **Exclusion Criteria**: Battery drain only (see `battery_power_charging`); App crash only (see `app_performance_crash`).
* **Empirical Frequency**: 31,658 occurrences (30.58% of matched patterns)
* **Real Dataset Examples**:
  1. *Customer*: "iOS 11.0.3 keeps failing to verify update on my iPhone 7. What should I do?"
     *AppleSupport*: "We'd be happy to help get your iPhone updated. Take a look at the troubleshooting steps here:"
  2. *Customer*: "My phone won’t finish downloading iOS 11 update, keeps saying error occurred."
     *AppleSupport*: "We can help get that update installed. Is your device connected to Wi-Fi and power?"
* **Typical Support Action**: Provide link to Apple Update support article; check device storage; guide force restart / iTunes recovery update.
* **Likely Escalation Requirement**: Low (unless update completely bricked the device / requires DFU restore).

---

### Intent 2: `battery_power_charging`
* **Definition**: Battery degradation, rapid percentage discharge, charging failures, charger/cable defects, and device overheating.
* **Inclusion Criteria**: Keywords: battery, drain, percentage dropping, won't charge, charger, cable, overheating, phone hot.
* **Exclusion Criteria**: Physical broken battery replacement scheduling at Apple Store (`hardware_repair_store_service`).
* **Empirical Frequency**: 10,464 occurrences (10.11%)
* **Real Dataset Examples**:
  1. *Customer*: "hi, please advise why the battery on my iPhone 6s is draining really quickly just lately?! It’s really annoying having to charge after 40 minutes use on the train. It’s going from 90% to 7% in that time"
     *AppleSupport*: "Great battery life from your iPhone is important, and we want to get to the bottom of what's happening here. How often do you fully charge your device?"
  2. *Customer*: "My phone is getting extremely hot while charging and the battery percentage is actually going down."
     *AppleSupport*: "Safety and performance are our top priority. Please disconnect the charger and join us in DM so we can assist immediately."
* **Typical Support Action**: Instruct battery health check in Settings; check background app refresh; suggest battery diagnostics.
* **Likely Escalation Requirement**: Moderate (High if safety hazard/swelling/overheating is reported).

---

### Intent 3: `app_performance_crash`
* **Definition**: Third-party or native app crashes, UI freezing, lagging, system unresponsiveness, and keyboard input bugs.
* **Inclusion Criteria**: App abruptly closing, UI freeze, keyboard glitch (e.g. the 'I' autocomplete bug), lag opening apps.
* **Exclusion Criteria**: Touch digitizer hardware failure (`screen_display_touch`).
* **Empirical Frequency**: 11,227 occurrences (10.84%)
* **Real Dataset Examples**:
  1. *Customer*: "My battery dies just while being in my pocket and my phones been freezing and just shutting out apps while I'm on them"
     *AppleSupport*: "We want to make sure your iPhone works the way you expect it to. Let's get paired up in DM to get started."
  2. *Customer*: "can you fix this glitch please!! Can’t type the letter I️"
     *AppleSupport*: "We can offer some guidance on this. DM us the device and iOS version and we'll go from there."
* **Typical Support Action**: Recommend app reinstallation, force closing app, clearing cache, or text replacement workaround.
* **Likely Escalation Requirement**: Low.

---

### Intent 4: `apple_id_account_security`
* **Definition**: Apple ID authentication, password recovery, Two-Factor Authentication (2FA) verification codes, account lockouts, and security questions.
* **Inclusion Criteria**: Forgotten Apple ID password, locked out of account, 2FA code not delivered, security question mismatch.
* **Exclusion Criteria**: iCloud storage space full (`icloud_storage_backup`).
* **Empirical Frequency**: 5,435 occurrences (5.25%)
* **Real Dataset Examples**:
  1. *Customer*: "ok, I’ve got a forgotten password. Go to use the security questions but says wrong DOB. No online chat to be found, help!"
     *AppleSupport*: "For support with your Apple ID, reach out to our Account Security support here:"
  2. *Customer*: "thank you! I was able to login and update it. But is there a way to resend the confirmation email?"
     *AppleSupport*: "The email won't be resent, but updates will go to the updated address. The previous link will let you check the status."
* **Typical Support Action**: Provide iforgot.apple.com link; route to Apple Account Security specialists.
* **Likely Escalation Requirement**: High (security protocols prohibit resolving account takeovers via public social media).

---

### Intent 5: `icloud_storage_backup`
* **Definition**: iCloud sync problems, "Storage Almost Full" warnings, photo library backup/syncing, and device storage management.
* **Inclusion Criteria**: Photos not uploading/downloading from iCloud, backup failing to complete, "Other/System" storage consuming all memory.
* **Exclusion Criteria**: Recurring monthly iCloud payment inquiries (`store_billing_subscription`).
* **Empirical Frequency**: 3,522 occurrences (3.40%)
* **Real Dataset Examples**:
  1. *Customer*: "how do I use my iCloud that I pay for on my iphone6? No space on phone but lots of iCloud doing nothing? Help please?"
     *AppleSupport*: "Great question! We'll be happy to provide some clarity on how iCloud works for your device. Send us a DM to continue."
  2. *Customer*: "Not enough space to update apps/system update. > TF is “Other”? > System = 8.5 GB of 16 GB iPad tf is this crap?"
     *AppleSupport*: "Thanks for reaching out. DM us which iPad and specific iOS version you are using to get started."
* **Typical Support Action**: Explain distinction between device storage and iCloud storage; guide optimizing iPhone storage; backup verification.
* **Likely Escalation Requirement**: Low to Moderate.

---

### Intent 6: `audio_call_accessory`
* **Definition**: Audio and sound hardware/software faults: AirPods, EarPods, microphone input, speaker output, and phone call volume.
* **Inclusion Criteria**: Caller cannot hear voice, speaker crackling, AirPods connection/audio dropout, headphone adapter issues.
* **Exclusion Criteria**: Cellular carrier dropouts during calls (`network_connectivity`).
* **Empirical Frequency**: 2,343 occurrences (2.26%)
* **Real Dataset Examples**:
  1. *Customer*: "Love my new #iphone8, . I would like to hear the people I speak to, but I might be just picky, right? Any hints?"
     *AppleSupport*: "We want to look into this with you. Can you tell us more about what's going on via DM?"
  2. *Customer*: "No, don’t have any other. Also when this happen, my headphones won’t allow skipping songs and volume control"
     *AppleSupport*: "Shoot us a DM and we'll look into the next best option."
* **Typical Support Action**: Guide receiver cleaning, sound balance settings, Bluetooth audio unpairing/repairing.
* **Likely Escalation Requirement**: Moderate (may require hardware repair if speaker diaphragm / mic is dead).

---

### Intent 7: `screen_display_touch`
* **Definition**: Display hardware issues, touch digitizer unresponsiveness, ghost touching, display flickering, black screen, and Face ID / Touch ID hardware sensors.
* **Inclusion Criteria**: Touch screen unresponsive, green/white lines on OLED display, black screen after boot, Touch ID not recognizing fingerprint.
* **Exclusion Criteria**: Booking repair appointments (`hardware_repair_store_service`).
* **Empirical Frequency**: 5,167 occurrences (4.99%)
* **Real Dataset Examples**:
  1. *Customer*: "Dear you all are really tryna serve me. All I did was update my software & now my MacBook won’t load past the startup screen. #WhatsReallyGood"
     *AppleSupport*: "Hey, we'll help you get your Mac back up and running. Send us a DM and we'll work together to get this figured out."
  2. *Customer*: "Screen freezes, cant hear calls & no one can hear me, when my alarm goes off it doesnt ring anymore - all started when new update came out."
     *AppleSupport*: "This is certainly not expected behavior. Please DM us and we'll be glad to look into this further with you."
* **Typical Support Action**: Force restart procedure; diagnostic check; repair intake recommendation.
* **Likely Escalation Requirement**: Moderate to High.

---

### Intent 8: `network_connectivity`
* **Definition**: Wi-Fi disconnects, Bluetooth device pairing, cellular data / LTE signal loss, and "No Service" status.
* **Inclusion Criteria**: Wi-Fi dropping repeatedly, Bluetooth failing to find devices, inability to connect to cellular internet.
* **Exclusion Criteria**: Telecom carrier service suspension.
* **Empirical Frequency**: 4,184 occurrences (4.04%)
* **Real Dataset Examples**:
  1. *Customer*: "tired of my WiFi dropping. There is a serious BUG with the newer iPhones (7 and up) !! My iPhone 6 can’t be near a 7/8 or ill drop!!"
     *AppleSupport*: "How many devices are connecting to your Wi-Fi network at a time? Does this issue happen when only a few iPhones are connected?"
  2. *Customer*: "I have the same issue on my new iPhone 8+. WiFi works great for a bit, then just stops. Restarted phone and toggled airplane several times"
     *AppleSupport*: "We'll help you out! Send us a DM, and we can work with you from there."
* **Typical Support Action**: Reset Network Settings; toggle Airplane Mode; router band configuration check.
* **Likely Escalation Requirement**: Low to Moderate.

---

### Intent 9: `store_billing_subscription`
* **Definition**: App Store transactions, subscription management, unauthorized charges, in-app purchases, and refund requests.
* **Inclusion Criteria**: Inquiries regarding unknown charges, subscription cancellation requests, receipt verification.
* **Exclusion Criteria**: Hardware repair quotes (`hardware_repair_store_service`).
* **Empirical Frequency**: 3,211 occurrences (3.10%)
* **Real Dataset Examples**:
  1. *Customer*: "how much money do you charge to update my phone and apps???"
     *AppleSupport*: "That’s a great question. The iOS update is free. Here’s a link that will show you how to complete that: For the apps, the charge will depend on the app developer. If there is a charge, you will be prompted to approve the charge."
  2. *Customer*: "I need a refund for an app subscription charged to my iTunes account today. How do I request it?"
     *AppleSupport*: "You can request a refund directly through reportaproblem.apple.com. Let us know if you need assistance navigating the page."
* **Typical Support Action**: Direct to reportaproblem.apple.com; guide subscription cancellation in Apple ID settings.
* **Likely Escalation Requirement**: High (billing and credit card disputes require authenticated human agent handling).

---

### Intent 10: `hardware_repair_store_service`
* **Definition**: Apple Store Genius Bar appointments, repair pricing, physical damage evaluation, warranty status, and AppleCare+ coverage.
* **Inclusion Criteria**: Scheduling Genius Bar, cracked back/front glass repair quotes, out-of-warranty replacement options.
* **Exclusion Criteria**: Software troubleshooting steps.
* **Empirical Frequency**: 1,908 occurrences (1.84%)
* **Real Dataset Examples**:
  1. *Customer*: "had the worst experience at GrandCentral genius bar, NYC. the problem wasn't resolved! plus a new one was created! #veryfrustrated"
     *AppleSupport*: "We'd like to hear about your store experience. Send us a DM with the details, please."
  2. *Customer*: "Went to the Apple repair center at Festival Mall to inquire about battery replacement for my iPod Touch. I was told it CANNOT be replaced & I need to pay them Php10,000 for a new one. So Apple is lying about this? I don’t think so"
     *AppleSupport*: "We'd love to look into this with you. Please click here to connect with us in DM. We'll pick up there:"
* **Typical Support Action**: Provide Apple Store appointment link; provide AppleCare repair pricing estimate table.
* **Likely Escalation Requirement**: High (involves physical store scheduling or customer service complaints).

---

### Intent 11: `general_complaint_feedback`
* **Definition**: Non-technical customer venting, brand complaints, sarcasm, or switching threats lacking a single actionable technical inquiry.
* **Inclusion Criteria**: Expressing anger/frustration without diagnosing a specific issue ("Apple is the worst company", "Switching to Samsung").
* **Exclusion Criteria**: Inquiries containing a distinct actionable technical failure alongside the complaint.
* **Empirical Frequency**: 4,631 occurrences (4.47%)
* **Real Dataset Examples**:
  1. *Customer*: "your new update sucks! Literally #sucks the life out of my battery☠️ No, I don’t want to purchase another new #iPhone fix the issue!"
     *AppleSupport*: "We know you rely on your battery and want to help. DM us a bit more information about what's happening."
  2. *Customer*: "the new IOS sucks. Its so glitchy and I have a grand new iPhone 8"
     *AppleSupport*: "That's not the experience we want you to have. Please meet us in DM with as much detail as possible about your issue."
* **Typical Support Action**: Empathy statement, invitation to private DM for detailed review.
* **Likely Escalation Requirement**: Moderate (depends on brand reputation risk and toxicity level).

---

## 6. Golden Evaluation Set & Annotation Artifacts

To maintain complete evaluation integrity:
1. **Unlabelled Golden Set (`data/golden/golden_unlabelled.jsonl`)**:
   - Contains **200 unlabelled candidate instances** sampled exclusively from the held-out test split.
   - Preserves natural category distributions, ambiguous multi-intent cases, and escalation scenarios.
   - Contains **zero fabricated labels** (`intent: null`, `requires_escalation: null`).
2. **Annotation Guide (`data/golden/ANNOTATION_GUIDE.md`)**:
   - Defines clear boundaries, inclusion/exclusion rules, escalation criteria, and tie-breaking guidelines for human annotators.
