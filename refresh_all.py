#!/usr/bin/env python3
"""
GSO Dashboard — Full Data Refresh Script
=========================================
Rebuilds ALL embedded data in dashboard.html from source JSON files.

Usage:
  python3 refresh_all.py           # Normal mode — validates before embedding
  python3 refresh_all.py --force   # Skip validation thresholds (use with caution)

This script handles:
  1. Channel tagging (BPO, Vendor Ops) — MUST be applied before embedding
  2. Before/after metric comparison — refuses to embed if metrics shift too much
  3. Slim format conversion for DSR facts
  4. Embedding all data blocks into dashboard.html
  5. Dashboard validation (syntax, size, data blocks)

Data Sources (JSON files must exist in same directory):
  - dsr_facts.json      — DSR Facts from Airtable (~40K records)
  - dsa_records.json    — DSA Records from Snowflake (~6K records)
  - late_cancels.json   — Late cancel summary
  - late_cancel_records.json — Late cancel detail records
  - csat_data.json      — CSAT from GetFeedback (~170 responses)
  - vendor_spend.json   — Vendor Spend from Airtable
  - goaling.json        — Goaling from Airtable
"""

import json, sys, os, re, shutil
from datetime import datetime

DASHBOARD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dashboard.html")
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".backups")

# ══════════════════════════════════════════════════════════════
# BUSINESS LOGIC — Channel tagging and name mapping
# ══════════════════════════════════════════════════════════════

# BPO team members — reports to Jennifer Walker
BPO_TEAM = {
    'Yesenia Lineth Echeverria Ochaeta', 'Jackelline Rodriguez', 'Abner Avila',
    'Serghei Miheev', 'Luis Solares', 'Danna Villagran', 'Cristian Plugaru',
    'Pamela Gil', 'Diana Giron', 'Ginger Torres', 'Karen Najarro',
    'Maria Torres', 'Julissa Rosa', 'Scarlet Recinos', 'Luis Rosales',
    'Jose Xocoy', 'Angel Mauricio', 'Rosa Hernandez', 'Lucia Zarceno',
    'Edgar Cocinero', 'Yanelis Morales', 'Michael Rivera', 'Josue De La Roca',
    'Leonel Guerra', 'Walter Perez', 'Melissa Alvarez', 'Karen Melendez',
    'Susan Enriquez', 'Erwin Gonzalez', 'Claudia Piedrasanta', 'Mellisa Gregorio',
}

# Vendor Ops team — uses DSR data names (not display names)
VENDOR_OPS = {
    'Megan Martchink', 'Kyle Rominger', 'Jean- Arthur', 'Meri Fakraufon',
}

# Current GSO roster — used for validation only (dashboard has its own copy)
GSO_ROSTER = {
    # US East — Meaghan Biederman
    'Austin Crittenden', 'Meven Le Corre', 'Joe Pharaon', 'Moussa Kamakate',
    'Brandon Redmond', 'Livia Horn-Scarpulla', 'Andrea Guevara', 'Griffin Ulsh',
    'Miles McMillin', 'Josie Vogt', 'Lee Williamson', 'Paige Benik', 'Chelsea Falato',
    # US West — Ben Pomeroy
    'Michael Bavaro', 'Ashley McDonald', 'Olignne Diaz', 'Travis Castroman',
    'Ruben Reynoso', 'Kalani Cuaresma', 'John Tudhope', 'Jasmine Johnson',
    'Taylar Jones', 'Kat Gleason', 'Janayra Rivera Algarin', 'Paul Kim',
    # EMEA — Caleb Cunningham
    'Alexandre Garreau', 'Arantxa Abellan', 'Eugeniu Vascu', 'Francisco Alvarez',
    'Igor Rusu', 'Kerry Nelson', 'Lupe Buitrago Echeverria', 'Merve Oancea',
    'Oleg Gnatovski', 'Olga Kanna',
    # APAC — Kamilla Schou Warr
    'Takao Kinjo', 'Misho Arai', 'Mary Hirata McJilton', 'Ben Braun',
    'Macarena Castillo', 'Kristian Bojsen-Moller', 'Chandreyee Bose',
    'Josh stoffels', 'Jamahl G',
    # Leadership
    'Meaghan Biederman', 'Ben Pomeroy', 'Caleb Cunningham',
}

COMPLETED_STATUSES = {'Implementation Complete', 'Completed', 'Transitioned'}
CANCELLED_STATUSES = {'Rejected', 'Lost - No Seller Contact', 'Lost - Churn', 'Lost'}
DRAFT_STATUSES = {'Draft'}


