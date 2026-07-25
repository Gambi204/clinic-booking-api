from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Clinic Booking API",
        "status": "running",
        "documentation": "/docs",
        "health": "/health",
    }


def test_health_endpoint_checks_database(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "clinic-booking-api",
        "database": "reachable",
    }