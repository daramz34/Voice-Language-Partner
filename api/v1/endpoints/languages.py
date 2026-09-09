from fastapi import APIRouter

router = APIRouter(prefix="/languages", tags=["LANGUAGES"])

DEMO_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English", "voice_id": "alba"},
    {"code": "es", "name": "Spanish", "native_name": "Español", "voice_id": "lola"},
    {"code": "fr", "name": "French", "native_name": "Français", "voice_id": "alba"},
    {"code": "de", "name": "German", "native_name": "Deutsch", "voice_id": "alba"},
    {"code": "it", "name": "Italian", "native_name": "Italiano", "voice_id": "alba"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português", "voice_id": "alba"},
]


@router.get("/supported")
def get_supported_languages():
    """The 6 demo languages available in the app, with their voices."""
    return {"languages": DEMO_LANGUAGES}
