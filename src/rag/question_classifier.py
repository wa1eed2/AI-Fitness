import re


ROUTE_RESEARCH = "research"
ROUTE_NUTRITION = "nutrition"
ROUTE_WORKOUT = "workout"
ROUTE_PERSONAL_DATA = "personal_data"
ROUTE_COACHING = "coaching"
ROUTE_SAFETY = "safety"
ROUTE_UNKNOWN = "unknown"

SAFETY_LEVEL_NONE = "none"
SAFETY_LEVEL_CAUTION = "caution"
SAFETY_LEVEL_URGENT = "urgent"


URGENT_SAFETY_PHRASES = {
    "chest pain",
    "chest pressure",
    "trouble breathing",
    "difficulty breathing",
    "cannot breathe",
    "can't breathe",
    "fainted",
    "fainting",
    "passed out",
    "severe shortness of breath",
    "sudden weakness",
    "sudden numbness",
    "severe bleeding",
    "loss of consciousness"
}


CAUTION_SAFETY_TERMS = {
    "pain",
    "painful",
    "injury",
    "injured",
    "swelling",
    "dizzy",
    "dizziness",
    "numb",
    "numbness",
    "tingling",
    "sharp pain",
    "medical restriction",
    "hurt",
    "hurts"
}


RESEARCH_TERMS = {
    "research",
    "evidence",
    "study",
    "studies",
    "paper",
    "papers",
    "scientific",
    "literature",
    "trial",
    "trials",
    "meta-analysis",
    "meta analysis",
    "systematic review",
    "umbrella review",
    "randomized",
    "randomised",
    "according to research",
    "what does research say",
    "what does the evidence say"
}


WORKOUT_GENERATION_PHRASES = {
    "build me a workout",
    "build a workout",
    "create me a workout",
    "create a workout",
    "generate me a workout",
    "generate a workout",
    "make me a workout",
    "make a workout",
    "plan me a workout",
    "plan a workout",
    "give me a workout",
    "workout plan for me",
    "weekly workout",
    "weekly workout plan",
    "week of workouts",
    "build my weekly workout",
    "build me a weekly workout",
    "create my weekly workout",
    "create a weekly workout",
    "generate a weekly workout",
    "plan my training week"
}


NUTRITION_TERMS = {
    "nutrition",
    "calorie",
    "calories",
    "macro",
    "macros",
    "protein",
    "carbohydrate",
    "carbohydrates",
    "carbs",
    "fat",
    "fats",
    "meal",
    "meals",
    "food",
    "foods",
    "diet",
    "allergy",
    "allergies",
    "allergen",
    "allergens"
}


PERSONAL_DATA_PHRASES = {
    "my workout",
    "my workouts",
    "my progress",
    "my weight",
    "my activity",
    "my activities",
    "my steps",
    "my training",
    "my profile",
    "my equipment",
    "my preference",
    "my preferences",
    "my limitation",
    "my limitations",
    "yesterday's workout",
    "yesterdays workout",
    "training history",
    "workout history",
    "activity history",
    "weight trend"
}


COACHING_TERMS = {
    "motivate",
    "motivation",
    "encourage",
    "encouragement",
    "accountability",
    "habit",
    "habits",
    "consistent",
    "consistency",
    "discipline",
    "routine",
    "coach",
    "coaching",
    "goal",
    "goals"
}


def normalize_question(question):
    if not isinstance(question, str):
        raise ValueError("Question must be a string")

    normalized = " ".join(question.strip().split())

    if not normalized:
        raise ValueError("Question cannot be empty")

    return normalized


def contains_phrase(text, phrases):
    lowered = text.casefold()

    return [
        phrase
        for phrase in phrases
        if phrase.casefold() in lowered
    ]


def tokenize(text):
    return re.findall(r"[a-zA-Z]+", text.casefold())


def is_probable_gibberish(question):
    tokens = tokenize(question)

    if not tokens:
        return True

    if len(tokens) != 1:
        return False

    token = tokens[0]

    if len(token) < 12:
        return False

    vowels = sum(
        1
        for character in token
        if character in "aeiou"
    )

    vowel_ratio = vowels / len(token)

    return vowel_ratio < 0.15


def classify_question(question):
    normalized = normalize_question(question)

    if is_probable_gibberish(normalized):
        return {
            "route": ROUTE_UNKNOWN,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": [],
            "reason": "The message could not be confidently classified."
        }

    urgent_matches = contains_phrase(
        normalized,
        URGENT_SAFETY_PHRASES
    )

    if urgent_matches:
        return {
            "route": ROUTE_SAFETY,
            "safety_level": SAFETY_LEVEL_URGENT,
            "matched_signals": sorted(urgent_matches),
            "reason": "The message contains a potentially urgent safety signal."
        }

    caution_matches = contains_phrase(
        normalized,
        CAUTION_SAFETY_TERMS
    )

    if caution_matches:
        return {
            "route": ROUTE_SAFETY,
            "safety_level": SAFETY_LEVEL_CAUTION,
            "matched_signals": sorted(caution_matches),
            "reason": "The message contains a pain, injury, or health-safety signal."
        }

    research_matches = contains_phrase(
        normalized,
        RESEARCH_TERMS
    )

    if research_matches:
        return {
            "route": ROUTE_RESEARCH,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": sorted(research_matches),
            "reason": "The user explicitly requested research or scientific evidence."
        }

    workout_matches = contains_phrase(
        normalized,
        WORKOUT_GENERATION_PHRASES
    )

    if workout_matches:
        return {
            "route": ROUTE_WORKOUT,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": sorted(workout_matches),
            "reason": "The user explicitly requested deterministic workout generation."
        }

    nutrition_matches = contains_phrase(
        normalized,
        NUTRITION_TERMS
    )

    if nutrition_matches:
        return {
            "route": ROUTE_NUTRITION,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": sorted(nutrition_matches),
            "reason": "The message is primarily about nutrition or stored nutrition targets."
        }

    coaching_matches = contains_phrase(
        normalized,
        COACHING_TERMS
    )

    if coaching_matches:
        return {
            "route": ROUTE_COACHING,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": sorted(coaching_matches),
            "reason": "The message contains explicit coaching, motivational, habit, or adherence intent."
        }

    personal_matches = contains_phrase(
        normalized,
        PERSONAL_DATA_PHRASES
    )

    if personal_matches:
        return {
            "route": ROUTE_PERSONAL_DATA,
            "safety_level": SAFETY_LEVEL_NONE,
            "matched_signals": sorted(personal_matches),
            "reason": "The message asks about the user's own stored fitness data."
        }

    return {
        "route": ROUTE_COACHING,
        "safety_level": SAFETY_LEVEL_NONE,
        "matched_signals": [],
        "reason": "No research, nutrition, workout-generation, personal-data, or safety signal was detected."
    }