import torch.nn as nn
import timm
import config

def build_model(num_classes=config.NUM_CLASSES, pretrained=config.PRETRAINED):
    # Using timm allows us to easily swap to mobile-friendly models later
    model = timm.create_model(
        config.MODEL_NAME, 
        pretrained=pretrained, 
        num_classes=num_classes
    )
    
    # Add custom head with dropout
    in_features = model.classifier.in_features
    model.classifier = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, num_classes)
    )
    
    return model.to(config.DEVICE)
