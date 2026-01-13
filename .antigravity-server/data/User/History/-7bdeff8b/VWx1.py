
import os
import sys
from lib.pipeline import HWPXPipeline

def main():
    """
    Run the full pipeline: PDF -> Ingest -> IR -> Compile -> Actions JSON
    """
    input_pdf = "sample.pdf"
    output_json = "output_actions.json"
    
    if not os.path.exists(input_pdf):
        print(f"Error: {input_pdf} not found.")
        sys.exit(1)
        
    print(f"Running HWPX Pipeline on {input_pdf}...")
    pipeline = HWPXPipeline()
    
    try:
        actions = pipeline.run(input_pdf, output_json)
        print(f"Success! Generated {len(actions)} actions.")
        
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
