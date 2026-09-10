import httpx
from fastapi import APIRouter, HTTPException

from core.config import settings

router = APIRouter(prefix="/voice", tags=["VOICE"])


@router.get("/token")
async def voice_token():
    """Mint a short-lived token so the browser can connect to the Voice Agent WS
    without ever seeing our API key. Retries once on transient network errors."""
    last_error = None
    for _ in range(2):
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                res = await client.get(
                    "https://agents.assemblyai.com/v1/token",
                    params={"expires_in_seconds": 600},
                    headers={"Authorization": f"Bearer {settings.ASSEMBLYAI_API_KEY}"},
                )
            if res.status_code == 200:
                return res.json()
            last_error = f"AssemblyAI returned {res.status_code}"
        except httpx.HTTPError as e:
            last_error = str(e)
    raise HTTPException(status_code=502, detail=f"Could not mint voice token: {last_error}")