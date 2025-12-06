import hashlib
import json
import re
from typing import Dict, Any, Generator, Tuple, List, Set

# --- Regex Tokenizer ---
# Captures words, identifiers with dots/dashes, IP addresses
TOKEN_PATTERN = re.compile(r'(?u)\b\w[\w\.\-\:]*\b')

def tokenize(text: str) -> List[str]:
    """
    Extracts tokens from text, filtering basic punctuation.
    Lowercases everything.
    """
    if not text:
        return []
    return TOKEN_PATTERN.findall(text.lower())

# --- JSON Flattening ---

def flatten_json(nested_json: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """
    Recursively flattens a nested dictionary.
    Returns a unified flat dict.
    
    Example:
    {'a': 1, 'b': {'c': 2}} -> {'a': 1, 'b.c': 2}
    """
    # Note: Using MutableMapping check is robust but 'dict' is fine for JSON
    items: List[Tuple[str, Any]] = []
    
    for k, v in nested_json.items():
        # Intern keys to save memory (String Interning)
        new_key = sys.intern(f"{parent_key}{sep}{k}") if parent_key else sys.intern(k)
        
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            for i, item in enumerate(v):
                list_key = sys.intern(f"{new_key}{sep}{i}")
                if isinstance(item, dict):
                    items.extend(flatten_json(item, list_key, sep=sep).items())
                else:
                    items.append((list_key, v)) # Correction: Logic for primitives in list
        else:
            items.append((new_key, v))
            
    return dict(items)

def flatten_json_generator(nested_json: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Generator[Tuple[str, Any], None, None]:
    """
    Generator version of flattened items used for Streaming FP-Growth.
    """
    for k, v in nested_json.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            yield from flatten_json_generator(v, new_key, sep)
        elif isinstance(v, list):
            for i, item in enumerate(v):
                list_key = f"{new_key}{sep}{i}"
                if isinstance(item, dict):
                    yield from flatten_json_generator(item, list_key, sep)
                else:
                    yield (list_key, item)
        else:
            yield (new_key, v)

# --- Canonicalization ---

def generate_event_signature(flat_log: Dict[str, Any]) -> str:
    """
    Generates a deterministic SHA-256 hash specific to the content.
    """
    # 1. Canonicalize: Sort keys
    canonical_str = json.dumps(flat_log, sort_keys=True)
    
    # 2. Encode
    encoded_str = canonical_str.encode('utf-8')
    
    # 3. Hash
    return hashlib.sha256(encoded_str).hexdigest()

import sys
