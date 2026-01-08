import uuid
import asyncio
from typing import Dict, Optional, List, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

from .schemas import (
    ConversationState, UserProfile, ConversationStage,
    Message, MessageRole, Intent, HesitationSignal
)

logger = logging.getLogger(__name__)

class StateManager:
    """Manages conversation state and session data"""
    
    def __init__(self):
        # In-memory storage (replace with Redis for production)
        self.sessions: Dict[str, ConversationState] = {}
        self.message_history: Dict[str, List[Message]] = {}
        self.analytics_data: Dict[str, Any] = defaultdict(int)
        
        logger.info("StateManager initialized")
    
    async def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid.uuid4())
        
        self.sessions[session_id] = ConversationState(
            session_id=session_id,
            stage=ConversationStage.GREETING,
            message_count=0,
            user_profile=UserProfile(),
            trust_built=False,
            ready_for_pitch=False,
            last_active=datetime.now()
        )
        
        self.message_history[session_id] = []
        self.analytics_data['total_sessions'] += 1
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    async def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation state for a session"""
        if session_id not in self.sessions:
            return None
        
        state = self.sessions[session_id]
        return state.model_dump()
    
    async def update_state(
        self,
        session_id: str,
        intent: Intent,
        hesitation: HesitationSignal
    ) -> Dict[str, Any]:
        """Update conversation state based on detected intent and signals"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        state = self.sessions[session_id]
        state.last_active = datetime.now()
        
        # Update user profile based on intent
        if intent.type.value == "interest" and intent.value:
            state.user_profile.interest = intent.value
            self.analytics_data[f'interest_{intent.value}'] += 1
        
        elif intent.type.value == "pain" and intent.value:
            state.user_profile.pain_point = intent.value
        
        elif intent.type.value == "background" and intent.value:
            state.user_profile.background = intent.value
        
        elif intent.type.value == "timeline" and intent.value:
            state.user_profile.timeline = intent.value
        
        elif intent.type.value == "objection" and intent.value:
            state.user_profile.main_objection = intent.value
            if intent.value not in state.objections_raised:
                state.objections_raised.append(intent.value)
                self.analytics_data[f'objection_{intent.value}'] += 1
        
        # Track buying signals and hesitation
        if hesitation.is_buying_signal:
            state.buying_signals += 1
        
        if hesitation.is_hesitant:
            state.hesitation_signals += 1
        
        # Update conversation stage based on message count and profile completeness
        state.stage = self._determine_stage(state)
        
        # Update trust and pitch readiness
        if state.message_count >= 3:
            state.trust_built = True
        
        if (state.trust_built and 
            state.message_count >= 6 and
            state.user_profile.interest and
            state.user_profile.pain_point):
            state.ready_for_pitch = True
        
        return state.model_dump()
    
    def _determine_stage(self, state: ConversationState) -> ConversationStage:
        """Determine conversation stage based on state"""
        msg_count = state.message_count
        profile = state.user_profile
        
        # Stage 1: Trust Building (Messages 1-3)
        if msg_count <= 3:
            if profile.interest:
                return ConversationStage.EXPLORING_MOTIVATION
            return ConversationStage.TRUST_BUILDING
        
        # Stage 2: Diagnosis (Messages 4-6)
        elif msg_count <= 6:
            if profile.timeline:
                return ConversationStage.SURFACING_PAIN
            if profile.background:
                return ConversationStage.UNDERSTANDING_URGENCY
            return ConversationStage.DIAGNOSING_PROBLEM
        
        # Stage 3: Solution Introduction (Messages 7-9)
        elif msg_count <= 9:
            if state.ready_for_pitch:
                return ConversationStage.SOFT_INTRODUCTION
            return ConversationStage.SURFACING_PAIN
        
        # Stage 4: Objection Handling & Closing (Messages 10+)
        else:
            if state.objections_raised:
                return ConversationStage.HANDLING_OBJECTION
            if state.buying_signals >= 2:
                return ConversationStage.CLOSING
            return ConversationStage.SOFT_INTRODUCTION
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict] = None
    ):
        """Add a message to conversation history"""
        if session_id not in self.message_history:
            self.message_history[session_id] = []
        
        message = Message(
            role=MessageRole(role),
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        self.message_history[session_id].append(message)
    
    async def get_history(self, session_id: str) -> Optional[List[Dict]]:
        """Get conversation history for a session"""
        if session_id not in self.message_history:
            return None
        
        return [msg.model_dump() for msg in self.message_history[session_id]]
    
    async def reset_session(self, session_id: str) -> bool:
        """Reset a conversation session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id] = ConversationState(
            session_id=session_id,
            stage=ConversationStage.GREETING,
            message_count=0,
            user_profile=UserProfile(),
            trust_built=False,
            ready_for_pitch=False
        )
        
        self.message_history[session_id] = []
        logger.info(f"Reset session: {session_id}")
        return True
    
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24):
        """Remove inactive sessions older than max_age_hours"""
        current_time = datetime.now()
        sessions_to_remove = []
        
        for session_id, state in self.sessions.items():
            age = current_time - state.last_active
            if age > timedelta(hours=max_age_hours):
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            del self.sessions[session_id]
            if session_id in self.message_history:
                del self.message_history[session_id]
        
        if sessions_to_remove:
            logger.info(f"Cleaned up {len(sessions_to_remove)} inactive sessions")
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get analytics data"""
        total_sessions = len(self.sessions)
        active_sessions = sum(
            1 for state in self.sessions.values()
            if (datetime.now() - state.last_active).seconds < 3600
        )
        
        # Calculate average conversation length
        total_messages = sum(state.message_count for state in self.sessions.values())
        avg_length = total_messages / total_sessions if total_sessions > 0 else 0
        
        # Calculate conversion rate (buying_signals >= 2)
        conversions = sum(
            1 for state in self.sessions.values()
            if state.buying_signals >= 2
        )
        conversion_rate = (conversions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Common objections
        common_objections = {
            "cost": self.analytics_data.get('objection_cost', 0),
            "time": self.analytics_data.get('objection_time', 0),
            "hesitation": self.analytics_data.get('objection_hesitation', 0)
        }
        
        # Drop-off stages
        drop_off_stages = defaultdict(int)
        for state in self.sessions.values():
            if state.message_count < 10:
                drop_off_stages[state.stage.value] += 1
        
        # Interest distribution
        interest_dist = {
            "data_science": self.analytics_data.get('interest_data science', 0),
            "web_development": self.analytics_data.get('interest_web development', 0),
            "digital_marketing": self.analytics_data.get('interest_digital marketing', 0)
        }
        
        # Average time to pitch
        pitch_times = [
            state.message_count for state in self.sessions.values()
            if state.ready_for_pitch
        ]
        avg_time_to_pitch = sum(pitch_times) / len(pitch_times) if pitch_times else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "avg_conversation_length": round(avg_length, 2),
            "conversion_rate": round(conversion_rate, 2),
            "common_objections": common_objections,
            "drop_off_stages": dict(drop_off_stages),
            "avg_time_to_pitch": round(avg_time_to_pitch, 2),
            "interest_distribution": interest_dist
        }
    
    async def cleanup(self):
        """Cleanup resources on shutdown"""
        logger.info("StateManager cleanup completed")