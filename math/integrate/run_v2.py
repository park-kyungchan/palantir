import sys
import os

# Add framework to path
sys.path.append("/home/palantir/integrate/framework")

from math_miner import MathMinerPipeline

def main():
    pdf_path = "/home/palantir/integrate/math-problem-and-answer/202106-h3-math-dif.pdf"
    output_dir = "/home/palantir/integrate/output_v2"
    
    pipeline = MathMinerPipeline(output_dir)
    pipeline.process_pdf(pdf_path)

if __name__ == "__main__":
    main()
