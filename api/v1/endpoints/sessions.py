from fastapi import APIRouter, status, Depends, HTTPException, Query
from schemas import SessionCreate, SessionResponse, MessageIn, EvaluationResponse,SessionUpdate, PaginatedResponse, MessageCreate, MessageResponse
from crud import create_session, get_my_sessions, get_session_by_id, update_session, save_message, get_session_transcript,get_session_evaluation, create_evaluation,save_mistakes
from database import get_db
from sqlalchemy.orm import Session
from models import User
from core.dependencies import get_current_user
from services.agent import build_agent_config
from services.gemini import evaluate_session
import json
import urllib.request
from core.config import settings

router = APIRouter(prefix="/session", tags=["SESSION"])

def _publish_agent(config: dict) -> str:
    """Create an AssemblyAI agent from the config dict. Returns the agent_id."""
    body = json.dumps(config).encode()
    req = urllib.request.Request(
        "https://agents.assemblyai.com/v1/agents",
        data=body,
        headers={
            "Authorization": f"Bearer {settings.ASSEMBLYAI_API_KEY}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            agent_id = data.get("agent_id") or data.get("id")
            if not agent_id:
                raise HTTPException(status_code=502, detail="AssemblyAI returned no agent_id")
            return agent_id
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not publish voice agent: {exc}")

def _enum_value(value):
    """Pull the plain value out of a Python enum member."""
    return getattr(value, "value", value)


@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED,description="Create Session")
def create_session_endpoint(session: SessionCreate, db:Session=Depends(get_db),  current_user: User=Depends(get_current_user)):
    db_session = create_session(db, session, current_user)
    try:
        config = build_agent_config(db_session)
    except Exception as exc:
        db.delete(db_session)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Invalid session config: {exc}")
    
    try:
        agent_id = _publish_agent(config)
    except Exception:
        db.delete(db_session)
        db.commit()
        raise

    db_session.assemblyai_agent_id = agent_id
    db.commit()
    db.refresh(db_session)
    return db_session

@router.get("/", response_model=PaginatedResponse, status_code=status.HTTP_200_OK,description="Get all sessions")
def session_history(page: int = Query(1, ge=1), limit: int=Query(10, ge=1, le=50),db:Session=Depends(get_db), current_user:User=Depends(get_current_user)):
    db_session = get_my_sessions(db, current_user, page, limit)

    return db_session

@router.get("/{session_id}", response_model=list[SessionResponse], status_code=status.HTTP_200_OK, description="Get Session")
def single_session(session_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    db_session = get_session_by_id(db, session_id, current_user)
    if not db_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Session not found"
        )
    return db_session


@router.patch("/{session_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK, description="Update Session")
def update_session_endpoint(session_id: int, update: SessionUpdate, db:Session=Depends(get_db), current_user: User=Depends(get_current_user)):
    db_session = update_session(db, session_id, update, current_user)
    if not db_session:
        raise HTTPException(
            status_code = status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    return db_session

@router.post("/{session_id}/message", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def add_message_route(session_id: int,payload: MessageIn,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    if not get_session_by_id(db, session_id, current_user):
        raise HTTPException(status_code=404, detail="Session not found")
    message = MessageCreate(session_id=session_id, **payload.model_dump())
    return save_message(db, message, current_user)


@router.get("/{session_id}/transcript", response_model=list[MessageResponse])
def transcript_route(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = get_session_transcript(db, session_id, current_user)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return messages

@router.post("/{session_id}/evaluate", response_model=EvaluationResponse)
def evaluate_session_route(session_id: int, db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    db_session = get_session_by_id(db, session_id, current_user)
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")

    existing = get_session_evaluation(db, session_id, current_user)
    if existing:
        return existing  # idempotent — no double-scoring

    messages = get_session_transcript(db, session_id, current_user)
    if not messages:
        raise HTTPException(status_code=400, detail="Session has no messages to evaluate")

    transcript = [
        {
            "speaker": _enum_value(m.speaker),
            "content": m.content,
            "language": _enum_value(m.language),
        }
        for m in messages
    ]

    result = evaluate_session(
        transcript,
        db_session.target_language,
        db_session.support_language,
        db_session.conversation_config,
        db_session.proficiency_level,
    )
    evaluation = create_evaluation(db, session_id, result, current_user)

    if result.get("mistakes"):
        save_mistakes(db, session_id, current_user.id, result["mistakes"])

    return evaluation
