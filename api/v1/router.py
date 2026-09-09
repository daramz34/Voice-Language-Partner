from fastapi import APIRouter
from api.v1.endpoints import auth, languages, mistake, progress, sessions


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(languages.router)
api_router.include_router(sessions.router)
api_router.include_router(progress.router)
api_router.include_router(mistake.router)
