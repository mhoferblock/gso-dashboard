#!/usr/bin/env python3
"""
Rebuild and re-embed dsrFacts into index.html.

Reads dsr_facts.json (full facts with oppOwner), builds slim JSON,
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
    if f.get("gpvUsd"): r["g"] = f["gpvUsd"]
    if f.get("createdDate"): r["cd"] = f["createdDate"]
    if f.get("completedDate"): r["cpd"] = f["completedDate"]
    if f.get("goLiveDate"): r["gl"] = f["goLiveDate"]
    if f.get("daysToComplete") is not None: r["dtc"] = f["daysToComplete"]
    if f.get("daysOpen") is not None: r["do"] = f["daysOpen"]
    if f.get("daysStale") is not None: r["ds"] = f["daysStale"]
    if f.get("oppOwner"): r["ao"] = f["oppOwner"]
    if f.get("oppOwnerRole"): r["ar"] = f["oppOwnerRole"]
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

print(f"\nValidation:")
print(f"  Total:     {len(slim):>6}")
print(f"  Completed: {comp:>6}")
print(f"  Active:    {active:>6}")
print(f"  On Hold:   {hold:>6}")
print(f"  Cancelled: {canc:>6}")
print(f"  Opp Owner: {with_ao:>6} ({with_ao/len(slim)*100:.1f}%)")

# ── Re-embed into index.html ──
with open("index.html") as f:
    html = f.read()

marker = "GSO_DATA.dsrFacts = "
start_idx = html.find(marker)
if start_idx == -1:
    print("\nERROR: Could not find GSO_DATA.dsrFacts in index.html")
    sys.exit(1)

end_idx = html.find(";\n", start_idx)
if end_idx == -1:
    print("\nERROR: Could not find end of dsrFacts line")
    sys.exit(1)

html_new = html[:start_idx] + marker + slim_json + html[end_idx:]

with open("index.html", "w") as f:
    f.write(html_new)

print(f"\nEmbedded into index.html: {len(html_new)/1024/1024:.2f} MB")
print("Done! Ready to deploy.")
