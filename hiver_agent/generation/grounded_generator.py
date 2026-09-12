"""Grounded response generator and policy adherence engine.

Enforces strict domain boundaries:
1. Never invent policies or warranty exceptions.
2. Never promise unapproved refunds or claim financial actions were completed.
3. Never claim backend access or pretend to inspect private Apple accounts/databases.
4. Escalate immediately when backend access, billing adjustments, account lockouts, or safety hazards occur.
5. Generate responses strictly formatted for Twitter (<280 characters).
"""
import re
from typing import List, Optional, Tuple
from hiver_agent.schema import RetrievedEvidence, AgentDecision

# Canonical verified Apple support paths (factual, non-hallucinatory)
CANONICAL_ACTIONS = {
    "ios_update_issue": (
        "We're here to help. Make sure your device is connected to Wi-Fi and power, then check Settings > General > Software Update. If it still fails, let's connect in DM with your device model."
    ),
    "battery_power_charging": (
        "We want to help with your battery. Check Settings > Battery to see which apps are using the most power. If your device is overheating or percentage drops abruptly, reach out in DM."
    ),
    "app_performance_crash": (
        "Let's get this sorted out. Try force closing the app, restarting your device, and checking the App Store for updates. If the issue continues, DM us your iOS version."
    ),
    "apple_id_account_security": (
        "For your security, we cannot access account details on Twitter. Please visit iforgot.apple.com to reset your credentials or verify your Apple ID, or DM us if you need navigation help."
    ),
    "icloud_storage_backup": (
        "We can clarify storage options! Check Settings > [Your Name] > iCloud > Manage Storage to review backups and photos. Send us a DM if you'd like step-by-step guidance."
    ),
    "audio_call_accessory": (
        "We'd be glad to help with your sound. Check Settings > Sounds & Haptics, test with Voice Memos, and unpair/re-pair any Bluetooth accessories. DM us if the issue persists."
    ),
    "screen_display_touch": (
        "Let's look into this display issue. Try a force restart on your device. If the screen is unresponsive or has visual glitches, reach out to us via DM so we can explore repair options."
    ),
    "network_connectivity": (
        "Let's help you get connected. Try toggling Airplane Mode on and off, or go to Settings > General > Reset > Reset Network Settings. If Wi-Fi still disconnects, DM us."
    ),
    "store_billing_subscription": (
        "For billing inquiries and refund requests, please sign in to reportaproblem.apple.com to view your purchase history and submit a request. For security, never share payment info publicly."
    ),
    "hardware_repair_store_service": (
        "To check repair pricing and book an appointment with an Apple Authorized Service Provider or Genius Bar, visit getsupport.apple.com. DM us if you need help finding a location."
    ),
    "general_complaint_feedback": (
        "We understand your frustration and want to make sure your feedback is heard. Please send us a DM with more details about your device so we can assist you directly."
    ),
}

# Intents requiring mandatory human escalation (cannot be fully resolved autonomously without backend)
MANDATORY_ESCALATION_INTENTS = {
    "apple_id_account_security": "Apple ID account credentials, 2FA lockouts, and identity verification require secure internal backend access.",
    "store_billing_subscription": "Financial transactions, credit card charges, and subscription refunds require authenticated billing system intervention.",
    "hardware_repair_store_service": "Hardware damage assessment, repair quoting, and Genius Bar reservation management require human store routing.",
}


class GroundedResponseGenerator:
    """Generates policy-compliant, grounded draft replies and performs escalation analysis."""

    def __init__(self, confidence_threshold: float = 0.50, similarity_threshold: float = 0.30):
        self.confidence_threshold = confidence_threshold
        self.similarity_threshold = similarity_threshold

    def evaluate_risks(
        self,
        customer_message: str,
        predicted_intent: str,
        intent_confidence: float,
        evidence: List[RetrievedEvidence],
    ) -> Tuple[bool, Optional[str], List[str]]:
        """Identify risk flags and determine whether to auto-handle or escalate."""
        risk_flags: List[str] = []
        escalation_reasons: List[str] = []

        msg_lower = customer_message.lower()

        # 1. Physical Safety / Hardware Hazard
        hazard_keywords = ["smoke", "smoking", "fire", "swollen", "burning", "burns", "hot to touch", "exploded", "melted"]
        if any(w in msg_lower for w in hazard_keywords):
            risk_flags.append("safety_hardware_hazard")
            escalation_reasons.append("Physical hardware hazard detected (overheating / battery swelling / fire risk). Immediate human intervention required.")

        # 2. Legal / Threat / Escalation Demand
        legal_keywords = ["lawyer", "lawsuit", "attorney", "legal action", "sue apple", "bbb", "consumer protection", "chargeback"]
        if any(w in msg_lower for w in legal_keywords):
            risk_flags.append("legal_or_severe_complaint")
            escalation_reasons.append("Customer mentioned legal action, regulatory complaints, or payment chargebacks.")

        # 3. Private Account / Financial Backend Requirement
        if predicted_intent in MANDATORY_ESCALATION_INTENTS:
            risk_flags.append(f"backend_auth_required:{predicted_intent}")
            escalation_reasons.append(MANDATORY_ESCALATION_INTENTS[predicted_intent])

        # 4. Low Intent Classification Confidence
        if intent_confidence < self.confidence_threshold:
            risk_flags.append("low_intent_confidence")
            escalation_reasons.append(f"Intent prediction confidence ({intent_confidence:.2f}) is below threshold ({self.confidence_threshold:.2f}).")

        # 5. Insufficient Historical Evidence
        top_sim = evidence[0].similarity_score if evidence else 0.0
        if top_sim < self.similarity_threshold:
            risk_flags.append("low_retrieval_similarity")
            escalation_reasons.append(f"Top retrieved historical evidence similarity ({top_sim:.2f}) is below threshold ({self.similarity_threshold:.2f}).")

        # Auto-handle is True ONLY when zero risk flags exist
        auto_handle = (len(risk_flags) == 0)
        escalation_reason = " | ".join(escalation_reasons) if not auto_handle else None

        return auto_handle, escalation_reason, risk_flags

    def generate_draft(
        self,
        customer_message: str,
        predicted_intent: str,
        evidence: List[RetrievedEvidence],
        auto_handle: bool,
    ) -> str:
        """Synthesize a Twitter-appropriate response (<280 chars) strictly adhering to grounded rules."""
        # Use verified canonical action for the predicted intent
        reply = CANONICAL_ACTIONS.get(predicted_intent, CANONICAL_ACTIONS["general_complaint_feedback"])

        # Enforce Twitter 280-character boundary
        if len(reply) > 280:
            reply = reply[:277] + "..."

        return reply

    def process(
        self,
        customer_message: str,
        predicted_intent: str,
        intent_confidence: float,
        evidence: List[RetrievedEvidence],
    ) -> AgentDecision:
        """Produce the complete structured AgentDecision payload."""
        auto_handle, escalation_reason, risk_flags = self.evaluate_risks(
            customer_message=customer_message,
            predicted_intent=predicted_intent,
            intent_confidence=intent_confidence,
            evidence=evidence,
        )

        draft_reply = self.generate_draft(
            customer_message=customer_message,
            predicted_intent=predicted_intent,
            evidence=evidence,
            auto_handle=auto_handle,
        )

        return AgentDecision(
            intent=predicted_intent,
            intent_confidence=round(intent_confidence, 4),
            draft_reply=draft_reply,
            auto_handle=auto_handle,
            escalation_reason=escalation_reason,
            risk_flags=risk_flags,
            retrieved_evidence=evidence,
        )
