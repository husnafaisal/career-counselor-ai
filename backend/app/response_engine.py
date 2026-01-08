import os
import logging
from typing import Dict, Any, Optional
from anthropic import Anthropic

from .schemas import Intent, HesitationSignal
from .personas import get_system_prompt
from .rules import ConversationRules

logger = logging.getLogger(__name__)

class ResponseEngine:
    """Generates contextual responses using LLM"""
    
    def __init__(self):
        self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = os.getenv("BOT_MODEL", "claude-sonnet-4-20250514")
        self.max_tokens = 1024
        
        logger.info(f"ResponseEngine initialized with model: {self.model}")
    
    async def generate(
        self,
        user_message: str,
        state: Dict[str, Any],
        intent: Dict[str, Any],
        hesitation: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> str:
        """Generate contextual response"""
        try:
            # Build system prompt with current state
            system_prompt = self._build_system_prompt(state, intent, hesitation, rules)
            
            # Build conversation history
            conversation_history = self._build_conversation_context(state)
            
            # Add current user message
            conversation_history.append({
                "role": "user",
                "content": user_message
            })
            
            # Generate response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system_prompt,
                messages=conversation_history
            )
            
            response_text = response.content[0].text
            logger.info(f"Generated response ({len(response_text)} chars)")
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}", exc_info=True)
            return self._get_fallback_response(intent)
    
    def _build_system_prompt(
        self,
        state: Dict[str, Any],
        intent: Dict[str, Any],
        hesitation: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> str:
        """Build dynamic system prompt based on conversation state"""
        base_prompt = get_system_prompt()
        
        # Add state-specific instructions
        stage = state.get('stage', 'greeting')
        msg_count = state.get('message_count', 0)
        profile = state.get('user_profile', {})
        
        state_context = f"""
## Current Conversation Context

**Stage**: {stage}
**Message Count**: {msg_count}
**Trust Built**: {state.get('trust_built', False)}
**Ready for Pitch**: {state.get('ready_for_pitch', False)}

**User Profile**:
- Interest: {profile.get('interest', 'Unknown')}
- Pain Point: {profile.get('pain_point', 'Unknown')}
- Background: {profile.get('background', 'Unknown')}
- Timeline: {profile.get('timeline', 'Unknown')}
- Main Objection: {profile.get('main_objection', 'None raised yet')}

**Detected Intent**: {intent.get('type')} - {intent.get('value')}
**Confidence**: {intent.get('confidence', 0.5)}

**Hesitation Analysis**:
- Is Hesitant: {hesitation.get('is_hesitant', False)}
- Is Buying Signal: {hesitation.get('is_buying_signal', False)}
- Objection Type: {hesitation.get('objection_type', 'None')}
"""
        
        # Add stage-specific guidance
        stage_guidance = self._get_stage_guidance(stage, state)
        
        # Add rules to follow
        rules_text = "\n".join([f"- {rule}" for rule in rules.get('active_rules', [])])
        
        full_prompt = f"""{base_prompt}

{state_context}

{stage_guidance}

## Rules to Follow
{rules_text if rules_text else "- Proceed with natural conversation flow"}

## Important Reminders
- Remember context from earlier in the conversation
- Be warm and consultative, never pushy
- Validate emotions before offering solutions
- Position courses as natural next steps, not hard sells
- Use the user's own words and interests in your responses
"""
        
        return full_prompt
    
    def _get_stage_guidance(self, stage: str, state: Dict[str, Any]) -> str:
        """Get stage-specific guidance for response generation"""
        guidance = {
            'greeting': """
## Stage Guidance: Greeting
- Welcome the user warmly
- Ask open-ended questions to understand what brings them here
- DO NOT mention courses yet - focus on understanding their needs
""",
            'trust_building': """
## Stage Guidance: Trust Building
- Validate any emotions they express
- Ask clarifying questions about their situation
- Show empathy and understanding
- Still NO course mentions - keep building rapport
""",
            'exploring_motivation': """
## Stage Guidance: Exploring Motivation
- Dig deeper into WHY they're interested in this field
- Distinguish between external pressure and genuine interest
- Help them articulate their goals
- Continue building trust - courses not yet appropriate
""",
            'diagnosing_problem': """
## Stage Guidance: Diagnosing Problem
- Identify specific pain points and obstacles
- Understand what they've tried before
- Surface the gap between where they are and where they want to be
- You can hint at solutions but don't pitch yet
""",
            'surfacing_pain': """
## Stage Guidance: Surfacing Pain
- Help them feel the cost of inaction
- Normalize their struggles
- Create urgency (if timeline is tight)
- Prepare for solution introduction in next response
""",
            'soft_introduction': """
## Stage Guidance: Soft Introduction
- NOW you can introduce your course as a bridge to their goals
- Frame it as solving THEIR specific problem
- Use their own words: "You mentioned you're [problem]... our course addresses exactly that"
- Be specific about outcomes and differentiation
- Keep it consultative, not salesy
""",
            'handling_objection': """
## Stage Guidance: Handling Objections
- Take the objection seriously, don't dismiss it
- Provide concrete data and details
- Reframe objections (cost → investment, time → efficiency)
- Offer alternatives (EMI, self-paced, etc.)
- Ask clarifying questions to understand the real concern
""",
            'closing': """
## Stage Guidance: Closing
- Make enrollment easy and clear
- Provide next steps
- Remove remaining friction (money-back guarantee, etc.)
- Create gentle urgency (batch size, start date) without pressure
- Give them autonomy: "What feels right to you?"
"""
        }
        
        return guidance.get(stage, "## Proceed with natural conversation")
    
    def _build_conversation_context(self, state: Dict[str, Any]) -> list:
        """Build conversation history for context"""
        # In a real implementation, you'd fetch message history
        # For now, we'll keep a minimal context window
        return []
    
    def _get_fallback_response(self, intent: Dict[str, Any]) -> str:
        """Generate fallback response if LLM fails"""
        fallbacks = {
            'interest': "That's a great field to explore! Tell me more about what draws you to it.",
            'pain': "I hear you - that can be really challenging. Let's work through this together.",
            'objection': "That's a valid concern. Let me provide some more information that might help.",
            'buying_signal': "Great! I'd love to help you get started. What questions do you have?",
            'general': "Thanks for sharing that. Could you tell me a bit more about your situation?"
        }
        
        intent_type = intent.get('type', 'general')
        return fallbacks.get(intent_type, "I appreciate you sharing that. How can I help you today?")