import torch
from PIL import Image
import numpy as np
import os
import config
from model import build_model
from transforms import get_inference_transforms

# Disease treatment recommendations for small farmers
REMEDIES = {
    "early_blight": "Apply copper-based fungicide; remove infected leaves; rotate crops.",
    "late_blight": "Use chlorothalonil/mancozeb; destroy infected plants; improve drainage.",
    "bacterial_spot": "Copper + mancozeb sprays; avoid overhead irrigation; remove debris.",
    "leaf_mold": "Improve ventilation; reduce humidity; apply fungicide if severe.",
    "mosaic_virus": "No cure. Remove infected plants; control aphids; disinfect tools.",
    "septoria_leaf_spot": "Apply azoxystrobin; remove lower infected leaves; mulch.",
    "spider_mites": "Spray neem oil or sulfur-based miticides; release predatory mites.",
    "target_spot": "Apply fungicides (e.g. chlorothalonil); improve air flow.",
    "yellow_leaf_curl_virus": "No cure. Control whiteflies; remove infected plants.",
    "healthy": "No action needed. Maintain watering & nutrition."
}

class AgriForgePredictor:
    def __init__(self, checkpoint_path=None):
        self.device = torch.device(config.DEVICE)
        if checkpoint_path is None:
            checkpoint_path = os.path.join(config.CHECKPOINT_DIR, config.CHECKPOINT_NAME)
            
        self.checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.classes = self.checkpoint['classes']
        
        self.model = build_model().to(self.device)
        self.model.load_state_dict(self.checkpoint['model_state_dict'])
        self.model.eval()
        
        self.transform = get_inference_transforms()

    def predict(self, image_path):
        image = Image.open(image_path).convert("RGB")
        image_np = np.array(image)
        input_tensor = self.transform(image=image_np)["image"].unsqueeze(0).to(self.device)

        with torch.no_grad():
            outputs = self.model(input_tensor)
            probs = torch.nn.functional.softmax(outputs, dim=1)[0]
            top3_conf, top3_idx = torch.topk(probs, k=3)

        predictions = []
        for i in range(3):
            class_name = self.classes[top3_idx[i]]
            plant, disease = class_name.split("_", 1)
            
            predictions.append({
                "plant": plant,
                "disease": disease,
                "confidence": top3_conf[i].item(),
                "remedy": REMEDIES.get(disease, "Consult local agronomist.")
            })
            
        return predictions

if __name__ == "__main__":
    predictor = AgriForgePredictor()
    test_img = r"need to change with the user dataimage.jpg" # Change to your test image path

    results = predictor.predict(test_img)
    primary_pred = results[0]
    
    print(f"\n🌿 Prediction for: {test_img}")
    print(f"Plant: {primary_pred['plant']}")
    print(f"Disease: {primary_pred['disease']}")
    print(f"Confidence: {primary_pred['confidence']*100:.2f}%")
    print(f"💡 Recommended Action: {primary_pred['remedy']}")
    
    print("\nOther possibilities:")
    for pred in results[1:]:
        print(f"- {pred['disease']} ({pred['confidence']*100:.2f}%)")
