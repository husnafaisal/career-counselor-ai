import os
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class ConversationRules:
    """Defines and enforces conversation rules"""
    
    # Configuration from environment
    PITCH_THRESHOLD = int(os.getenv("PITCH_THRESHOLD_MESSAGES", 6))
    TRUST_BUILDING_MESSAGES = int(os.getenv("TRUST_BUILDING_MESSAGES", 3))
    MAX_OBJECTION_REPETITION = 2
    
    @classmethod
    def evaluate(cls, state: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate which rules apply to current state"""
        active_rules = []
        warnings = []
        
        msg_count = state.get('message_count', 0)
        stage = state.get('stage', '')
        profile = state.get('user_profile', {})
        trust_built = state.get('trust_built', False)
        ready_for_pitch = state.get('ready_for_pitch', False)
        objections_raised = state.get('objections_raised', [])
        
        # Rule 1: Don't pitch too early
        if msg_count < cls.PITCH_THRESHOLD:
            active_rules.append(
                "DO NOT mention courses yet. Focus on understanding user needs and building trust."
            )
        
        # Rule 2: Build trust first
        if msg_count < cls.TRUST_BUILDING_MESSAGES:
            active_rules.append(
                "Primary goal: Build rapport. Ask open-ended questions. Validate emotions."
            )
        
        # Rule 3: Complete profile before pitching
        if not trust_built or not ready_for_pitch:
            missing = cls._get_missing_profile_info(profile)
            if missing:
                active_rules.append(
                    f"Gather missing information: {', '.join(missing)}. Ask naturally, don't interrogate."
                )
        
        # Rule 4: Only pitch when appropriate
        if ready_for_pitch and msg_count >= cls.PITCH_THRESHOLD:
            active_rules.append(
                "User is ready for course introduction. Frame it as solving THEIR problem, not a generic pitch."
            )
        
        # Rule 5: Address objections properly
        if objections_raised:
            most_recent = objections_raised[-1]
            repetition_count = objections_raised.count(most_recent)
            
            if repetition_count >= cls.MAX_OBJECTION_REPETITION:
                warnings.append(
                    f"User has raised '{most_recent}' objection {repetition_count} times. They may not be ready. Consider backing off or offering alternatives."
                )
            
            active_rules.append(
                f"Address the '{most_recent}' objection with empathy and data. Don't be defensive."
            )
        
        # Rule 6: Never make false promises
        active_rules.append(
            "NEVER guarantee outcomes. Use phrases like 'most students', 'typical results', 'based on our data'."
        )
        
        # Rule 7: Respect stated constraints
        if profile.get('main_objection') == 'cost':
            active_rules.append(
                "User is cost-sensitive. Emphasize ROI, offer EMI options, mention money-back guarantee."
            )
        
        if profile.get('main_objection') == 'time':
            active_rules.append(
                "User is time-constrained. Emphasize self-paced nature, provide weekly hour breakdown, lifetime access."
            )
        
        # Rule 8: Use their language
        if profile.get('interest'):
            active_rules.append(
                f"User is interested in '{profile['interest']}'. Always reference this field in your responses."
            )
        
        # Rule 9: Maintain consultative tone
        active_rules.append(
            "Be consultative, not transactional. You're a career counselor, not a sales rep."
        )
        
        # Rule 10: Give them autonomy
        active_rules.append(
            "Always give users choice. Use phrases like 'What feels right to you?' not 'You should'."
        )
        
        return {
            'active_rules': active_rules,
            'warnings': warnings,
            'can_pitch': ready_for_pitch and msg_count >= cls.PITCH_THRESHOLD,
            'missing_info': cls._get_missing_profile_info(profile)
        }
    
    @classmethod
    def _get_missing_profile_info(cls, profile: Dict[str, Any]) -> List[str]:
        """Identify missing critical profile information"""
        missing = []
        
        if not profile.get('interest'):
            missing.append('career interest/field')
        
        if not profile.get('pain_point'):
            missing.append('current challenge/pain point')
        
        if not profile.get('background'):
            missing.append('experience level')
        
        return missing
    
    @classmethod
    def should_back_off(cls, state: Dict[str, Any]) -> bool:
        """Determine if bot should back off from selling"""
        # Back off if:
        # 1. Same objection raised 3+ times
        # 2. User explicitly says "not interested"
        # 3. Conversation is getting circular
        
        objections = state.get('objections_raised', [])
        if objections:
            most_common_count = max(objections.count(obj) for obj in set(objections))
            if most_common_count >= 3:
                return True
        
        msg_count = state.get('message_count', 0)
        buying_signals = state.get('buying_signals', 0)
        
        # If 15+ messages and no buying signals, user likely not interested
        if msg_count >= 15 and buying_signals == 0:
            return True
        
        return False
    
    @classmethod
    def get_guardrails(cls) -> List[str]:
        """Get list of hard guardrails the bot must never violate"""
        return [
            "NEVER use fake urgency tactics (limited seats, prices going up soon, etc.) unless true",
            "NEVER make promises about guaranteed job placement or salary increases",
            "NEVER pressure users with aggressive closing tactics",
            "NEVER recommend a course that doesn't fit the user's stated needs",
            "NEVER ignore budget constraints or push expensive options on cost-conscious users",
            "NEVER dismiss objections or make users feel wrong for hesitating",
            "NEVER lie about course details, outcomes, or policies",
            "NEVER be condescending or judgmental about their current situation",
            "ALWAYS provide accurate information about refund policies, time commitments, etc.",
            "ALWAYS respect when a user says they need to think about it"
        ]