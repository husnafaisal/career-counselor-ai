from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    """Message roles in conversation"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStage(str, Enum):
    """Stages of conversation funnel"""
    GREETING = "greeting"
    TRUST_BUILDING = "trust_building"
    EXPLORING_MOTIVATION = "exploring_motivation"
    DIAGNOSING_PROBLEM = "diagnosing_problem"
    UNDERSTANDING_URGENCY = "understanding_urgency"
    SURFACING_PAIN = "surfacing_pain"
    SOFT_INTRODUCTION = "soft_introduction"
    HANDLING_OBJECTION = "handling_objection"
    CLOSING = "closing"
    POST_ENROLLMENT = "post_enrollment"

class IntentType(str, Enum):
    """Types of user intent"""
    INTEREST = "interest"
    PAIN = "pain"
    BACKGROUND = "background"
    TIMELINE = "timeline"
    OBJECTION = "objection"
    BUYING_SIGNAL = "buying_signal"
    QUESTION = "question"
    GENERAL = "general"

class ObjectionType(str, Enum):
    """Types of objections"""
    COST = "cost"
    TIME = "time"
    DOUBT = "doubt"
    HESITATION = "hesitation"
    COMPARISON = "comparison"

# Request/Response Models
class ChatRequest(BaseModel):
    """Chat message request"""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional metadata")

class ChatResponse(BaseModel):
    """Chat message response"""
    response: str = Field(..., description="Bot response message")
    session_id: str = Field(..., description="Session identifier")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Response metadata")

class SessionCreate(BaseModel):
    """Session creation request"""
    user_metadata: Optional[Dict[str, Any]] = Field(default=None, description="Optional user metadata")

class Message(BaseModel):
    """Individual message in conversation"""
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None

class UserProfile(BaseModel):
    """User profile built during conversation"""
    interest: Optional[str] = None
    pain_point: Optional[str] = None
    background: Optional[str] = None
    timeline: Optional[str] = None
    main_objection: Optional[str] = None
    budget_range: Optional[str] = None
    career_goal: Optional[str] = None
    constraints: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)

class ConversationState(BaseModel):
    """Complete conversation state"""
    session_id: str
    stage: ConversationStage = ConversationStage.GREETING
    message_count: int = 0
    user_profile: UserProfile = Field(default_factory=UserProfile)
    trust_built: bool = False
    ready_for_pitch: bool = False
    objections_raised: List[str] = Field(default_factory=list)
    courses_mentioned: List[str] = Field(default_factory=list)
    buying_signals: int = 0
    hesitation_signals: int = 0
    sentiment_score: float = 0.5
    last_active: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Intent(BaseModel):
    """Detected user intent"""
    type: IntentType
    value: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    entities: Dict[str, Any] = Field(default_factory=dict)

class HesitationSignal(BaseModel):
    """Detected hesitation or buying signal"""
    is_hesitant: bool = False
    is_buying_signal: bool = False
    objection_type: Optional[ObjectionType] = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    triggers: List[str] = Field(default_factory=list)

class AnalyticsResponse(BaseModel):
    """Analytics dashboard data"""
    total_sessions: int
    active_sessions: int
    avg_conversation_length: float
    conversion_rate: float
    common_objections: Dict[str, int]
    drop_off_stages: Dict[str, int]
    avg_time_to_pitch: float
    interest_distribution: Dict[str, int]

class Course(BaseModel):
    """Course information"""
    id: str
    name: str
    description: str
    duration: str
    price: float
    currency: str = "INR"
    outcomes: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    start_date: Optional[str] = None
    availability: int
    emi_available: bool = False
    emi_details: Optional[Dict[str, Any]] = None

class ResponseContext(BaseModel):
    """Context for generating responses"""
    user_message: str
    state: ConversationState
    intent: Intent
    hesitation: HesitationSignal
    retrieved_content: Optional[str] = None
    rules_triggered: List[str] = Field(default_factory=list)