from typing import Any, Optional


class CropValidationLayer:
    """Lightweight input-safety / uncertainty layer for the closed-set classifier.

    The DL model is a closed-set classifier trained only on tomato and potato.
    High softmax confidence does NOT prove the input is a supported crop (e.g. a
    guava leaf can be classified as a tomato disease with high confidence). This
    layer does not attempt robust out-of-distribution detection (that needs
    future model work); it provides honest, conservative uncertainty signals:

    - a persistent advisory that only tomato/potato are supported, and
    - a low-confidence / small-margin flag that hints the prediction may be
      unreliable (including possible unsupported input).
    """

    SUPPORTED_CROPS = {"tomato", "potato"}

    # Below this top-1 probability the prediction is treated as uncertain.
    CONFIDENCE_THRESHOLD = 0.60
    # If top-1 and top-2 are this close, the model is effectively undecided.
    MARGIN_THRESHOLD = 0.15

    def validate(
        self,
        plant: str,
        confidence: float,
        predictions: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        is_supported = plant.lower() in self.SUPPORTED_CROPS

        margin = None
        if predictions and len(predictions) >= 2:
            top1 = float(predictions[0].get("confidence", 0.0) or 0.0)
            top2 = float(predictions[1].get("confidence", 0.0) or 0.0)
            margin = round(top1 - top2, 4)

        low_confidence = confidence < self.CONFIDENCE_THRESHOLD
        small_margin = margin is not None and margin < self.MARGIN_THRESHOLD
        uncertain = low_confidence or small_margin

        warning = None
        if not is_supported:
            warning = "Predicted crop is outside the trained classes (tomato, potato). Results may be unreliable."
        elif uncertain:
            warning = (
                "Prediction confidence is low. Please confirm the image is a clear "
                "tomato or potato leaf; other crops are not supported and may be "
                "misclassified."
            )

        return {
            "is_supported_crop": is_supported,
            "supported_crops": sorted(self.SUPPORTED_CROPS),
            "confidence": confidence,
            "top2_margin": margin,
            "uncertain": uncertain,
            "advisory": "This model supports tomato and potato leaves only.",
            "ood_warning": warning,
        }
