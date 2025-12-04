import sys
import os
sys.path.append("/home/palantir")
from integrate.framework.math_miner.pipeline import MathMinerPipeline

# Initialize Pipeline
output_dir = "/home/palantir/integrate/output_v2"
pipeline = MathMinerPipeline(output_dir)

# Run Vectorization Step
print("Running Vectorization on Diagrams...")
pipeline.vectorize_diagrams()

# Run Validation Step
print("Running Manifest Validation...")
pipeline.validate_manifest()
print("Done.")
