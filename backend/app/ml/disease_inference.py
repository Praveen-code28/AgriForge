import sys
from pathlib import Path
from typing import Any


class DiseaseInferenceService:
    """Wrap AgriForgePredictor without changing preprocessing."""

    _instance: "DiseaseInferenceService | None" = None

    def __init__(self, checkpoint_path: str | Path):
        dd_path = Path(__file__).resolve().parents[2] / "disease_detection"
        if str(dd_path) not in sys.path:
            sys.path.insert(0, str(dd_path))

        from inference import AgriForgePredictor  # noqa: WPS433

        self.predictor = AgriForgePredictor(checkpoint_path=str(checkpoint_path))
        self.classes = self.predictor.classes

    @classmethod
    def get_instance(cls, checkpoint_path: str | Path) -> "DiseaseInferenceService":
        if cls._instance is None:
            cls._instance = cls(checkpoint_path)
        return cls._instance

    def predict(self, image_path: str | Path) -> list[dict[str, Any]]:
        return self.predictor.predict(str(image_path))

    def supported_crops_metadata(self) -> dict[str, list[str]]:
        crops: dict[str, set[str]] = {}
        for class_name in self.classes:
            plant, disease = class_name.split("_", 1)
            crops.setdefault(plant, set()).add(disease)
        return {crop: sorted(diseases) for crop, diseases in sorted(crops.items())}
