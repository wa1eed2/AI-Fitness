from src.api.test_helpers import (
    auth_headers,
    create_test_client,
    register_account,
    safe_delete_user
)


class RecordingVisionAnalyzer:
    def __init__(
        self
    ):
        self.calls = []

    def __call__(
        self,
        **kwargs
    ):
        self.calls.append(
            kwargs
        )

        return {
            "status": "analyzed",
            "exercise": "squat",
            "source": "video",
            "pose_backend": "test_pose_backend",
            "rep_count": 2,
            "video": {
                "path": kwargs[
                    "video_path"
                ],
                "fps": 30.0,
                "reported_frame_count": 120,
                "decoded_frame_count": 120,
                "sampled_frame_count": 120,
                "sample_every_n_frames": kwargs[
                    "sample_every_n_frames"
                ],
                "width": 1280,
                "height": 720,
                "reported_duration_seconds": 4.0
            },
            "detection_summary": {
                "pose_detected_frame_count": 110,
                "no_pose_frame_count": 10,
                "insufficient_landmark_frame_count": 0
            },
            "repetitions": [
                {
                    "repetition_number": 1,
                    "duration_seconds": 2.0,
                    "knee_range_of_motion_degrees": 75.0
                },
                {
                    "repetition_number": 2,
                    "duration_seconds": 2.0,
                    "knee_range_of_motion_degrees": 76.0
                }
            ],
            "summary": {
                "average_rep_duration_seconds": 2.0,
                "average_range_of_motion_degrees": 75.5,
                "variability_classification": "low_variability"
            },
            "limitations": [
                "Observed 2D geometry does not establish medical safety."
            ],
            "frame_observations": [
                {
                    "timestamp_seconds": 0.0
                }
            ]
        }


def upload_video(
    client,
    account,
    filename="squat.mp4",
    content=b"fake-video-content",
    content_type="video/mp4"
):
    headers = auth_headers(
        account
    )

    headers[
        "Content-Type"
    ] = content_type

    return client.post(
        "/api/v1/vision/squat-video",
        params={
            "filename": filename
        },
        headers=headers,
        content=content
    )


def test_video_analysis_requires_authentication():
    client = create_test_client(
        vision_analyzer=RecordingVisionAnalyzer(),
        vision_model_path="unused.task"
    )

    response = client.post(
        "/api/v1/vision/squat-video",
        params={
            "filename": "squat.mp4"
        },
        headers={
            "Content-Type": "video/mp4"
        },
        content=b"video"
    )

    if response.status_code not in {
        401,
        403
    }:
        raise ValueError(
            f"FAIL: Unauthenticated vision upload returned {response.status_code}"
        )

    print("PASS: Video analysis requires authentication")


