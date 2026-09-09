from enum import Enum


class SupportedLanguage(str, Enum):
    english = "english"
    spanish = "spanish"
    french = "french"
    german = "german"
    italian = "italian"
    portuguese = "portuguese"

class ProficiencyLevel(str, Enum):
    beginner = "beginner"
    intermediate = "intermediate"
    advanced = "advanced"

class PracticeMode(str, Enum):
    free_conversation = "free_conversation"
    scenario = "scenario"
    tutor = "tutor"
    vocabulary = "vocabulary"

class ConversationConfig(str, Enum):
    target_target = "target_target"      # both speak target language
    support_target = "support_target"    # user speaks support, AI speaks target
    target_support = "target_support"    # user speaks target, AI speaks support

class SessionStatus(str, Enum):
    active = "active"
    completed = "completed"
    abandoned = "abandoned"

class ScenarioType(str, Enum):
    restaurant = "restaurant"
    airport = "airport"
    hotel = "hotel"
    shopping = "shopping"
    job_interview = "job_interview"
    directions = "directions"


class Speaker(str, Enum):
    user = "user"
    agent = "agent"

class Mistake_Type(str, Enum):
    grammar = "grammar"
    vocabulary = "vocabulary"
    fluency = "fluency"