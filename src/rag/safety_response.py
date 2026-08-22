from src.rag.question_classifier import (
    ROUTE_SAFETY,
    SAFETY_LEVEL_CAUTION,
    SAFETY_LEVEL_URGENT
)


URGENT_SAFETY_MESSAGE = (
    "Stop the exercise. The symptoms you described may require urgent medical "
    "assessment. If symptoms are severe, sudden, worsening, or include chest pain, "
    "difficulty breathing, fainting, severe weakness, or loss of consciousness, "
    "seek urgent medical care or emergency services. I cannot diagnose the cause."
)


CAUTION_SAFETY_MESSAGE = (
    "Avoid movements that reproduce or worsen the symptom. I cannot diagnose the "
    "cause from a chat. If the pain or symptom is persistent, worsening, associated "
    "with significant swelling, weakness, numbness, or follows a meaningful injury, "
    "consider evaluation by an appropriate healthcare professional before continuing "
    "the affected activity."
)


def build_safety_response(classification):
    if not isinstance(classification, dict):
        raise ValueError("Classification must be a dictionary")

    if classification.get("route") != ROUTE_SAFETY:
        raise ValueError("Safety response requires a safety classification")

    level = classification.get(
        "safety_level"
    )

    if level == SAFETY_LEVEL_URGENT:
        return URGENT_SAFETY_MESSAGE

    if level == SAFETY_LEVEL_CAUTION:
        return CAUTION_SAFETY_MESSAGE

    raise ValueError("Safety classification has invalid safety level")