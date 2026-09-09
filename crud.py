from sqlalchemy.orm import Session
from models import User, PracticeSession, UserProgress, ConversationMessage, SessionEvaluation, Mistake
from schemas import ( UserCreate, SessionCreate, SessionUpdate, MessageCreate)
from core.security import verify_password, hashed_password
from datetime import date
import enums


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email==email).first()

def authenticate_user(db: Session, username: str, password: str):
    db_user = get_user_by_username(db, username)
    if not db_user:
        return None
    if not verify_password(password, db_user.hashed_password):
        return None
    return db_user
def create_user(db: Session, user:UserCreate):
    db_user = User(**user.model_dump(exclude={"password"}),
                   hashed_password = hashed_password(user.password))

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user






def create_session(db:Session, session: SessionCreate, current_user: User):
    db_session = PracticeSession(**session.model_dump(), user_id=current_user.id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    get_or_create_progress(db, current_user.id, session.target_language)
    return db_session

def get_my_sessions(db:Session, current_user: User, page: int= 1, limit: int=10):
    query = db.query(PracticeSession).filter(PracticeSession.user_id == current_user.id)

    total = query.count()
    

    
    sessions = (query.order_by(PracticeSession.started_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
                .all())
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "results": sessions
    }

def get_session_by_id(db:Session, session_id: int, current_user: User):
    db_session = db.query(PracticeSession).filter(PracticeSession.id == session_id,
                                                  PracticeSession.user_id == current_user.id).first()

    return db_session

def update_session(db:Session, session_id: int, update: SessionUpdate, current_user: User):
    db_session = get_session_by_id(db, session_id, current_user)
    if not db_session:
        return None

    for key, value in update.model_dump(exclude_unset=True).items():
        setattr(db_session, key, value)

    db.commit()
    db.refresh(db_session)

    return db_session



# Messages

def save_message(db:Session, message: MessageCreate, current_user: User): 

    session = get_session_by_id(db, message.session_id, current_user)
    if not session:
        return None  # not found 
    
    db_message = ConversationMessage(**message.model_dump())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message

def get_session_transcript(db: Session, session_id: int, current_user: User):
    session = get_session_by_id(db, session_id, current_user)
    if not session:
        return None
    
    db_session = db.query(ConversationMessage).filter(ConversationMessage.session_id == session_id).order_by(ConversationMessage.timestamp.asc()).all() # how will i use current_user here

    

    return db_session


# Evaluation
def get_session_evaluation(db: Session, session_id: int, current_user: User):
    return (
        db.query(SessionEvaluation)
        .join(PracticeSession, PracticeSession.id == SessionEvaluation.session_id)
        .filter(
            SessionEvaluation.session_id == session_id,
            PracticeSession.user_id == current_user.id,
        )
        .first()
    )


def create_evaluation(db: Session,session_id: int,evaluation_data: dict, current_user: User) -> SessionEvaluation | None:
    
    db_session = get_session_by_id(db, session_id, current_user)
    if not db_session:
        return None

    existing = get_session_evaluation(db, session_id, current_user)
    if existing:
        return existing  # idempotent

    # 3. Save allowed report-card fields only.
    allowed = {
        "overall_score",
        "grammar_score",
        "vocabulary_score",
        "fluency_score",
        "comprehension_score",
        "pronunciation_score",
        "target_language_percentage",
        "feedback",
        "recommendation",
    }
    clean_data = {k: v for k, v in evaluation_data.items() if k in allowed}

    evaluation = SessionEvaluation(session_id=session_id, **clean_data)
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    # 4. Now update the sticker chart.
    update_progress(
        db,
        user_id=current_user.id,
        language=db_session.target_language,
        evaluation_data=evaluation_data,
        duration_seconds=db_session.duration_seconds or 0,
    )

    return evaluation



def _coerce_mistake_type(value):
    """Turn 'grammar', 'GRAMMAR', or enum member into a proper MistakeType."""
    if isinstance(value, enums.Mistake_Type):
        return value

    value_str = str(value)
    for member in enums.Mistake_Type:
        if member.value == value_str or member.name == value_str.upper():
            return member

    raise ValueError(f"Invalid mistake type: {value}")


def save_mistakes(db: Session,session_id: int,user_id: int, mistakes: list[dict]) -> list[Mistake]:
    rows = [
        Mistake(
            session_id=session_id,
            user_id=user_id,
            original_text=m["original_text"],
            corrected_text=m["corrected_text"],
            mistake_type=_coerce_mistake_type(m["mistake_type"]),
            explanation=m.get("explanation", ""),
        )
        for m in mistakes
    ]

    if not rows:
        return []

    db.add_all(rows)
    db.commit()
    for row in rows:
        db.refresh(row)

    return rows


def get_my_mistakes(db: Session,current_user: User,language=None,) -> list[Mistake]:
    """All my mistakes, optionally filtered by target language."""
    query = (
        db.query(Mistake)
        .join(PracticeSession, PracticeSession.id == Mistake.session_id)
        .filter(Mistake.user_id == current_user.id)
    )

    if language is not None:
        query = query.filter(PracticeSession.target_language == language)

    return query.order_by(Mistake.created_at.desc()).all()

def get_or_create_progress(db: Session,user_id: int,language) -> UserProgress:
    """Find my chart for a language. If I don't have one, make a fresh empty one."""
    progress = (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == user_id,
            UserProgress.target_language == language,
        )
        .first()
    )

    if progress:
        return progress

    progress = UserProgress(
        user_id=user_id,
        target_language=language,
        sessions_count=0,
        total_practice_minutes=0,
        avg_overall_score=0.0,
        avg_grammar_score=0.0,
        avg_vocabulary_score=0.0,
        avg_fluency_score=0.0,
        best_score=0.0,
        current_streak=0,
        longest_streak=0,
    )
    db.add(progress)
    db.commit()
    db.refresh(progress)
    return progress


