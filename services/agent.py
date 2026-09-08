from models import PracticeSession

# AssemblyAI realtime-supported codes (Universal-3.5 Pro streaming)
AA_SUPPORTED_CODES = {
    "en", "es", "fr", "de", "it", "pt", "tr", "nl", "sv",
    "da", "fi", "hi", "vi", "ar", "he", "ja", "zh", "no",
}

# Best-effort voice map — full catalog:
# https://www.assemblyai.com/docs/voice-agents/voice-agent-api/voices
VOICE_MAP = {"en": "alba", "es": "lola"}

CODE_TO_NAME = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German",
    "it": "Italian", "pt": "Portuguese", "tr": "Turkish", "nl": "Dutch",
    "sv": "Swedish", "da": "Danish", "fi": "Finnish", "hi": "Hindi",
    "vi": "Vietnamese", "ar": "Arabic", "he": "Hebrew", "ja": "Japanese",
    "zh": "Mandarin Chinese", "no": "Norwegian",
}

GREETINGS = {
    "en": "Hi! Ready to practice? How are you today?",
    "es": "¡Hola! ¿Listo para practicar? ¿Cómo estás hoy?",
    "fr": "Bonjour ! Prêt à pratiquer ? Comment ça va ?",
    "de": "Hallo! Bereit zum Üben? Wie geht es dir?",
    "it": "Ciao! Pronto a praticare? Come stai?",
    "pt": "Olá! Pronto para praticar? Como você está?",
    "tr": "Merhaba! Pratik yapmaya hazır mısın? Bugün nasılsın?",
    "nl": "Hallo! Klaar om te oefenen? Hoe gaat het?",
    "sv": "Hej! Redo att öva? Hur mår du idag?",
    "da": "Hej! Klar til at øve? Hvordan har du det i dag?",
    "fi": "Hei! Valmis harjoittelemaan? Mitä kuuluu tänään?",
    "no": "Hei! Klar til å øve? Hvordan har du det i dag?",
    "hi": "नमस्ते! अभ्यास के लिए तैयार हैं? आज आप कैसे हैं?",
    "vi": "Chào bạn! Sẵn sàng luyện tập chưa? Hôm nay bạn thế nào?",
    "ar": "مرحباً! هل أنت مستعد للتمرن؟ كيف حالك اليوم؟",
    "he": "שלום! מוכן לתרגל? מה שלומך היום?",
    "ja": "こんにちは！練習する準備はできていますか？",
    "zh": "你好！准备好练习了吗？你怎么样？",
}

SCENARIO_ROLE_PLACE = {
    "restaurant": ("a waiter", "a restaurant"),
    "airport": ("an airport check-in agent", "an airport"),
    "hotel": ("a hotel receptionist", "a hotel"),
    "cafe": ("a barista", "a café"),
    "grocery_store": ("a cashier", "a grocery store"),
    "pharmacy": ("a pharmacist", "a pharmacy"),
    "doctor": ("a doctor", "a clinic"),
}


# ---------- helpers ----------

def _name(value) -> str:
    """Lowercase enum member name (or the string itself), '-' → '_'."""
    if hasattr(value, "name"):
        return str(value.name).lower().replace("-", "_")
    return str(value).lower().replace("-", "_")


def _code(value) -> str:
    """Map a language enum/string to an AssemblyAI language code."""
    name = _name(value)
    aliases = {
        "english": "en", "en": "en", "spanish": "es", "french": "fr",
        "german": "de", "italian": "it", "portuguese": "pt", "dutch": "nl",
        "swedish": "sv", "danish": "da", "finnish": "fi", "hindi": "hi",
        "vietnamese": "vi", "arabic": "ar", "hebrew": "he", "japanese": "ja",
        "mandarin_chinese": "zh", "chinese": "zh", "norwegian": "no",
        "yoruba": "yo", "yo": "yo", "igbo": "ig", "ig": "ig",
    }
    if name in aliases:
        return aliases[name]
    raw = getattr(value, "value", value)
    return str(raw).lower()


def _lang_name(code: str) -> str:
    return CODE_TO_NAME.get(code, code.upper())


# ---------- public API ----------