def tag_channels(facts):
    """Apply channel tags to DSR facts based on rep name.
    
    Returns tagged facts and prints summary.
    CRITICAL: This must run before embedding. Without it, BPO and Vendor Ops
    records will be mixed into GSO metrics.
    """
    bpo_count = 0
    vo_count = 0
    other_count = 0
    
    for f in facts:
        rep = f.get('rep', '')
        if rep in BPO_TEAM:
            f['channel'] = 'bpo'
            bpo_count += 1
        elif rep in VENDOR_OPS:
            f['channel'] = 'vendorops'
            vo_count += 1
        else:
            f['channel'] = ''
            other_count += 1
    
    print(f"  Channel tagging: {bpo_count} BPO, {vo_count} Vendor Ops, {other_count} GSO/other")
    
    if bpo_count == 0:
        print("  ❌ WARNING: Zero BPO records tagged! Check BPO_TEAM list.")
    if vo_count == 0:
        print("  ❌ WARNING: Zero Vendor Ops records tagged! Check VENDOR_OPS list.")
    
    return facts


def compute_metrics(facts):
    """Compute key metrics from DSR facts for before/after comparison."""
    gso = [f for f in facts if f.get('channel', '') not in ('bpo', 'vendorops')]
    bpo = [f for f in facts if f.get('channel') == 'bpo']
    vo = [f for f in facts if f.get('channel') == 'vendorops']
    
    workable = [f for f in gso if f.get('status') not in DRAFT_STATUSES]
    
    # Current month
    now = datetime.now()
    month_prefix = now.strftime('%Y-%m')
    
    created_month = len([f for f in workable if (f.get('createdDate') or '').startswith(month_prefix)])
    comp_month = len([f for f in workable if f.get('status') in COMPLETED_STATUSES 
                      and (f.get('completedDate') or '').startswith(month_prefix)])
    
    # Active pipeline (roster only)
    active_statuses = [f for f in workable if f.get('status') not in COMPLETED_STATUSES 
                       and f.get('status') not in CANCELLED_STATUSES 
                       and f.get('status') not in DRAFT_STATUSES
                       and f.get('status') != 'On Hold'
                       and f.get('rep') in GSO_ROSTER]
    on_hold = [f for f in workable if f.get('status') == 'On Hold' and f.get('rep') in GSO_ROSTER]
    
    return {
        'total': len(facts),
        'gso': len(gso),
        'bpo': len(bpo),
        'vo': len(vo),
        'drafts': len([f for f in gso if f.get('status') in DRAFT_STATUSES]),
        'workable': len(workable),
        'created_month': created_month,
        'completed_month': comp_month,
        'active_roster': len(active_statuses),
        'on_hold_roster': len(on_hold),
        'pipeline': len(active_statuses) + len(on_hold),
    }


def extract_current_metrics(content):
    """Extract key metrics from the currently embedded dashboard data."""
    # Find and parse the embedded dsrFacts
    marker = 'GSO_DATA.dsrFacts = '
    idx = content.find(marker)
    if idx == -1:
        return None
    
    val_start = idx + len(marker)
    # Find the end — it's a single line ending with ;
    line_end = content.find('\n', val_start)
    if line_end == -1:
        return None
    
    json_str = content[val_start:line_end].rstrip().rstrip(';')
    
    try:
        slim_facts = json.loads(json_str)
    except json.JSONDecodeError:
        print("  ⚠️ Could not parse current dsrFacts for comparison")
        return None
    
    # Expand slim to full format for metric computation
    facts = []
    for sf in slim_facts:
        facts.append({
            'id': sf.get('i', ''),
            'rep': sf.get('r', ''),
            'status': sf.get('st', ''),
            'channel': sf.get('ch', ''),
            'createdDate': sf.get('cd', ''),
            'completedDate': sf.get('cpd', ''),
            'country': sf.get('co', ''),
        })
    
    return compute_metrics(facts)