def get_my_progress(db: Session, current_user: User) -> list[UserProgress]:
    """All my sticker charts, newest-updated first."""
    return (
        db.query(UserProgress)
        .filter(UserProgress.user_id == current_user.id)
        .order_by(UserProgress.updated_at.desc())
        .all()
    )


def get_progress_by_language(
    db: Session,
    current_user: User,
    language,
) -> UserProgress | None:
    """Just one language's chart, or None if I've never practiced that language."""
    return (
        db.query(UserProgress)
        .filter(
            UserProgress.user_id == current_user.id,
            UserProgress.target_language == language,
        )
        .first()
    )


def update_progress(db: Session,user_id: int,language,evaluation_data: dict, duration_seconds: int = 0,) -> UserProgress:
    """The ONLY place stickers get added / averages recalculated / streak updated."""
    progress = get_or_create_progress(db, user_id, language)

    old_count = progress.sessions_count
    new_count = old_count + 1
    progress.sessions_count = new_count

    # total practice minutes
    progress.total_practice_minutes += duration_seconds // 60

    # running averages for the 4 fields UserProgress actually tracks
    for key in ("overall", "grammar", "vocabulary", "fluency"):
        new_score = evaluation_data.get(f"{key}_score")
        if new_score is None:
            continue
        old_avg = getattr(progress, f"avg_{key}_score") or 0.0
        new_avg = (old_avg * old_count + new_score) / new_count
        setattr(progress, f"avg_{key}_score", round(new_avg, 2))

    # best overall score
    new_best = evaluation_data.get("overall_score")
    if new_best is not None and new_best > (progress.best_score or 0):
        progress.best_score = new_best

    # streak — the "practice tracker on a calendar" rule:
    today = date.today()
    if progress.last_practice_date:
        day_gap = (today - progress.last_practice_date).days
        if day_gap == 0:
            pass  # already practiced today: don't double-count the streak
        elif day_gap == 1:
            progress.current_streak += 1
        else:
            progress.current_streak = 1
    else:
        progress.current_streak = 1

    progress.longest_streak = max(
        progress.longest_streak or 0,
        progress.current_streak or 0,
    )
    progress.last_practice_date = today

    db.commit()
    db.refresh(progress)
    return progress