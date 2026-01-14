
import os
import shutil
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("LifecycleManager")

AGENTS_ROOT = "/home/palantir/.agent"
PLANS_DIR = os.path.join(AGENTS_ROOT, "plans")
ARCHIVE_ROOT = os.path.join(AGENTS_ROOT, "archives", "plans")

class LifecycleManager:
    """
    Manages the lifecycle of ephemeral artifacts (Plans, Logs).
    Enforces Entropy Reduction by archiving old artifacts.
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.cutoff_time = datetime.now() - timedelta(hours=retention_hours)

    def run_archival(self):
        """Main entry point for archival process."""
        logger.info(f"🧹 Starting Entropy Reduction (Retention: {self.retention_hours}h)...")
        
        if not os.path.exists(PLANS_DIR):
            logger.warning(f"Plan directory not found: {PLANS_DIR}")
            return

        files = [f for f in os.listdir(PLANS_DIR) if os.path.isfile(os.path.join(PLANS_DIR, f))]
        archived_count = 0

        for filename in files:
            file_path = os.path.join(PLANS_DIR, filename)
            
            # Skip the visualization file we just made if it's new, but generally check all
            if self._should_archive(file_path):
                self._archive_file(file_path)
                archived_count += 1

        logger.info(f"✨ Entropy Reduction Complete. Archived {archived_count} files.")

    def _should_archive(self, file_path: str) -> bool:
        """Determines if a file is old enough to be archived."""
        try:
            # 1. Try to read JSON metadata (Most accurate)
            if file_path.endswith(".json"):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    created_at_str = data.get("created_at")
                    if created_at_str:
                        # Handle various ISO formats if needed, assuming ISO 8601
                        created_at = datetime.fromisoformat(created_at_str)
                        return created_at < self.cutoff_time
            
            # 2. Fallback to File System MTime
            mtime_timestamp = os.path.getmtime(file_path)
            mtime = datetime.fromtimestamp(mtime_timestamp)
            return mtime < self.cutoff_time

        except Exception as e:
            logger.warning(f"Failed to check file {file_path}: {e}")
            return False

    def _archive_file(self, source_path: str):
        """Moves file to the appropriate archive directory."""
        try:
            mtime_timestamp = os.path.getmtime(source_path)
            dt = datetime.fromtimestamp(mtime_timestamp)
            
            # Structure: archives/plans/YYYY/MM/DD/
            target_dir = os.path.join(
                ARCHIVE_ROOT,
                f"{dt.year:04d}",
                f"{dt.month:02d}",
                f"{dt.day:02d}"
            )
            
            os.makedirs(target_dir, exist_ok=True)
            
            filename = os.path.basename(source_path)
            target_path = os.path.join(target_dir, filename)
            
            shutil.move(source_path, target_path)
            logger.info(f"📦 Archived: {filename} -> {target_path}")
            
        except Exception as e:
            logger.error(f"❌ Failed to archive {source_path}: {e}")

if __name__ == "__main__":
    # If run directly, run archival
    manager = LifecycleManager(retention_hours=24)
    manager.run_archival()
