import re
from typing import Dict, Any, List
import logging

from .schemas import Intent, IntentType

logger = logging.getLogger(__name__)

class IntentDetector:
    """Detects user intent from messages"""
    
    def __init__(self):
        # Interest keywords mapping
        self.interest_keywords = {
            'data science': [
                'data science', 'data analyst', 'machine learning', 'ml',
                'ai', 'artificial intelligence', 'analytics', 'big data',
                'python data', 'data engineer', 'statistics'
            ],
            'web development': [
                'web dev', 'web development', 'frontend', 'backend',
                'fullstack', 'full stack', 'website', 'react', 'node',
                'javascript', 'html', 'css', 'web design'
            ],
            'digital marketing': [
                'marketing', 'digital marketing', 'seo', 'social media',
                'content marketing', 'google ads', 'facebook ads',
                'email marketing', 'growth hacking', 'instagram'
            ],
            'design': [
                'design', 'ui', 'ux', 'user interface', 'user experience',
                'graphic design', 'figma', 'adobe', 'photoshop', 'illustrator'
            ],
            'cloud computing': [
                'cloud', 'aws', 'azure', 'gcp', 'devops', 'kubernetes',
                'docker', 'cloud engineer', 'cloud architecture'
            ],
            'cybersecurity': [
                'security', 'cybersecurity', 'ethical hacking', 'penetration',
                'infosec', 'network security', 'security analyst'
            ]
        }
        
        # Pain point keywords
        self.pain_keywords = {
            'overwhelmed': [
                'stuck', 'confused', 'lost', 'overwhelmed', 'don\'t know',
                'unsure', 'uncertain', 'no idea', 'help', 'guidance'
            ],
            'self_learning_failed': [
                'tried', 'youtube', 'tutorial', 'self-learn', 'online course',
                'gave up', 'didn\'t work', 'couldn\'t finish', 'incomplete',
                'struggled', 'difficult'
            ],
            'no_direction': [
                'where to start', 'how to begin', 'first step', 'roadmap',
                'path', 'direction', 'guide me', 'show me', 'what next'
            ],
            'fear_of_failure': [
                'afraid', 'scared', 'worry', 'nervous', 'anxious',
                'what if', 'fail', 'wrong choice', 'mistake'
            ]
        }
        
        # Background keywords
        self.background_keywords = {
            'beginner': [
                'beginner', 'no experience', 'never', 'starting', 'fresh',
                'new to', 'zero', 'scratch', 'basics', 'fundamentals'
            ],
            'intermediate': [
                'some experience', 'tried before', 'basic', 'know a little',
                'dabbled', 'familiar', 'heard of', 'played with'
            ],
            'advanced': [
                'experienced', 'professional', 'years', 'expert', 'worked',
                'career', 'currently', 'job'
            ]
        }
        
        # Timeline keywords
        self.timeline_keywords = {
            'urgent': [
                'soon', 'quickly', 'fast', 'asap', 'immediate', 'month',
                '3 months', '6 months', 'need to', 'urgent', 'deadline'
            ],
            'flexible': [
                'exploring', 'considering', 'thinking about', 'maybe',
                'eventually', 'long term', 'no rush', 'taking time'
            ]
        }
        
        # Objection keywords
        self.objection_keywords = {
            'cost': [
                'expensive', 'cost', 'price', 'afford', 'money', 'budget',
                'cheap', 'free', 'payment', 'too much', 'costly'
            ],
            'time': [
                'time', 'busy', 'schedule', 'hours', 'commitment',
                'don\'t have time', 'work full time', 'no time'
            ],
            'doubt': [
                'worth it', 'really', 'sure', 'guarantee', 'promise',
                'actually', 'proven', 'reviews', 'testimonials'
            ],
            'hesitation': [
                'think about it', 'not sure', 'maybe', 'let me',
                'consider', 'decide later', 'need to', 'have to'
            ]
        }
        
        # Buying signal keywords
        self.buying_keywords = [
            'how do i', 'sign up', 'enroll', 'join', 'register',
            'start', 'when', 'next batch', 'available', 'interested',
            'want to', 'ready', 'let\'s do', 'okay', 'sounds good'
        ]
        
        logger.info("IntentDetector initialized with keyword mappings")
    
    def analyze(self, message: str, state: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze message and detect intent"""
        message_lower = message.lower()
        
        # Check for interests
        for interest, keywords in self.interest_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._create_intent(
                    IntentType.INTEREST,
                    interest,
                    confidence=0.8,
                    entities={'mentioned_keywords': [kw for kw in keywords if kw in message_lower]}
                )
        
        # Check for pain points
        for pain_type, keywords in self.pain_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._create_intent(
                    IntentType.PAIN,
                    pain_type,
                    confidence=0.75
                )
        
        # Check for background
        for bg_level, keywords in self.background_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._create_intent(
                    IntentType.BACKGROUND,
                    bg_level,
                    confidence=0.7
                )
        
        # Check for timeline
        for timeline, keywords in self.timeline_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._create_intent(
                    IntentType.TIMELINE,
                    timeline,
                    confidence=0.7
                )
        
        # Check for objections
        for objection, keywords in self.objection_keywords.items():
            if any(kw in message_lower for kw in keywords):
                return self._create_intent(
                    IntentType.OBJECTION,
                    objection,
                    confidence=0.85
                )
        
        # Check for buying signals
        if any(kw in message_lower for kw in self.buying_keywords):
            return self._create_intent(
                IntentType.BUYING_SIGNAL,
                "interested",
                confidence=0.9
            )
        
        # Check if it's a question
        if message.strip().endswith('?') or any(
            message_lower.startswith(q) for q in ['what', 'how', 'when', 'where', 'why', 'is', 'can', 'do']
        ):
            return self._create_intent(
                IntentType.QUESTION,
                "information_seeking",
                confidence=0.6
            )
        
        # Default to general
        return self._create_intent(IntentType.GENERAL, None, confidence=0.5)
    
    def _create_intent(
        self,
        intent_type: IntentType,
        value: str = None,
        confidence: float = 0.5,
        entities: Dict = None
    ) -> Dict[str, Any]:
        """Create intent dictionary"""
        return {
            'type': intent_type.value,
            'value': value,
            'confidence': confidence,
            'entities': entities or {}
        }
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract named entities from message"""
        entities = {}
        
        # Extract numbers (could be budget, timeline, etc.)
        numbers = re.findall(r'\d+', message)
        if numbers:
            entities['numbers'] = numbers
        
        # Extract currency mentions
        if any(curr in message.lower() for curr in ['₹', 'rupees', 'inr', 'lakh', 'thousand']):
            entities['currency_mentioned'] = True
        
        # Extract time periods
        time_periods = re.findall(
            r'(\d+)\s*(month|week|year|day)',
            message.lower()
        )
        if time_periods:
            entities['time_periods'] = time_periods
        
        return entities