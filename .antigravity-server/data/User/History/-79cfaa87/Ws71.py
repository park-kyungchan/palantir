import subprocess
import re
from typing import List
from lib.knowledge.schema import EventDefinition

class TextEventIngestor:
    """
    Parses '한글오토메이션EventHandler추가_2504.pdf' to extract Event Definitions.
    Focuses on 'IHwpObjectEvents' implementation patterns.
    """
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def process(self) -> List[EventDefinition]:
        cmd = ["pdftotext", "-layout", self.pdf_path, "-"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        full_text = result.stdout
        
        events = []
        
        # Pattern: STDMETHOD(EventName)(Args)
        # Handle multiline args if necessary, though commonly single line in this logic
        pattern = re.compile(r"STDMETHOD\s*\(\s*(\w+)\s*\)\s*\((.*?)\)")
        
        matches = pattern.findall(full_text)
        
        for event_name, args in matches:
            # Clean args
            args_clean = args.strip()
            
            # Create Definition
            # Description is hard to reliably parse from code body without complex state machine.
            # We'll default to standard label.
            
            event = EventDefinition(
                event_id=event_name,
                arguments=args_clean,
                description=f"HWP Automation Event: {event_name}"
            )
            events.append(event)
            
        # Deduplicate by ID
        unique_events = {e.event_id: e for e in events}
        return list(unique_events.values())

if __name__ == "__main__":
    ingestor = TextEventIngestor("한글오토메이션EventHandler추가_2504.pdf")
    events = ingestor.process()
    print(f"Extracted {len(events)} Events:")
    for e in events:
        print(f" - {e.event_id}({e.arguments})")
