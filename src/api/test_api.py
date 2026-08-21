from fastapi.testclient import TestClient

from src.api.app import (
    APP_TITLE,
    APP_VERSION,
    API_VERSION,
    create_app
)


def create_test_client():
    return TestClient(
        create_app()
    )


def test_root_endpoint():
    client = create_test_client()

    response = client.get(
        "/"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: Root endpoint did not return HTTP 200")

    data = response.json()

    if data["service"] != APP_TITLE:
        raise ValueError("FAIL: Root endpoint returned incorrect service name")

    if data["api_version"] != API_VERSION:
        raise ValueError("FAIL: Root endpoint returned incorrect API version")

    if data["docs"] != "/docs":
        raise ValueError("FAIL: Root endpoint returned incorrect documentation path")

    print("PASS: API root endpoint returns service information")


def test_health_endpoint():
    client = create_test_client()

    response = client.get(
        "/health"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: Health endpoint did not return HTTP 200")

    if response.json() != {
        "status": "healthy"
    }:
        raise ValueError("FAIL: Health endpoint returned incorrect response")

    print("PASS: API health endpoint reports healthy status")


def test_versioned_system_endpoint():
    client = create_test_client()

    response = client.get(
        "/api/v1/system/info"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: Versioned system endpoint did not return HTTP 200")

    data = response.json()

    if data["service"] != APP_TITLE:
        raise ValueError("FAIL: System endpoint returned incorrect service name")

    if data["api_version"] != API_VERSION:
        raise ValueError("FAIL: System endpoint returned incorrect API version")

    if data["status"] != "running":
        raise ValueError("FAIL: System endpoint returned incorrect status")

    print("PASS: Versioned API routing works correctly")


def test_unknown_route_returns_404():
    client = create_test_client()

    response = client.get(
        "/api/v1/does-not-exist"
    )

    if response.status_code != 404:
        raise ValueError("FAIL: Unknown API route did not return HTTP 404")

    print("PASS: Unknown API routes return HTTP 404")


def test_unsupported_method_returns_405():
    client = create_test_client()

    response = client.post(
        "/health"
    )

    if response.status_code != 405:
        raise ValueError("FAIL: Unsupported HTTP method did not return HTTP 405")

    print("PASS: Unsupported HTTP methods return HTTP 405")


def test_openapi_schema_available():
    client = create_test_client()

    response = client.get(
        "/openapi.json"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: OpenAPI schema was not available")

    schema = response.json()

    if schema["info"]["title"] != APP_TITLE:
        raise ValueError("FAIL: OpenAPI schema returned incorrect application title")

    if schema["info"]["version"] != APP_VERSION:
        raise ValueError("FAIL: OpenAPI schema returned incorrect application version")

    paths = schema[
        "paths"
    ]

    expected_paths = {
        "/",
        "/health",
        "/api/v1/system/info"
    }

    if not expected_paths.issubset(
        set(
            paths.keys()
        )
    ):
        raise ValueError("FAIL: OpenAPI schema is missing application routes")

    print("PASS: OpenAPI schema exposes API metadata and routes")


def test_swagger_docs_available():
    client = create_test_client()

    response = client.get(
        "/docs"
    )

    if response.status_code != 200:
        raise ValueError("FAIL: Swagger documentation endpoint was unavailable")

    if "text/html" not in response.headers[
        "content-type"
    ]:
        raise ValueError("FAIL: Swagger documentation did not return HTML")

    print("PASS: Swagger API documentation is available")


def test_app_factory_creates_independent_apps():
    first_app = create_app()
    second_app = create_app()

    if first_app is second_app:
        raise ValueError("FAIL: Application factory returned the same app instance")

    print("PASS: FastAPI application factory creates independent instances")


def test_value_error_becomes_http_400():
    app = create_app()

    @app.get(
        "/test/value-error"
    )
    def trigger_value_error():
        raise ValueError("Invalid test value")

    client = TestClient(
        app
    )

    response = client.get(
        "/test/value-error"
    )

    if response.status_code != 400:
        raise ValueError("FAIL: ValueError was not converted to HTTP 400")

    if response.json() != {
        "detail": "Invalid test value"
    }:
        raise ValueError("FAIL: ValueError handler returned incorrect response")

    print("PASS: Domain ValueErrors become HTTP 400 responses")


def test_json_endpoints_return_json_content_type():
    client = create_test_client()

    endpoints = [
        "/",
        "/health",
        "/api/v1/system/info"
    ]

    for endpoint in endpoints:
        response = client.get(
            endpoint
        )

        content_type = response.headers.get(
            "content-type",
            ""
        )

        if "application/json" not in content_type:
            raise ValueError(f"FAIL: Endpoint did not return JSON: {endpoint}")

    print("PASS: API endpoints return JSON responses")


if __name__ == "__main__":
    test_root_endpoint()
    test_health_endpoint()
    test_versioned_system_endpoint()
    test_unknown_route_returns_404()
    test_unsupported_method_returns_405()
    test_openapi_schema_available()
    test_swagger_docs_available()
    test_app_factory_creates_independent_apps()
    test_value_error_becomes_http_400()
    test_json_endpoints_return_json_content_type()