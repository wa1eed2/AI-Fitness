import os
import tempfile


from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status
)


from src.api.dependencies import (
    get_current_auth
)

from src.database.query_vision_analysis_database import (
    delete_vision_analysis,
    get_user_vision_analyses,
    get_vision_analysis
)

from src.vision.mediapipe_pose_adapter import (
    PoseBackendUnavailableError,
    PoseModelNotFoundError
)

from src.vision.video_squat_pipeline import (
    VideoBackendUnavailableError,
    VideoDecodeError,
    VideoMetadataError,
    VideoOpenError
)

from src.vision.vision_analysis_service import (
    MAX_VIDEO_UPLOAD_BYTES,
    analyze_and_store_squat_video,
    get_video_extension,
    validate_upload_filename
)


router = APIRouter(
    prefix="/api/v1/vision",
    tags=[
        "Computer Vision"
    ]
)


ALLOWED_VIDEO_CONTENT_TYPES = {
    "application/octet-stream",
    "video/avi",
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/x-matroska"
}


def get_request_content_type(
    request
):
    content_type = request.headers.get(
        "content-type",
        ""
    )

    return (
        content_type
        .split(
            ";",
            1
        )[
            0
        ]
        .strip()
        .casefold()
    )


async def write_request_video_to_temp_file(
    request,
    extension
):
    temporary_file = tempfile.NamedTemporaryFile(
        prefix="ai_fitness_vision_",
        suffix=extension,
        delete=False
    )

    temporary_path = temporary_file.name

    temporary_file.close()

    total_bytes = 0

    try:
        with open(
            temporary_path,
            "wb"
        ) as file_handle:
            async for chunk in request.stream():
                if not chunk:
                    continue

                total_bytes += len(
                    chunk
                )

                if total_bytes > MAX_VIDEO_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail="Uploaded video exceeds maximum allowed size"
                    )

                file_handle.write(
                    chunk
                )

        if total_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded video cannot be empty"
            )

        return (
            temporary_path,
            total_bytes
        )

    except Exception:
        if os.path.isfile(
            temporary_path
        ):
            os.remove(
                temporary_path
            )

        raise


@router.post(
    "/squat-video",
    status_code=status.HTTP_201_CREATED,
    summary="Analyze a squat video"
)
async def create_squat_video_analysis(
    request: Request,
    filename: str = Query(
        min_length=1,
        max_length=255
    ),
    sample_every_n_frames: int = Query(
        default=1,
        ge=1,
        le=30
    ),
    max_analyzed_frames: int | None = Query(
        default=None,
        ge=1,
        le=10000
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    normalized_filename = validate_upload_filename(
        filename
    )

    extension = get_video_extension(
        normalized_filename
    )

    content_type = get_request_content_type(
        request
    )

    if content_type not in ALLOWED_VIDEO_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported video content type"
        )

    temporary_path = None

    try:
        (
            temporary_path,
            file_size_bytes
        ) = await write_request_video_to_temp_file(
            request,
            extension
        )

        analyzer = getattr(
            request.app.state,
            "vision_analyzer",
            None
        )

        model_path = getattr(
            request.app.state,
            "vision_model_path",
            None
        )

        return analyze_and_store_squat_video(
            user_id=current_auth[
                "user_id"
            ],
            video_path=temporary_path,
            original_filename=normalized_filename,
            file_size_bytes=file_size_bytes,
            model_path=model_path,
            sample_every_n_frames=sample_every_n_frames,
            max_analyzed_frames=max_analyzed_frames,
            analyzer=analyzer
        )

    except PoseModelNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(
                error
            )
        )

    except (
        PoseBackendUnavailableError,
        VideoBackendUnavailableError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(
                error
            )
        )

    except (
        VideoOpenError,
        VideoMetadataError,
        VideoDecodeError
    ) as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(
                error
            )
        )

    finally:
        if (
            temporary_path is not None
            and os.path.isfile(
                temporary_path
            )
        ):
            os.remove(
                temporary_path
            )


@router.get(
    "/analyses"
)
def list_vision_analyses(
    limit: int = Query(
        default=20,
        ge=1,
        le=100
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    return get_user_vision_analyses(
        current_auth[
            "user_id"
        ],
        limit=limit
    )


@router.get(
    "/analyses/{analysis_id}"
)
def get_saved_vision_analysis(
    analysis_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    analysis = get_vision_analysis(
        current_auth[
            "user_id"
        ],
        analysis_id
    )

    if analysis is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vision analysis not found"
        )

    return analysis


@router.delete(
    "/analyses/{analysis_id}"
)
def remove_saved_vision_analysis(
    analysis_id: int = Path(
        ge=1
    ),
    current_auth=Depends(
        get_current_auth
    )
):
    deleted = delete_vision_analysis(
        current_auth[
            "user_id"
        ],
        analysis_id
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vision analysis not found"
        )

    return {
        "deleted": True,
        "analysis_id": analysis_id
    }