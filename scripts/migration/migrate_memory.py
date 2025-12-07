
import os
import json
import shutil
import glob
from datetime import datetime
from typing import Dict, Any

from scripts.ontology.manager import ObjectManager
from scripts.ontology.schemas.memory import OrionInsight, OrionPattern, InsightProvenance, InsightContent, PatternStructure

MEMORY_ROOT = "/home/palantir/.agent/memory/semantic"
ARCHIVE_ROOT = os.path.join(MEMORY_ROOT, "archived")

def parse_iso(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))

def migrate_insight(data: Dict[str, Any]):
    return OrionInsight(
        id=data["id"],
        created_at=parse_iso(data["meta"]["created_at"]),
        updated_at=parse_iso(data["meta"]["updated_at"]),
        version=1, # Default to 1 or verify if exists?
        
        confidence_score=data["meta"].get("confidence_score", 1.0),
        decay_factor=data["meta"].get("decay_factor"),
        
        provenance=InsightProvenance(**data["provenance"]),
        content=InsightContent(**data["content"]),
        
        supports=data.get("relations", {}).get("supports", []),
        contradicts=data.get("relations", {}).get("contradicts", []),
        related_to=data.get("relations", {}).get("related_to", [])
    )

def migrate_pattern(data: Dict[str, Any]):
    return OrionPattern(
        id=data["id"],
        created_at=parse_iso(data["meta"]["created_at"]),
        updated_at=parse_iso(data["meta"]["updated_at"]),
        version=1,
        
        frequency_count=data["meta"].get("frequency_count", 0),
        success_rate=data["meta"].get("success_rate", 0.0),
        last_used=parse_iso(data["meta"]["last_used"]) if data["meta"].get("last_used") else None,
        
        structure=PatternStructure(**data["structure"]),
        code_snippet_ref=data.get("code_snippet_ref")
    )

def run_migration():
    print("=== STARTING MEMORY MIGRATION (Phase 4) ===")
    
    om = ObjectManager()
    om.register_type(OrionInsight)
    om.register_type(OrionPattern)
    
    # 1. Insights
    insight_files = glob.glob(os.path.join(MEMORY_ROOT, "insights", "**", "*.json"), recursive=True)
    print(f"[Info] Found {len(insight_files)} Insight files.")
    
    for fpath in insight_files:
        if "archived" in fpath: continue
        
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            
            obj = migrate_insight(data)
            om.save(obj)
            print(f"[Success] Migrated Insight: {obj.id}")
            
            # Archive
            # dest_dir = os.path.dirname(fpath).replace(MEMORY_ROOT, ARCHIVE_ROOT)
            # os.makedirs(dest_dir, exist_ok=True)
            # shutil.move(fpath, os.path.join(dest_dir, os.path.basename(fpath)))
            
        except Exception as e:
            print(f"[Error] Failed to migrate {fpath}: {e}")

    # 2. Patterns
    pattern_files = glob.glob(os.path.join(MEMORY_ROOT, "patterns", "**", "*.json"), recursive=True)
    print(f"[Info] Found {len(pattern_files)} Pattern files.")
    
    for fpath in pattern_files:
        if "archived" in fpath: continue
        
        try:
            with open(fpath, 'r') as f:
                data = json.load(f)
            
            obj = migrate_pattern(data)
            om.save(obj)
            print(f"[Success] Migrated Pattern: {obj.id}")
            
            # Archive
            # dest_dir = os.path.dirname(fpath).replace(MEMORY_ROOT, ARCHIVE_ROOT)
            # os.makedirs(dest_dir, exist_ok=True)
            # shutil.move(fpath, os.path.join(dest_dir, os.path.basename(fpath)))
            
        except Exception as e:
            print(f"[Error] Failed to migrate {fpath}: {e}")

    print("=== MIGRATION COMPLETED ===")

if __name__ == "__main__":
    run_migration()
