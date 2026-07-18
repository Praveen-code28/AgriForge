import sys
from pathlib import Path
from typing import Any


class CropValidationLayer:
    """Stub for future out-of-distribution crop detection."""

    SUPPORTED_CROPS = {"tomato", "potato"}

    def validate(self, plant: str, confidence: float) -> dict[str, Any]:
        is_supported = plant.lower() in self.SUPPORTED_CROPS
        return {
            "is_supported_crop": is_supported,
            "ood_warning": None
            if is_supported
            else "Predicted crop may be outside trained classes. Results may be unreliable.",
            "confidence": confidence,
        }
