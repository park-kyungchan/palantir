import os
import sys
import json
import uuid
import glob
from typing import List, Dict, Set, Any
from datetime import datetime

# Paths
WORKSPACE_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(WORKSPACE_ROOT)

from lib.oda.ontology.learning.algorithms.preprocessing import flatten_json
from lib.oda.lib.fpgrowth import FPTree
from lib.oda.lib.textrank import extract_summary
from lib.oda.memory.manager import MemoryManager

TRACE_DIR = os.path.join(WORKSPACE_ROOT, ".agent", "traces")

def load_traces(lookback_limit: int = 100) -> List[Dict[str, Any]]:
    """Loads raw trace files."""
    files = glob.glob(os.path.join(TRACE_DIR, "*.json"))
    # Sort by time newest first
    files.sort(key=os.path.getmtime, reverse=True)
    
    traces = []
    for f in files[:lookback_limit]:
        try:
            with open(f, 'r') as fd:
                data = json.load(fd)
                traces.append(data)
        except Exception as e:
            print(f"⚠️ Failed to load {f}: {e}")
    return traces

def transform_to_transactions(traces: List[Dict[str, Any]]) -> List[List[str]]:
    """
    Flattens traces into transactions for FP-Growth.
    Returns: List of lists of strings (e.g. ['status=FAILED', 'component=Executor'])
    """
    transactions = []
    
    for trace_data in traces:
        # Focus on the 'trace' object and events
        trace = trace_data.get('trace', {})
        events = trace_data.get('events', [])
        
        # Base transaction from Trace Meta
        # Flatten and convert to "key=value" strings
        flat_meta = flatten_json(trace)
        transaction_items = set()
        
        # Add high-level meta (status, etc)
        if 'status' in flat_meta:
            transaction_items.add(f"status={flat_meta['status']}")
            
        # Analyze Events
        # Basic heuristic: bag of event types and components
        for event in events:
            etype = event.get('event_type')
            comp = event.get('component')
            if etype: transaction_items.add(f"event={etype}")
            if comp: transaction_items.add(f"component={comp}")
            
            # If error, add error signature
            if etype == "ERROR" or event.get("type") == "ActionFailed":
                details = event.get('details', {})
                if isinstance(details, dict) and 'error' in details:
                    # Naive error tokenization for pattern mining
                    # e.g. "error_type=ImportError"
                    err_msg = str(details['error'])
                    if "ImportError" in err_msg: transaction_items.add("error_type=ImportError")
                    elif "ValueError" in err_msg: transaction_items.add("error_type=ValueError")
                    elif "FileNotFound" in err_msg: transaction_items.add("error_type=FileNotFound")
                    # Generic catch-all for mining
                    transaction_items.add("has_error=True")

        if transaction_items:
            transactions.append(list(transaction_items))
            
    return transactions

async def consolidate():
    print("🧠 [Consolidation Engine] Waking up...")
    
    # 1. Ingest
    traces = load_traces()
    print(f"   📥 Loaded {len(traces)} traces.")
    
    if not traces:
        print("   😴 No traces to process.")
        return

    # 2. Transform
    transactions = transform_to_transactions(traces)
    
    # 3. Mine (FP-Growth)
    min_sup = 2 # Minimum 2 occurrences to be a pattern
    if len(transactions) < 2:
        print("   📉 Insufficient data for mining (need > 1 trace).")
        return

    print(f"   ⛏️  Mining patterns (Min Support: {min_sup})...")
    tree = FPTree(transactions, min_sup)
    patterns = list(tree.mine())
    
    print(f"   ✨ Found {len(patterns)} frequent patterns.")
    
    # 4. Synthesize & Persist
    mm = MemoryManager()
    await mm.initialize()
    
    for pattern, support in patterns:
        if len(pattern) < 2: continue # Skip single items
        
        # Check if interesting (Heuristic)
        pat_list = list(pattern)
        if "status=FAILED" in pat_list or "has_error=True" in pat_list:
            print(f"   🚨 ANALYZING FAILURE PATTERN: {pat_list} (Count: {support})")
            
            # 5. Summarize (TextRank)
            # Find relevant traces
            relevant_texts = []
            for t in traces:
                # Re-check if this trace has the pattern (Basic check)
                # Ideally, we map transaction ID back to trace ID.
                # For now, brute force scan of events
                events = t.get('events', [])
                for e in events:
                    if e.get('event_type') == "ERROR" or e.get('type') == "ActionFailed":
                        details = e.get('details', {})
                        if 'error' in details:
                            relevant_texts.append(str(details['error']))
            
            summary = "Unknown Error Pattern"
            if relevant_texts:
                summary = extract_summary(relevant_texts)
                print(f"      📝 Semantic Summary: \"{summary}\"")
                
            # 6. Save as Pattern
            pat_obj = {
                "id": f"PAT-{uuid.uuid4().hex[:6]}",
                "frequency_count": support,
                "success_rate": 0.0, # Anti-pattern
                "structure": {
                    "trigger": "System Error",
                    "steps": [], # Steps not mined yet
                    "anti_patterns": list(pattern)
                }
            }
            # ODA Compliance: Await the async save
            await mm.save_object("pattern", pat_obj)
            print("      💾 Saved to Memory.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(consolidate())
