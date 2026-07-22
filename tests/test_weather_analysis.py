import pytest
from fastapi.testclient import TestClient

from backend.app.db.session import get_db
from backend.app.main import create_app
from ml.weather.location import Location, LocationResolver
from ml.weather.orchestrator import WeatherIntelligence


@pytest.fixture
def weather_client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as client:
        yield client


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = "weather-test@example.com"
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "TestPass123", "full_name": "Weather Tester"},
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": "TestPass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_weather_analysis_missing_location_returns_422(weather_client: TestClient):
    headers = _auth_headers(weather_client)

    response = weather_client.post(
        "/api/v1/analysis/weather",
        json={
            "crop": "tomato",
            "disease": "late_blight",
            "confidence": 0.88,
            "lat": None,
            "lon": None,
            "address": None,
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert "location" in response.json()["detail"].lower() or "address" in response.json()["detail"].lower()


def test_weather_process_returns_fallback_for_unavailable_weather(monkeypatch):
    engine = WeatherIntelligence(knowledge_base_path="ml/weather/knowledge", api_key=None)
    monkeypatch.setattr(engine.location_resolver, "resolve", lambda lat, lon, address: Location(lat=12.34, lon=56.78))

    result = engine.process(crop="tomato", disease="late_blight", confidence=0.88, lat=12.34, lon=56.78, address=None)

    assert result["skipped"] is True
    assert "weather" in result["reason"].lower() or "unavailable" in result["reason"].lower()
