from fastapi import APIRouter, status, Depends, HTTPException
from core.security import  create_access_token
from schemas import TokenResponse, UserResponse, UserCreate
from crud import create_user, authenticate_user, get_user_by_email, get_user_by_username
from database import get_db
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from models import User
from core.dependencies import get_current_user
router = APIRouter(prefix="/auth", tags=["AUTH"])




@router.post("/register", response_model=UserResponse, description="Register user")
def register(user: UserCreate, db:Session=Depends(get_db)):
    existing_user = get_user_by_username(db, user.username)
    existing_email = get_user_by_email(db, user.email)

    if existing_user:
        raise HTTPException(
            status_code= status.HTTP_409_CONFLICT,
            detail="User is already registered"
        )
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered "
        )

    db_user = create_user(db, user)

    return db_user

@router.post("/login", response_model=TokenResponse, description="User Login")
def login(request:OAuth2PasswordRequestForm=Depends(), db:Session=Depends(get_db)):
    user = authenticate_user(db,request.username, request.password)

    if not user: 
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Username or password"
        )

    token = create_access_token({"sub": str(user.id)})
    return {
        "access_token": token,
        "token_type":"bearer"
    }

@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)):
    return current_user