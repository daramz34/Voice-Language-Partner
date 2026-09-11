import random
import time
from typing import Dict, List, Optional

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)
MODEL = settings.GEMINI_MODEL   # defaults to "gemini-2.5-flash" in config.py


# ---------- Pydantic response schema (Gemini must match this) ----------

class _Mistake(BaseModel):
    original: str = ""
    corrected: str = ""
    type: str = "grammar"
    explanation: str = ""

class _Feedback(BaseModel):
    """Fixed keys — free Gemini API can't handle free-form dicts in schemas."""
    grammar: str = ""
    vocabulary: str = ""
    fluency: str = ""

class _EvaluationResult(BaseModel):
    overall_score: float = 0
    grammar_score: float = 0
    vocabulary_score: float = 0
    fluency_score: float = 0
    comprehension_score: float = 0
    pronunciation_score: Optional[float] = None
    target_language_percentage: float = 0.0
    mistakes: List[_Mistake] = Field(default_factory=list)
    feedback: _Feedback = Field(default_factory=_Feedback)
    recommendations: str = ""


# ---------- helpers ----------

def _clamp(value) -> float:
    """Force any score into 0-100, or 0.0 if Gemini returned junk."""
    try:
        return round(max(0.0, min(100.0, float(value))), 2)
    except (TypeError, ValueError):
        return 0.0


def _call_gemini(prompt: str, schema=None):
    """Call Gemini with 5 retries + exponential backoff + jitter.
    Survives flaky networks (SSL EOF, timeouts) that kill single attempts."""
    last_err = None
    for attempt in range(5):
        try:
            return client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0.2,
                ),
            )
        except Exception as e:
            last_err = e
            time.sleep((2 ** attempt) + random.random())  # ~1s, 2s, 4s, 8s, 16s
    raise RuntimeError(f"Gemini call failed after 5 attempts: {last_err}")


# ---------- public API ----------

def evaluate_session(
    transcript: list[dict],
    target_language,
    support_language,
    conversation_config,
    proficiency_level,
) -> dict:
    """Grades one practice session with Gemini. Returns a DB-ready dict."""

    target = getattr(target_language, "value", target_language)
    support = getattr(support_language, "value", support_language)
    config = getattr(conversation_config, "name", conversation_config)
    level = getattr(proficiency_level, "name", proficiency_level)

    transcript_text = "\n".join(
        f"{m.get('speaker', '?')} [{m.get('language', '?')}]: {m.get('content', '')}"
        for m in transcript
    )

    prompt = f"""You are a rigorous language tutor.

        Target language: {target}
        Support language: {support}
        Conversation config: {config}   (target = language being practiced, support = learner's native language)
        Proficiency level: {level}

        A voice conversation happened. Here is the transcript:
        {transcript_text or "(empty transcript)"}

        Evaluate the LEARNER's messages only.
        - Score every category 0-100.
        - pronunciation_score must be null — you only see text, not audio.
        - target_language_percentage = what % of the learner's words were in the target language.
        - mistakes must be real errors the learner made. Use type = grammar, vocabulary, or fluency only.
        - feedback: short 1-2 sentence comments per category.
        - recommendations: one specific next practice suggestion.

        Return JSON exactly matching the required schema."""

    response = _call_gemini(prompt, schema=_EvaluationResult)
    parsed = _EvaluationResult.model_validate_json(response.text)

    # Normalize to exactly what crud.py / models.py expect.
    return {
        "overall_score": _clamp(parsed.overall_score),
        "grammar_score": _clamp(parsed.grammar_score),
        "vocabulary_score": _clamp(parsed.vocabulary_score),
        "fluency_score": _clamp(parsed.fluency_score),
        "comprehension_score": _clamp(parsed.comprehension_score),
        "pronunciation_score": None,            # text-only: no audio to judge
        "target_language_percentage": _clamp(parsed.target_language_percentage),
        "mistakes": [
            {
                "original_text": m.original,
                "corrected_text": m.corrected,
                "mistake_type": m.type,
                "explanation": m.explanation,
            }
            for m in parsed.mistakes
        ],
        "feedback": parsed.feedback.model_dump(),
        # create_evaluation's DB column is "recommendation" (singular)
        "recommendation": parsed.recommendations,
        "recommendations": parsed.recommendations,   # keep blueprint's plural key too
    }


def generate_recommendations(mistakes: list, progress: dict) -> str:
    """One concrete next-practice suggestion, based on recurring weaknesses."""
    if not mistakes and not progress:
        return "Keep practicing — consistency matters more than any single session."

    mistake_text = "\n".join(
        f"- {m.get('mistake_type')}: {m.get('original_text')} -> {m.get('corrected_text')}"
        for m in mistakes
    )
    progress_text = (
        f"avg overall: {progress.get('avg_overall_score', '?')}, "
        f"avg grammar: {progress.get('avg_grammar_score', '?')}, "
        f"avg vocabulary: {progress.get('avg_vocabulary_score', '?')}, "
        f"best score: {progress.get('best_score', '?')}"
    )

    prompt = f"""You are a language coach. The learner made these recent mistakes:
{mistake_text or "(no specific mistakes recorded)"}

Their progress so far:
{progress_text}

Look for recurring weaknesses. Give ONE specific, actionable next practice suggestion in 2-3 plain sentences. Do not use markdown, bullets, or headers."""

    response = _call_gemini(prompt)   # plain text call, same retry protection
    return response.text.strip()
