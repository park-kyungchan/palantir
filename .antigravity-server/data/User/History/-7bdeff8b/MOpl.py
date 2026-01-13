
import os
import sys
import json
import argparse
from lib.pipeline import HWPXPipeline

def main():
    """
    Run the full pipeline: PDF -> Ingest -> IR -> Compile -> Actions JSON
    """
    parser = argparse.ArgumentParser(description="HWPX Reconstruction Pipeline")
    parser.add_argument("input_pdf", help="Input PDF file")
    parser.add_argument("output_json", help="Output JSON/PDF path")
    parser.add_argument("--pdf", action="store_true", help="Generate PDF Output instead of HWPX")
    
    args = parser.parse_args()
    
    input_pdf = args.input_pdf
    output_path = args.output_json
    
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found.")
        sys.exit(1)
        
    print(f"Running HWPX Pipeline on {input_pdf}...")
    
    # Initialize Pipeline
    # Default to use_mathpix=True for now as per Phase 7
    pipeline = HWPXPipeline(use_mathpix=True)
    
    try:
        # Run
        actions = pipeline.run(input_pdf, output_path, generate_pdf=args.pdf)
        
        if not args.pdf:
            # Save JSON
            print(f"Saving JSON output to: {output_path}")
            print(f"Success! Generated {len(actions)} actions.")
        else:
            print(f"Success! Generated PDF output to: {output_path}")
        
        # Simple stats
        action_types = {}
        for a in actions:
            t = a.get('action_type', 'Unknown')
            action_types[t] = action_types.get(t, 0) + 1
            
        print("Action Stats:", action_types)
        
    except Exception as e:
        print(f"Pipeline Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
