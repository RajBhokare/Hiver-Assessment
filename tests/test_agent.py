"""Unit and integration tests for Hiver Agent, baselines, and grounded generation."""
from hiver_agent.schema import AgentDecision, RetrievedEvidence
from hiver_agent.baselines.majority_baseline import MajorityIntentBaseline, TrivialEscalationStrategy
from hiver_agent.baselines.tfidf_logistic import TFIDFLogisticBaseline
from hiver_agent.generation.grounded_generator import GroundedResponseGenerator
from hiver_agent.agent import HiverAgent


def test_schema_serialization():
    evidence = [
        RetrievedEvidence(
            customer_query="Battery dying",
            historical_response="We can help in DM",
            similarity_score=0.85,
        )
    ]
    decision = AgentDecision(
        intent="battery_power_charging",
        intent_confidence=0.95,
        draft_reply="Check Settings > Battery to review power usage.",
        auto_handle=True,
        escalation_reason=None,
        risk_flags=[],
        retrieved_evidence=evidence,
    )
    dumped = decision.model_dump()
    assert dumped["intent"] == "battery_power_charging"
    assert dumped["auto_handle"] is True
    assert len(dumped["retrieved_evidence"]) == 1


def test_majority_baseline():
    train_texts = ["query 1", "query 2", "query 3"]
    train_labels = ["ios_update_issue", "ios_update_issue", "battery_power_charging"]

    model = MajorityIntentBaseline()
    model.fit(train_texts, train_labels)
    assert model.majority_intent == "ios_update_issue"

    preds = model.predict(["unknown query", "another query"])
    assert preds == ["ios_update_issue", "ios_update_issue"]


def test_trivial_escalation_strategy():
    strategy = TrivialEscalationStrategy(mode="keyword_rule_trivial")
    
    # Normal query
    auto_handle, reason, flags = strategy.decide("How do I update to iOS 11?")
    assert auto_handle is True
    assert len(flags) == 0

    # High-risk query
    auto_handle, reason, flags = strategy.decide("I want a refund for an unauthorized charge!")
    assert auto_handle is False
    assert len(flags) > 0


def test_tfidf_logistic_baseline_fit_and_eval():
    texts = [
        "battery draining fast and getting hot",
        "battery percentage drops to zero",
        "iOS 11 update failed to install",
        "cannot install latest software update",
    ]
    labels = [
        "battery_power_charging",
        "battery_power_charging",
        "ios_update_issue",
        "ios_update_issue",
    ]

    clf = TFIDFLogisticBaseline(max_features=50)
    clf.fit(texts, labels)

    pred, conf = clf.predict_with_confidence("my battery is draining")
    assert pred in labels
    assert 0.0 <= conf <= 1.0


def test_grounded_generator_safety_and_length():
    generator = GroundedResponseGenerator()
    evidence = [
        RetrievedEvidence(
            customer_query="similar query",
            historical_response="official reply",
            similarity_score=0.8,
        )
    ]

    # Safe technical query
    decision = generator.process(
        customer_message="How do I check my wifi settings?",
        predicted_intent="network_connectivity",
        intent_confidence=0.90,
        evidence=evidence,
    )
    assert len(decision.draft_reply) <= 280
    assert decision.auto_handle is True

    # Account security query (must escalate)
    sec_decision = generator.process(
        customer_message="I'm locked out of my Apple ID and need to reset password",
        predicted_intent="apple_id_account_security",
        intent_confidence=0.95,
        evidence=evidence,
    )
    assert sec_decision.auto_handle is False
    assert "backend_auth_required" in sec_decision.risk_flags[0]


def test_agent_end_to_end():
    agent = HiverAgent.load_or_train()
    decision = agent.respond("My iPhone screen is completely black and won't turn on.")
    assert isinstance(decision, AgentDecision)
    assert len(decision.draft_reply) <= 280
    assert decision.intent is not None
    assert decision.intent_confidence > 0.0
