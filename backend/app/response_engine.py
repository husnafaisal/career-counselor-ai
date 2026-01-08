import os
import logging
from typing import Dict, Any

from openai import OpenAI
from fastapi.concurrency import run_in_threadpool

from .personas import get_system_prompt

logger = logging.getLogger(__name__)


class ResponseEngine:
    """Generates contextual responses using OpenAI"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("BOT_MODEL", "gpt-4.1-mini")
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
        """Generate AI response based on conversation state"""
        try:
            system_prompt = self._build_system_prompt(
                state, intent, hesitation, rules
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ]

            response = await run_in_threadpool(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=self.max_tokens,
                temperature=0.7,
            )

            response_text = response.choices[0].message.content.strip()
            logger.info(f"Generated response ({len(response_text)} chars)")

            return response_text

        except Exception as e:
            logger.error("LLM generation failed", exc_info=True)
            return self._get_fallback_response(intent)

    def _build_system_prompt(
        self,
        state: Dict[str, Any],
        intent: Dict[str, Any],
        hesitation: Dict[str, Any],
        rules: Dict[str, Any]
    ) -> str:
        """Create dynamic system prompt"""
        base_prompt = get_system_prompt()

        stage = state.get("stage", "greeting")
        msg_count = state.get("message_count", 0)
        profile = state.get("user_profile", {})

        rules_text = "\n".join(
            f"- {r}" for r in rules.get("active_rules", [])
        ) or "- Continue naturally"

        return f"""{base_prompt}

## Conversation Context
Stage: {stage}
Message Count: {msg_count}
Trust Built: {state.get('trust_built', False)}
Ready for Pitch: {state.get('ready_for_pitch', False)}

## User Profile
- Interest: {profile.get('interest', 'Unknown')}
- Pain Point: {profile.get('pain_point', 'Unknown')}
- Background: {profile.get('background', 'Unknown')}
- Timeline: {profile.get('timeline', 'Unknown')}
- Main Objection: {profile.get('main_objection', 'None')}

## Detected Intent
- Type: {intent.get('type')}
- Confidence: {intent.get('confidence', 0.5)}

## Hesitation Signals
- Hesitant: {hesitation.get('is_hesitant', False)}
- Buying Signal: {hesitation.get('is_buying_signal', False)}
- Objection Type: {hesitation.get('objection_type', 'None')}

## Rules
{rules_text}
"""

    def _get_fallback_response(self, intent: Dict[str, Any]) -> str:
        """Fallback response if OpenAI fails"""
        fallbacks = {
            "interest": "That’s a great field to explore. What made you curious about it?",
            "pain": "That sounds frustrating. Want to tell me more about what’s been difficult?",
            "objection": "That’s a valid concern. Let’s talk it through together.",
            "buying_signal": "Nice! What would you like to know before moving ahead?",
            "general": "Tell me a bit more about your situation."
        }

        return fallbacks.get(
            intent.get("type", "general"),
            "I’m here to help. What’s on your mind?"
        )
