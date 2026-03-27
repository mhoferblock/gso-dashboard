#!/usr/bin/env python3
"""
Delta Sync: Snowflake → Airtable

Pulls only DSRs modified since the last sync and upserts them into Airtable.
Run this to refresh the data, then run build_dashboard_data.py + embed_data.py.

Usage:
  python3 delta_sync.py              # sync since last sync date
  python3 delta_sync.py --days 7     # sync last 7 days
  python3 delta_sync.py --full       # full re-sync (all records)

Requires: goose session with Snowflake + Airtable access
  This script outputs commands for goose to execute.
"""

import json
import os
import sys
from datetime import datetime, timedelta

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')
SYNC_STATE_FILE = os.path.join(DATA_DIR, '_sync_state.json')

AIRTABLE_BASE = 'appsnfWWzptN9cwD0'
AIRTABLE_TABLE = 'DSR Facts'

# The 39 active reps (from Team Roster)
ACTIVE_REPS = None  # Loaded from roster at runtime

# FX rates
FX_RATES = {
    'USD': 1.0, 'CAD': 0.72, 'AUD': 0.65, 'GBP': 1.27,
    'EUR': 1.09, 'JPY': 0.0067, 'NZD': 0.60, 'SEK': 0.097
}


def load_roster():
    """Load active reps from roster file."""
    roster_path = os.path.join(DATA_DIR, '_airtable_roster.json')
    if not os.path.exists(roster_path):
        print("ERROR: _airtable_roster.json not found. Run the Airtable read step first.")
        sys.exit(1)
    with open(roster_path) as f:
        roster = json.load(f)
    return [r['Rep Name'] for r in roster if r.get('Rep Name')]


def get_last_sync_date():
    """Get the last sync date from state file."""
    if os.path.exists(SYNC_STATE_FILE):
        with open(SYNC_STATE_FILE) as f:
            state = json.load(f)
            return state.get('last_sync_date')
    return None


def save_sync_state(sync_date, records_added, records_updated):
    """Save sync state."""
    state = {
        'last_sync_date': sync_date,
        'last_sync_at': datetime.now().isoformat(),
        'records_added': records_added,
        'records_updated': records_updated
    }
    with open(SYNC_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)
    print(f"Sync state saved: {json.dumps(state, indent=2)}")