def compare_metrics(old, new, force=False):
    """Compare before/after metrics and flag anomalies.
    
    Returns (ok, warnings) tuple. If ok is False, embedding should be aborted.
    """
    if old is None:
        return True, ["⚠️ No previous metrics to compare (first embed or parse failed)"]
    
    warnings = []
    errors = []
    
    def check(name, old_val, new_val, max_pct_change=25, min_val=0):
        if old_val == 0:
            if new_val > 0:
                warnings.append(f"  {name}: 0 → {new_val} (new data)")
            return
        pct = abs(new_val - old_val) / old_val * 100
        direction = "↑" if new_val > old_val else "↓"
        if pct > max_pct_change:
            msg = f"  {name}: {old_val:,} → {new_val:,} ({direction}{pct:.0f}%) — exceeds {max_pct_change}% threshold"
            errors.append(msg)
        elif pct > 10:
            warnings.append(f"  {name}: {old_val:,} → {new_val:,} ({direction}{pct:.0f}%)")
        if new_val < min_val:
            errors.append(f"  {name}: {new_val} is below minimum {min_val}")
    
    check("Total records", old['total'], new['total'], max_pct_change=10)
    check("BPO records", old['bpo'], new['bpo'], max_pct_change=25, min_val=100)
    check("Vendor Ops records", old['vo'], new['vo'], max_pct_change=25, min_val=10)
    check("GSO records", old['gso'], new['gso'], max_pct_change=15)
    check("Created this month", old['created_month'], new['created_month'], max_pct_change=50)
    check("Completed this month", old['completed_month'], new['completed_month'], max_pct_change=50)
    check("Pipeline (roster)", old['pipeline'], new['pipeline'], max_pct_change=30)
    
    # Zero checks
    if new['bpo'] == 0:
        errors.append("  BPO records = 0 — channel tagging likely failed!")
    if new['vo'] == 0:
        errors.append("  Vendor Ops records = 0 — channel tagging likely failed!")
    if new['created_month'] == 0:
        warnings.append("  Created this month = 0 — is this expected?")
    
    if warnings:
        print("\n⚠️ WARNINGS:")
        for w in warnings:
            print(w)
    
    if errors:
        print("\n❌ METRIC SHIFTS EXCEED THRESHOLDS:")
        for e in errors:
            print(e)
        if force:
            print("\n⚠️ --force flag set, proceeding anyway...")
            return True, warnings + errors
        else:
            print("\n❌ Aborting embed. Use --force to override.")
            return False, warnings + errors
    
    return True, warnings


# ══════════════════════════════════════════════════════════════
# EMBED FUNCTIONS
# ══════════════════════════════════════════════════════════════

def backup_dashboard():
    """Create a timestamped backup before modifying."""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"dashboard_{ts}.html")
    shutil.copy2(DASHBOARD, backup_path)
    print(f"✅ Backup: {backup_path}")
    # Keep only last 10 backups
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith("dashboard_")])
    for old in backups[:-10]:
        os.remove(os.path.join(BACKUP_DIR, old))
    return backup_path


def read_dashboard():
    with open(DASHBOARD, "r") as f:
        return f.read()


def write_dashboard(content):
    with open(DASHBOARD, "w") as f:
        f.write(content)


def replace_data_block(content, var_name, new_value_json):
    """Replace GSO_DATA.varName = ...; with new value."""
    marker = f"GSO_DATA.{var_name} = "
    idx = content.find(marker)
    if idx == -1:
        print(f"  ⚠️ Could not find {marker} — skipping")
        return content
    
    val_start = idx + len(marker)
    line_end = content.find('\n', val_start)
    if line_end == -1:
        line_end = len(content)
    
    line_content = content[val_start:line_end]
    
    if line_content.rstrip().endswith(';'):
        semi = content.rfind(';', val_start, line_end + 1)
        return content[:idx] + marker + new_value_json + content[semi:]
    
    if content[val_start] in '[{':
        bracket = 0
        i = val_start
        while i < len(content):
            if content[i] in '[{': bracket += 1
            if content[i] in ']}': bracket -= 1
            if bracket == 0:
                end = content.find(';', i)
                if end == -1:
                    return content
                return content[:idx] + marker + new_value_json + content[end:]
            i += 1
    else:
        end = content.find(';', val_start)
        if end == -1:
            return content
        return content[:idx] + marker + new_value_json + content[end:]
    
    return content


