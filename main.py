from fastapi import FastAPI, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from fastapi.staticfiles import StaticFiles
from database import engine, get_db, Base
import models  
from core.security import settings
from api.v1.router import api_router

app = FastAPI(
    title=settings.APP_NAME,
    description="Practice languages by talking to an AI voice partner",
    version=settings.VERSION,
)


# Create tables on startup (dev convenience — proper migrations come later)
Base.metadata.create_all(bind=engine)


app.include_router(api_router, prefix="/api/v1")

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
@app.get("/")
def root():
    return {"message": "Voice Language Partner API", "docs": "/docs"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "connected"}
