from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RiskAssessment(BaseModel):
    score: int = Field(..., ge=0, le=100, description="Numerical risk score from 0 to 100")
    level: RiskLevel = Field(..., description="Categorized risk tier: low, medium, high")
    action_type: str
    reasons: List[str] = Field(default_factory=list)
    security_flags: List[str] = Field(default_factory=list)
    requires_approval: bool = False


class PolicyViolation(BaseModel):
    policy_name: str
    rule: str
    description: str
    severity: str = "high"  # warning, high, blocking


class PolicyEvaluationResult(BaseModel):
    is_compliant: bool
    violations: List[PolicyViolation] = Field(default_factory=list)
    requires_human_approval: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApprovalRequestCreate(BaseModel):
    user_id: str
    action_type: str
    payload: Dict[str, Any]
    risk_score: Optional[int] = None


class ApprovalResponse(BaseModel):
    id: str
    user_id: str
    action_type: str
    payload: Dict[str, Any]
    status: ApprovalStatus
    approved_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str
