"""
PatchPilot Data Models

Structured Pydantic models for data exchange between backend components
and agents. Maintains both structured fields for application logic and
human-readable explanations for developers.
"""

from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, conint
from typing import Optional, List, Dict, Any


class IssueStatus(str, Enum):
    """Status of a bug investigation across the multi-agent state machine."""
    NEW = "new"
    ASSIGNED = "assigned"
    INVESTIGATING = "investigating"
    REPORTED = "reported"
    RESOLVED = "resolved"
    VALIDATING_INPUT = "validating_input"
    VISION_RUNNING = "vision_running"
    VISION_COMPLETED = "vision_completed"
    VISION_FAILED = "vision_failed"
    TRIAGE_RUNNING = "triage_running"
    INVESTIGATION_ASSIGNED = "investigation_assigned"
    INVESTIGATION_RUNNING = "investigation_running"
    AWAITING_REVIEW = "awaiting_review"
    REINVESTIGATION_REQUIRED = "reinvestigation_required"
    REPORT_READY = "report_ready"
    COMPLETED = "completed"
    FAILED = "failed"
    CLOSED = "closed"


class EvidenceCategory(str, Enum):
    """Rigorous 5-level epistemological classification for findings."""
    OBSERVED = "OBSERVED"           # Directly visible or extracted via OCR
    INFERRED = "INFERRED"           # Reasoned technical hypothesis
    CODE_VERIFIED = "CODE_VERIFIED" # Empirically verified in inspected source code
    TEST_VERIFIED = "TEST_VERIFIED" # Validated through an executed test
    PROPOSED = "PROPOSED"           # Suggested patch/remediation not yet applied


class IssueClassification(str, Enum):
    """Classification of the bug type."""
    UI_BUG = "ui_bug"
    FUNCTIONAL_BUG = "functional_bug"
    BACKEND_ERROR = "backend_error"
    API_INTEGRATION_ERROR = "api_integration_error"
    VALIDATION_ERROR = "validation_error"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_CONCERN = "security_concern"
    UNKNOWN = "unknown"


class SeverityLevel(str, Enum):
    """Severity classification."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ConfidenceLevel(str, Enum):
    """Confidence level for agent findings."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class AgentRole(str, Enum):
    """Role of each agent."""
    VISION = "vision"
    TRIAGE = "triage"
    INVESTIGATION = "investigation"


class PydanticIssueBase(BaseModel):
    """Base issue representation."""
    id: str = Field(default_factory=lambda: f"issue-{datetime.utcnow().timestamp()}")
    description: str
    screenshot_reference: Optional[str] = None  # path or identifier
    original_description: Optional[str] = None
    status: IssueStatus = IssueStatus.NEW
    classification: IssueClassification = IssueClassification.UNKNOWN
    severity: SeverityLevel = SeverityLevel.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PydanticVisionObservations(BaseModel):
    """Structured observations from the Vision Agent."""
    issue_id: Optional[str] = None
    error_messages: List[str] = Field(default_factory=list)
    affected_components: List[str] = Field(default_factory=list)
    approximate_location: Optional[str] = None  # e.g., "registration page, submit button"
    evidence: List[str] = Field(default_factory=list)  # quoted text, error codes seen
    possible_behavioral_implications: List[str] = Field(default_factory=list)
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    uncertainties: List[str] = Field(default_factory=list)
    raw_observation: Optional[str] = None  # human-readable summary

    model_config = {"use_enum_values": True}


class PydanticTriageClassification(BaseModel):
    """Triage agent classification output."""
    issue_id: Optional[str] = None
    classification: IssueClassification
    severity: SeverityLevel
    issue_summary: str = Field(default="", max_length=500)
    affected_components: List[str] = Field(default_factory=list)
    supporting_observations: List[str] = Field(default_factory=list)
    missing_information: List[str] = Field(default_factory=list)
    investigation_objective: str = Field(default="Investigate the reported issue and identify root cause", max_length=500)
    assigned_agent: AgentRole = AgentRole.INVESTIGATION
    reason_for_delegation: str = Field(default="Delegate to Investigation Agent for root-cause analysis", max_length=500)

    model_config = {"use_enum_values": True}


class PydanticInvestigationFindings(BaseModel):
    """Investigation agent findings output."""
    issue_id: Optional[str] = None
    investigation_summary: str = Field(default="", max_length=1000)
    suspected_root_cause: Optional[str] = None
    relevant_source_files: List[str] = Field(default_factory=list)
    relevant_code_locations: List[str] = Field(default_factory=list)  # e.g., "app.py:42-55"
    supporting_evidence: List[str] = Field(default_factory=list)
    reasoning: str = Field(default="No root cause identified yet", max_length=2000)
    proposed_fix: Optional[str] = None
    proposed_code_changes: Optional[str] = None  # unified diff or snippet
    recommended_tests: List[str] = Field(default_factory=list)
    actual_test_results: Optional[str] = None
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    remaining_uncertainties: List[str] = Field(default_factory=list)
    challenges_previous_findings: Optional[List[str]] = Field(default_factory=list)  # where it disagreed with other agents

    model_config = {"use_enum_values": True}


class PydanticAgentActivity(BaseModel):
    """Traceable agent activity history."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    agent_role: AgentRole
    action: str
    details: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None


class PydanticFinalReport(BaseModel):
    """Final investigation report presented to developer."""
    issue_id: Optional[str] = None
    original_description: str
    screenshot_reference: Optional[str] = None
    vision_observations: Optional[PydanticVisionObservations] = None
    triage_classification: Optional[PydanticTriageClassification] = None
    investigation_findings: Optional[PydanticInvestigationFindings] = None
    status: IssueStatus = IssueStatus.REPORT_READY
    created_at: datetime
    agent_activity_history: List[PydanticAgentActivity] = Field(default_factory=list)
    evidence_breakdown: Dict[str, List[str]] = Field(default_factory=lambda: {
        "OBSERVED": [],
        "INFERRED": [],
        "CODE_VERIFIED": [],
        "TEST_VERIFIED": [],
        "PROPOSED": [],
    })

    model_config = {"use_enum_values": True}