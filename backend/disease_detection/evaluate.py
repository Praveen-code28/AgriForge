import os
import torch
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
from tqdm import tqdm

import config
from transforms import get_val_transforms
from dataset import get_loaders
from model import build_model
from utils import set_seed

def evaluate():
    set_seed()
    device = torch.device(config.DEVICE)
    val_transform = get_val_transforms()
    
    # Use *extra to absorb any extra items returned by get_loaders
    train_loader, val_loader, *extra = get_loaders(
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

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for images, labels in tqdm(val_loader, desc="Evaluating"):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            _, preds = outputs.max(1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    # Generate the classification report as a string
    report = classification_report(all_labels, all_preds, target_names=classes)
    
    print("\n📊 Classification Report:")
    print(report)
    
    # NEW: Save the report to a text file so you can read it without PowerShell scrambling it!
    with open("classification_report.txt", "w") as f:
        f.write(report)
    print("✅ Classification report saved as 'classification_report.txt'")

    cm = confusion_matrix(all_labels, all_preds, normalize='true')
    plt.figure(figsize=(14, 12))
    sns.heatmap(
        cm, 
        annot=True, 
        fmt=".2f", 
        xticklabels=classes, 
        yticklabels=classes, 
        cmap='Blues'
    )
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix - AgriForge Crop Health')
    plt.tight_layout()
    
    # FIX: bbox_inches='tight' forces matplotlib to expand the image borders 
    # so labels like "potato_early_blight" don't get cut off on the edges.
    plt.savefig('confusion_matrix.png', bbox_inches='tight')
    print("✅ Confusion matrix saved as confusion_matrix.png")

if __name__ == "__main__":
    evaluate()
