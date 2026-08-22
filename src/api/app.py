from pathlib import Path


from fastapi import (
    Depends,
    FastAPI,
    Request
)

from fastapi.responses import (
    JSONResponse
)


from src.api.dependencies import (
    require_current_user
)

from src.api.routes.system import (
    router as system_router
)

from src.api.routes.auth import (
    router as auth_router
)

from src.api.routes.users import (
    router as users_router
)

from src.api.routes.user_settings import (
    router as user_settings_router
)

from src.api.routes.workouts import (
    router as workouts_router
)

from src.api.routes.progress import (
    router as progress_router
)

from src.api.routes.calendar import (
    router as calendar_router
)

from src.api.routes.analytics import (
    router as analytics_router
)

from src.api.routes.ai import (
    router as ai_router
)

from src.api.routes.ai_conversations import (
    router as ai_conversations_router
)

from src.api.routes.adaptations import (
    router as adaptations_router
)

from src.api.routes.vision import (
    router as vision_router
)


from src.database.setup_auth_database import (
    setup_auth_database
)

from src.database.setup_ai_conversation_database import (
    setup_ai_conversation_database
)

from src.database.setup_adaptation_database import (
    setup_adaptation_database
)

from src.database.setup_vision_database import (
    setup_vision_database
)


from src.vision.video_squat_pipeline import (
    analyze_squat_video
)


APP_TITLE = "AI-Fitness API"
APP_VERSION = "0.1.0"
API_VERSION = "v1"


DEFAULT_VISION_MODEL_PATH = str(
    Path(__file__).resolve().parents[2]
    / "data"
    / "models"
    / "pose_landmarker_lite.task"
)


def create_app(
    llm_provider=None,
    vision_analyzer=None,
    vision_model_path=None
):
    setup_auth_database()
    setup_ai_conversation_database()
    setup_adaptation_database()
    setup_vision_database()

    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description="Backend API for the AI-Fitness platform"
    )

    app.state.llm_provider = llm_provider

    app.state.vision_analyzer = (
        vision_analyzer
        if vision_analyzer is not None
        else analyze_squat_video
    )

    app.state.vision_model_path = (
        vision_model_path
        if vision_model_path is not None
        else DEFAULT_VISION_MODEL_PATH
    )

    @app.exception_handler(
        ValueError
    )
    async def value_error_handler(
        request: Request,
        exception: ValueError
    ):
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(
                    exception
                )
            }
        )

    @app.get(
        "/",
        tags=[
            "System"
        ]
    )
    def root():
        return {
            "service": APP_TITLE,
            "api_version": API_VERSION,
            "docs": "/docs"
        }

    @app.get(
        "/health",
        tags=[
            "System"
        ]
    )
    def health():
        return {
            "status": "healthy"
        }

    app.include_router(
        system_router
    )

    app.include_router(
        auth_router
    )

    app.include_router(
        users_router
    )

    app.include_router(
        user_settings_router,
        dependencies=[
            Depends(
                require_current_user
            )
        ]
    )

    app.include_router(
        workouts_router,
        dependencies=[
            Depends(
                require_current_user
            )
        ]
    )

    app.include_router(
        progress_router,
        dependencies=[
            Depends(
                require_current_user
            )
        ]
    )

    app.include_router(
        calendar_router,
        dependencies=[
            Depends(
                require_current_user
            )
        ]
    )

    app.include_router(
        analytics_router,
        dependencies=[
            Depends(
                require_current_user
            )
        ]
    )

    app.include_router(
        ai_router
    )

    app.include_router(
        ai_conversations_router
    )

    app.include_router(
        adaptations_router
    )

    app.include_router(
        vision_router
    )

    return app


app = create_app()