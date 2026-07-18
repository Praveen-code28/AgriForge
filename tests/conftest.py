import io
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.config import get_settings
from backend.app.db.base import Base
from backend.app.db.session import get_db
from backend.app.main import create_app
from backend.app.ml.crop_validation import CropValidationLayer
from backend.app.ml.disease_inference import DiseaseInferenceService
from backend.app.services.analysis_service import AnalysisService, DiseaseService, WeatherService
from backend.app.services.treatment_service import TreatmentService
from ml.weather.knowledge_adapter import adapt_knowledge


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    mock_predictions = [
        {
            "plant": "tomato",
            "disease": "early_blight",
            "confidence": 0.91,
            "remedy": "Apply copper-based fungicide.",
        }
    ]

    class MockDiseaseInference:
        classes = ["tomato_early_blight", "tomato_healthy", "potato_late_blight"]

        def predict(self, image_path):
            return mock_predictions

        def supported_crops_metadata(self):
            return {"tomato": ["early_blight", "healthy"], "potato": ["late_blight"]}

    mock_inference = MockDiseaseInference()
    DiseaseInferenceService._instance = mock_inference

    def mock_get_disease_inference():
        return mock_inference

    from backend.app.api import deps

    app.dependency_overrides[deps.get_disease_inference] = mock_get_disease_inference
    app.dependency_overrides[deps.get_disease_service] = lambda: DiseaseService(
        mock_inference, CropValidationLayer()
    )

    settings = get_settings()
    treatment = TreatmentService(settings.repo_root / settings.KNOWLEDGE_BASE_PATH)
    weather_mock = MagicMock()
    weather_mock.analyze.return_value = {"weather_analysis": {"risk": "Moderate", "risk_score": 45}}
    weather_mock.analyze_healthy_summary.return_value = {"skipped": True}

    app.dependency_overrides[deps.get_treatment_service] = lambda: treatment
    app.dependency_overrides[deps.get_weather_service] = lambda: WeatherService(weather_mock)
    app.dependency_overrides[deps.get_analysis_service] = lambda: AnalysisService(
        DiseaseService(mock_inference, CropValidationLayer()),
        treatment,
        WeatherService(weather_mock),
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
    DiseaseInferenceService._instance = None


def _make_test_image() -> io.BytesIO:
    buf = io.BytesIO()
    Image.new("RGB", (224, 224), color=(34, 139, 34)).save(buf, format="JPEG")
    buf.seek(0)
    return buf
