"""Pydantic schemas and structured output definitions for Hiver Agent."""
from typing import List, Optional
from pydantic import BaseModel, Field


class RetrievedEvidence(BaseModel):
    """Historical customer-response pair retrieved as grounding evidence."""
    customer_query: str = Field(..., description="Historical customer message")
    historical_response: str = Field(..., description="Historical AppleSupport reply")
    similarity_score: float = Field(..., description="Cosine / TF-IDF similarity score")


class AgentDecision(BaseModel):
    """Structured output representing the final decision and draft from the agent."""
    intent: str = Field(..., description="Predicted customer intent from frozen taxonomy")
    intent_confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
    draft_reply: str = Field(..., description="Grounded, Twitter-appropriate draft response (<280 chars)")
    auto_handle: bool = Field(..., description="True if safe to auto-respond; False if human escalation required")
    escalation_reason: Optional[str] = Field(None, description="Detailed explanation if auto_handle is False")
    risk_flags: List[str] = Field(default_factory=list, description="Identified risk triggers (e.g. billing, legal, hardware_hazard)")
    retrieved_evidence: List[RetrievedEvidence] = Field(default_factory=list, description="Historical examples used as context")
