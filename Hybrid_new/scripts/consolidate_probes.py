"""Consolidate all probes into main file."""

import json
from pathlib import Path

DATA_DIR = Path(r"L:\PROGETTI\Hybrid\Hybrid\data")

# Read all probe result files
all_probes = []
files = [
    "probe_result.json",
    "single_probe_result.json",
    "followup_results.json",
    "new_probe_results.json",
    "simple_probe_results.json",
    "targeted_probe_results.json",
    "optimal_probe_results.json",
]

for fname in files:
    fpath = DATA_DIR / fname
    if fpath.exists():
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    item["source_file"] = fname
                all_probes.extend(data)
            elif isinstance(data, dict):
                data["source_file"] = fname
                all_probes.append(data)

print(f"Loaded {len(all_probes)} probes from individual files")

# Read main file
main_path = DATA_DIR / "all_probes_and_replies.json"
with open(main_path, "r", encoding="utf-8") as f:
    main_data = json.load(f)

existing_probes = main_data["probes_and_replies"]
print(f"Existing probes in main file: {len(existing_probes)}")

# Deduplicate by tweet_id or probe text
existing_ids = set()
for p in existing_probes:
    if "tweet_id" in p:
        existing_ids.add(p["tweet_id"])
    elif "probe" in p:
        existing_ids.add(p["probe"])

new_probes = []
for p in all_probes:
    pid = p.get("tweet_id") or p.get("probe", "")
    if pid not in existing_ids:
        new_probes.append(p)
        existing_ids.add(pid)

print(f"New unique probes to add: {len(new_probes)}")

# Add new probes to main file
for i, p in enumerate(new_probes, len(existing_probes) + 1):
    main_data["probes_and_replies"].append({
        "batch": "consolidated",
        "probe_id": i,
        "probe": p.get("probe") or p.get("probe_text", ""),
        "tweet_id": p.get("tweet_id") or p.get("probe_id", ""),
        "reply": p.get("reply") or p.get("reply_text"),
        "reply_id": p.get("reply_id"),
        "analysis": f"From {p.get('source_file', 'unknown')}",
        "source_file": p.get("source_file", "unknown"),
    })

# Update counts
main_data["total_probes"] = len(main_data["probes_and_replies"])
main_data["total_replies"] = len([p for p in main_data["probes_and_replies"] if p.get("reply")])

# Save updated file
with open(main_path, "w", encoding="utf-8") as f:
    json.dump(main_data, f, indent=2, ensure_ascii=False)

print(f"\nUpdated main file:")
print(f"  Total probes: {main_data['total_probes']}")
print(f"  Total replies: {main_data['total_replies']}")
print(f"  Saved to: {main_path}")
