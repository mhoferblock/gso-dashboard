#!/usr/bin/env python3
"""
Rebuild and re-embed dsrFacts into index.html.

Reads dsr_facts.json (full facts with oppOwner + channel), builds slim JSON,
and replaces the GSO_DATA.dsrFacts block in index.html.

Usage:
  python3 rebuild_embed.py
"""
import json, sys, os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

# ── Load full facts ──
if not os.path.exists("dsr_facts.json"):
    print("ERROR: dsr_facts.json not found. Pull from Airtable first.")
    sys.exit(1)

with open("dsr_facts.json") as f:
    facts = json.load(f)

print(f"Loaded {len(facts)} facts from dsr_facts.json")

# ── Build slim JSON ──
slim = []
for f in facts:
    r = {}
    r["i"] = f["id"]
    if f.get("rep"): r["r"] = f["rep"]
    if f.get("teamLead"): r["tl"] = f["teamLead"]
    if f.get("seller"): r["s"] = f["seller"]
    if f.get("workType"): r["w"] = f["workType"]
    if f.get("status"): r["st"] = f["status"]
    if f.get("subStatus"): r["ss"] = f["subStatus"]
    if f.get("requestReason"): r["rr"] = f["requestReason"]
    if f.get("country"): r["co"] = f["country"]
    # Use gpv (TOTAL_ANNUAL_GPV_C) which has better fill than gpvUsd (LIFETIME_GPV_C)
    gpv_val = f.get("gpv") or f.get("gpvUsd") or 0
    if gpv_val: r["g"] = gpv_val
    if f.get("createdDate"): r["cd"] = f["createdDate"]
    if f.get("completedDate"): r["cpd"] = f["completedDate"]
    if f.get("goLiveDate"): r["gl"] = f["goLiveDate"]
    if f.get("daysToComplete") is not None: r["dtc"] = f["daysToComplete"]
    if f.get("daysOpen") is not None: r["do"] = f["daysOpen"]
    if f.get("daysStale") is not None: r["ds"] = f["daysStale"]
    if f.get("oppOwner"): r["ao"] = f["oppOwner"]
    if f.get("oppOwnerRole"): r["ar"] = f["oppOwnerRole"]
    if f.get("channel"): r["ch"] = f["channel"]
    slim.append(r)

slim_json = json.dumps(slim, separators=(",", ":"))

with open("dsr_facts_slim.json", "w") as f:
    f.write(slim_json)

print(f"Built slim JSON: {len(slim_json)/1024/1024:.2f} MB ({len(slim)} records)")

# ── Validate ──
COMPLETED = {"Implementation Complete", "Completed", "Transitioned"}
CANCELLED = {"Rejected", "Lost - No Seller Contact", "Lost - Churn", "Lost"}

comp = sum(1 for r in slim if r.get("st", "") in COMPLETED)
canc = sum(1 for r in slim if r.get("st", "") in CANCELLED)
hold = sum(1 for r in slim if r.get("st", "") == "On Hold")
active = len(slim) - comp - canc - hold
with_ao = sum(1 for r in slim if "ao" in r)

# Channel breakdown
channels = {}
for r in slim:
    ch = r.get("ch", "other")
    channels[ch] = channels.get(ch, 0) + 1

print(f"\nValidation:")
print(f"  Total:     {len(slim):>6}")
print(f"  Completed: {comp:>6}")
print(f"  Active:    {active:>6}")
print(f"  On Hold:   {hold:>6}")
print(f"  Cancelled: {canc:>6}")
print(f"  Opp Owner: {with_ao:>6} ({with_ao/len(slim)*100:.1f}%)")
print(f"\n  Channels:")
for ch, cnt in sorted(channels.items()):
    print(f"    {ch}: {cnt}")

# ── Re-embed into dashboard.html ──
target_file = "dashboard.html"
with open(target_file) as f:
    html = f.read()

marker = "GSO_DATA.dsrFacts = "
start_idx = html.find(marker)
if start_idx == -1:
    print(f"\nERROR: Could not find GSO_DATA.dsrFacts in {target_file}")
    sys.exit(1)

# Find end of the array value (track brackets)
val_start = start_idx + len(marker)
bracket = 0
i = val_start
while i < len(html):
    if html[i] == '[': bracket += 1
    if html[i] == ']': bracket -= 1
    if bracket == 0 and html[i] == ']':
        end_idx = html.find(';', i)
        break
    i += 1

if end_idx == -1:
    print(f"\nERROR: Could not find end of dsrFacts in {target_file}")
    sys.exit(1)

html_new = html[:start_idx] + marker + slim_json + html[end_idx:]

with open(target_file, "w") as f:
    f.write(html_new)

print(f"\nEmbedded into {target_file}: {len(html_new)/1024/1024:.2f} MB")
print("Done! Ready to deploy.")
