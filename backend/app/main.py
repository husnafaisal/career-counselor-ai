from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from typing import Dict, Optional
import os
from dotenv import load_dotenv

from .schemas import ChatRequest, ChatResponse, SessionCreate, AnalyticsResponse
from .state_manager import StateManager
from .intent_detector import IntentDetector
from .hesitation_detector import HesitationDetector
from .response_engine import ResponseEngine
from .rules import ConversationRules
from app.middleware.request_id import request_id_middleware




# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
state_manager: Optional[StateManager] = None
intent_detector: Optional[IntentDetector] = None
hesitation_detector: Optional[HesitationDetector] = None
response_engine: Optional[ResponseEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup application resources"""
    global state_manager, intent_detector, hesitation_detector, response_engine
    
    logger.info("Starting Career Counselor AI...")
    
    # Initialize components
    state_manager = StateManager()
    intent_detector = IntentDetector()
    hesitation_detector = HesitationDetector()
    response_engine = ResponseEngine()
    
    logger.info("All components initialized successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down Career Counselor AI...")
    await state_manager.cleanup()

# Create FastAPI app
app = FastAPI(
    title="Career Counselor AI API",
    description="Intelligent career guidance chatbot with psychological principles",
    version="1.0.0",
    lifespan=lifespan
)
app.middleware("http")(request_id_middleware)
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Career Counselor AI",
        "version": "1.0.0"
    }

@app.post("/api/sessions", response_model=Dict[str, str])
async def create_session():
    """Create a new conversation session"""
    try:
        session_id = await state_manager.create_session()
        logger.info(f"Created new session: {session_id}")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create session")

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        session_id = request.session_id
        user_message = request.message
        
        logger.info(f"Session {session_id}: Received message: {user_message[:50]}...")
        
        # Get conversation state
        state = await state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update message count
        state['message_count'] += 1
        
        # Detect user intent
        intent = intent_detector.analyze(user_message, state)
        logger.info(f"Session {session_id}: Detected intent - {intent['type']}: {intent['value']}")
        
        # Detect hesitation/buying signals
        hesitation = hesitation_detector.analyze(user_message, state)
        
        # Update state based on intent
        state = await state_manager.update_state(session_id, intent, hesitation)
        
        # Check conversation rules
        rules_check = ConversationRules.evaluate(state)
        
        # Generate response
        response_text = await response_engine.generate(
            user_message=user_message,
            state=state,
            intent=intent,
            hesitation=hesitation,
            rules=rules_check
        )
        
        # Add messages to history
        await state_manager.add_message(session_id, "user", user_message)
        await state_manager.add_message(session_id, "assistant", response_text)
        
        logger.info(f"Session {session_id}: Generated response ({len(response_text)} chars)")
        
        return ChatResponse(
            response=response_text,
            session_id=session_id,
            metadata={
                "stage": state['stage'],
                "intent_type": intent['type'],
                "message_count": state['message_count'],
                "trust_level": state.get('trust_built', False)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/sessions/{session_id}/state")
async def get_session_state(session_id: str):
    """Get current conversation state for a session"""
    try:
        state = await state_manager.get_state(session_id)
        if not state:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "state": state
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching state: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch state")

@app.get("/api/sessions/{session_id}/history")
async def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = await state_manager.get_history(session_id)
        if history is None:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "messages": history
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

@app.post("/api/sessions/{session_id}/reset")
async def reset_session(session_id: str):
    """Reset a conversation session"""
    try:
        success = await state_manager.reset_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session reset successfully", "session_id": session_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting session: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to reset session")

@app.get("/api/analytics/dashboard", response_model=AnalyticsResponse)
async def get_analytics():
    """Get analytics dashboard data"""
    try:
        analytics = await state_manager.get_analytics()
        return AnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching analytics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch analytics")

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "state_manager": state_manager is not None,
            "intent_detector": intent_detector is not None,
            "response_engine": response_engine is not None
        },
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=os.getenv("DEBUG", "False") == "True"
    )