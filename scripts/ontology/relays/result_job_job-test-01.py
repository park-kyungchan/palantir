#!/usr/bin/env python3
import sys
import shutil
import subprocess

# Ensure project root is in path
sys.path.append("/home/palantir/orion-orchestrator-v2")

from scripts.ontology.schemas.result import JobResult
from scripts.ontology.manager import ObjectManager


def main() -> None:
    checked_path = "/home/palantir"

    try:
        df_output = subprocess.check_output(["df", "-h"], text=True)
    except Exception as e:
        df_output = f"df -h failed: {e}"

    total, used, free = shutil.disk_usage(checked_path)
    free_gb = free / (1024**3)

    status = "SUCCESS" if free_gb > 10 else "FAILURE"

    result = JobResult(
        job_id="job-test-01",
        status=status,
        output_artifacts=[],
        metrics={
            "checked_path": checked_path,
            "free_bytes": free,
            "free_gb": round(free_gb, 2),
            "df_h": df_output,
        },
    )

    manager = ObjectManager()
    manager.save(result)
    print(f"✅ Job {result.job_id} Result Committed ({result.status}).")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Verification Failed: {e}")
        sys.exit(1)
