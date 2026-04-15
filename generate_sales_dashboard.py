#!/usr/bin/env python3
"""
GSO Sales Dashboard — Data Embed Script
========================================
Copies relevant data blocks from dashboard.html into sales_dashboard.html.

Only embeds GSO-channel data (excludes BPO and Vendor Ops).
The sales dashboard JS also filters these out, but pre-filtering keeps the file smaller.

Usage:
  python3 generate_sales_dashboard.py
"""

import json, re, os, sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_DASHBOARD = os.path.join(SCRIPT_DIR, "dashboard.html")
SALES_DASHBOARD = os.path.join(SCRIPT_DIR, "sales_dashboard.html")


def extract_data_block(content, var_name):
    """Extract a GSO_DATA block from dashboard.html content.
    
    Uses a string-aware bracket matcher that skips brackets inside
    JSON string literals (which can contain [ ] { } characters).
    """
    marker = f"GSO_DATA.{var_name} = "
    idx = content.find(marker)
    if idx == -1:
        return None
    
    val_start = idx + len(marker)
    
    # Check if it starts with [ or {
    if content[val_start] in '[{':
        bracket = 0
        in_string = False
        escape = False
        i = val_start
        while i < len(content):
            c = content[i]
            if escape:
                escape = False
            elif c == '\\' and in_string:
                escape = True
            elif c == '"' and not escape:
                in_string = not in_string
            elif not in_string:
                if c in '[{': bracket += 1
                if c in ']}': bracket -= 1
                if bracket == 0:
                    return content[val_start:i+1]
            i += 1
    else:
        # Simple value — find next ;
        line_end = content.find('\n', val_start)
        val = content[val_start:line_end].rstrip().rstrip(';')
        return val
    
    return None


def replace_data_block(content, var_name, new_value):
    """Replace a GSO_DATA block in the sales dashboard."""
    marker = f"GSO_DATA.{var_name} = "
    idx = content.find(marker)
    if idx == -1:
        print(f"  ⚠️ {var_name} not found in sales dashboard")
        return content
    
    val_start = idx + len(marker)
    line_end = content.find('\n', val_start)
    
    # Find the end of the current value (up to ;)
    line = content[val_start:line_end]
    if line.rstrip().endswith(';'):
        semi = content.rfind(';', val_start, line_end + 1)
        return content[:idx] + marker + new_value + content[semi:]
    
    # Bracket match
    if content[val_start] in '[{':
        bracket = 0
        i = val_start
        while i < len(content):
            if content[i] in '[{': bracket += 1
            if content[i] in ']}': bracket -= 1
            if bracket == 0:
                block_end = i + 1
                next_nl = content.find('\n', block_end)
                remaining = content[block_end:next_nl]
                semi_offset = remaining.find(';')
                if semi_offset != -1:
                    end = block_end + semi_offset
                    return content[:idx] + marker + new_value + content[end:]
                else:
                    return content[:idx] + marker + new_value + ";" + content[block_end:]
            i += 1
    
    return content[:idx] + marker + new_value + ";" + content[line_end:]


def main():
    print("=" * 60)
    print("GSO Sales Dashboard — Embed Data")
    print("=" * 60)
    
    if not os.path.exists(MAIN_DASHBOARD):
        print(f"❌ Main dashboard not found: {MAIN_DASHBOARD}")
        sys.exit(1)
    
    if not os.path.exists(SALES_DASHBOARD):
        print(f"❌ Sales dashboard not found: {SALES_DASHBOARD}")
        sys.exit(1)
    
    # Read both files
    with open(MAIN_DASHBOARD) as f:
        main_content = f.read()
    with open(SALES_DASHBOARD) as f:
        sales_content = f.read()
    
    # Extract DSR facts and filter to GSO channel only
    print("\n📦 Extracting data from main dashboard...")
    
    dsr_json = extract_data_block(main_content, "dsrFacts")
    if dsr_json:
        facts = json.loads(dsr_json)
        # Filter to GSO channel only (exclude BPO and Vendor Ops)
        gso_facts = [f for f in facts if f.get('ch', '') not in ('bpo', 'vendorops')]
        gso_json = json.dumps(gso_facts, separators=(',', ':'))
        sales_content = replace_data_block(sales_content, "dsrFacts", gso_json)
        print(f"  ✅ dsrFacts: {len(facts)} total → {len(gso_facts)} GSO-only ({len(gso_json)/1024/1024:.1f} MB)")
    
    # CSAT responses (all are GSO)
    csat_json = extract_data_block(main_content, "csatResponses")
    if csat_json:
        csat = json.loads(csat_json)
        sales_content = replace_data_block(sales_content, "csatResponses", csat_json)
        print(f"  ✅ csatResponses: {len(csat)} responses")
    
    # Strat PM monthly
    strat_json = extract_data_block(main_content, "stratPmMonthly")
    if strat_json:
        sales_content = replace_data_block(sales_content, "stratPmMonthly", strat_json)
        print(f"  ✅ stratPmMonthly")
    
    # Draft monthly
    draft_json = extract_data_block(main_content, "draftMonthly")
    if draft_json:
        sales_content = replace_data_block(sales_content, "draftMonthly", draft_json)
        print(f"  ✅ draftMonthly")
    
    # Update refresh date
    today = datetime.now().strftime("%b %d, %Y")
    sales_content = re.sub(
        r'Data refreshed: [^|<]+',
        f'Data refreshed: {today} ',
        sales_content
    )
    print(f"  ✅ Updated refresh date to {today}")
    
    # Write
    with open(SALES_DASHBOARD) as f:
        old_size = len(f.read())
    with open(SALES_DASHBOARD, 'w') as f:
        f.write(sales_content)
    new_size = len(sales_content)
    
    print(f"\n✅ Sales dashboard updated: {new_size/1024/1024:.1f} MB")
    print(f"   File: {SALES_DASHBOARD}")
    print(f"\nNext: Deploy to Blockcell as 'gso-sales-dashboard'")


if __name__ == "__main__":
    main()
