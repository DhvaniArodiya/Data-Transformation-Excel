import glob
import os
import json

files = sorted(glob.glob("jobs/*.json"), key=os.path.getmtime)
for fpath in files[-3:]:
    print(f"\n--- File: {fpath} ---")
    with open(fpath, 'r') as f:
        job = json.load(f)
        print(f"Status: {job.get('status')}")
        plan = job.get("transformation_plan")
        if plan:
            print("Plan Transformations:")
            for t in plan.get("transformations", []):
                print(f" - [{t.get('function')}] Output: {t.get('output_col')} Inputs: {t.get('input_cols') or t.get('input_col')}")
        else:
            print("No plan.")
