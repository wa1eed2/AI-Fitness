from fastapi import (
    Depends,
    FastAPI,
    Request
)

from fastapi.responses import JSONResponse

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

from src.database.setup_auth_database import (
    setup_auth_database
)


APP_TITLE = "AI-Fitness API"
APP_VERSION = "0.1.0"
API_VERSION = "v1"


def create_app():
    setup_auth_database()

    app = FastAPI(
        title=APP_TITLE,
        version=APP_VERSION,
        description="Backend API for the AI-Fitness platform"
    )

    @app.exception_handler(ValueError)
    async def value_error_handler(
        request: Request,
        exception: ValueError
    ):
        return JSONResponse(
            status_code=400,
            content={
                "detail": str(exception)
            }
        )

    @app.get(
        "/",
        tags=["System"]
    )
    def root():
        return {
            "service": APP_TITLE,
            "api_version": API_VERSION,
            "docs": "/docs"
        }

    @app.get(
        "/health",
        tags=["System"]
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

    return app


app = create_app()