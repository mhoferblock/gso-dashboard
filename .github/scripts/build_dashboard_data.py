#!/usr/bin/env python3
"""
Build processed_data.json from Airtable exports.

Reads:
  .github/data/_airtable_dsrs.json     (DSR Facts)
  .github/data/_airtable_roster.json   (Team Roster)
  .github/data/_airtable_goaling.json  (Goaling)

Writes:
  .github/data/processed_data.json     (embedded in index.html)
  .github/data/goaling_data.json       (embedded in index.html)
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import median

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(SCRIPT_DIR, '..', 'data')

# ============================================================
# FX RATES (USD conversion)
# ============================================================
FX_RATES = {
    'USD': 1.0, 'CAD': 0.72, 'AUD': 0.65, 'GBP': 1.27,
    'EUR': 1.09, 'JPY': 0.0067, 'NZD': 0.60, 'SEK': 0.097
}

# ============================================================
# STATUS CLASSIFICATION
# ============================================================
COMPLETED_STATUSES = {
    'Implementation Complete', 'Completed', 'Completed - Good Fit',
    'Completed - Unworkable', 'Completed - Bad Fit', 'Transitioned',
    'Tasks Complete'
}
CANCELLED_STATUSES = {
    'Rejected', 'Lost', 'Lost - No Seller Contact', 'Lost - Churn',
    'Seller No Show', 'No Action Required'
}

def classify(status, sub_status=None):
    if status in COMPLETED_STATUSES:
        return 'completed'
    if status in CANCELLED_STATUSES:
        return 'cancelled'
    if status == 'On Hold':
        return 'onHold'
    if sub_status and str(sub_status).startswith('On Hold'):
        return 'onHold'
    return 'active'


def safe_int(v, default=0):
    if v is None:
        return default
    try:
        return int(v)
    except (ValueError, TypeError):
        return default


def safe_float(v, default=0.0):
    if v is None:
        return default
    try:
        return float(v)
    except (ValueError, TypeError):
        return default


def gpv_usd(gpv_local, currency):
    rate = FX_RATES.get(currency, 1.0)
    return safe_float(gpv_local) * rate


# ============================================================
# LOAD DATA
# ============================================================
def load_json(filename):
    path = os.path.join(DATA_DIR, filename)
    with open(path) as f:
        return json.load(f)


def main():
    print("Loading Airtable exports...")
    dsrs = load_json('_airtable_dsrs.json')
    roster = load_json('_airtable_roster.json')
    goaling_raw = load_json('_airtable_goaling.json')

    print(f"  DSRs: {len(dsrs)}")
    print(f"  Roster: {len(roster)}")
    print(f"  Goaling: {len(goaling_raw)}")

    # ============================================================
    # BUILD TEAM MAP FROM ROSTER (source of truth)
    # ============================================================
    teams = defaultdict(list)
    rep_team = {}
    active_reps = set()

    for r in roster:
        name = r.get('Rep Name', '')
        lead = r.get('Team Lead', '')
        if name and lead:
            teams[lead].append(name)
            rep_team[name] = lead
            if r.get('Active'):
                active_reps.add(name)

    # Sort team members
    teams = {k: sorted(v) for k, v in sorted(teams.items())}
    print(f"  Teams: {len(teams)} ({sum(len(v) for v in teams.values())} reps)")

    # ============================================================
    # FILTER DSRs TO ACTIVE REPS (match current dashboard)
    # ============================================================
    # Only include DSRs owned by reps in the roster
    reps_with_data = set()
    filtered_dsrs = []
    for d in dsrs:
        rep = d.get('Rep', '')
        if rep in rep_team:
            filtered_dsrs.append(d)
            reps_with_data.add(rep)

    print(f"  Filtered DSRs: {len(filtered_dsrs)} (from {len(dsrs)} total)")
    print(f"  Reps with data: {len(reps_with_data)}")

    # ============================================================
    # REP SUMMARY
    # ============================================================
    rep_summary = {}
    for rep in reps_with_data:
        rep_dsrs = [d for d in filtered_dsrs if d.get('Rep') == rep]
        wt_counts = defaultdict(int)
        comp = act = oh = canc = 0
        total_gpv = 0.0

        for d in rep_dsrs:
            cls = classify(d.get('Status', ''), d.get('Sub Status'))
            if cls == 'completed': comp += 1
            elif cls == 'active': act += 1
            elif cls == 'onHold': oh += 1
            elif cls == 'cancelled': canc += 1

            wt = d.get('Work Type', 'Unknown')
            wt_counts[wt] += 1
            total_gpv += gpv_usd(d.get('GPV Annual'), d.get('Currency', 'USD'))

        rep_summary[rep] = {
            'completed': comp,
            'active': act,
            'onHold': oh,
            'cancelled': canc,
            'total': len(rep_dsrs),
            'gpv': round(total_gpv),
            'workTypes': dict(wt_counts)
        }

    # ============================================================
    # WORK TYPE SUMMARY
    # ============================================================
    wt_summary = defaultdict(lambda: {'completed': 0, 'active': 0, 'onHold': 0, 'cancelled': 0, 'total': 0})
    for d in filtered_dsrs:
        wt = d.get('Work Type', 'Unknown')
        cls = classify(d.get('Status', ''), d.get('Sub Status'))
        wt_summary[wt][cls] += 1
        wt_summary[wt]['total'] += 1
    wt_summary = dict(wt_summary)

    # ============================================================
    # TOTALS
    # ============================================================
    total_comp = sum(r['completed'] for r in rep_summary.values())
    total_act = sum(r['active'] for r in rep_summary.values())
    total_oh = sum(r['onHold'] for r in rep_summary.values())
    total_canc = sum(r['cancelled'] for r in rep_summary.values())
    total_dsrs = sum(r['total'] for r in rep_summary.values())
    total_gpv = sum(r['gpv'] for r in rep_summary.values())

    # Count 90-day completions
    cutoff_90d = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    completed_90d = []
    for d in filtered_dsrs:
        cls = classify(d.get('Status', ''), d.get('Sub Status'))
        comp_date = d.get('Completed Date') or d.get('Transitioned Date')
        if cls == 'completed' and comp_date and comp_date >= cutoff_90d:
            completed_90d.append(d)

    totals = {
        'dsrs': total_dsrs,
        'completed': total_comp,
        'active': total_act,
        'onHold': total_oh,
        'cancelled': total_canc,
        'gpv': total_gpv,
        'activePipelineCount': total_act + total_oh,
        'completedCount90d': len(completed_90d),
        'currency': 'USD'
    }

    print(f"\n  Totals: {json.dumps(totals, indent=2)}")

    # ============================================================
    # MONTHLY TREND (last 13 months)
    # ============================================================
    monthly = defaultdict(lambda: {'completed': 0, 'active': 0, 'cancelled': 0, 'onHold': 0})

    for d in filtered_dsrs:
        cls = classify(d.get('Status', ''), d.get('Sub Status'))
        created = d.get('Created Date', '')
        comp_date = d.get('Completed Date') or d.get('Transitioned Date')

        if created:
            month = created[:7]
            monthly[month][cls] += 1

        # Also count completions by completion month
        if cls == 'completed' and comp_date:
            comp_month = comp_date[:7]
            if comp_month != (created or '')[:7]:
                monthly[comp_month]['completed'] += 1

    # Keep last 13 months
    months_sorted = sorted(monthly.keys())
    recent_months = months_sorted[-13:] if len(months_sorted) > 13 else months_sorted
    monthly = {m: dict(monthly[m]) for m in recent_months}

    # ============================================================
    # ACTIVE PIPELINE (by stage)
    # ============================================================
    active_pipeline = defaultdict(list)
    for d in filtered_dsrs:
        cls = classify(d.get('Status', ''), d.get('Sub Status'))
        if cls in ('active', 'onHold'):
            stage = d.get('Status', 'Unknown')
            active_pipeline[stage].append({
                'rep': d.get('Rep', ''),
                'seller': d.get('Seller', ''),
                'workType': d.get('Work Type', ''),
                'gpv': gpv_usd(d.get('GPV Annual'), d.get('Currency', 'USD')),
                'currency': d.get('Currency', 'USD'),
                'created': d.get('Created Date', ''),
                'goLive': d.get('Go Live Date', ''),
                'daysOpen': safe_int(d.get('Days Open')),
                'daysStale': safe_int(d.get('Days Stale'))
            })
    active_pipeline = dict(active_pipeline)

    pipeline_count = sum(len(v) for v in active_pipeline.values())
    print(f"  Active pipeline: {pipeline_count} items across {len(active_pipeline)} stages")

    # ============================================================
    # COMPLETED SELLERS (last 90 days)
    # ============================================================
    completed_sellers = []
    for d in completed_90d:
        comp_date = d.get('Completed Date') or d.get('Transitioned Date') or ''
        gpv_local = safe_float(d.get('GPV Annual'))
        completed_sellers.append({
            'rep': d.get('Rep', ''),
            'seller': d.get('Seller', ''),
            'workType': d.get('Work Type', ''),
            'gpv': gpv_usd(d.get('GPV Annual'), d.get('Currency', 'USD')),
            'gpvLocal': gpv_local,
            'currency': d.get('Currency', 'USD'),
            'country': d.get('Country', ''),
            'completedDate': comp_date,
            'daysToComplete': safe_int(d.get('Days to Complete'))
        })
    completed_sellers.sort(key=lambda x: x['completedDate'], reverse=True)
    print(f"  Completed sellers (90d): {len(completed_sellers)}")

    # ============================================================
    # WEEKLY COMPLETIONS (last 14 weeks)
    # ============================================================
    weekly_raw = defaultdict(list)
    for d in filtered_dsrs:
        cls = classify(d.get('Status', ''), d.get('Sub Status'))
        comp_date = d.get('Completed Date') or d.get('Transitioned Date')
        if cls == 'completed' and comp_date:
            try:
                dt = datetime.strptime(comp_date, '%Y-%m-%d')
                monday = dt - timedelta(days=dt.weekday())
                week_key = monday.strftime('%Y-%m-%d')
                weekly_raw[week_key].append(safe_int(d.get('Days to Complete')))
            except ValueError:
                pass

    weeks_sorted = sorted(weekly_raw.keys())
    recent_weeks = weeks_sorted[-14:] if len(weeks_sorted) > 14 else weeks_sorted
    weekly_completions = {}
    for w in recent_weeks:
        days_list = [d for d in weekly_raw[w] if d >= 0]
        weekly_completions[w] = {
            'total': len(weekly_raw[w]),
            'medianDays': round(median(days_list)) if days_list else 0
        }

    # ============================================================
    # JOURNEY TIMING (milestone medians from completed DSRs)
    # ============================================================
    # We don't have per-milestone timestamps from Airtable (that would need the history table).
    # Preserve the existing journey timing from the current processed_data.json if it exists.
    existing_journey = {}
    existing_stage_duration = {}
    existing_path = os.path.join(DATA_DIR, 'processed_data.json')
    if os.path.exists(existing_path):
        with open(existing_path) as f:
            existing = json.load(f)
            existing_journey = existing.get('journeyTiming', {})
            existing_stage_duration = existing.get('stageDuration', {})
        print(f"  Preserved journey timing: {len(existing_journey)} milestones")
        print(f"  Preserved stage duration: {len(existing_stage_duration)} stages")

    # ============================================================
    # GOALING DATA
    # ============================================================
    # Build roster lookup for country/level
    roster_lookup = {}
    for r in roster:
        name = r.get('Rep Name', '')
        if name:
            roster_lookup[name] = r

    goaling = {}
    goaling_meta = None
    for g in goaling_raw:
        rep = g.get('Rep Name', '')
        if not rep:
            continue
        rl = roster_lookup.get(rep, {})
        level_str = rl.get('Level', g.get('Level', 'L2'))
        goaling[rep] = {
            'level': safe_int(str(level_str).replace('L', '')),
            'country': rl.get('Country', ''),
            'dsrGoal': safe_int(g.get('DSR Goal')),
            'dsrPacingGoal': safe_int(g.get('DSR Pacing Goal')),
            'dsrActual': safe_int(g.get('DSR Actual')),
            'dsrPacingPct': round(safe_float(g.get('DSR Pacing %')) * 100, 1),
            'dsrQuarterPct': round(safe_float(g.get('DSR Quarter %')) * 100, 1),
            'ptsGoal': safe_int(g.get('Points Goal')),
            'ptsPacingGoal': safe_int(g.get('Points Pacing Goal')),
            'ptsActual': safe_int(g.get('Points Actual')),
            'ptsPacingPct': round(safe_float(g.get('Points Pacing %')) * 100, 1),
            'ptsQuarterPct': round(safe_float(g.get('Points Quarter %')) * 100, 1),
            'daysGoal': safe_int(g.get('Days Goal')),
            'status': g.get('Status', 'Off Track')
        }
        if not goaling_meta:
            goaling_meta = {
                'quarter': g.get('Quarter', 'Q1 FY2026'),
                'daysElapsed': 86,  # Will be updated
                'daysInQuarter': 90,
                'updated': datetime.now().strftime('%Y-%m-%d')
            }

    # Calculate days elapsed in quarter
    if goaling_meta:
        q = goaling_meta['quarter']
        # Q1 FY2026 = Jan 1 - Mar 31, 2026
        # Q2 FY2026 = Apr 1 - Jun 30, 2026
        today = datetime.now()
        if 'Q1' in q:
            q_start = datetime(today.year, 1, 1)
            q_end = datetime(today.year, 3, 31)
        elif 'Q2' in q:
            q_start = datetime(today.year, 4, 1)
            q_end = datetime(today.year, 6, 30)
        elif 'Q3' in q:
            q_start = datetime(today.year, 7, 1)
            q_end = datetime(today.year, 9, 30)
        else:
            q_start = datetime(today.year, 10, 1)
            q_end = datetime(today.year, 12, 31)
        
        goaling_meta['daysElapsed'] = min((today - q_start).days, (q_end - q_start).days)
        goaling_meta['daysInQuarter'] = (q_end - q_start).days

    print(f"  Goaling: {len(goaling)} reps")

    # ============================================================
    # ASSEMBLE processed_data.json
    # ============================================================
    processed = {
        'teams': teams,
        'repSummary': rep_summary,
        'workTypeSummary': wt_summary,
        'monthly': monthly,
        'journeyTiming': existing_journey,
        'stageDuration': existing_stage_duration,
        'activePipeline': active_pipeline,
        'completedSellers': completed_sellers,
        'weeklyCompletions': weekly_completions,
        'totals': totals
    }

    # Write processed_data.json
    out_path = os.path.join(DATA_DIR, 'processed_data.json')
    with open(out_path, 'w') as f:
        json.dump(processed, f, separators=(',', ':'))
    print(f"\n  Written: processed_data.json ({os.path.getsize(out_path) / 1024:.0f} KB)")

    # Write goaling_data.json
    goaling_path = os.path.join(DATA_DIR, 'goaling_data.json')
    with open(goaling_path, 'w') as f:
        json.dump(goaling, f, separators=(',', ':'))
    print(f"  Written: goaling_data.json ({os.path.getsize(goaling_path) / 1024:.0f} KB)")

    # Write goaling meta separately
    meta_path = os.path.join(DATA_DIR, 'goaling_meta.json')
    with open(meta_path, 'w') as f:
        json.dump(goaling_meta, f, separators=(',', ':'))

    # ============================================================
    # VALIDATION
    # ============================================================
    print("\n=== VALIDATION ===")
    print(f"Total DSRs: {totals['dsrs']}")
    print(f"  Completed: {totals['completed']}")
    print(f"  Active: {totals['active']}")
    print(f"  On Hold: {totals['onHold']}")
    print(f"  Cancelled: {totals['cancelled']}")
    print(f"  Sum: {totals['completed'] + totals['active'] + totals['onHold'] + totals['cancelled']}")
    print(f"  Match: {totals['dsrs'] == totals['completed'] + totals['active'] + totals['onHold'] + totals['cancelled']}")
    print(f"GPV: ${totals['gpv']:,.0f}")
    print(f"Pipeline: {pipeline_count} items")
    print(f"Completed 90d: {len(completed_sellers)}")
    print(f"Reps in summary: {len(rep_summary)}")
    print(f"Work types: {len(wt_summary)}")

    return processed, goaling, goaling_meta


if __name__ == '__main__':
    main()