def test_unsupported_video_extension_is_rejected():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-extension"
    )

    try:
        response = upload_video(
            client,
            account,
            filename="payload.exe"
        )

        if response.status_code != 400:
            raise ValueError(
                f"FAIL: Unsupported extension returned {response.status_code}"
            )

        if analyzer.calls:
            raise ValueError(
                "FAIL: Analyzer ran for unsupported file extension"
            )

        print("PASS: Vision API rejects unsupported video extension before analysis")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_unsupported_content_type_is_rejected():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-content-type"
    )

    try:
        response = upload_video(
            client,
            account,
            content_type="text/plain"
        )

        if response.status_code != 415:
            raise ValueError(
                f"FAIL: Unsupported MIME type returned {response.status_code}"
            )

        if analyzer.calls:
            raise ValueError(
                "FAIL: Analyzer ran for unsupported content type"
            )

        print("PASS: Vision API rejects unsupported video content type")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_empty_video_upload_is_rejected():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-empty"
    )

    try:
        response = upload_video(
            client,
            account,
            content=b""
        )

        if response.status_code != 400:
            raise ValueError(
                f"FAIL: Empty upload returned {response.status_code}"
            )

        if analyzer.calls:
            raise ValueError(
                "FAIL: Analyzer ran for empty video"
            )

        print("PASS: Vision API rejects empty video uploads")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_authenticated_video_analysis_is_persisted():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-success"
    )

    try:
        response = upload_video(
            client,
            account
        )

        if response.status_code != 201:
            raise ValueError(
                f"FAIL: Vision upload returned {response.status_code}: {response.text}"
            )

        result = response.json()

        if result["rep_count"] != 2:
            raise ValueError(
                "FAIL: Vision API returned wrong repetition count"
            )

        if result["source_filename"] != "squat.mp4":
            raise ValueError(
                "FAIL: Vision API lost original safe filename"
            )

        if len(
            analyzer.calls
        ) != 1:
            raise ValueError(
                "FAIL: Vision analyzer call count is incorrect"
            )

        print("PASS: Authenticated video analysis is persisted")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_persisted_result_does_not_expose_temporary_file():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-privacy"
    )

    try:
        response = upload_video(
            client,
            account
        )

        if response.status_code != 201:
            raise ValueError(
                "FAIL: Vision privacy fixture upload failed"
            )

        analysis = response.json()[
            "analysis_result"
        ]

        if "path" in analysis[
            "video"
        ]:
            raise ValueError(
                "FAIL: API exposed temporary filesystem path"
            )

        if "frame_observations" in analysis:
            raise ValueError(
                "FAIL: API persisted raw frame observations"
            )

        print("PASS: Vision API strips temporary path and frame observations")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_user_can_list_and_retrieve_own_analysis():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-history"
    )

    try:
        created_response = upload_video(
            client,
            account
        )

        if created_response.status_code != 201:
            raise ValueError(
                "FAIL: Vision history fixture upload failed"
            )

        created = created_response.json()

        list_response = client.get(
            "/api/v1/vision/analyses",
            headers=auth_headers(
                account
            )
        )

        if list_response.status_code != 200:
            raise ValueError(
                "FAIL: Vision history endpoint failed"
            )

        if len(
            list_response.json()
        ) != 1:
            raise ValueError(
                "FAIL: Vision history returned wrong count"
            )

        get_response = client.get(
            f"/api/v1/vision/analyses/{created['analysis_id']}",
            headers=auth_headers(
                account
            )
        )

        if get_response.status_code != 200:
            raise ValueError(
                "FAIL: Vision analysis retrieval failed"
            )

        if get_response.json()[
            "analysis_id"
        ] != created[
            "analysis_id"
        ]:
            raise ValueError(
                "FAIL: Vision retrieval returned wrong record"
            )

        print("PASS: Authenticated user can list and retrieve own vision analyses")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_vision_analysis_is_hidden_cross_user():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    owner = register_account(
        client,
        "vision-owner"
    )

    other = register_account(
        client,
        "vision-other"
    )

    try:
        created_response = upload_video(
            client,
            owner
        )

        created = created_response.json()

        response = client.get(
            f"/api/v1/vision/analyses/{created['analysis_id']}",
            headers=auth_headers(
                other
            )
        )

        if response.status_code != 404:
            raise ValueError(
                f"FAIL: Cross-user vision retrieval returned {response.status_code}"
            )

        other_history = client.get(
            "/api/v1/vision/analyses",
            headers=auth_headers(
                other
            )
        )

        if other_history.json():
            raise ValueError(
                "FAIL: Cross-user vision history leaked analysis"
            )

        print("PASS: Vision analysis API enforces authenticated ownership")

    finally:
        safe_delete_user(
            owner[
                "user_id"
            ]
        )

        safe_delete_user(
            other[
                "user_id"
            ]
        )


def test_user_can_delete_own_vision_analysis():
    analyzer = RecordingVisionAnalyzer()

    client = create_test_client(
        vision_analyzer=analyzer,
        vision_model_path="unused.task"
    )

    account = register_account(
        client,
        "vision-delete"
    )

    try:
        created_response = upload_video(
            client,
            account
        )

        created = created_response.json()

        delete_response = client.delete(
            f"/api/v1/vision/analyses/{created['analysis_id']}",
            headers=auth_headers(
                account
            )
        )

        if delete_response.status_code != 200:
            raise ValueError(
                "FAIL: Vision analysis deletion failed"
            )

        get_response = client.get(
            f"/api/v1/vision/analyses/{created['analysis_id']}",
            headers=auth_headers(
                account
            )
        )

        if get_response.status_code != 404:
            raise ValueError(
                "FAIL: Deleted vision analysis remained accessible"
            )

        print("PASS: User can explicitly delete own stored vision analysis")

    finally:
        safe_delete_user(
            account[
                "user_id"
            ]
        )


def test_openapi_documents_vision_routes():
    client = create_test_client(
        vision_analyzer=RecordingVisionAnalyzer(),
        vision_model_path="unused.task"
    )

    schema = client.get(
        "/openapi.json"
    ).json()

    paths = schema[
        "paths"
    ]

    required_paths = {
        "/api/v1/vision/squat-video",
        "/api/v1/vision/analyses",
        "/api/v1/vision/analyses/{analysis_id}"
    }

    missing = (
        required_paths
        - set(
            paths
        )
    )

    if missing:
        raise ValueError(
            f"FAIL: OpenAPI is missing vision routes: {sorted(missing)}"
        )

    print("PASS: OpenAPI documents authenticated computer-vision routes")


if __name__ == "__main__":
    test_video_analysis_requires_authentication()
    test_unsupported_video_extension_is_rejected()
    test_unsupported_content_type_is_rejected()
    test_empty_video_upload_is_rejected()
    test_authenticated_video_analysis_is_persisted()
    test_persisted_result_does_not_expose_temporary_file()
    test_user_can_list_and_retrieve_own_analysis()
    test_vision_analysis_is_hidden_cross_user()
    test_user_can_delete_own_vision_analysis()
    test_openapi_documents_vision_routes()