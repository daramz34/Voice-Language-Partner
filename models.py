from datetime import datetime, timezone
from sqlalchemy import Column, String, Enum, Date, Text, Float, DateTime,Integer, ForeignKey, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base
import enums


def utcnow():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    native_language = Column(String(20), nullable=False, default="English")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    practice_sessions = relationship("PracticeSession", back_populates="user", cascade="all, delete-orphan")
    mistakes = relationship("Mistake", back_populates="user", cascade="all, delete-orphan")
    user_progress = relationship("UserProgress", back_populates="user", cascade="all, delete-orphan")


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    target_language = Column(Enum(enums.SupportedLanguage), nullable=False)
    support_language = Column(Enum(enums.SupportedLanguage), nullable=False)
    conversation_config = Column(Enum(enums.ConversationConfig), nullable=False)
    practice_mode = Column(Enum(enums.PracticeMode), nullable=False)
    proficiency_level = Column(Enum(enums.ProficiencyLevel), nullable=False)
    scenario_type = Column(Enum(enums.ScenarioType), nullable=True)
    topic = Column(String, nullable=False)
    status = Column(Enum(enums.SessionStatus), nullable=False, default=enums.SessionStatus.active)
    assemblyai_agent_id = Column(String, nullable=True)
    started_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=False, default=0)

    user = relationship("User", back_populates="practice_sessions")
    messages = relationship("ConversationMessage", back_populates="session", cascade="all, delete-orphan")
    evaluation = relationship("SessionEvaluation", back_populates="session", cascade="all, delete-orphan", uselist=False)
    mistakes = relationship("Mistake", back_populates="session", cascade="all, delete-orphan")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), index=True, nullable=False)
    speaker = Column(Enum(enums.Speaker), nullable=False)
    content = Column(Text, nullable=False)
    language = Column(Enum(enums.SupportedLanguage), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("PracticeSession", back_populates="messages")


class SessionEvaluation(Base):
    __tablename__ = "session_evaluations"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), unique=True, nullable=False)
    overall_score = Column(Float, nullable=False)
    grammar_score = Column(Float, nullable=False)
    vocabulary_score = Column(Float, nullable=False)
    fluency_score = Column(Float, nullable=False)
    comprehension_score = Column(Float, nullable=False)
    pronunciation_score = Column(Float, nullable=True)
    target_language_percentage = Column(Float, nullable=False)
    feedback = Column(JSON, nullable=False, default=dict)
    recommendation = Column(Text, nullable=False)
    evaluated_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("PracticeSession", back_populates="evaluation")


class Mistake(Base):
    __tablename__ = "mistakes"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    original_text = Column(Text, nullable=False)
    corrected_text = Column(Text, nullable=False)
    mistake_type = Column(Enum(enums.Mistake_Type), nullable=False)
    explanation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="mistakes")
    session = relationship("PracticeSession", back_populates="mistakes")


class UserProgress(Base):
    __tablename__ = "user_progress"
    __table_args__ = (
        UniqueConstraint("user_id", "target_language", name="uq_user_progress_user_lang"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    target_language = Column(Enum(enums.SupportedLanguage), nullable=False)
    sessions_count = Column(Integer, default=0, nullable=False)
    total_practice_minutes = Column(Integer, default=0, nullable=False)
    avg_overall_score = Column(Float, default=0.0, nullable=False)
    avg_grammar_score = Column(Float, default=0.0, nullable=False)
    avg_vocabulary_score = Column(Float, default=0.0, nullable=False)
    avg_fluency_score = Column(Float, default=0.0, nullable=False)
    best_score = Column(Float, default=0.0, nullable=False)
    current_streak = Column(Integer, default=0, nullable=False)
    longest_streak = Column(Integer, default=0, nullable=False)
    last_practice_date = Column(Date, nullable=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow,
                        onupdate=utcnow, nullable=False)

    user = relationship("User", back_populates="user_progress")
