from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, Any
import enums
from datetime import datetime, date

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    native_language: str = "english"

class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    native_language: str
    created_at: datetime

    model_config= ConfigDict(from_attributes=True)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCreate(BaseModel):
    target_language : enums.SupportedLanguage
    support_language: enums.SupportedLanguage
    conversation_config: enums.ConversationConfig
    practice_mode: enums.PracticeMode
    proficiency_level: enums.ProficiencyLevel
    scenario_type: Optional[enums.ScenarioType] = None
    topic: str



class SessionResponse(BaseModel):
    id: int
    user_id: int
    target_language : enums.SupportedLanguage
    support_language: enums.SupportedLanguage
    conversation_config: enums.ConversationConfig
    practice_mode: enums.PracticeMode
    proficiency_level: enums.ProficiencyLevel
    scenario_type: Optional[enums.ScenarioType] = None
    topic: str
    status: enums.SessionStatus
    assemblyai_agent_id: Optional[str] = None
    started_at : datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = 0


    model_config= ConfigDict(from_attributes=True)
    
    


class SessionUpdate(BaseModel):
    target_language : Optional[enums.SupportedLanguage] = None
    support_language: Optional[enums.SupportedLanguage] = None
    conversation_config: Optional[enums.ConversationConfig] = None
    practice_mode: Optional[enums.PracticeMode] = None
    proficiency_level: Optional[enums.ProficiencyLevel] = None
    scenario_type: Optional[enums.ScenarioType] = None
    topic: Optional[str] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None



class MessageCreate(BaseModel):
    session_id: int
    speaker: enums.Speaker
    content: str
    language: enums.SupportedLanguage


class MessageResponse(BaseModel):
    id: int
    session_id: int
    speaker: enums.Speaker
    content: str
    language: enums.SupportedLanguage
    timestamp: datetime

    model_config= ConfigDict(from_attributes=True)


class EvaluationResponse(BaseModel):
    id: int
    session_id : int
    overall_score: float
    grammar_score : float
    vocabulary_score: float
    fluency_score: float
    comprehension_score: float
    pronunciation_score: Optional[float] = None
    target_language_percentage: float
    feedback: dict[str, Any]
    recommendation: str
    evaluated_at: datetime

    model_config= ConfigDict(from_attributes=True)
    


class MistakeResponse(BaseModel):
    id: int
    session_id : int
    original_text: str
    corrected_text: str
    mistake_type : enums.Mistake_Type
    explanation: str
    created_at: datetime

    model_config= ConfigDict(from_attributes=True)



class ProgressResponse(BaseModel):
    id: int
    user_id: int
    target_language: enums.SupportedLanguage
    sessions_count: int = 0
    total_practice_minutes: int = 0
    avg_overall_score: float = 0.0
    avg_grammar_score: float =0.0
    avg_vocabulary_score: float =0.0
    avg_fluency_score: float=0.0
    best_score : float= 0.0
    current_streak: int =0
    longest_streak: int =0
    last_practice_date : Optional[date] = None
    updated_at : datetime

    model_config= ConfigDict(from_attributes=True)
    



class AgentConfigRequest(BaseModel):
    session_id: int

class AgentConfigResponse(BaseModel):
    agent_id: str
    config: dict[str, Any]

    
    
