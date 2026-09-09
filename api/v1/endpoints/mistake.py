from fastapi import APIRouter, status, Depends, HTTPException
from schemas import MistakeResponse
from crud import get_my_mistakes
from database import get_db
import enums
from typing import Optional
from sqlalchemy.orm import Session
from models import User
from core.dependencies import get_current_user


router = APIRouter(prefix="/mistake", tags=["MISTAKE"])



@router.get("/", response_model=list[MistakeResponse])
def my_mistakes_route(language: Optional[enums.SupportedLanguage] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """All my mistakes — optionally filtered by target language."""
    return get_my_mistakes(db, current_user, language=language)