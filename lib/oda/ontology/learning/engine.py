"""
Orion Phase 5 - Adaptive Tutoring Engine Core
Orchestrates metric collection, dependency analysis, and TCS calculation.
Implements the 'Mathematics of Teaching Complexity' formula.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import math

from .types import TeachingComplexityScore, MetricType, CodeMetric
from .metrics import analyze_file
from .graph import DependencyGraph

# Configuration Constants
IGNORE_DIRS = {
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".git",
    ".idea",
    ".venv",
    ".agent",
    "build",
    "dist",
    "node_modules",
    "vendor",
    "coverage",
    "tests",
}
INTERESTING_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".mjs",
    ".cjs",
    ".mts",
    ".cts",
    ".go",
}

# Phase 5.1 Pattern Weights
PATTERN_WEIGHTS = {
    "repository_pattern": 5.0,
    "proposal_workflows": 4.0, # Heuristic detection required 
    "action_type": 3.0,
    "pydantic_model": 2.0,
    "ontology_object": 3.0, # Higher than plain model
    "enum_definition": 1.0, # Low weight
    "async_function": 2.0,   # Async adds load
    # Frontend / TS / JS
    "react_component": 4.0,
    "react_hook": 3.0,
    "blueprint_ui": 3.0,
    "osdk_client": 4.0,
    "graphql": 3.0,
    "websocket": 3.0,
    "worker_thread": 3.0,
    # Go / backend
    "goroutine": 2.0,
    "channel": 3.0,
    "http_server": 2.0,
    "grpc": 4.0,
}

class TutoringEngine:
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        self.metrics: Dict[str, CodeMetric] = {} # path -> metric
        self.scores: Dict[str, TeachingComplexityScore] = {} # path -> score
        self.dependency_graph = DependencyGraph(str(self.root))
        
    def scan_codebase(self) -> None:
        """Walks the codebase and parses all interesting files."""
        files_to_process = []
        
        for root, dirs, files in os.walk(self.root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for f in files:
                if Path(f).suffix.lower() in INTERESTING_EXTENSIONS:
                    full_path = Path(root) / f
                    rel_path = str(full_path.relative_to(self.root))
                    
                    try:
                        with open(full_path, "r", encoding="utf-8") as file:
                            content = file.read()
                        
                        # 1. Calculate Raw Metrics
                        metric = analyze_file(rel_path, content)
                        self.metrics[rel_path] = metric
                        files_to_process.append(rel_path)
                        
                    except Exception as e:
                        # Skip files that can't be read/parsed
                        print(f"Skipping {rel_path}: {e}")
                        continue
        
        # 2. Build Dependency Graph
        self.dependency_graph.build(files_to_process)
        
    def calculate_scores(self) -> None:
        """Computes TCS for all scanned files."""
        depths = self.dependency_graph.calculate_depths()
        
        max_depth = max(depths.values()) if depths else 1
        
        for rel_path, metric in self.metrics.items():
            # 1. Cognitive Complexity Component
            # Normalized: assume 50 is very high complexity. Cap at 1.0 logic?
            # Or use relative distribution. Spec implys a specific weight.
            # Let's use a sigmoid-like or linear scaling vs a reference baseline.
            # Here satisfying: 0.3 * (CC / 20) * 100? No, let's keep it simple score-points.
            # Phase 5 Formula says: 0.30 x Cognitive_Complexity_normalized
            # Assuming normalized refers to a 0-100 scale where 100 is "Too Hard".
            # Let's map CC=15 to 100.
            cc_norm = min(metric.control_flow_count * 5.0, 100.0)
            
            # 2. Dependency Depth Component
            # Ratio of max depth.
            depth = depths.get(rel_path, 0)
            dd_ratio = (depth / max(max_depth, 1)) * 100.0
            
            # 3. Novel Concept Density
            # Concepts per 100 LOC.
            total_concepts = metric.classes + metric.functions + metric.pydantic_models + metric.async_patterns
            density = (total_concepts / max(metric.loc, 1)) * 100.0
            # Scale density: 10% density is high (score 100).
            nc_norm = min(density * 10.0, 100.0)
            
            # 4. Domain Pattern Weight
            # Sum of identified patterns
            pattern_sum = sum(PATTERN_WEIGHTS.get(p, 0) for p in metric.identified_patterns)
            # Heuristic: "proposal" in path implies proposal workflow
            if "proposal" in rel_path.lower():
                pattern_sum += PATTERN_WEIGHTS["proposal_workflows"]
            
            # Scale: Score 20 = 100 (Expert heavy)
            dp_norm = min(pattern_sum * 5.0, 100.0)
            
            # 5. Halstead
            # Placeholder for now
            hd_norm = 0.0
            
            # Composite Calculation
            total = (
                0.30 * cc_norm +
                0.25 * dd_ratio +
                0.20 * nc_norm +
                0.15 * dp_norm +
                0.10 * hd_norm
            )
            
            self.scores[rel_path] = TeachingComplexityScore(
                total_score=total,
                cognitive_component=cc_norm,
                dependency_component=dd_ratio,
                novelty_component=nc_norm,
                pattern_component=dp_norm,
                halstead_component=hd_norm
            )

    def get_report(self) -> List[dict]:
        """Returns sorted list of file scores."""
        report = []
        for path, score in self.scores.items():
            report.append({
                "file": path,
                "tcs": round(score.total_score, 1),
                "breakdown": str(score),
                "metrics": self.metrics[path].model_dump(exclude={"imports"})
            })
        
        # Sort by TCS (easiest to hardest)
        return sorted(report, key=lambda x: x["tcs"])
