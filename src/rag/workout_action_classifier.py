from src.rag.question_classifier import normalize_question


ACTION_SINGLE_WORKOUT = "single_workout"
ACTION_WEEKLY_WORKOUT = "weekly_workout"


WEEKLY_WORKOUT_PHRASES = {
    "weekly workout",
    "weekly workout plan",
    "week of workouts",
    "workout week",
    "training week",
    "plan my week",
    "plan my training week",
    "build my weekly workout",
    "build me a weekly workout",
    "create my weekly workout",
    "create a weekly workout",
    "generate a weekly workout"
}


def classify_workout_action(question):
    normalized = normalize_question(question)
    lowered = normalized.casefold()

    matches = sorted(
        phrase
        for phrase in WEEKLY_WORKOUT_PHRASES
        if phrase in lowered
    )

    if matches:
        return {
            "action": ACTION_WEEKLY_WORKOUT,
            "matched_signals": matches,
            "reason": "The user requested a multi-day or weekly workout plan."
        }

    return {
        "action": ACTION_SINGLE_WORKOUT,
        "matched_signals": [],
        "reason": "The user requested a single workout plan."
    }