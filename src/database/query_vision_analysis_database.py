import json

from src.database.setup_vision_database import (
    get_vision_database_connection
)


VALID_VISION_STATUSES = {
    "analyzed",
    "insufficient_data"
}


VALID_EXERCISES = {
    "squat"
}


def validate_user_id(
    user_id
):
    if not isinstance(user_id, int) or isinstance(user_id, bool):
        raise ValueError("user_id must be an integer")

    if user_id < 1:
        raise ValueError("user_id must be positive")

    return user_id


def validate_analysis_id(
    analysis_id
):
    if not isinstance(analysis_id, int) or isinstance(analysis_id, bool):
        raise ValueError("analysis_id must be an integer")

    if analysis_id < 1:
        raise ValueError("analysis_id must be positive")

    return analysis_id


def validate_source_filename(
    source_filename
):
    if not isinstance(source_filename, str):
        raise ValueError("source_filename must be a string")

    normalized = source_filename.strip()

    if not normalized:
        raise ValueError("source_filename cannot be empty")

    if len(normalized) > 255:
        raise ValueError("source_filename cannot exceed 255 characters")

    return normalized


def validate_file_size_bytes(
    file_size_bytes
):
    if not isinstance(file_size_bytes, int) or isinstance(file_size_bytes, bool):
        raise ValueError("file_size_bytes must be an integer")

    if file_size_bytes < 1:
        raise ValueError("file_size_bytes must be positive")

    return file_size_bytes


def validate_sample_every_n_frames(
    sample_every_n_frames
):
    if not isinstance(sample_every_n_frames, int) or isinstance(sample_every_n_frames, bool):
        raise ValueError("sample_every_n_frames must be an integer")

    if sample_every_n_frames < 1:
        raise ValueError("sample_every_n_frames must be positive")

    return sample_every_n_frames


def validate_analysis_result(
    analysis_result
):
    if not isinstance(analysis_result, dict):
        raise ValueError("analysis_result must be a dictionary")

    exercise = analysis_result.get(
        "exercise"
    )

    if exercise not in VALID_EXERCISES:
        raise ValueError("Unsupported vision exercise")

    analysis_status = analysis_result.get(
        "status"
    )

    if analysis_status not in VALID_VISION_STATUSES:
        raise ValueError("Unsupported vision analysis status")

    rep_count = analysis_result.get(
        "rep_count"
    )

    if not isinstance(rep_count, int) or isinstance(rep_count, bool):
        raise ValueError("analysis_result rep_count must be an integer")

    if rep_count < 0:
        raise ValueError("analysis_result rep_count cannot be negative")

    video = analysis_result.get(
        "video"
    )

    detection_summary = analysis_result.get(
        "detection_summary"
    )

    summary = analysis_result.get(
        "summary"
    )

    repetitions = analysis_result.get(
        "repetitions"
    )

    limitations = analysis_result.get(
        "limitations"
    )

    if not isinstance(video, dict):
        raise ValueError("analysis_result requires video metadata")

    if not isinstance(detection_summary, dict):
        raise ValueError("analysis_result requires detection_summary")

    if not isinstance(summary, dict):
        raise ValueError("analysis_result requires summary")

    if not isinstance(repetitions, list):
        raise ValueError("analysis_result requires repetitions list")

    if not isinstance(limitations, list):
        raise ValueError("analysis_result requires limitations list")

    return analysis_result


def serialize_json(
    value,
    field_name
):
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(
                ",",
                ":"
            )
        )

    except (
        TypeError,
        ValueError
    ) as error:
        raise ValueError(
            f"{field_name} must be JSON serializable"
        ) from error


def deserialize_json(
    value,
    field_name
):
    try:
        return json.loads(
            value
        )

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Stored {field_name} contains invalid JSON"
        ) from error


def deserialize_full_analysis_row(
    row
):
    if row is None:
        return None

    analysis_result = deserialize_json(
        row[
            "analysis_result_json"
        ],
        "analysis_result_json"
    )

    if not isinstance(analysis_result, dict):
        raise ValueError(
            "Stored analysis_result_json must decode to a dictionary"
        )

    return {
        "analysis_id": row[
            "analysis_id"
        ],
        "user_id": row[
            "user_id"
        ],
        "exercise": row[
            "exercise"
        ],
        "status": row[
            "status"
        ],
        "rep_count": row[
            "rep_count"
        ],
        "source_filename": row[
            "source_filename"
        ],
        "file_size_bytes": row[
            "file_size_bytes"
        ],
        "sample_every_n_frames": row[
            "sample_every_n_frames"
        ],
        "analysis_result": analysis_result,
        "created_at": row[
            "created_at"
        ]
    }


