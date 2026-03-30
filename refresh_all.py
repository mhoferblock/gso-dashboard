#!/usr/bin/env python3
"""
GSO Dashboard — Full Data Refresh Script
=========================================
Rebuilds ALL embedded data in dashboard.html from source systems.

Usage (run via goose session):
  1. goose runs this script's steps using its Snowflake + Airtable extensions
  2. Or: python3 refresh_all.py  (for the embed step only, after data is pulled)

Data Sources:
  1. DSR Facts     — Snowflake → Airtable → embed (~40K records, ~11MB)
  2. DSA Records   — Snowflake direct (~6K records, ~800KB)
  3. DSA Summaries — Computed from DSA records
  4. Late Cancels  — Snowflake direct (~400 records, ~58KB)
  5. CSAT          — GetFeedback API (~170 responses, ~29KB)
  6. Vendor Spend  — Airtable Vendor Spend table (~926 invoices)
  7. Goaling       — Airtable Goaling table

Static data (not refreshed automatically):
  - dispatchPartners (partner config — manual)
  - dsaStatusMap (status normalization — static)
  - stratPmMonthly (from Looker — manual)
  - goalingMeta (quarter config — manual)

Architecture:
  dashboard.html is the single-file SPA. All data is embedded as GSO_DATA.xxx = {...};
  This script replaces each data block in-place using marker-based replacement.
"""

import json, sys, os, re, shutil
from datetime import datetime, timedelta

DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backups")

def backup_dashboard():
    """Create a timestamped backup before modifying."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"dashboard_{ts}.html")
    shutil.copy2(DASHBOARD, backup_path)
    print(f"✅ Backup: {backup_path}")
    # Keep only last 5 backups
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("dashboard_")])
    for old in backups[:-5]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return backup_path

def read_dashboard():
    with open(DASHBOARD, "r") as f:
        return f.read()

def write_dashboard(content):
    with open(DASHBOARD, "w") as f:
        f.write(content)

def replace_data_block(content, var_name, new_value_json):
    """Replace GSO_DATA.varName = ...; with new value.
    
    All data blocks are single-line: GSO_DATA.xxx = VALUE;\n
    For large blocks (dsrFacts ~11MB), we find the line end directly.
    For multi-line blocks (dispatchPartners), we track brackets.
    """
    marker = f"GSO_DATA.{var_name} = "
    idx = content.find(marker)
    if idx == -1:
        print(f"  ⚠️ Could not find {marker} — skipping")
        return content
    
    val_start = idx + len(marker)
    
    # Fast path: find the end of the line (works for single-line values)
    line_end = content.find('\n', val_start)
    if line_end == -1:
        line_end = len(content)
    
    line_content = content[val_start:line_end]
    
    # Check if the line ends with a semicolon (single-line value)
    if line_content.rstrip().endswith(';'):
        # Single-line — find the semicolon
        semi = content.rfind(';', val_start, line_end + 1)
        new_content = content[:idx] + marker + new_value_json + content[semi:]
        return new_content
    
    # Multi-line value — track brackets
    if content[val_start] in '[{':
        bracket = 0
        i = val_start
        while i < len(content):
            if content[i] in '[{': bracket += 1
            if content[i] in ']}': bracket -= 1
            if bracket == 0:
                end = content.find(';', i)
                if end == -1:
                    print(f"  ⚠️ Could not find semicolon after {var_name}")
                    return content
                new_content = content[:idx] + marker + new_value_json + content[end:]
                return new_content
            i += 1
    else:
        # Simple value (number, string) — find next semicolon
        end = content.find(';', val_start)
        if end == -1:
            return content
        new_content = content[:idx] + marker + new_value_json + content[end:]
        return new_content
    
    return content

def embed_dsr_facts(content, facts_json_path):
    """Embed DSR facts from a JSON file."""
    if not os.path.exists(facts_json_path):
        print(f"  ⚠️ {facts_json_path} not found")
        return content
    
    with open(facts_json_path) as f:
        facts = json.load(f)
    
    print(f"  Loaded {len(facts)} DSR facts")
    
    # Build slim format
    slim = []
    for f_rec in facts:
        r = {}
        r["i"] = f_rec.get("id", "")
        if f_rec.get("rep"): r["r"] = f_rec["rep"]
        if f_rec.get("teamLead"): r["tl"] = f_rec["teamLead"]
        if f_rec.get("seller"): r["s"] = f_rec["seller"]
        if f_rec.get("workType"): r["w"] = f_rec["workType"]
        if f_rec.get("status"): r["st"] = f_rec["status"]
        if f_rec.get("subStatus"): r["ss"] = f_rec["subStatus"]
        if f_rec.get("requestReason"): r["rr"] = f_rec["requestReason"]
        if f_rec.get("country"): r["co"] = f_rec["country"]
        gpv = f_rec.get("gpv") or f_rec.get("gpvUsd") or 0
        if gpv: r["g"] = gpv
        if f_rec.get("createdDate"): r["cd"] = f_rec["createdDate"]
        if f_rec.get("completedDate"): r["cpd"] = f_rec["completedDate"]
        if f_rec.get("goLiveDate"): r["gl"] = f_rec["goLiveDate"]
        if f_rec.get("daysToComplete") is not None: r["dtc"] = f_rec["daysToComplete"]
        if f_rec.get("daysOpen") is not None: r["do"] = f_rec["daysOpen"]
        if f_rec.get("daysStale") is not None: r["ds"] = f_rec["daysStale"]
        if f_rec.get("oppOwner"): r["ao"] = f_rec["oppOwner"]
        if f_rec.get("oppOwnerRole"): r["ar"] = f_rec["oppOwnerRole"]
        if f_rec.get("channel"): r["ch"] = f_rec["channel"]
        slim.append(r)
    
    slim_json = json.dumps(slim, separators=(",", ":"))
    
    # Save slim file too
    slim_path = facts_json_path.replace(".json", "_slim.json")
    with open(slim_path, "w") as f:
        f.write(slim_json)
    
    content = replace_data_block(content, "dsrFacts", slim_json)
    print(f"  ✅ Embedded {len(slim)} DSR facts ({len(slim_json)/1024/1024:.1f} MB)")
    return content

def embed_json_file(content, var_name, json_path):
    """Embed a JSON file as a data block."""
    if not os.path.exists(json_path):
        print(f"  ⚠️ {json_path} not found")
        return content
    
    with open(json_path) as f:
        data = f.read().strip()
    
    content = replace_data_block(content, var_name, data)
    print(f"  ✅ Embedded {var_name} ({len(data)/1024:.1f} KB)")
    return content

def validate_dashboard(content):
    """Basic validation that the dashboard isn't broken."""
    errors = []
    
    # Check script tag balance
    opens = len(re.findall(r'<script', content))
    closes = len(re.findall(r'</script>', content))
    if opens != closes:
        errors.append(f"Script tag mismatch: {opens} open, {closes} close")
    
    # Check for TypeScript syntax that breaks browsers
    for pattern in ['as any', ': [string,', ': any)']:
        if pattern in content:
            idx = content.index(pattern)
            line = content[:idx].count('\n') + 1
            errors.append(f"TypeScript syntax '{pattern}' at line {line}")
    
    # Check key data blocks exist
    for var in ['dsrFacts', 'dsaRecords', 'csatResponses', 'lateCancels', 'goaling']:
        if f'GSO_DATA.{var}' not in content:
            errors.append(f"Missing GSO_DATA.{var}")
    
    # Check file size is reasonable (should be 10-15MB)
    size_mb = len(content) / 1024 / 1024
    if size_mb < 5:
        errors.append(f"File too small ({size_mb:.1f} MB) — data may be missing")
    if size_mb > 25:
        errors.append(f"File too large ({size_mb:.1f} MB) — possible data corruption")
    
    return errors

