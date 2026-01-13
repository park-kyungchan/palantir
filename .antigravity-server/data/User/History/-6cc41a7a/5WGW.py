import logging
import sys
from pathlib import Path
from ultralytics import YOLO
import torch
import numpy as np
from PIL import Image

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_model():
    model_path = "models/doclayout_yolo_docstructbench_imgsz1024.pt"
    if not Path(model_path).exists():
        logger.error(f"Model not found at {model_path}")
        return

    logger.info(f"Loading model from {model_path}...")
    try:
        model = YOLO(model_path)
        logger.info("Model loaded.")
        
        # Create dummy image
        img = Image.new('RGB', (1024, 1024), color='white')
        
        logger.info("Running inference...")
        results = model(img, imgsz=1024)
        logger.info("Inference successful.")
        print(results)
        
    except Exception as e:
        logger.error(f"Inference failed: {e}", exc_info=True)
        
        # Inspection
        if 'model' in locals():
            logger.info("Applying Patch...")
            import torch.nn as nn
            count = 0
            for m in model.model.modules():
                if "Conv" in m.__class__.__name__ and not hasattr(m, 'bn'):
                    setattr(m, 'bn', nn.Identity())
                    count += 1
            logger.info(f"Patched {count} modules. Retrying inference...")
            
            try:
                results = model(img, imgsz=1024)
                logger.info("Inference successful AFTER patch!")
                print(results)
            except Exception as e2:
                logger.error(f"Inference failed AGAIN: {e2}")


if __name__ == "__main__":
    test_model()
