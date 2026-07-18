from typing import Annotated

from fastapi import APIRouter, Depends

from backend.app.api.deps import get_disease_inference, get_settings_dep
from backend.app.core.config import Settings
from backend.app.ml.disease_inference import DiseaseInferenceService
from backend.app.schemas import SupportedCropInfo, SupportedCropsResponse

router = APIRouter()

OOD_MSG = (
    "The model is trained on tomato and potato diseases only. "
    "Images of other crops may receive incorrect predictions. "
    "CropValidationLayer OOD detection is not yet implemented."
)


@router.get("/supported-crops", response_model=SupportedCropsResponse)
def supported_crops(
    settings: Annotated[Settings, Depends(get_settings_dep)],
    inference: Annotated[DiseaseInferenceService, Depends(get_disease_inference)],
):
    try:
        metadata = inference.supported_crops_metadata()
    except Exception:
        metadata = {
            "tomato": [
                "bacterial_spot",
                "early_blight",
                "healthy",
                "late_blight",
                "leaf_mold",
                "mosaic_virus",
                "septoria_leaf_spot",
                "spider_mites",
                "target_spot",
                "yellow_leaf_curl_virus",
            ],
            "potato": ["early_blight", "healthy", "late_blight"],
        }
    crops = [SupportedCropInfo(crop=c, diseases=d) for c, d in metadata.items()]
    return SupportedCropsResponse(crops=crops, ood_limitation=OOD_MSG)
