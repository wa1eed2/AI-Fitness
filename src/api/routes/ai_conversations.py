from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status
)

from pydantic import (
    BaseModel,
    Field
)

from src.api.dependencies import (
    get_current_auth
)

from src.api.routes.ai import (
    ResearchAnswerRequest,
    get_application_llm_provider
)

from src.database.query_ai_conversation_database import (
    create_ai_conversation,
    delete_ai_conversation,
    get_ai_conversation,
    get_ai_conversation_messages,
    get_user_ai_conversations,
    update_ai_conversation_title
)

from src.rag.conversation_router import (
    route_conversation_message
)

from src.rag.conversation_service import (
    ConversationNotFoundError
)

from src.rag.llm_provider import (
    LLMProviderUnavailableError
)


router = APIRouter(
    prefix="/api/v1/ai/conversations",
    tags=["AI Conversations"]
)


class ConversationCreateRequest(BaseModel):
    title: str | None = Field(
        default=None,
        max_length=120
    )


class ConversationUpdateRequest(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120
    )


class ConversationMessageRequest(ResearchAnswerRequest):
    history_message_limit: int = Field(
        default=8,
        ge=1,
        le=20
    )

    max_history_chars: int = Field(
        default=4000,
        ge=200,
        le=12000
    )

    meal_fraction: float = Field(
        default=0.25,
        gt=0,
        le=1
    )

    exercise_count: int | None = Field(
        default=None,
        ge=1,
        le=20
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED
)
def create_conversation(
    payload: ConversationCreateRequest,
    current_auth=Depends(get_current_auth)
):
    return create_ai_conversation(
        current_auth["user_id"],
        title=payload.title
    )


@router.get("")
def list_conversations(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    current_auth=Depends(get_current_auth)
):
    return get_user_ai_conversations(
        current_auth["user_id"],
        limit=limit
    )


@router.get("/{conversation_id}")
def get_conversation(
    conversation_id: int = Path(ge=1),
    current_auth=Depends(get_current_auth)
):
    conversation = get_ai_conversation(
        current_auth["user_id"],
        conversation_id
    )

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return conversation


@router.patch("/{conversation_id}")
def rename_conversation(
    payload: ConversationUpdateRequest,
    conversation_id: int = Path(ge=1),
    current_auth=Depends(get_current_auth)
):
    conversation = update_ai_conversation_title(
        current_auth["user_id"],
        conversation_id,
        payload.title
    )

    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return conversation


@router.delete("/{conversation_id}")
def remove_conversation(
    conversation_id: int = Path(ge=1),
    current_auth=Depends(get_current_auth)
):
    deleted = delete_ai_conversation(
        current_auth["user_id"],
        conversation_id
    )

    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return {
        "deleted": True,
        "conversation_id": conversation_id
    }


@router.get("/{conversation_id}/messages")
def get_conversation_messages(
    conversation_id: int = Path(ge=1),
    limit: int = Query(
        default=20,
        ge=1,
        le=20
    ),
    current_auth=Depends(get_current_auth)
):
    messages = get_ai_conversation_messages(
        current_auth["user_id"],
        conversation_id,
        limit=limit
    )

    if messages is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return messages


@router.post("/{conversation_id}/messages")
def send_conversation_message(
    payload: ConversationMessageRequest,
    request: Request,
    conversation_id: int = Path(ge=1),
    current_auth=Depends(get_current_auth)
):
    if payload.strong_relevance_score < payload.min_relevance_score:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="strong_relevance_score cannot be lower than min_relevance_score")

    if payload.min_year is not None and payload.max_year is not None and payload.min_year > payload.max_year:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="min_year cannot be greater than max_year")

    try:
        provider = get_application_llm_provider(
            request
        )

        return route_conversation_message(
            user_id=current_auth["user_id"],
            conversation_id=conversation_id,
            question=payload.question,
            provider=provider,
            top_k=payload.top_k,
            min_relevance_score=payload.min_relevance_score,
            strong_relevance_score=payload.strong_relevance_score,
            max_context_chars=payload.max_context_chars,
            max_personal_context_chars=payload.max_personal_context_chars,
            history_limit=payload.history_limit,
            history_message_limit=payload.history_message_limit,
            max_history_chars=payload.max_history_chars,
            meal_fraction=payload.meal_fraction,
            exercise_count=payload.exercise_count,
            topic=payload.topic,
            subtopic=payload.subtopic,
            min_year=payload.min_year,
            max_year=payload.max_year,
            study_design=payload.study_design
        )

    except ConversationNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    except LLMProviderUnavailableError as error:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))