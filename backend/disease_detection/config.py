from pathlib import Path
import torch

# --- DYNAMIC PATH HANDLING ---
BASE_DIR = Path(__file__).resolve().parent

# Paths
DATASET_PATH = BASE_DIR / ".." / "data" / "crop_disease_dataset"
CHECKPOINT_DIR = BASE_DIR / ".." / ".." / "checkpoints"
CHECKPOINT_NAME = "agriforge_crop_health_v1.pth"
LOG_FILE = BASE_DIR / "training_log.csv"

# Model
MODEL_NAME = "efficientnet_b0"  # Much lighter & accurate for mobile than resnet18
NUM_CLASSES = 13               # 10 tomato + 3 potato classes
PRETRAINED = True
SEED = 42

# Image
IMG_SIZE = 224

# Training hyperparams
BATCH_SIZE = 64       # Increased batch size since AMP uses less memory
EPOCHS = 50
LEARNING_RATE = 1e-4
WEIGHT_DECAY = 1e-4

# Scheduler
SCHEDULER_FACTOR = 0.5
SCHEDULER_PATIENCE = 3

# Early stopping
EARLY_STOP_PATIENCE = 10

# Mixed Precision (AMP) - makes training ~2x faster on GPUs
USE_AMP = True if torch.cuda.is_available() else False

# Device
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Class weight mode ("balanced" or "focal")
CLASS_WEIGHT_MODE = "balanced"
