from fastapi import APIRouter, status, Depends, HTTPException
from schemas import ProgressResponse
from crud import get_my_progress, get_progress_by_language
from database import get_db
import enums
from sqlalchemy.orm import Session
from models import User
from core.dependencies import get_current_user
router = APIRouter(prefix="/progress", tags=["PROGRESS"])




@router.get("/", response_model=list[ProgressResponse])
def my_progress_route(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """My progress across ALL languages I've practiced."""
    return get_my_progress(db, current_user)



@router.get("/{language}", response_model=ProgressResponse)
def progress_by_language_route(language: enums.SupportedLanguage,db: Session = Depends(get_db),current_user: User = Depends(get_current_user)):
    """Progress for one specific language (404 if I've never practiced it)."""
    progress = get_progress_by_language(db, current_user, language)
    if not progress:
        raise HTTPException(status_code=404, detail=f"No progress for '{language}' yet — practice first!")
    return progress