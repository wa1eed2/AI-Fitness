from src.rag.question_classifier import normalize_question


ACTION_MEAL_GENERATION = "meal_generation"
ACTION_NUTRITION_CONTEXT = "nutrition_context"


MEAL_GENERATION_PHRASES = {
    "build me a meal",
    "build a meal",
    "make me a meal",
    "make a meal",
    "create me a meal",
    "create a meal",
    "generate me a meal",
    "generate a meal",
    "plan me a meal",
    "plan a meal",
    "recommend me a meal",
    "recommend a meal",
    "meal recommendation",
    "meal suggestion",
    "give me a meal",
    "what should i eat"
}


def classify_nutrition_action(question):
    normalized = normalize_question(
        question
    )

    lowered = normalized.casefold()

    matches = sorted(
        phrase
        for phrase in MEAL_GENERATION_PHRASES
        if phrase in lowered
    )

    if matches:
        return {
            "action": ACTION_MEAL_GENERATION,
            "matched_signals": matches,
            "reason": "The user explicitly requested a concrete meal."
        }

    return {
        "action": ACTION_NUTRITION_CONTEXT,
        "matched_signals": [],
        "reason": "The message asks about nutrition without explicitly requesting meal generation."
    }