def deserialize_summary_row(
    row
):
    return {
        "analysis_id": row[
            "analysis_id"
        ],
        "user_id": row[
            "user_id"
        ],
        "exercise": row[
            "exercise"
        ],
        "status": row[
            "status"
        ],
        "rep_count": row[
            "rep_count"
        ],
        "source_filename": row[
            "source_filename"
        ],
        "file_size_bytes": row[
            "file_size_bytes"
        ],
        "sample_every_n_frames": row[
            "sample_every_n_frames"
        ],
        "created_at": row[
            "created_at"
        ]
    }


def create_vision_analysis(
    user_id,
    source_filename,
    file_size_bytes,
    sample_every_n_frames,
    analysis_result
):
    validate_user_id(
        user_id
    )

    source_filename = validate_source_filename(
        source_filename
    )

    validate_file_size_bytes(
        file_size_bytes
    )

    validate_sample_every_n_frames(
        sample_every_n_frames
    )

    validate_analysis_result(
        analysis_result
    )

    video_metadata_json = serialize_json(
        analysis_result[
            "video"
        ],
        "video"
    )

    detection_summary_json = serialize_json(
        analysis_result[
            "detection_summary"
        ],
        "detection_summary"
    )

    summary_json = serialize_json(
        analysis_result[
            "summary"
        ],
        "summary"
    )

    repetitions_json = serialize_json(
        analysis_result[
            "repetitions"
        ],
        "repetitions"
    )

    limitations_json = serialize_json(
        analysis_result[
            "limitations"
        ],
        "limitations"
    )

    analysis_result_json = serialize_json(
        analysis_result,
        "analysis_result"
    )

    connection = get_vision_database_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO vision_analyses (
                user_id,
                exercise,
                status,
                rep_count,
                source_filename,
                file_size_bytes,
                sample_every_n_frames,
                video_metadata_json,
                detection_summary_json,
                summary_json,
                repetitions_json,
                limitations_json,
                analysis_result_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                analysis_result[
                    "exercise"
                ],
                analysis_result[
                    "status"
                ],
                analysis_result[
                    "rep_count"
                ],
                source_filename,
                file_size_bytes,
                sample_every_n_frames,
                video_metadata_json,
                detection_summary_json,
                summary_json,
                repetitions_json,
                limitations_json,
                analysis_result_json
            )
        )

        analysis_id = cursor.lastrowid

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return get_vision_analysis(
        user_id,
        analysis_id
    )


def get_vision_analysis(
    user_id,
    analysis_id
):
    validate_user_id(
        user_id
    )

    validate_analysis_id(
        analysis_id
    )

    connection = get_vision_database_connection()

    try:
        row = connection.execute(
            """
            SELECT
                analysis_id,
                user_id,
                exercise,
                status,
                rep_count,
                source_filename,
                file_size_bytes,
                sample_every_n_frames,
                analysis_result_json,
                created_at
            FROM vision_analyses
            WHERE user_id = ?
              AND analysis_id = ?
            """,
            (
                user_id,
                analysis_id
            )
        ).fetchone()

    finally:
        connection.close()

    return deserialize_full_analysis_row(
        row
    )


def get_user_vision_analyses(
    user_id,
    limit=20
):
    validate_user_id(
        user_id
    )

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("limit must be an integer")

    if limit < 1 or limit > 100:
        raise ValueError("limit must be between 1 and 100")

    connection = get_vision_database_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                analysis_id,
                user_id,
                exercise,
                status,
                rep_count,
                source_filename,
                file_size_bytes,
                sample_every_n_frames,
                created_at
            FROM vision_analyses
            WHERE user_id = ?
            ORDER BY created_at DESC, analysis_id DESC
            LIMIT ?
            """,
            (
                user_id,
                limit
            )
        ).fetchall()

    finally:
        connection.close()

    return [
        deserialize_summary_row(
            row
        )
        for row in rows
    ]


def count_user_vision_analyses(
    user_id
):
    validate_user_id(
        user_id
    )

    connection = get_vision_database_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS analysis_count
            FROM vision_analyses
            WHERE user_id = ?
            """,
            (
                user_id,
            )
        ).fetchone()

    finally:
        connection.close()

    return row[
        "analysis_count"
    ]


def delete_vision_analysis(
    user_id,
    analysis_id
):
    validate_user_id(
        user_id
    )

    validate_analysis_id(
        analysis_id
    )

    connection = get_vision_database_connection()

    try:
        cursor = connection.execute(
            """
            DELETE FROM vision_analyses
            WHERE user_id = ?
              AND analysis_id = ?
            """,
            (
                user_id,
                analysis_id
            )
        )

        deleted = (
            cursor.rowcount
            == 1
        )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

    return deleted