def embed_dsr_facts(content, facts_json_path):
    """Tag channels, validate, and embed DSR facts."""
    if not os.path.exists(facts_json_path):
        print(f"  ⚠️ {facts_json_path} not found")
        return content, None
    
    with open(facts_json_path) as f:
        facts = json.load(f)
    
    print(f"  Loaded {len(facts)} DSR facts")
    
    # CRITICAL: Apply channel tagging
    facts = tag_channels(facts)
    
    # Save tagged version back (so it's available for debugging)
    with open(facts_json_path, 'w') as f:
        json.dump(facts, f, separators=(',', ':'))
    
    # Compute new metrics
    new_metrics = compute_metrics(facts)
    
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
    
    slim_path = facts_json_path.replace(".json", "_slim.json")
    with open(slim_path, "w") as f:
        f.write(slim_json)
    
    content = replace_data_block(content, "dsrFacts", slim_json)
    print(f"  ✅ Embedded {len(slim)} DSR facts ({len(slim_json)/1024/1024:.1f} MB)")
    return content, new_metrics


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
    """Validate the dashboard isn't broken."""
    errors = []
    
    opens = len(re.findall(r'<script', content))
    closes = len(re.findall(r'</script>', content))
    if opens != closes:
        errors.append(f"Script tag mismatch: {opens} open, {closes} close")
    
    for pattern in ['as any', ': [string,', ': any)']:
        if pattern in content:
            idx = content.index(pattern)
            line = content[:idx].count('\n') + 1
            errors.append(f"TypeScript syntax '{pattern}' at line {line}")
    
    for var in ['dsrFacts', 'dsaRecords', 'csatResponses', 'lateCancels', 'goaling']:
        if f'GSO_DATA.{var}' not in content:
            errors.append(f"Missing GSO_DATA.{var}")
    
    size_mb = len(content) / 1024 / 1024
    if size_mb < 5:
        errors.append(f"File too small ({size_mb:.1f} MB) — data may be missing")
    if size_mb > 25:
        errors.append(f"File too large ({size_mb:.1f} MB) — possible data corruption")
    
    return errors


