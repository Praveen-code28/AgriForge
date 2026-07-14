import os
from torch.utils.data import Dataset, DataLoader
from PIL import Image
from collections import Counter
import numpy as np
import torch
import config


class CropDiseaseDataset(Dataset):
    def __init__(self, root, transform=None, class_to_idx=None):
        self.root = root
        self.transform = transform
        self.samples = []
        
        self.class_to_idx = class_to_idx if class_to_idx is not None else {}
        self.classes = list(class_to_idx.keys()) if class_to_idx is not None else []

        idx = 0
        for crop in sorted(os.listdir(root)):
            crop_dir = os.path.join(root, crop)
            if not os.path.isdir(crop_dir): continue
            
            for class_name in sorted(os.listdir(crop_dir)):
                class_dir = os.path.join(crop_dir, class_name)
                if not os.path.isdir(class_dir): continue
                
                full_class_name = f"{crop}_{class_name}"
                
                if class_to_idx is None:
                    if full_class_name not in self.class_to_idx:
                        self.class_to_idx[full_class_name] = idx
                        self.classes.append(full_class_name)
                        idx += 1

                current_idx = self.class_to_idx[full_class_name]
                
                for img_name in os.listdir(class_dir):
                    if img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.webp')) and not img_name.startswith('.'):
                        self.samples.append((os.path.join(class_dir, img_name), current_idx))

    def __len__(self): return len(self.samples)

    def __getitem__(self, idx):
        img_path, label = self.samples[idx]
        try:
            image = Image.open(img_path).convert("RGB")
            image = np.array(image) # Convert to numpy for Albumentations
        except Exception as e:
            print(f"Error loading image {img_path}: {e}")
            image = np.zeros((config.IMG_SIZE, config.IMG_SIZE, 3), dtype=np.uint8)
            
        if self.transform:
            image = self.transform(image=image)["image"]
        return image, label


def get_loaders(data_dir, train_transform, val_transform, batch_size, num_workers=4):
    train_path = os.path.join(data_dir, "train")
    val_path = os.path.join(data_dir, "val")
    
    train_dataset = CropDiseaseDataset(train_path, transform=train_transform)
    val_dataset = CropDiseaseDataset(val_path, transform=val_transform, class_to_idx=train_dataset.class_to_idx)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, 
                              num_workers=num_workers, pin_memory=torch.cuda.is_available())
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, 
                            num_workers=num_workers, pin_memory=torch.cuda.is_available())

    return train_loader, val_loader, train_dataset.classes, train_dataset.class_to_idx


def compute_class_weights(dataset):
    labels = [label for _, label in dataset.samples]
    counts = Counter(labels)
    total = sum(counts.values())
    num_classes = len(dataset.classes)
    weights = [total / (num_classes * counts.get(c, 1)) for c in range(num_classes)]
    return torch.tensor(weights, dtype=torch.float)
