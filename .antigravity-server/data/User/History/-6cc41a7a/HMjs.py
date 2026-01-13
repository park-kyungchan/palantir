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
            logger.info("Inspecting model modules...")
            try:
                for name, module in model.model.named_modules():
                    if 'Conv' in str(type(module)):
                        if not hasattr(module, 'bn'):
                             print(f"Module {name} ({type(module)}) missing 'bn'")
            except Exception as inspect_err:
                logger.error(f"Inspection failed: {inspect_err}")

if __name__ == "__main__":
    test_model()