def update_refresh_date(content):
    """Update the 'Last refreshed' date in the footer."""
    today = datetime.now().strftime("%b %d, %Y")
    pattern = r'(Last refreshed:?\s*</?\w*>?\s*)([\w\s,]+)(<)'
    match = re.search(pattern, content)
    if match:
        content = content[:match.start(2)] + today + content[match.end(2):]
        print(f"  ✅ Updated refresh date to {today}")
    return content


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════
if __name__ == "__main__":
    force = '--force' in sys.argv
    
    print("=" * 60)
    print("GSO Dashboard — Embed Data" + (" [FORCE MODE]" if force else ""))
    print("=" * 60)
    
    # Backup
    backup_path = backup_dashboard()
    
    # Read current dashboard
    content = read_dashboard()
    original_size = len(content)
    
    # Extract current metrics for comparison
    print("\n📊 Extracting current metrics from dashboard...")
    old_metrics = extract_current_metrics(content)
    if old_metrics:
        print(f"  Current: {old_metrics['total']:,} total, {old_metrics['bpo']:,} BPO, "
              f"{old_metrics['vo']:,} VO, {old_metrics['pipeline']:,} pipeline")
    
    # Embed each data source
    data_dir = os.path.dirname(DASHBOARD)
    new_metrics = None
    
    print("\n📦 Embedding data...")
    
    # DSR Facts (with channel tagging + validation)
    dsr_path = os.path.join(data_dir, "dsr_facts.json")
    if os.path.exists(dsr_path):
        content, new_metrics = embed_dsr_facts(content, dsr_path)
    else:
        print("  ⏭ dsr_facts.json not found — skipping DSR Facts")
    
    # Before/after comparison
    if new_metrics:
        print(f"\n📊 New metrics: {new_metrics['total']:,} total, {new_metrics['bpo']:,} BPO, "
              f"{new_metrics['vo']:,} VO, {new_metrics['pipeline']:,} pipeline, "
              f"{new_metrics['drafts']:,} drafts excluded")
        
        ok, warnings = compare_metrics(old_metrics, new_metrics, force=force)
        if not ok:
            print(f"\n❌ Embed aborted. Restoring from backup...")
            shutil.copy2(backup_path, DASHBOARD)
            sys.exit(1)
    
    # DSA Records
    dsa_path = os.path.join(data_dir, "dsa_records.json")
    if os.path.exists(dsa_path):
        content = embed_json_file(content, "dsaRecords", dsa_path)
    
    # BPO Activities (Deal Support Activities with Record Type = BPO Activity)
    bpo_act_path = os.path.join(data_dir, "bpo_activities.json")
    if os.path.exists(bpo_act_path):
        content = embed_json_file(content, "bpoActivities", bpo_act_path)
    
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
    
    # Merge goal overrides (from Settings page exports)
    overrides_path = os.path.join(data_dir, "goal_overrides.json")
    if os.path.exists(overrides_path):
        try:
            with open(overrides_path) as f:
                overrides = json.load(f)
            if overrides and isinstance(overrides, dict):
                # Find the goaling data block using bracket matching (handles no-semicolon case)
                marker = 'GSO_DATA.goaling = '
                marker_idx = content.find(marker)
                if marker_idx != -1:
                    val_start = marker_idx + len(marker)
                    # Bracket-match to find end of JSON object
                    depth = 0
                    val_end = val_start
                    for ci in range(val_start, min(val_start + 200000, len(content))):
                        if content[ci] == '{': depth += 1
                        elif content[ci] == '}': depth -= 1
                        if depth == 0:
                            val_end = ci + 1
                            break
                    goaling_json = content[val_start:val_end]
                    goaling_data = json.loads(goaling_json)
                    
                    merge_count = 0
                    for rep, changes in overrides.items():
                        if rep in goaling_data and isinstance(changes, dict):
                            for field, val in changes.items():
                                if field in ('ptsGoal', 'dsrGoal', 'daysGoal', 'level'):
                                    goaling_data[rep][field] = val
                                    merge_count += 1
                    if merge_count > 0:
                        # Recalculate pacing for overridden reps
                        meta_match = re.search(r'GSO_DATA\.goalingMeta = (\{[^}]+\});', content)
                        meta = json.loads(meta_match.group(1)) if meta_match else {}
                        days_elapsed = meta.get('daysElapsed', 85)
                        days_in_quarter = meta.get('daysInQuarter', 89)
                        pacing_factor = days_elapsed / days_in_quarter if days_in_quarter > 0 else 1
                        for rep in overrides:
                            if rep in goaling_data:
                                g = goaling_data[rep]
                                g['ptsPacingGoal'] = round(g['ptsGoal'] * pacing_factor)
                                g['dsrPacingGoal'] = round(g['dsrGoal'] * pacing_factor)
                                g['ptsPacingPct'] = round(g['ptsActual'] / g['ptsPacingGoal'] * 1000) / 10 if g['ptsPacingGoal'] > 0 else 0
                                g['dsrPacingPct'] = round(g['dsrActual'] / g['dsrPacingGoal'] * 1000) / 10 if g['dsrPacingGoal'] > 0 else 0
                                g['ptsQuarterPct'] = round(g['ptsActual'] / g['ptsGoal'] * 1000) / 10 if g['ptsGoal'] > 0 else 0
                                g['dsrQuarterPct'] = round(g['dsrActual'] / g['dsrGoal'] * 1000) / 10 if g['dsrGoal'] > 0 else 0
                                if g['ptsPacingPct'] >= 95: g['status'] = 'On Track'
                                elif g['ptsPacingPct'] >= 80: g['status'] = 'At Risk'
                                else: g['status'] = 'Off Track'
                        # Re-embed using replace_data_block (handles semicolon/no-semicolon)
                        new_goaling = json.dumps(goaling_data, separators=(',', ':'))
                        content = replace_data_block(content, "goaling", new_goaling)
                        print(f"  ✅ Merged {len(overrides)} goal override(s) ({merge_count} field changes) from goal_overrides.json")
                    else:
                        print(f"  ⚠️ goal_overrides.json found but no matching reps to merge")
                else:
                    print(f"  ⚠️ Could not find goaling data block to merge overrides into")
        except Exception as e:
            print(f"  ⚠️ Failed to merge goal overrides: {e}")
    
    # Update refresh date
    content = update_refresh_date(content)
    
    # Final validation
    print("\n" + "=" * 60)
    print("Validation")
    print("=" * 60)
    errors = validate_dashboard(content)
    if errors:
        print("❌ ERRORS FOUND:")
        for e in errors:
            print(f"  ❌ {e}")
        print(f"\n⚠️ Dashboard NOT updated. Restoring from backup...")
        shutil.copy2(backup_path, DASHBOARD)
        sys.exit(1)
    else:
        print("✅ All validation checks passed")
    
    # Write
    write_dashboard(content)
    new_size = len(content)
    print(f"\n✅ Dashboard updated: {original_size/1024/1024:.1f} MB → {new_size/1024/1024:.1f} MB")
    print(f"   Backup at: {backup_path}")
    print("\nNext steps:")
    print("  1. Upload to Blockcell")
    print("  2. Git commit and push")
