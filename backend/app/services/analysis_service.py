import logging
import time
from typing import Any

from backend.app.ml.crop_validation import CropValidationLayer
from backend.app.ml.disease_inference import DiseaseInferenceService
from backend.app.ml.weather_inference import WeatherInferenceService
from backend.app.services.treatment_service import TreatmentService

logger = logging.getLogger(__name__)


class DiseaseService:
    def __init__(self, inference: DiseaseInferenceService, crop_validator: CropValidationLayer):
        self.inference = inference
        self.crop_validator = crop_validator

    def predict_disease(self, image_path: str) -> dict[str, Any]:
        predictions = self.inference.predict(image_path)
        primary = predictions[0]
        validation = self.crop_validator.validate(
            primary["plant"], primary["confidence"], predictions
        )
        return {
            "primary": primary,
            "predictions": predictions,
            "crop_validation": validation,
        }


class WeatherService:
    def __init__(self, inference: WeatherInferenceService):
        self.inference = inference

    def analyze(
        self,
        crop: str,
        disease: str,
        confidence: float,
        lat: float | None = None,
        lon: float | None = None,
        address: str | None = None,
    ) -> dict[str, Any]:
        if disease.lower() == "healthy":
            return self.inference.analyze_healthy_summary(crop, lat, lon)
        return self.inference.analyze(crop, disease, confidence, lat, lon, address)


class AnalysisService:
    def __init__(
        self,
        disease_service: DiseaseService,
        treatment_service: TreatmentService,
        weather_service: WeatherService,
    ):
        self.disease_service = disease_service
        self.treatment_service = treatment_service
        self.weather_service = weather_service

    def complete_analysis(
        self,
        image_path: str,
        lat: float | None = None,
        lon: float | None = None,
        address: str | None = None,
    ) -> dict[str, Any]:
        t0 = time.perf_counter()
        disease_result = self.disease_service.predict_disease(image_path)
        dl_time = round(time.perf_counter() - t0, 3)
        primary = disease_result["primary"]
        crop = primary["plant"]
        disease = primary["disease"]
        confidence = primary["confidence"]

        t1 = time.perf_counter()
        treatment = self.treatment_service.get_treatment(crop, disease)
        treatment_time = round(time.perf_counter() - t1, 3)

        t2 = time.perf_counter()
        weather = self.weather_service.analyze(crop, disease, confidence, lat, lon, address)
        weather_time = round(time.perf_counter() - t2, 3)

        logger.info(
            "TIMING dl_inference=%ss treatment=%ss weather=%ss",
            dl_time,
            treatment_time,
            weather_time,
        )

        combined = {
            "crop": crop,
            "disease": disease,
            "confidence": confidence,
            "crop_validation": disease_result["crop_validation"],
            "top_predictions": disease_result["predictions"],
            "treatment_summary": treatment.get("farmer_advice") or treatment.get("message"),
            "weather_risk": None
            if isinstance(weather, dict) and weather.get("skipped")
            else weather.get("weather_analysis", {}).get("risk")
            if isinstance(weather, dict) and "weather_analysis" in weather
            else None,
            "spray_today": None
            if isinstance(weather, dict) and weather.get("skipped")
            else weather.get("spray_recommendation", {}).get("spray_today")
            if isinstance(weather, dict) and "spray_recommendation" in weather
            else None,
        }

        return {
            "disease": disease_result,
            "treatment": treatment,
            "weather": weather,
            "combined": combined,
        }
