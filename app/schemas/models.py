"""
models.py
=========
LAYER: Schemas / API contracts

All Pydantic v2 request/response models for the FastAPI layer.
These are what external callers (frontend, other microservices) send and receive.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
import uuid
from datetime import datetime


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class EscalationStatus(str, Enum):
    PENDING = "PENDING"
    ESCALATED = "ESCALATED"
    RESOLVED = "RESOLVED"
    AUTO_BLOCKED = "AUTO_BLOCKED"


class TransactionRequest(BaseModel):
    transaction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    account_id: str = Field(..., description="Source account ID")
    amount: float = Field(..., gt=0, description="Transaction amount in EUR")
    currency: str = Field(default="EUR")
    merchant: str = Field(..., description="Merchant name")
    merchant_category: str = Field(default="UNKNOWN")
    country: str = Field(default="NL")
    ip_address: Optional[str] = None
    device_fingerprint: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    session_id: Optional[str] = None

    model_config = {"json_schema_extra": {
        "example": {
            "account_id": "ACC-001",
            "amount": 4999.99,
            "currency": "EUR",
            "merchant": "CryptoExchange XYZ",
            "merchant_category": "CRYPTO",
            "country": "RU",
            "ip_address": "185.220.101.1"
        }
    }}


class AgentDecision(BaseModel):
    agent_name: str
    decision: str
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str
    tools_called: List[str] = []
    latency_ms: Optional[float] = None


class AnalysisResponse(BaseModel):
    transaction_id: str
    session_id: str
    risk_level: RiskLevel
    fraud_score: float = Field(ge=0.0, le=1.0)
    escalation_status: EscalationStatus
    agent_decisions: List[AgentDecision]
    summary: str
    recommendations: List[str]
    audit_trail_id: str
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    services: dict


class EscalationRequest(BaseModel):
    transaction_id: str
    reason: str
    agent_name: str
    risk_level: RiskLevel
    human_reviewer_id: Optional[str] = None


class EscalationResponse(BaseModel):
    escalation_id: str
    transaction_id: str
    status: EscalationStatus
    assigned_to: Optional[str]
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
