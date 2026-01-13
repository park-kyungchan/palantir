import argparse
import sys
import os

from lib.pipeline import HWPXPipeline

def main():
    parser = argparse.ArgumentParser(description="HWPX Automation Pipeline: PDF to HWP Actions")
    parser.add_argument("input_file", help="Path to input PDF file")
    parser.add_argument("--output", "-o", help="Path to output JSON file (default: input_file.json)")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR (Use only layout analysis)")
    
    args = parser.parse_args()
    
    input_path = os.path.abspath(args.input_file)
    if not os.path.exists(input_path):
        print(f"Error: Input file '{input_path}' does not exist.")
        sys.exit(1)
        
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        # Default: input filename + .json
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = os.path.join(os.path.dirname(input_path), f"{base_name}_actions.json")
        
    print(f"Starting HWPX Pipeline...")
    print(f"Input: {input_path}")
    print(f"Output: {output_path}")
    
    try:
        pipeline = HWPXPipeline(use_mathpix=not args.no_ocr)
        actions = pipeline.run(input_path, output_path)
        print(f"Success! Generated {len(actions)} actions.")
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