def build_agent_config(session: PracticeSession) -> dict:
    """Builds the AssemblyAI Voice Agent config for a PracticeSession."""
    target_code = _code(session.target_language)
    support_code = _code(session.support_language)
    conversation_config = _name(session.conversation_config)
    mode = _name(session.practice_mode)
    level = _name(session.proficiency_level)

    # Who speaks what? (blueprint names)
    #   target_target   = agent speaks target, user speaks target
    #   support_target  = agent speaks target, user speaks support
    #   target_support  = agent speaks support, user speaks target
    if conversation_config == "support_target":
        agent_code, user_code = target_code, support_code
    elif conversation_config == "target_support":
        agent_code, user_code = support_code, target_code
    else:  # target_target and anything unforeseen
        agent_code, user_code = target_code, target_code

    # Realtime limitation: fail EARLY with a clear message, not mid-demo.
    unsupported = [c for c in (agent_code, user_code) if c not in AA_SUPPORTED_CODES]
    if unsupported:
        raise ValueError(
            "AssemblyAI Voice Agent does not support these realtime languages: "
            f"{', '.join(unsupported)}. Supported: {', '.join(sorted(AA_SUPPORTED_CODES))}"
        )

    agent_lang = _lang_name(agent_code)
    target_lang = _lang_name(target_code)
    support_lang = _lang_name(support_code)
    voice_id = VOICE_MAP.get(agent_code, "alba")

    # ----- MODE OVERLAY -----
    if mode == "free_conversation":
        topic = (session.topic or "").strip()
        mode_prompt = (
            f"Have a natural conversation. Topic: {topic}. Don't turn it into a formal lesson."
            if topic
            else "Have a natural conversation. Ask the learner what they want to talk about."
        )
    elif mode == "scenario":
        scenario = _name(session.scenario_type) if session.scenario_type else ""
        role, place = SCENARIO_ROLE_PLACE.get(
            scenario,
            ("a local", f"a {scenario} situation" if scenario else "an everyday situation"),
        )
        mode_prompt = f"You are {role} at {place}. Stay in character the whole time. Start with a greeting."
    elif mode == "tutor":
        mode_prompt = (
            "Act as a patient language tutor. Correct mistakes briefly after the learner "
            "finishes their thought. Be encouraging."
        )
    elif mode == "vocabulary":
        words = (session.topic or "common everyday vocabulary").strip()
        mode_prompt = (
            f"Naturally weave these words/topics into the conversation: {words}. "
            "Do not list them — use them naturally."
        )
    else:
        mode_prompt = "Have a natural, friendly conversation."

    # ----- DIFFICULTY OVERLAY -----
    if level == "beginner":
        level_prompt = "Use simple sentences. Speak slowly. Be encouraging. Ask one short question at a time."
    elif level == "advanced":
        level_prompt = "Speak naturally. Use idioms where natural. Do not oversimplify."
    else:  # intermediate
        level_prompt = "Use a natural pace. Allow some complexity. Correct only when it affects meaning."

    # ----- LANGUAGE OVERLAY -----
    if conversation_config == "support_target":
        lang_prompt = (
            f"Speak only in {target_lang}. The learner will reply in {support_lang}. "
            f"Help them understand and gradually respond in {target_lang}."
        )
    elif conversation_config == "target_support":
        lang_prompt = (
            f"The learner will speak in {target_lang}. You reply in {support_lang}. "
            f"Understand them completely and answer naturally in {support_lang}."
        )
    else:
        lang_prompt = (
            f"Both you and the learner speak only in {target_lang}. "
            f"Encourage them to stay in {target_lang}."
        )

    system_prompt = " ".join([
        f"You are a {agent_lang} conversation partner helping someone practice {target_lang}.",
        f"The learner is at {level} proficiency.",
        mode_prompt,
        lang_prompt,
        level_prompt,
        "Keep replies short and spoken-style. Never use lists, bullet points, or markdown.",
        "Ask at most one question at a time.",
    ])

    return {
        "name": "Voice Language Partner",
        "system_prompt": system_prompt,
        "voice": {"voice_id": voice_id},
        "greeting": GREETINGS.get(agent_code, GREETINGS["en"]),
        "input": {"language_codes": [user_code]},
    }
