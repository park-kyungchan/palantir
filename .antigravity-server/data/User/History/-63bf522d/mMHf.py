#!/usr/bin/env python3
import os
import json
import argparse
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Set
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# --- KB 29: TRACE METHODOLOGY MAPPING ---
TRACE_PATTERNS = {
    "KB_20_Hash_Maps": {
        "pattern": r"new Map<|new Set<|dict\(|\.get\(|\.set\(",
        "concept": "Hash Maps / Caching",
        "description": "Efficient O(1) lookups using hash-based structures."
    },
    "KB_21_Trees_Graphs": {
        "pattern": r"TreeNode|GraphNode|left:|right:|children:|bfs\(|dfs\(",
        "concept": "Hierarchical Data Structures",
        "description": "Tree or Graph traversal signals."
    },
    "KB_22_Dynamic_Programming": {
        "pattern": r"memo\[|cache\[|dp\[|lru_cache",
        "concept": "Memoization / DP",
        "description": "Optimization via caching intermediate results."
    },
    "KB_00d_Async": {
        "pattern": r"async def|await |Promise<|new Promise",
        "concept": "Asynchronous Concurrency",
        "description": "Non-blocking I/O operations."
    },
    "KB_00e_TypeScript": {
        "pattern": r"interface |type |<T>|extends |implements ",
        "concept": "Type Safety",
        "description": "Static typing and contract definitions."
    },
    "KB_24_System_Design": {
        "pattern": r"class .*Repository|class .*Service|class .*Controller|Singleton|Factory",
        "concept": "Architectural Patterns",
        "description": "Structured design patterns (Repository, Service, etc.)."
    },
    "KB_02_React": {
        "pattern": r"useState|useEffect|useContext|useReducer",
        "concept": "React Hooks",
        "description": "Functional state management."
    },
    "KB_11_OSDK": {
        "pattern": r"createClient|@osdk/client|@FoundryFunction|@OntologyEditFunction|Obj\.create",
        "concept": "Palantir OSDK / Foundry",
        "description": "Interaction with Palantir Foundry Ontology."
    }
}

class TraceAnalysisEngine:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.architecture = {"Domain": [], "Application": [], "Infrastructure": []}
        self.modules = []
        self.patterns_found = []

    def scan_codebase(self):
        """Executes the TRACE method: Trace, Recognize, Analyze, Catalog."""
        logger.info(f"Starting TRACE analysis on {self.root_dir}...")
        
        for root, dirs, files in os.walk(self.root_dir):
            if '.git' in dirs: dirs.remove('.git')
            if 'node_modules' in dirs: dirs.remove('node_modules')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            if '.agent' in dirs: dirs.remove('.agent')
            
            for file in files:
                file_path = Path(root) / file
                self._analyze_file(file_path)

    def _analyze_file(self, file_path: Path):
        """Analyzes a file for patterns and assigns it to a layer."""
        try:
            relative_path = file_path.relative_to(self.root_dir)
            str_path = str(relative_path)
            
            # --- 1. Layer Classification (Architecture) ---
            layer = "Application" # Default
            if "ontology" in str_path or "types" in str_path or "model" in str_path:
                layer = "Domain"
            elif "database" in str_path or "storage" in str_path or "api" in str_path:
                layer = "Infrastructure"
            
            self.architecture[layer].append(str_path)

            # --- 2. Pattern Recognition (Text Analysis) ---
            if file_path.suffix in ['.py', '.ts', '.tsx', '.js', '.md']:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    found_concepts = []
                    # Check regex patterns
                    for kb_id, config in TRACE_PATTERNS.items():
                        if re.search(config["pattern"], content):
                            found_concepts.append(config["concept"])
                            self.patterns_found.append({
                                "pattern": config["concept"],
                                "file": str_path,
                                "kb_ref": kb_id
                            })
                    
                    # Check for Markdown headers (Documentation Layer)
                    if file_path.suffix == '.md':
                        if "Universal Concept" in content:
                            found_concepts.append("FDE Knowledge Artifact")
                    
                    # --- 3. Module Catalog ---
                    self.modules.append({
                        "name": file_path.stem,
                        "path": str_path,
                        "concepts": found_concepts,
                        "layer": layer
                    })

        except Exception as e:
            logger.warning(f"Error analyzing {file_path}: {e}")

    def generate_xml_report(self, output_path: str):
        """Generates the <codebase_analysis> XML structure."""
        root = Element('codebase_analysis')
        
        # --- Architecture Overview ---
        arch_elem = SubElement(root, 'architecture_overview')
        for layer_name, files in self.architecture.items():
            layer_node = SubElement(arch_elem, 'layer', name=layer_name)
            layer_node.text = f"{len(files)} files"

        # --- Module Breakdown ---
        modules_elem = SubElement(root, 'module_breakdown')
        for mod in self.modules:
            if not mod['concepts']: continue # Skip empty
            mod_node = SubElement(modules_elem, 'module', name=mod['name'], path=mod['path'])
            desc = SubElement(mod_node, 'description')
            desc.text = f"Implements {', '.join(mod['concepts'])}"
            
            kb_map = SubElement(mod_node, 'kb_map')
            kb_map.text = "See TRACE Patterns"

        # --- Key Patterns ---
        patterns_elem = SubElement(root, 'key_patterns')
        unique_patterns = {} # Dedup by file+pattern
        for p in self.patterns_found:
            key = f"{p['file']}:{p['pattern']}"
            if key not in unique_patterns:
                unique_patterns[key] = p
                pat_node = SubElement(patterns_elem, 'pattern', name=p['pattern'])
                SubElement(pat_node, 'file').text = p['file']
                SubElement(pat_node, 'kb_ref').text = p['kb_ref']

        # --- Learning Exercises (Generated) ---
        exercises_elem = SubElement(root, 'learning_exercises')
        
        # Heuristic for exercises
        count = 0
        for p in self.patterns_found:
            if count >= 3: break
            if "Repository" in p['pattern'] or "Service" in p['pattern']:
                ex = SubElement(exercises_elem, 'exercise')
                SubElement(ex, 'goal').text = f"Implement {p['pattern']} from scratch"
                SubElement(ex, 'context').text = p['file']
                SubElement(ex, 'difficulty').text = "Medium"
                count += 1

        # Pretty print
        xml_str = minidom.parseString(tostring(root)).toprettyxml(indent="  ")
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(xml_str)
        
        logger.info(f"TRACE Analysis XML generated at {output_path}")

def main():
    parser = argparse.ArgumentParser(description="Palantir FDE TRACE Analysis Engine")
    parser.add_argument("--target", required=True, help="Root directory of the codebase")
    parser.add_argument("--mode", default="trace", help="Analysis mode")
    parser.add_argument("--output", default=".agent/learning/codebase_analysis.xml", help="Output path")
    
    args = parser.parse_args()
    
    engine = TraceAnalysisEngine(args.target)
    engine.scan_codebase()
    engine.generate_xml_report(args.output)

if __name__ == "__main__":
    main()
