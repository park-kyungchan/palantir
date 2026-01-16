
import sys
import os
import json
import argparse
from typing import List, Dict, Any

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from lib.oda.memory.manager import MemoryManager

def format_as_xml(results: List[Dict[str, Any]]) -> str:
    """Formats the retrieval results as System Context XML."""
    xml = ["<long_term_memory_injection>"]
    
    if not results:
        xml.append("  <status>NO_RELEVANT_MEMORY_FOUND</status>")
    else:
        xml.append(f"  <status>RETRIEVED_{len(results)}_ITEMS</status>")
        xml.append("  <memory_items>")
        for item in results:
            xml.append("    <item>")
            xml.append(f"      <id>{item.get('id', 'unknown')}</id>")
            xml.append(f"      <type>{item.get('type', 'unknown')}</type>")
            xml.append(f"      <relevance_score>{item.get('score', 0.0):.4f}</relevance_score>")
            
            # Content flattening
            content = item.get('content', {})
            if isinstance(content, dict):
                for k, v in content.items():
                    xml.append(f"      <{k}>{v}</{k}>")
            else:
                xml.append(f"      <content>{content}</content>")
                
            xml.append("    </item>")
        xml.append("  </memory_items>")
    
    xml.append("</long_term_memory_injection>")
    return "\n".join(xml)

async def recall(query: str, limit: int = 5, verbose: bool = False):
    if verbose:
        print(f"🧠 [Recall] Searching LTM for: '{query}'")
        
    try:
        mm = MemoryManager()
        results = await mm.search(query, limit=limit)
        
        xml_output = format_as_xml(results)
        print(xml_output)
        
    except Exception as e:
        print(f"<long_term_memory_error>{str(e)}</long_term_memory_error>")
        if verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Recall Long-Term Memory Context")
    parser.add_argument("query", help="Search query string")
    parser.add_argument("--limit", type=int, default=5, help="Max results")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logs")
    
    args = parser.parse_args()
    
    import asyncio
    asyncio.run(recall(args.query, args.limit, args.verbose))
