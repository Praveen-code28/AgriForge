import albumentations as A
from albumentations.pytorch import ToTensorV2
import config

def get_train_transforms():
    return A.Compose([
        A.RandomResizedCrop(size=(config.IMG_SIZE, config.IMG_SIZE), scale=(0.8, 1.0)),
        A.HorizontalFlip(p=0.5),
        A.VerticalFlip(p=0.5),
        A.Rotate(limit=20, p=0.5),
        A.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05, p=0.5),
        
        # FIX: Removed A.CoarseDropout entirely to avoid Albumentations version conflicts.
        # Dropout is already handled inside our EfficientNet model!
        
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

def get_val_transforms():
    return A.Compose([
        A.Resize(height=256, width=256),
        A.CenterCrop(height=config.IMG_SIZE, width=config.IMG_SIZE),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])

def get_inference_transforms():
    return A.Compose([
        A.Resize(height=config.IMG_SIZE, width=config.IMG_SIZE),
        A.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ToTensorV2(),
    ])