def build_snowflake_query(since_date, reps):
    """Build the Snowflake query for delta sync."""
    rep_list = "'" + "','".join(r.replace("'", "\\'") for r in reps) + "'"
    
    # Core fields query
    core_query = f"""
    SELECT 
      d.ID as SFDC_ID,
      u.NAME as REP,
      d.ACCOUNT_NAME_C as SELLER,
      d.PURCHASED_IMPLEMENTATION_SERVICES_C as WORK_TYPE,
      d.STATUS_C as STATUS,
      d.SUB_STATUS_C as SUB_STATUS,
      d.COUNTRY_CODE_C as COUNTRY,
      d.CURRENCY_ISO_CODE as CURRENCY,
      d.TOTAL_ANNUAL_GPV_C as GPV_LOCAL,
      d.ONSITE_C as IS_ONSITE,
      TO_CHAR(d.CREATED_DATE, 'YYYY-MM-DD') as CREATED_DATE,
      TO_CHAR(d.DATE_COMPLETED_C, 'YYYY-MM-DD') as COMPLETED_DATE,
      TO_CHAR(d.DATE_TRANSITIONED_C, 'YYYY-MM-DD') as TRANSITIONED_DATE,
      TO_CHAR(d.DESIRED_GO_LIVE_DATE_C, 'YYYY-MM-DD') as GO_LIVE,
      TO_CHAR(d.LAST_MODIFIED_DATE, 'YYYY-MM-DDTHH24:MI:SS') as LAST_MODIFIED
    FROM FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C d
    LEFT JOIN FIVETRAN.APP_SALES_SFDC.USER u ON d.OWNER_ID = u.ID
    WHERE d.IS_DELETED = FALSE AND d._FIVETRAN_DELETED = FALSE
      AND d.RECORD_TYPE_ID = '0124W0000011dFnQAI'
      AND d.DEAL_SUPPORT_TEAM_C = 'GSO Global Seller Onboarding'
      AND u.NAME IN ({rep_list})
    """
    
    if since_date:
        core_query += f"  AND d.LAST_MODIFIED_DATE >= '{since_date}'\n"
    
    core_query += "ORDER BY d.LAST_MODIFIED_DATE DESC"
    
    # Enrichment fields query
    enrich_query = f"""
    SELECT 
      d.ID as SFDC_ID,
      d.REQUEST_REASON_C as REQUEST_REASON,
      d.LANGUAGE_C as LANGUAGE,
      d.COMPLEXITY_SCORE_C as COMPLEXITY,
      d.NUMBER_OF_LOCATIONS_C as NUM_LOCATIONS,
      d.COMPETITOR_POS_C as COMPETITOR_POS,
      d.MERCHANT_TOKEN_C as MERCHANT_TOKEN,
      TO_CHAR(d.FIRST_TOUCH_C, 'YYYY-MM-DD') as FIRST_TOUCH,
      TO_CHAR(d.AE_DESIRED_GO_LIVE_C, 'YYYY-MM-DD') as AE_GO_LIVE,
      CASE 
        WHEN d.DATE_COMPLETED_C IS NOT NULL THEN DATEDIFF('day', d.CREATED_DATE, d.DATE_COMPLETED_C)
        WHEN d.DATE_TRANSITIONED_C IS NOT NULL THEN DATEDIFF('day', d.CREATED_DATE, d.DATE_TRANSITIONED_C)
        ELSE NULL
      END as DAYS_TO_COMPLETE,
      DATEDIFF('day', d.CREATED_DATE, CURRENT_DATE()) as DAYS_OPEN,
      DATEDIFF('day', d.LAST_MODIFIED_DATE, CURRENT_DATE()) as DAYS_STALE
    FROM FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C d
    LEFT JOIN FIVETRAN.APP_SALES_SFDC.USER u ON d.OWNER_ID = u.ID
    WHERE d.IS_DELETED = FALSE AND d._FIVETRAN_DELETED = FALSE
      AND d.RECORD_TYPE_ID = '0124W0000011dFnQAI'
      AND d.DEAL_SUPPORT_TEAM_C = 'GSO Global Seller Onboarding'
      AND u.NAME IN ({rep_list})
    """
    
    if since_date:
        enrich_query += f"  AND d.LAST_MODIFIED_DATE >= '{since_date}'\n"
    
    enrich_query += "ORDER BY d.ID"
    
    return core_query, enrich_query


def merge_records(core_rows, enrich_rows):
    """Merge core and enrichment data."""
    enrich_map = {r['SFDC_ID']: r for r in enrich_rows}
    
    merged = []
    for c in core_rows:
        e = enrich_map.get(c['SFDC_ID'], {})
        gpv_local = c.get('GPV_LOCAL') or 0
        rate = FX_RATES.get(c.get('CURRENCY', 'USD'), 1.0)
        
        merged.append({
            'SFDC_ID': c['SFDC_ID'],
            'REP': c['REP'],
            'SELLER': c['SELLER'],
            'WORK_TYPE': c['WORK_TYPE'],
            'STATUS': c['STATUS'],
            'SUB_STATUS': c.get('SUB_STATUS'),
            'REQUEST_REASON': e.get('REQUEST_REASON'),
            'COUNTRY': c.get('COUNTRY'),
            'LANGUAGE': e.get('LANGUAGE'),
            'CURRENCY': c.get('CURRENCY'),
            'GPV_LOCAL': gpv_local,
            'GPV_USD': round(gpv_local * rate),
            'COMPLEXITY': e.get('COMPLEXITY'),
            'NUM_LOCATIONS': e.get('NUM_LOCATIONS'),
            'COMPETITOR_POS': e.get('COMPETITOR_POS'),
            'MERCHANT_TOKEN': e.get('MERCHANT_TOKEN'),
            'CREATED_DATE': c.get('CREATED_DATE'),
            'FIRST_TOUCH': e.get('FIRST_TOUCH'),
            'GO_LIVE': c.get('GO_LIVE'),
            'AE_GO_LIVE': e.get('AE_GO_LIVE'),
            'COMPLETED_DATE': c.get('COMPLETED_DATE'),
            'TRANSITIONED_DATE': c.get('TRANSITIONED_DATE'),
            'LAST_MODIFIED': c.get('LAST_MODIFIED'),
            'DAYS_TO_COMPLETE': e.get('DAYS_TO_COMPLETE'),
            'DAYS_OPEN': e.get('DAYS_OPEN'),
            'DAYS_STALE': e.get('DAYS_STALE'),
            'IS_ONSITE': c.get('IS_ONSITE', False)
        })
    
    return merged


