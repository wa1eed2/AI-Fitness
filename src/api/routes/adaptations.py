from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status
)

from pydantic import (
    BaseModel
)

from src.api.dependencies import (
    get_current_auth
)

from src.database.query_adaptation_application_database import (
    get_adaptation_application_by_proposal,
    get_user_adaptation_applications
)

from src.database.query_adaptation_database import (
    create_adaptation_proposal,
    get_adaptation_proposal,
    get_user_adaptation_proposals,
    resolve_adaptation_proposal
)

from src.personalization.adaptation_application_service import (
    AdaptationAlreadyAppliedError,
    AdaptationApplicationNotFoundError,
    AdaptationProposalNotFoundError,
    apply_accepted_adaptation,
    rollback_applied_adaptation
)

from src.personalization.adaptation_engine import (
    evaluate_training_adaptation
)


router = APIRouter(
    prefix="/api/v1/adaptations",
    tags=["Adaptations"]
)


class AdaptationEvaluationRequest(BaseModel):
    reference_date: date | None = None


@router.post(
    "/evaluate",
    status_code=status.HTTP_201_CREATED
)
def evaluate_adaptation(
    payload: AdaptationEvaluationRequest,
    current_auth=Depends(
        get_current_auth
    )
):
    user_id = current_auth[
        "user_id"
    ]

    evaluation = evaluate_training_adaptation(
        user_id=user_id,
        reference_date=payload.reference_date
    )

    return create_adaptation_proposal(
        user_id,
        evaluation
    )


@router.get("")
def list_adaptation_proposals(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    proposal_status: str | None = Query(
        default=None,
        alias="status"
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    return get_user_adaptation_proposals(
        current_auth[
            "user_id"
        ],
        limit=limit,
        status=proposal_status
    )


@router.get(
    "/applications/history"
)
def list_adaptation_application_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    return get_user_adaptation_applications(
        current_auth[
            "user_id"
        ],
        limit=limit
    )


@router.post(
    "/applications/{application_id}/rollback"
)
def rollback_adaptation_application(
    application_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    try:
        return rollback_applied_adaptation(
            current_auth[
                "user_id"
            ],
            application_id
        )

    except AdaptationApplicationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation application not found"
        )


@router.get(
    "/{proposal_id}/application"
)
def get_proposal_application(
    proposal_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    application = get_adaptation_application_by_proposal(
        current_auth[
            "user_id"
        ],
        proposal_id
    )

    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation application not found"
        )

    return application


@router.get(
    "/{proposal_id}"
)
def get_adaptation(
    proposal_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    proposal = get_adaptation_proposal(
        current_auth[
            "user_id"
        ],
        proposal_id
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation proposal not found"
        )

    return proposal


@router.post(
    "/{proposal_id}/accept"
)
def accept_adaptation(
    proposal_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    proposal = resolve_adaptation_proposal(
        current_auth[
            "user_id"
        ],
        proposal_id,
        "accepted"
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation proposal not found"
        )

    return {
        "proposal": proposal,
        "applied": False,
        "message": (
            "The adaptation proposal was accepted. No workout or profile setting "
            "has been changed yet. Apply it explicitly to make the bounded change."
        )
    }


@router.post(
    "/{proposal_id}/reject"
)
def reject_adaptation(
    proposal_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    proposal = resolve_adaptation_proposal(
        current_auth[
            "user_id"
        ],
        proposal_id,
        "rejected"
    )

    if proposal is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation proposal not found"
        )

    return {
        "proposal": proposal,
        "applied": False,
        "message": "The adaptation proposal was rejected and no training change was applied."
    }


@router.post(
    "/{proposal_id}/apply"
)
def apply_adaptation(
    proposal_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    try:
        return apply_accepted_adaptation(
            current_auth[
                "user_id"
            ],
            proposal_id
        )

    except AdaptationProposalNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Adaptation proposal not found"
        )

    except AdaptationAlreadyAppliedError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Adaptation proposal has already been applied"
        )