def update_refresh_date(content):
    """Update the 'Last refreshed' date in the footer."""
    today = datetime.now().strftime("%b %d, %Y")
    # Look for the refresh date pattern
    pattern = r'(Last refreshed:?\s*</?\w*>?\s*)([\w\s,]+)(<)'
    match = re.search(pattern, content)
    if match:
        content = content[:match.start(2)] + today + content[match.end(2):]
        print(f"  ✅ Updated refresh date to {today}")
    return content

# ══════════════════════════════════════════════════════════════
# MAIN — Embed step (run after data has been pulled by goose)
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("GSO Dashboard — Embed Data")
    print("=" * 60)
    
    # Backup
    backup_path = backup_dashboard()
    
    # Read current dashboard
    content = read_dashboard()
    original_size = len(content)
    
    # Embed each data source if the file exists
    data_dir = os.path.dirname(DASHBOARD)
    
    # DSR Facts
    dsr_path = os.path.join(data_dir, "dsr_facts.json")
    if os.path.exists(dsr_path):
        content = embed_dsr_facts(content, dsr_path)
    else:
        print("  ⏭ dsr_facts.json not found — skipping DSR Facts")
    
    # DSA Records
    dsa_path = os.path.join(data_dir, "dsa_records.json")
    if os.path.exists(dsa_path):
        content = embed_json_file(content, "dsaRecords", dsa_path)
    
    # CSAT
    csat_path = os.path.join(data_dir, "csat_data.json")
    if os.path.exists(csat_path):
        content = embed_json_file(content, "csatResponses", csat_path)
    
    # Late Cancels
    lc_path = os.path.join(data_dir, "late_cancels.json")
    if os.path.exists(lc_path):
        content = embed_json_file(content, "lateCancels", lc_path)
    
    lc_detail_path = os.path.join(data_dir, "late_cancel_records.json")
    if os.path.exists(lc_detail_path):
        content = embed_json_file(content, "lateCancelRecords", lc_detail_path)
    
    # Vendor Spend
    spend_path = os.path.join(data_dir, "vendor_spend.json")
    if os.path.exists(spend_path):
        with open(spend_path) as f:
            spend = json.load(f)
        for key in ["spendByPartner", "spendInvoicesByPartner", "spendMonthly", 
                     "spendByCurrency", "spendTotal", "spendInvoiceCount", "spendMonthlyByPartner"]:
            if key in spend:
                val = json.dumps(spend[key], separators=(",", ":"))
                content = replace_data_block(content, key, val)
                print(f"  ✅ Embedded {key}")
    
    # Goaling
    goaling_path = os.path.join(data_dir, "goaling.json")
    if os.path.exists(goaling_path):
        content = embed_json_file(content, "goaling", goaling_path)
    
    # Update refresh date
    content = update_refresh_date(content)
    
    # Validate
    print("\n" + "=" * 60)
    print("Validation")
    print("=" * 60)
    errors = validate_dashboard(content)
    if errors:
        print("❌ ERRORS FOUND:")
        for e in errors:
            print(f"  ❌ {e}")
        print(f"\n⚠️ Dashboard NOT updated. Backup at: {backup_path}")
        sys.exit(1)
    else:
        print("✅ All validation checks passed")
    
    # Write
    write_dashboard(content)
    new_size = len(content)
    print(f"\n✅ Dashboard updated: {original_size/1024/1024:.1f} MB → {new_size/1024/1024:.1f} MB")
    print(f"   Backup at: {backup_path}")
    print("\nNext steps:")
    print("  1. Upload to Blockcell: blockcell upload gso-dashboard .")
    print("  2. Git commit and push")
