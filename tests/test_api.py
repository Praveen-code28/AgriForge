import io

from PIL import Image

from ml.weather.knowledge_adapter import adapt_knowledge


def _make_test_image() -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color=(34, 139, 34)).save(buf, format="JPEG")
    buf.seek(0)
    return buf


def test_health(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_register_and_login(client):
    resp = client.post(
        "/api/v1/auth/register",
        json={"email": "farmer@test.com", "password": "secret123", "full_name": "Test Farmer"},
    )
    assert resp.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "farmer@test.com", "password": "secret123"},
    )
    assert login.status_code == 200
    assert "access_token" in login.json()


def test_complete_analysis(client):
    client.post(
        "/api/v1/auth/register",
        json={"email": "analysis@test.com", "password": "secret123"},
    )
    token = client.post(
        "/api/v1/auth/login",
        data={"username": "analysis@test.com", "password": "secret123"},
    ).json()["access_token"]

    image = _make_test_image()
    resp = client.post(
        "/api/v1/analysis/complete",
        headers={"Authorization": f"Bearer {token}"},
        files={"image": ("leaf.jpg", image, "image/jpeg")},
        data={"lat": "12.97", "lon": "77.59"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["prediction_id"] > 0
    assert body["combined"]["crop"] == "tomato"
    assert body["treatment"]["found"] is True


def test_supported_crops(client):
    resp = client.get("/api/v1/metadata/supported-crops")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["crops"]) >= 1
    assert "ood_limitation" in data


def test_knowledge_adapter_maps_schema():
    raw = {
        "favorable_conditions": {
            "temperature_celsius": {"min": 20, "max": 30},
            "humidity": "Moderate to high",
        }
    }
    adapted = adapt_knowledge(raw)
    assert "favorable_weather" in adapted
    assert adapted["favorable_weather"]["temperature_min"] == 20
    assert "spray_rules" in adapted
    assert "treatment_window" in adapted
