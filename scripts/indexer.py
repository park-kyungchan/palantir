#!/usr/bin/env python3
import os
import re
import json
import glob
import argparse
from collections import defaultdict

WORKSPACE_ROOT = os.path.abspath("/home/palantir")

class CodeIndexer:
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.dependency_graph = defaultdict(set) # file -> {dependencies}
        self.reverse_graph = defaultdict(set)    # file -> {dependents}
        self.file_map = {} # filename -> full_path (for resolution)

    def scan_workspace(self):
        """Scan all relevant files and build the graph."""
        extensions = ['**/*.py', '**/*.ts', '**/*.js', '**/*.json', '**/*.md']
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.root_dir, ext), recursive=True))
        
        # 1. Index Files
        for f in files:
            if "node_modules" in f or ".git" in f or "__pycache__" in f:
                continue
            rel_path = os.path.relpath(f, self.root_dir)
            self.file_map[os.path.basename(f)] = rel_path
            
        # 2. Parse Dependencies
        for f in files:
            if "node_modules" in f or ".git" in f or "__pycache__" in f:
                continue
            self._parse_file(f)

    def _parse_file(self, file_path):
        rel_path = os.path.relpath(file_path, self.root_dir)
        ext = os.path.splitext(file_path)[1]
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            deps = set()
            if ext == '.py':
                # import X, from X import Y
                deps.update(re.findall(r'^\s*import\s+(\w+)', content, re.MULTILINE))
                deps.update(re.findall(r'^\s*from\s+(\.?\w+)', content, re.MULTILINE))
            elif ext in ['.ts', '.js']:
                # import ... from 'X', require('X')
                deps.update(re.findall(r'from\s+[\'"](.+?)[\'"]', content))
                deps.update(re.findall(r'require\s*\(\s*[\'"](.+?)[\'"]\s*\)', content))
            elif ext == '.json':
                # Naive: look for strings that match known filenames
                # This is useful for config files referencing other files
                pass 

            # Resolve Dependencies
            for dep in deps:
                resolved = self._resolve_path(file_path, dep)
                if resolved:
                    self.dependency_graph[rel_path].add(resolved)
                    self.reverse_graph[resolved].add(rel_path)
                    
        except Exception as e:
            # print(f"⚠️ Error parsing {rel_path}: {e}")
            pass

    def _resolve_path(self, current_file, import_str):
        """Resolve import string to a file path."""
        # 1. Relative Import
        if import_str.startswith('.'):
            base_dir = os.path.dirname(current_file)
            # Try extensions
            candidates = [
                os.path.join(base_dir, import_str),
                os.path.join(base_dir, import_str + '.py'),
                os.path.join(base_dir, import_str + '.ts'),
                os.path.join(base_dir, import_str + '.js'),
                os.path.join(base_dir, import_str, 'index.ts'),
            ]
            for c in candidates:
                if os.path.exists(c):
                    return os.path.relpath(c, self.root_dir)
        
        # 2. Absolute/Module Import (Naive)
        # Check if it matches any known filename
        # (This is a heuristic for this environment)
        for filename, rel_path in self.file_map.items():
            if import_str in filename: # Loose matching
                 # Avoid self-reference
                if rel_path != os.path.relpath(current_file, self.root_dir):
                    return rel_path
                    
        return None

    def get_impact(self, target_file):
        """Get all files that depend on the target file (recursive)."""
        target_rel = os.path.relpath(target_file, self.root_dir) if os.path.isabs(target_file) else target_file
        
        impacted = set()
        queue = [target_rel]
        visited = set()
        
        while queue:
            current = queue.pop(0)
            if current in visited:
                continue
            visited.add(current)
            
            dependents = self.reverse_graph.get(current, set())
            for dep in dependents:
                if dep not in visited:
                    impacted.add(dep)
                    queue.append(dep)
                    
        return list(impacted)

def main():
    parser = argparse.ArgumentParser(description="Orion Impact Engine")
    parser.add_argument("command", choices=["impact", "graph"], help="Command to run")
    parser.add_argument("target", nargs="?", help="Target file for impact analysis")
    
    args = parser.parse_args()
    
    indexer = CodeIndexer(WORKSPACE_ROOT)
    indexer.scan_workspace()
    
    if args.command == "impact":
        if not args.target:
            print("❌ Target file required for impact analysis.")
            return
            
        impacted = indexer.get_impact(args.target)
        print(f"🔍 Impact Analysis for: {args.target}")
        if impacted:
            print(f"⚠️  {len(impacted)} files will be affected:")
            for f in impacted:
                print(f"   - {f}")
        else:
            print("✅ No direct dependencies found (Safe to edit?).")
            
    elif args.command == "graph":
        print(json.dumps({k: list(v) for k, v in indexer.reverse_graph.items()}, indent=2))

if __name__ == "__main__":
    main()
