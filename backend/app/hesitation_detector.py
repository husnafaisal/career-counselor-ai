from typing import Dict, Any, List
import logging

from .schemas import HesitationSignal, ObjectionType

logger = logging.getLogger(__name__)

class HesitationDetector:
    """Detects hesitation signals and buying intent"""
    
    def __init__(self):
        # Strong buying signals
        self.buying_signals = [
            'how do i sign up', 'how to enroll', 'i want to join',
            'when can i start', 'next batch', 'i\'m ready',
            'let\'s do this', 'sounds good', 'i\'m interested',
            'what\'s the process', 'how to register', 'book my spot'
        ]
        
        # Hesitation signals
        self.hesitation_signals = [
            'think about it', 'not sure', 'maybe', 'let me check',
            'need to discuss', 'talk to', 'i\'ll get back',
            'consider', 'decide later', 'need time'
        ]
        
        # Objection triggers
        self.objection_triggers = {
            ObjectionType.COST: [
                'too expensive', 'can\'t afford', 'too much money',
                'high price', 'costly', 'budget', 'cheaper option'
            ],
            ObjectionType.TIME: [
                'don\'t have time', 'too busy', 'full schedule',
                'no time', 'work full time', 'family commitments'
            ],
            ObjectionType.DOUBT: [
                'will it work', 'is it worth', 'really help',
                'guarantee', 'sure about', 'proven', 'actually'
            ],
            ObjectionType.COMPARISON: [
                'other options', 'compared to', 'what about',
                'better than', 'versus', 'difference between'
            ]
        }
        
        # Positive sentiment indicators
        self.positive_indicators = [
            'great', 'perfect', 'awesome', 'excellent', 'sounds good',
            'interesting', 'excited', 'love', 'like', 'helpful'
        ]
        
        # Negative sentiment indicators
        self.negative_indicators = [
            'worried', 'concerned', 'afraid', 'scared', 'anxious',
            'nervous', 'uncertain', 'doubt', 'problem', 'issue'
        ]
        
        logger.info("HesitationDetector initialized")
    
    def analyze(
        self,
        message: str,
        state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze message for hesitation and buying signals"""
        message_lower = message.lower()
        
        # Initialize signal
        signal = {
            'is_hesitant': False,
            'is_buying_signal': False,
            'objection_type': None,
            'confidence': 0.5,
            'triggers': []
        }
        
        # Check for buying signals
        buying_matches = [
            trigger for trigger in self.buying_signals
            if trigger in message_lower
        ]
        if buying_matches:
            signal['is_buying_signal'] = True
            signal['confidence'] = 0.9
            signal['triggers'] = buying_matches
            return signal
        
        # Check for hesitation signals
        hesitation_matches = [
            trigger for trigger in self.hesitation_signals
            if trigger in message_lower
        ]
        if hesitation_matches:
            signal['is_hesitant'] = True
            signal['confidence'] = 0.8
            signal['triggers'] = hesitation_matches
        
        # Check for specific objections
        for obj_type, triggers in self.objection_triggers.items():
            matches = [t for t in triggers if t in message_lower]
            if matches:
                signal['is_hesitant'] = True
                signal['objection_type'] = obj_type.value
                signal['confidence'] = 0.85
                signal['triggers'].extend(matches)
                break
        
        # Analyze sentiment
        positive_count = sum(
            1 for ind in self.positive_indicators
            if ind in message_lower
        )
        negative_count = sum(
            1 for ind in self.negative_indicators
            if ind in message_lower
        )
        
        # Adjust confidence based on sentiment
        if negative_count > positive_count:
            signal['is_hesitant'] = True
            signal['confidence'] = min(signal['confidence'] + 0.1, 1.0)
        elif positive_count > negative_count and not signal['is_hesitant']:
            signal['is_buying_signal'] = True
            signal['confidence'] = min(signal['confidence'] + 0.15, 1.0)
        
        # Context-aware adjustments
        message_count = state.get('message_count', 0)
        ready_for_pitch = state.get('ready_for_pitch', False)
        
        # If user asks multiple questions after pitch, might be hesitant
        if ready_for_pitch and message_count > 8 and message.endswith('?'):
            signal['is_hesitant'] = True
            signal['confidence'] = max(signal['confidence'], 0.6)
        
        # Short, positive responses after pitch = buying signal
        if ready_for_pitch and len(message.split()) <= 5 and positive_count > 0:
            signal['is_buying_signal'] = True
            signal['confidence'] = 0.75
        
        return signal
    
    def analyze_conversation_momentum(
        self,
        state: Dict[str, Any],
        message_history: List[Dict]
    ) -> Dict[str, Any]:
        """Analyze overall conversation momentum"""
        if not message_history:
            return {'momentum': 'neutral', 'score': 0.5}
        
        recent_messages = message_history[-5:]  # Last 5 messages
        
        hesitation_count = 0
        buying_count = 0
        question_count = 0
        
        for msg in recent_messages:
            if msg['role'] == 'user':
                content = msg['content'].lower()
                
                if any(hs in content for hs in self.hesitation_signals):
                    hesitation_count += 1
                
                if any(bs in content for bs in self.buying_signals):
                    buying_count += 1
                
                if content.strip().endswith('?'):
                    question_count += 1
        
        # Calculate momentum score
        momentum_score = (buying_count * 2 - hesitation_count - question_count * 0.5) / 5
        momentum_score = max(0, min(1, (momentum_score + 1) / 2))  # Normalize to 0-1
        
        # Determine momentum direction
        if momentum_score > 0.6:
            momentum = 'positive'
        elif momentum_score < 0.4:
            momentum = 'negative'
        else:
            momentum = 'neutral'
        
        return {
            'momentum': momentum,
            'score': round(momentum_score, 2),
            'hesitation_count': hesitation_count,
            'buying_count': buying_count,
            'question_count': question_count
        }
    
    def should_address_hesitation(
        self,
        signal: Dict[str, Any],
        state: Dict[str, Any]
    ) -> bool:
        """Determine if hesitation should be explicitly addressed"""
        # Address hesitation if:
        # 1. High confidence hesitation signal
        # 2. After pitch has been made
        # 3. Multiple hesitation signals in conversation
        
        if signal['confidence'] >= 0.75 and signal['is_hesitant']:
            return True
        
        if (state.get('ready_for_pitch', False) and 
            state.get('hesitation_signals', 0) >= 2):
            return True
        
        if signal['objection_type'] is not None:
            return True
        
        return False