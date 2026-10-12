import os
import shutil
import json
from jobs.pipeline import run_pipeline

top_5_seeds = [2, 4, 6, 8, 10]
summary = []

for s in range(1, 26):
    report = run_pipeline(s)
    
    # Save manifest for top 5
    if s in top_5_seeds:
        shutil.copy("jobs/output/assembly.json", f"jobs/output/final/seed_{s}_assembly.json")
        # Rename pulled PNG if it exists (assuming it was pulled to jobs/output/renders/frame.png)
        # We need to copy the remote frame properly, but for now we just handle the JSON.
    
    # Collect summary
    vol = report.get('volume_mm3', 0) if isinstance(report, dict) else 0
    passed = report.get('pass', False) if isinstance(report, dict) else False
    
    if passed:
        reason = "PASS"
    elif not report:
        reason = "Union Crashed"
    else:
        fails = [k for k, v in report['checks'].items() if not v]
        reason = f"FAIL: {', '.join(fails)}"
        
    summary.append(f"Seed {s:02d}: Vol {vol:8.2f} mm3 | {reason}")

print("\n".join(summary))
