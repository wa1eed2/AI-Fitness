from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    status
)

from pydantic import (
    BaseModel,
    Field
)

from src.api.dependencies import get_current_auth

from src.rag.llm_provider import LLMProviderUnavailableError

from src.rag.personalized_answer_generator import (
    generate_personalized_research_answer
)

from src.rag.provider_factory import get_default_llm_provider


router = APIRouter(
    prefix="/api/v1/ai",
    tags=["AI"]
)


class ResearchAnswerRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000
    )

    top_k: int = Field(
        default=5,
        ge=1,
        le=10
    )

    min_relevance_score: float = Field(
        default=0.05,
        ge=0,
        le=1
    )

    strong_relevance_score: float = Field(
        default=0.20,
        ge=0,
        le=1
    )

    max_context_chars: int = Field(
        default=6000,
        ge=500,
        le=20000
    )

    max_personal_context_chars: int = Field(
        default=5000,
        ge=500,
        le=15000
    )

    history_limit: int = Field(
        default=5,
        ge=1,
        le=20
    )

    topic: str | None = None
    subtopic: str | None = None
    min_year: int | None = None
    max_year: int | None = None
    study_design: str | None = None


def get_application_llm_provider(request: Request):
    provider = getattr(
        request.app.state,
        "llm_provider",
        None
    )

    if provider is not None:
        return provider

    return get_default_llm_provider()


@router.post("/research-answer")
def generate_ai_research_answer(
    payload: ResearchAnswerRequest,
    request: Request,
    current_auth=Depends(get_current_auth)
):
    if payload.strong_relevance_score < payload.min_relevance_score:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="strong_relevance_score cannot be lower than min_relevance_score"
        )

    if payload.min_year is not None and payload.max_year is not None and payload.min_year > payload.max_year:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_year cannot be greater than max_year"
        )

    try:
        provider = get_application_llm_provider(request)

        return generate_personalized_research_answer(
            user_id=current_auth["user_id"],
            question=payload.question,
            provider=provider,
            top_k=payload.top_k,
            min_relevance_score=payload.min_relevance_score,
            strong_relevance_score=payload.strong_relevance_score,
            max_context_chars=payload.max_context_chars,
            max_personal_context_chars=payload.max_personal_context_chars,
            history_limit=payload.history_limit,
            topic=payload.topic,
            subtopic=payload.subtopic,
            min_year=payload.min_year,
            max_year=payload.max_year,
            study_design=payload.study_design
        )

    except LLMProviderUnavailableError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error)
        )