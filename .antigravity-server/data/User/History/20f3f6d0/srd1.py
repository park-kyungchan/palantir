
import sys
import logging
import torch.nn as nn
from pathlib import Path

# Setup simple logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure lib is finding
import sys
import os
sys.path.append(os.getcwd())

from lib.layout.detector import LayoutDetector, DetectionConfig

def test_patch():
    print("--- Starting Patch Test ---")
    config = DetectionConfig()
    detector = LayoutDetector(config)
    
    print("Calling _load_model()...")
    detector._load_model()
    print("_load_model() returned.")
    
    # Verify Patch
    model = detector._model.model # This is likely DocLayoutWrapper now, or not?
    print(f"Model type: {type(model)}")
    
    if hasattr(model, 'model'): # Wrapper wraps the model
        internal_model = model.model
    else:
        internal_model = model
        
    print(f"Internal model type: {type(internal_model)}")
    
    # Traverse and check for bn on Conv/dcv
    found_dcv = False
    patched_dcv = False
    
    for name, m in internal_model.named_modules():
        if "DilatedBottleneck" in m.__class__.__name__:
             if hasattr(m, 'dcv'):
                 found_dcv = True
                 dcv = m.dcv
                 if hasattr(dcv, 'bn'):
                     print(f"SUCCESS: {name}.dcv has 'bn'!")
                     patched_dcv = True
                 else:
                     print(f"FAILURE: {name}.dcv MISSING 'bn'!")
    
    if not found_dcv:
        print("WARNING: Did not find any DilatedBottleneck modules to check.")
        
    if patched_dcv:
        print("--- Patch Verification PASSED ---")
    else:
        print("--- Patch Verification FAILED ---")

if __name__ == "__main__":
    test_patch()
