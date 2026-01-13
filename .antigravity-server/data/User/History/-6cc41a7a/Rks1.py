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
                # results = model(img, imgsz=1024) # Skip this, we know it fails
                pass 
            except Exception as e2:
                logger.error(f"Inference failed AGAIN: {e2}")

            try:
                # Direct forward pass to inspect output
                import torch
                dummy_input = torch.zeros(1, 3, 1024, 1024).to(model.device)
                logger.info("Running direct forward pass on model.model...")
                # Note: model.model call might default to train mode? 
                model.model.eval()
                raw_out = model.model(dummy_input)
                logger.info(f"Raw output type: {type(raw_out)}")
                if isinstance(raw_out, dict):
                    logger.info(f"Raw output keys: {raw_out.keys()}")
                    for k, v in raw_out.items():
                         if hasattr(v, 'shape'):
                             logger.info(f"Key '{k}' shape: {v.shape}")
                
            except Exception as e3:
                logger.error(f"Raw forward failed: {e3}", exc_info=True)


if __name__ == "__main__":
    test_model()
