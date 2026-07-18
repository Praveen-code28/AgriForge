import json
from pathlib import Path
from typing import Any


class TreatmentService:
    def __init__(self, knowledge_base_path: str | Path):
        self.knowledge_base_path = Path(knowledge_base_path)

    def get_treatment(self, crop: str, disease: str) -> dict[str, Any]:
        crop = crop.lower()
        disease = disease.lower()
        filepath = self.knowledge_base_path / crop / f"{disease}.json"
        if not filepath.exists():
            return {
                "crop": crop,
                "disease": disease,
                "found": False,
                "message": "No detailed knowledge file; consult local agronomist.",
                "prevention": [],
                "treatment": {},
            }
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return {
            "crop": crop,
            "disease": disease,
            "found": True,
            "disease_name": data.get("disease_name"),
            "description": data.get("description"),
            "symptoms": data.get("symptoms", []),
            "prevention": data.get("prevention", []),
            "treatment": data.get("treatment", {}),
            "severity_guidance": data.get("severity_guidance", {}),
            "farmer_advice": data.get("farmer_advice"),
            "disclaimer": data.get("disclaimer"),
        }
