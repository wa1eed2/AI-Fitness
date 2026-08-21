from fastapi import APIRouter


router = APIRouter(
    prefix="/api/v1/system",
    tags=["System"]
)


@router.get("/info")
def get_system_info():
    return {
        "service": "AI-Fitness API",
        "api_version": "v1",
        "status": "running"
    }