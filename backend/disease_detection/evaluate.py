import os
import torch
import torch.nn.functional as F
from tqdm import tqdm
from PIL import Image
import numpy as np

import config
from transforms import get_val_transforms
from dataset import get_loaders
from model import build_model

def verify_misclassifications():
    device = torch.device(config.DEVICE)
    val_transform = get_val_transforms()
    
    # Get the dataset (assuming dataset returns image paths)
    _, val_loader, dataset = get_loaders(
        config.DATASET_PATH, 
        None, 
        val_transform, 
        config.BATCH_SIZE
    )

    checkpoint_path = os.path.join(config.CHECKPOINT_DIR, config.CHECKPOINT_NAME)
    checkpoint = torch.load(checkpoint_path, map_location=device, weights_only=False)
    classes = checkpoint['classes']
    
    model = build_model().to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()

    # Create a folder to save the wrong images
    save_dir = "misclassified_images"
    os.makedirs(save_dir, exist_ok=True)

    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(tqdm(val_loader, desc="Verifying")):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            
            # Get confidence scores using Softmax
            probabilities = F.softmax(outputs, dim=1)
            confidences, preds = torch.max(probabilities, 1)
            
            for i in range(len(images)):
                true_label = labels[i].item()
                pred_label = preds[i].item()
                confidence = confidences[i].item()
                
                # If the model got it wrong
                if true_label != pred_label:
                    true_class = classes[true_label]
                    pred_class = classes[pred_label]
                    
                    print(f"\n❌ Wrong Prediction!")
                    print(f"   True: {true_class} | Predicted: {pred_class} | Confidence: {confidence*100:.2f}%")
                    
                    # If you want to save the actual image to look at it:
                    # try:
                    #     # This depends on how your dataset is structured. 
                    #     # Standard PyTorch datasets allow you to access the original image via index.
                    #     global_idx = batch_idx * config.BATCH_SIZE + i
                    #     original_img, _ = dataset[global_idx] 
                    #     if isinstance(original_img, torch.Tensor):
                    #         original_img = original_img.permute(1, 2, 0).numpy()
                    #     img = Image.fromarray((original_img * 255).astype(np.uint8))
                    #     img.save(os.path.join(save_dir, f"true_{true_class}_pred_{pred_class}.png"))
                    # except Exception as e:
                    #     pass

if __name__ == "__main__":
    verify_misclassifications()