def to_airtable_fields(row):
    """Convert a merged row to Airtable fields format."""
    fields = {
        'SFDC ID': row['SFDC_ID'],
        'Rep': row['REP'],
        'Seller': row['SELLER'] or '',
        'Status': row['STATUS'] or '',
        'Country': row['COUNTRY'] or '',
        'Currency': row['CURRENCY'] or '',
    }
    
    if row.get('WORK_TYPE'): fields['Work Type'] = row['WORK_TYPE']
    if row.get('SUB_STATUS'): fields['Sub Status'] = row['SUB_STATUS']
    if row.get('REQUEST_REASON'): fields['Request Reason'] = row['REQUEST_REASON']
    if row.get('LANGUAGE'): fields['Language'] = row['LANGUAGE']
    if row.get('GPV_LOCAL'): fields['GPV Annual'] = row['GPV_LOCAL']
    if row.get('GPV_USD'): fields['GPV USD'] = row['GPV_USD']
    if row.get('COMPLEXITY') is not None: fields['Complexity Score'] = row['COMPLEXITY']
    if row.get('NUM_LOCATIONS'): fields['Num Locations'] = row['NUM_LOCATIONS']
    if row.get('COMPETITOR_POS'): fields['Competitor POS'] = row['COMPETITOR_POS']
    if row.get('MERCHANT_TOKEN'): fields['Merchant Token'] = row['MERCHANT_TOKEN']
    if row.get('CREATED_DATE'): fields['Created Date'] = row['CREATED_DATE']
    if row.get('FIRST_TOUCH'): fields['First Touch Date'] = row['FIRST_TOUCH']
    if row.get('GO_LIVE'): fields['Go Live Date'] = row['GO_LIVE']
    if row.get('AE_GO_LIVE'): fields['AE Desired Go Live'] = row['AE_GO_LIVE']
    if row.get('COMPLETED_DATE'): fields['Completed Date'] = row['COMPLETED_DATE']
    if row.get('TRANSITIONED_DATE'): fields['Transitioned Date'] = row['TRANSITIONED_DATE']
    if row.get('LAST_MODIFIED'): fields['Last Modified'] = row['LAST_MODIFIED']
    if row.get('DAYS_TO_COMPLETE') is not None: fields['Days to Complete'] = row['DAYS_TO_COMPLETE']
    if row.get('DAYS_OPEN') is not None: fields['Days Open'] = row['DAYS_OPEN']
    if row.get('DAYS_STALE') is not None: fields['Days Stale'] = row['DAYS_STALE']
    if row.get('IS_ONSITE'): fields['Is Onsite'] = True
    
    return fields


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Delta sync Snowflake → Airtable')
    parser.add_argument('--days', type=int, help='Sync records modified in last N days')
    parser.add_argument('--full', action='store_true', help='Full re-sync')
    parser.add_argument('--dry-run', action='store_true', help='Show queries without executing')
    args = parser.parse_args()

    reps = load_roster()
    print(f"Loaded {len(reps)} reps from roster")

    # Determine sync date
    if args.full:
        since_date = None
        print("Mode: FULL re-sync")
    elif args.days:
        since_date = (datetime.now() - timedelta(days=args.days)).strftime('%Y-%m-%dT00:00:00')
        print(f"Mode: Last {args.days} days (since {since_date})")
    else:
        since_date = get_last_sync_date()
        if since_date:
            print(f"Mode: Delta since last sync ({since_date})")
        else:
            # Default to last 7 days if no sync state
            since_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT00:00:00')
            print(f"Mode: No sync state found, defaulting to last 7 days ({since_date})")

    # Build queries
    core_query, enrich_query = build_snowflake_query(since_date, reps)
    
    if args.dry_run:
        print("\n=== CORE QUERY ===")
        print(core_query)
        print("\n=== ENRICHMENT QUERY ===")
        print(enrich_query)
        print("\nDry run complete. No data was fetched or written.")
        return

    # Save queries for goose to execute
    queries = {
        'core_query': core_query,
        'enrich_query': enrich_query,
        'since_date': since_date,
        'sync_start': datetime.now().isoformat()
    }
    
    queries_path = os.path.join(DATA_DIR, '_delta_queries.json')
    with open(queries_path, 'w') as f:
        json.dump(queries, f, indent=2)
    
    print(f"\nQueries saved to {queries_path}")
    print("Next: Execute these queries in Snowflake, then run delta_apply.py")


if __name__ == '__main__':
    main()
