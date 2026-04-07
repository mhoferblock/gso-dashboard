#!/usr/bin/env python3
"""
Generate the GSO Rep Dashboard — a stripped-down view of the main dashboard
focused on what individual reps and team leads need day-to-day.

Reads data from the same JSON files as the main dashboard refresh pipeline.
Produces a single self-contained HTML file (rep_dashboard.html).

Usage:
    python3 generate_rep_dashboard.py
"""

import json, os, re
from datetime import datetime

OUTFILE = 'rep_dashboard.html'

def load_json(filename):
    """Load a JSON file, return empty list/dict if not found."""
    if os.path.exists(filename):
        with open(filename) as f:
            return json.load(f)
    return []

def extract_teams_from_dashboard():
    """Extract team lead -> reps mapping from dashboard.html."""
    with open('dashboard.html') as f:
        html = f.read()
    idx = html.index('"Kamilla')
    search_start = max(0, idx - 2000)
    segment = html[search_start:idx]
    brace_pos = segment.rfind('{')
    obj_start = search_start + brace_pos
    depth = 0
    for i in range(obj_start, len(html)):
        if html[i] == '{': depth += 1
        elif html[i] == '}':
            depth -= 1
            if depth == 0:
                return json.loads(html[obj_start:i+1])
    return {}

def extract_exchange_rates():
    """Extract exchange rates from dashboard.html."""
    with open('dashboard.html') as f:
        html = f.read()
    m = re.search(r'GSO_DATA\.exchangeRates\s*=\s*(\{[^}]+\})', html)
    if m:
        return json.loads(m.group(1))
    return {}

def main():
    print("📊 Building GSO Rep Dashboard...")
    
    # Load all data
    teams = extract_teams_from_dashboard()
    exchange_rates = extract_exchange_rates()
    dsr_facts = load_json('dsr_facts.json')
    dsa_records = load_json('dsa_records.json')
    bpo_activities = load_json('bpo_activities.json')
    csat_data = load_json('csat_data.json')
    
    print(f"   Teams: {len(teams)} leads")
    print(f"   DSR Facts: {len(dsr_facts):,}")
    print(f"   DSA Records: {len(dsa_records):,}")
    print(f"   BPO Activities: {len(bpo_activities):,}")
    print(f"   CSAT Responses: {len(csat_data):,}")
    print(f"   Exchange Rates: {len(exchange_rates)} currencies")
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Serialize data
    teams_json = json.dumps(teams, separators=(',', ':'))
    rates_json = json.dumps(exchange_rates, separators=(',', ':'))
    dsr_json = json.dumps(dsr_facts, separators=(',', ':'))
    dsa_json = json.dumps(dsa_records, separators=(',', ':'))
    bpo_json = json.dumps(bpo_activities, separators=(',', ':'))
    csat_json = json.dumps(csat_data, separators=(',', ':'))
    
    total_data = len(dsr_json) + len(dsa_json) + len(bpo_json) + len(csat_json)
    print(f"   Total embedded data: {total_data/1024/1024:.1f} MB")
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GSO Rep Dashboard</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:'Inter',-apple-system,sans-serif;background:#f8fafc;color:#1e293b;line-height:1.5;}}

/* Header */
.header{{background:linear-gradient(135deg,#1e1b4b,#312e81);color:#fff;padding:16px 24px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;position:sticky;top:0;z-index:100;}}
.header-title{{font-size:1.1rem;font-weight:800;letter-spacing:-0.5px;}}
.header-sub{{font-size:0.7rem;color:#a5b4fc;}}
.header-controls{{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}}
.header-controls select,.header-controls input{{font-size:0.75rem;padding:6px 10px;border:1px solid rgba(255,255,255,0.2);border-radius:6px;background:rgba(255,255,255,0.1);color:#fff;}}
.header-controls select option{{color:#1e293b;background:#fff;}}
.header-controls input::placeholder{{color:rgba(255,255,255,0.5);}}

/* Main content */
.main{{max-width:1400px;margin:0 auto;padding:16px;}}

/* Tabs */
.tab-bar{{display:flex;gap:4px;margin-bottom:16px;border-bottom:2px solid #e2e8f0;padding-bottom:0;}}
.tab-btn{{padding:8px 16px;font-size:0.8rem;font-weight:600;color:#64748b;background:none;border:none;cursor:pointer;border-bottom:2px solid transparent;margin-bottom:-2px;transition:all 0.15s;}}
.tab-btn:hover{{color:#4f46e5;}}
.tab-btn.active{{color:#4f46e5;border-bottom-color:#4f46e5;}}
.tab-content{{display:none;}}
.tab-content.active{{display:block;}}

/* Cards */
.card{{background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:16px;margin-bottom:16px;}}
.card-title{{font-size:0.9rem;font-weight:700;color:#1e293b;margin-bottom:8px;}}
.card-subtitle{{font-size:0.7rem;color:#64748b;margin-bottom:12px;}}

/* KPI row */
.kpi-row{{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px;}}
.kpi{{text-align:center;padding:12px 16px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;min-width:100px;flex:1;}}
.kpi-val{{font-size:1.4rem;font-weight:800;color:#0f172a;}}
.kpi-val.green{{color:#16a34a;}}
.kpi-val.yellow{{color:#ca8a04;}}
.kpi-val.red{{color:#dc2626;}}
.kpi-val.blue{{color:#2563eb;}}
.kpi-label{{font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.3px;}}

/* Readiness */
.r-gauge{{width:100%;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden;display:flex;margin:8px 0;}}
.r-gauge-seg{{height:100%;}}

/* Alerts */
.alert-list{{display:flex;flex-direction:column;gap:6px;max-height:400px;overflow-y:auto;}}
.alert-card{{display:flex;align-items:center;gap:12px;padding:10px 14px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;cursor:pointer;transition:all 0.15s;border-left:4px solid #e2e8f0;}}
.alert-card:hover{{box-shadow:0 2px 8px rgba(0,0,0,0.06);transform:translateX(2px);}}
.alert-card-red{{border-left-color:#ef4444;}}
.alert-card-yellow{{border-left-color:#eab308;}}
.alert-seller{{font-size:0.8rem;font-weight:700;color:#0f172a;}}
.alert-meta{{font-size:0.7rem;color:#64748b;}}
.alert-score{{font-size:0.75rem;font-weight:700;padding:2px 8px;border-radius:5px;white-space:nowrap;}}
.alert-score-red{{background:#fee2e2;color:#dc2626;}}
.alert-score-yellow{{background:#fef3c7;color:#ca8a04;}}

/* Tracker */
.tracker-controls{{display:flex;gap:8px;align-items:center;margin-bottom:12px;flex-wrap:wrap;}}
.tracker-controls select,.tracker-controls input{{font-size:0.75rem;padding:6px 10px;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#374151;}}
.tracker-controls input{{min-width:160px;}}
.tracker-legend{{display:flex;gap:10px;font-size:0.65rem;color:#64748b;margin-left:auto;}}
.tracker-legend-dot{{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:3px;vertical-align:middle;}}
.tracker-board{{display:flex;gap:10px;overflow-x:auto;padding-bottom:8px;min-height:200px;}}
.tracker-col{{min-width:200px;max-width:240px;flex-shrink:0;background:#f8fafc;border-radius:8px;padding:8px;}}
.tracker-col-header{{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px;}}
.tracker-col-title{{font-size:0.7rem;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:0.3px;}}
.tracker-col-badge{{font-size:0.65rem;font-weight:700;padding:1px 7px;border-radius:10px;color:#fff;}}
.tracker-health-bar{{width:100%;height:3px;background:#e2e8f0;border-radius:2px;overflow:hidden;display:flex;margin-bottom:6px;}}
.tracker-card{{background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;margin-bottom:6px;cursor:pointer;transition:box-shadow 0.15s;border-left:3px solid #22c55e;}}
.tracker-card:hover{{box-shadow:0 2px 8px rgba(0,0,0,0.08);}}
.tracker-card-yellow{{border-left-color:#eab308;}}
.tracker-card-red{{border-left-color:#ef4444;}}
.tracker-card-seller{{font-size:0.78rem;font-weight:700;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.tracker-card-meta{{font-size:0.65rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.tracker-card-stale{{font-size:0.65rem;font-weight:600;}}

/* Table */
.data-table{{width:100%;border-collapse:collapse;font-size:0.75rem;}}
.data-table th{{text-align:left;padding:8px 10px;background:#f8fafc;color:#475569;font-weight:700;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.3px;border-bottom:2px solid #e2e8f0;position:sticky;top:0;cursor:pointer;}}
.data-table th:hover{{background:#eef2ff;}}
.data-table td{{padding:6px 10px;border-bottom:1px solid #f1f5f9;}}
.data-table tr:hover{{background:#f8fafc;}}
.data-table tr{{cursor:pointer;}}
.table-wrap{{max-height:500px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:8px;}}

/* Status badges */
.badge{{display:inline-block;font-size:0.6rem;font-weight:700;padding:2px 8px;border-radius:10px;}}
.badge-active{{background:#dbeafe;color:#1d4ed8;}}
.badge-completed{{background:#dcfce7;color:#166534;}}
.badge-cancelled{{background:#fee2e2;color:#991b1b;}}
.badge-onhold{{background:#fef3c7;color:#92400e;}}

/* Trend chart */
.trend-bars{{display:flex;gap:3px;align-items:flex-end;height:100px;}}
.trend-bar{{flex:1;border-radius:3px 3px 0 0;min-width:20px;position:relative;}}
.trend-labels{{display:flex;gap:3px;}}
.trend-labels span{{flex:1;text-align:center;font-size:0.5rem;color:#94a3b8;min-width:20px;}}

/* Seller Detail Modal */
.sd-overlay{{position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(15,23,42,0.5);z-index:9999;display:none;justify-content:flex-end;}}
.sd-panel{{width:min(600px,90vw);height:100vh;background:#fff;overflow-y:auto;box-shadow:-4px 0 24px rgba(0,0,0,0.15);animation:sdSlideIn 0.2s ease-out;}}
@keyframes sdSlideIn{{from{{transform:translateX(100%);}}to{{transform:translateX(0);}}}}
.sd-close{{position:absolute;top:12px;right:16px;font-size:1.5rem;color:#94a3b8;cursor:pointer;background:none;border:none;z-index:10;}}
.sd-close:hover{{color:#475569;}}
.sd-hero{{background:linear-gradient(135deg,#f8fafc,#eef2ff);padding:20px;position:relative;}}
.sd-hero h2{{font-size:1.1rem;font-weight:800;color:#0f172a;margin-bottom:4px;padding-right:30px;}}
.sd-hero-sub{{font-size:0.8rem;color:#64748b;margin-bottom:12px;}}
.sd-badge{{display:inline-block;font-size:0.65rem;font-weight:700;padding:3px 10px;border-radius:12px;margin-bottom:8px;}}
.sd-badge-active{{background:#dbeafe;color:#1d4ed8;}}
.sd-badge-completed{{background:#dcfce7;color:#166534;}}
.sd-badge-cancelled{{background:#fee2e2;color:#991b1b;}}
.sd-badge-onhold{{background:#fef3c7;color:#92400e;}}
.sd-kpis{{display:flex;gap:8px;flex-wrap:wrap;}}
.sd-kpi{{text-align:center;padding:8px 12px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;min-width:70px;}}
.sd-kpi-val{{font-size:1rem;font-weight:800;color:#0f172a;}}
.sd-kpi-val.red{{color:#dc2626;}}
.sd-kpi-val.yellow{{color:#ca8a04;}}
.sd-kpi-val.green{{color:#16a34a;}}
.sd-kpi-label{{font-size:0.55rem;color:#94a3b8;text-transform:uppercase;}}
.sd-section{{padding:16px 20px;border-bottom:1px solid #f1f5f9;}}
.sd-section-title{{font-size:0.85rem;font-weight:700;color:#1e293b;margin-bottom:10px;}}
.sd-timeline{{display:flex;align-items:center;gap:0;overflow-x:auto;padding:8px 0;}}
.sd-tl-stage{{display:flex;flex-direction:column;align-items:center;min-width:60px;position:relative;}}
.sd-tl-dot{{width:14px;height:14px;border-radius:50%;border:2px solid #d1d5db;background:#fff;z-index:1;}}
.sd-tl-dot.done{{background:#22c55e;border-color:#22c55e;}}
.sd-tl-dot.current{{background:#6366f1;border-color:#6366f1;animation:sdPulse 1.5s infinite;}}
@keyframes sdPulse{{0%,100%{{box-shadow:0 0 0 0 rgba(99,102,241,0.4);}}50%{{box-shadow:0 0 0 6px rgba(99,102,241,0);}}}}
.sd-tl-label{{font-size:0.55rem;color:#94a3b8;text-align:center;margin-top:4px;max-width:70px;}}
.sd-tl-label.current{{color:#4f46e5;font-weight:700;}}
.sd-tl-line{{flex:1;height:2px;background:#e2e8f0;min-width:10px;}}
.sd-tl-line.done{{background:#22c55e;}}
.sd-tl-days{{font-size:0.5rem;color:#6366f1;font-weight:600;}}
.sd-field-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;}}
.sd-field{{background:#f8fafc;border-radius:6px;padding:8px 10px;}}
.sd-field-label{{font-size:0.6rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.3px;}}
.sd-field-value{{font-size:0.8rem;font-weight:600;color:#1e293b;}}
.sd-dsa-card{{display:flex;align-items:center;gap:10px;padding:8px 12px;border:1px solid #f1f5f9;border-radius:6px;margin-bottom:4px;border-left:3px solid #e2e8f0;}}
.sd-dsa-completed{{border-left-color:#22c55e;}}
.sd-dsa-scheduled{{border-left-color:#3b82f6;}}
.sd-dsa-cancelled{{border-left-color:#ef4444;}}
.sd-dsa-type{{font-size:0.8rem;font-weight:600;color:#1e293b;}}
.sd-dsa-meta{{font-size:0.65rem;color:#94a3b8;}}
.sd-dsa-status{{font-size:0.65rem;font-weight:600;padding:2px 8px;border-radius:4px;white-space:nowrap;margin-left:auto;}}
.sd-dsa-status.sd-dsa-completed{{background:#dcfce7;color:#166534;}}
.sd-dsa-status.sd-dsa-scheduled{{background:#dbeafe;color:#1d4ed8;}}
.sd-dsa-status.sd-dsa-cancelled{{background:#fee2e2;color:#991b1b;}}
.sd-dsa-status.sd-dsa-other{{background:#f1f5f9;color:#475569;}}
.sd-empty{{text-align:center;padding:16px;color:#94a3b8;font-size:0.8rem;}}
.sd-csat-card{{padding:10px 12px;border:1px solid #f1f5f9;border-radius:6px;margin-bottom:4px;}}
.sd-csat-stars{{color:#eab308;font-size:0.9rem;}}
.sd-csat-comment{{font-size:0.8rem;color:#475569;margin-top:4px;font-style:italic;}}
.sd-csat-meta{{font-size:0.65rem;color:#94a3b8;margin-top:2px;}}

/* Export */
.export-group{{position:relative;display:inline-block;}}
.export-btn{{font-size:0.7rem;padding:5px 12px;border:1px solid #d1d5db;border-radius:6px;background:#fff;color:#475569;cursor:pointer;display:inline-flex;align-items:center;gap:4px;}}
.export-btn:hover{{background:#f1f5f9;}}
.export-menu{{display:none;position:absolute;right:0;bottom:100%;margin-bottom:4px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:50;min-width:140px;overflow:hidden;}}
.export-menu.show{{display:block;}}
.export-menu button{{display:block;width:100%;text-align:left;padding:8px 14px;font-size:0.75rem;border:none;background:none;cursor:pointer;color:#374151;}}
.export-menu button:hover{{background:#f1f5f9;}}

@media(max-width:768px){{
  .header{{padding:12px 16px;}}
  .main{{padding:8px;}}
  .kpi-row{{gap:6px;}}
  .kpi{{min-width:80px;padding:8px;}}
  .kpi-val{{font-size:1.1rem;}}
}}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div>
    <div class="header-title">🎯 GSO Rep Dashboard</div>
    <div class="header-sub">Last refreshed: {now}</div>
  </div>
  <div class="header-controls">
    <select id="teamFilter"><option value="">All Teams</option></select>
    <select id="repFilter"><option value="">All Reps</option></select>
    <select id="maxStale">
      <option value="">No Stale Limit</option>
      <option value="14">Hide &gt; 14d stale</option>
      <option value="30">Hide &gt; 30d stale</option>
      <option value="60" selected>Hide &gt; 60d stale</option>
      <option value="90">Hide &gt; 90d stale</option>
    </select>
    <input type="text" id="searchBox" placeholder="Search seller, rep, AE…" />
  </div>
</div>

<!-- Main -->
<div class="main">

  <!-- Tabs -->
  <div class="tab-bar">
    <button class="tab-btn active" data-tab="tracker">My Projects</button>
    <button class="tab-btn" data-tab="pipeline">Pipeline</button>
    <button class="tab-btn" data-tab="completed">Completed</button>
    <button class="tab-btn" data-tab="performance">My Performance</button>
  </div>

  <!-- Tab: My Projects (Tracker + Readiness + Alerts) -->
  <div class="tab-content active" id="tab-tracker">
    <div id="kpiRow" class="kpi-row"></div>
    <div id="readinessPanel" class="card" style="display:none;"></div>
    <div id="staleAlerts" class="card" style="display:none;"></div>
    <div class="card">
      <div class="card-title">Project Stage Tracker</div>
      <div class="card-subtitle">Every active project in its current stage. Card color = staleness.</div>
      <div class="tracker-controls">
        <select id="trackerSort">
          <option value="stale">Most Stale First</option>
          <option value="open">Longest Open First</option>
          <option value="gpv">Highest GPV First</option>
          <option value="recent">Most Recent First</option>
        </select>
        <div class="tracker-legend">
          <span><span class="tracker-legend-dot" style="background:#22c55e;"></span>Fresh (&lt;7d)</span>
          <span><span class="tracker-legend-dot" style="background:#eab308;"></span>Aging (7–14d)</span>
          <span><span class="tracker-legend-dot" style="background:#ef4444;"></span>Stale (&gt;14d)</span>
        </div>
      </div>
      <div id="trackerBoard" class="tracker-board"></div>
      <div style="text-align:right;margin-top:8px;">
        <div class="export-group">
          <button class="export-btn" onclick="toggleMenu('trackerExportMenu')">📥 Export ▾</button>
          <div class="export-menu" id="trackerExportMenu">
            <button onclick="exportData('tracker','csv')">📄 CSV</button>
            <button onclick="exportData('tracker','excel')">📊 Excel</button>
            <button onclick="exportData('tracker','pdf')">📑 PDF</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Tab: Pipeline Table -->
  <div class="tab-content" id="tab-pipeline">
    <div id="pipelineKpis" class="kpi-row"></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="card-title">Active Pipeline</div>
        <div class="export-group">
          <button class="export-btn" onclick="toggleMenu('pipelineExportMenu')">📥 Export ▾</button>
          <div class="export-menu" id="pipelineExportMenu">
            <button onclick="exportData('pipeline','csv')">📄 CSV</button>
            <button onclick="exportData('pipeline','excel')">📊 Excel</button>
            <button onclick="exportData('pipeline','pdf')">📑 PDF</button>
          </div>
        </div>
      </div>
      <div class="table-wrap"><table class="data-table" id="pipelineTable"><thead></thead><tbody></tbody></table></div>
    </div>
  </div>

  <!-- Tab: Completed -->
  <div class="tab-content" id="tab-completed">
    <div id="completedKpis" class="kpi-row"></div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div><div class="card-title">Recent Completions</div><div class="card-subtitle">Last 90 days</div></div>
        <div class="export-group">
          <button class="export-btn" onclick="toggleMenu('completedExportMenu')">📥 Export ▾</button>
          <div class="export-menu" id="completedExportMenu">
            <button onclick="exportData('completed','csv')">📄 CSV</button>
            <button onclick="exportData('completed','excel')">📊 Excel</button>
            <button onclick="exportData('completed','pdf')">📑 PDF</button>
          </div>
        </div>
      </div>
      <div class="table-wrap"><table class="data-table" id="completedTable"><thead></thead><tbody></tbody></table></div>
    </div>
  </div>

  <!-- Tab: My Performance -->
  <div class="tab-content" id="tab-performance">
    <div id="perfKpis" class="kpi-row"></div>
    <div class="card">
      <div class="card-title">📈 Weekly Completion Trend</div>
      <div class="card-subtitle">Last 12 weeks</div>
      <div id="weeklyTrend"></div>
    </div>
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;">
        <div class="card-title">📊 Completion Time by Work Type</div>
        <div class="export-group">
          <button class="export-btn" onclick="toggleMenu('perfExportMenu')">📥 Export ▾</button>
          <div class="export-menu" id="perfExportMenu">
            <button onclick="exportData('performance','csv')">📄 CSV</button>
            <button onclick="exportData('performance','excel')">📊 Excel</button>
            <button onclick="exportData('performance','pdf')">📑 PDF</button>
          </div>
        </div>
      </div>
      <div class="table-wrap"><table class="data-table" id="wtTable"><thead></thead><tbody></tbody></table></div>
    </div>
  </div>

</div>

<!-- Seller Detail Modal -->
<div id="sellerDetailOverlay" class="sd-overlay" onclick="if(event.target===this)closeSellerDetail();">
  <div class="sd-panel" id="sellerDetailPanel"></div>
</div>

<!-- DATA -->
<script>
const TEAMS = {teams_json};
const EXCHANGE_RATES = {rates_json};
const GSO_DATA = {{}};
GSO_DATA.dsrFacts = {dsr_json};
GSO_DATA.dsaRecords = {dsa_json};
GSO_DATA.bpoActivities = {bpo_json};
GSO_DATA.csatResponses = {csat_json};
</script>

<!-- APP -->
<script>
"use strict";

// ============================================================
// UTILITIES
// ============================================================
function esc(s){{return s==null?'':String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}
function fmtNum(n){{return n==null?'—':Number(n).toLocaleString();}}
function fmtUSD(n){{if(n==null)return'—';if(n>=1e6)return'$'+(n/1e6).toFixed(1)+'M';if(n>=1e3)return'$'+(n/1e3).toFixed(0)+'K';return'$'+Math.round(n);}}
const SF_BASE='https://squareinc.lightning.force.com/lightning/r/';
function sfUrl(id){{return SF_BASE+encodeURIComponent(id)+'/view';}}

const COMPLETED_STATUSES=new Set(['Implementation Complete','Transitioned','Completed']);
const CANCELLED_STATUSES=new Set(['Rejected','Lost','Lost - No Seller Contact','Lost - Churn']);
function classify(s){{if(COMPLETED_STATUSES.has(s))return'completed';if(CANCELLED_STATUSES.has(s))return'cancelled';if(s==='On Hold')return'onHold';if(s==='Draft')return'draft';return'active';}}

// Expand compressed facts
const DSR_FACTS=(GSO_DATA.dsrFacts||[]).map(function(r){{
  r.id=r.id||r.i||'';r.rep=r.rep||r.r||'';r.teamLead=r.teamLead||r.tl||'';
  r.seller=r.seller||r.s||'';r.workType=r.workType||r.wt||r.w||'';
  r.status=r.status||r.st||'';r.subStatus=r.subStatus||r.ss||'';
  r.country=r.country||r.co||'';r.channel=r.channel||r.ch||'';
  r.createdDate=r.createdDate||r.cd||'';r.completedDate=r.completedDate||r.cpd||'';
  r.goLiveDate=r.goLiveDate||r.gld||'';
  r.daysOpen=r.daysOpen!=null?r.daysOpen:r.do_!=null?r.do_:null;
  r.daysToComplete=r.daysToComplete!=null?r.daysToComplete:r.dtc!=null?r.dtc:null;
  r.daysStale=r.daysStale!=null?r.daysStale:r.ds!=null?r.ds:null;
  r.gpvUsd=r.gpvUsd!=null?r.gpvUsd:r.gpv!=null?r.gpv:r.g!=null?r.g:null;
  r.oppOwner=r.oppOwner||r.oo||'';r.oppOwnerRole=r.oppOwnerRole||r.oor||'';
  r.requestReason=r.requestReason||r.rr||'';r.competitorPos=r.competitorPos||r.cp||'';
  r.complexityScore=r.complexityScore!=null?r.complexityScore:r.cx!=null?r.cx:null;
  r.numLocations=r.numLocations!=null?r.numLocations:r.nl!=null?r.nl:null;
  r.category=classify(r.status);
  return r;
}});

// Build roster
const ROSTER=new Set();
Object.keys(TEAMS).forEach(function(lead){{
  ROSTER.add(lead);
  (TEAMS[lead]||[]).forEach(function(r){{ROSTER.add(r);}});
}});

// Rep to lead map
const REP_TO_LEAD={{}};
Object.keys(TEAMS).forEach(function(lead){{
  REP_TO_LEAD[lead]=lead;
  (TEAMS[lead]||[]).forEach(function(r){{REP_TO_LEAD[r]=lead;}});
}});

// DSA count map
const DSA_COUNT={{}};
(GSO_DATA.dsaRecords||[]).forEach(function(d){{if(d.dr)DSA_COUNT[d.dr]=(DSA_COUNT[d.dr]||0)+1;}});

// ============================================================
// READINESS SCORE
// ============================================================
const WT_TARGET={{
  'Optimization Call':3,'Tasks Only':5,'Plus':5,'Payroll':5,
  'Premium':8,'In-Person Refresh':8,'Half-day 3rd Party Vendor Install':10,
  'Onsite':10,'Full-day 3rd Party Vendor Install':14
}};
const STAGE_IDX={{
  'Submitted':0,'Assigned':1,'Seller Outreach Complete':2,'Consultation Complete':3,
  'First Call Complete':4,'Dashboard Training Complete':5,'App Training Complete':6,
  'SO Training Complete':7,'Trainings Complete - Post Implementation':8,
  '3P Service In Progress':5,'Task In Progress':5,
  '1st Q&A Completed':9,'2nd Q&A Completed':10,'On Hold':-1
}};

function readinessScore(f){{
  var dO=f.daysOpen||0,dS=f.daysStale||0,tgt=WT_TARGET[f.workType]||14;
  var sIdx=STAGE_IDX[f.status]||0,hasDsa=(DSA_COUNT[f.id]||0)>0;
  var pace=dO<=tgt?100-(dO/Math.max(tgt,1)*50):Math.max(0,50-(dO-tgt)*3);
  var fresh=dS<=3?100:dS<=7?75:dS<=14?40:Math.max(0,20-(dS-14));
  var prog=f.category==='onHold'?10:Math.min(100,sIdx*12);
  var act=hasDsa?50:0;
  var score=Math.round(pace*0.35+fresh*0.30+prog*0.20+act*0.15);
  return{{score:score,risk:score>=60?'on-track':score>=35?'at-risk':'off-track'}};
}}

// ============================================================
// TRACKER STAGES
// ============================================================
const STAGES=['Submitted','Assigned','Seller Outreach Complete','Consultation Complete',
  'First Call Complete','Dashboard Training Complete','App Training Complete',
  'SO Training Complete','Trainings Complete - Post Implementation',
  '3P Service In Progress','Task In Progress','1st Q&A Completed','2nd Q&A Completed','On Hold'];
const STAGE_SHORT={{'Submitted':'Submitted','Assigned':'Assigned','Seller Outreach Complete':'Seller Outreach',
  'Consultation Complete':'Consultation','First Call Complete':'First Call',
  'Dashboard Training Complete':'Dash Training','App Training Complete':'App Training',
  'SO Training Complete':'SO Training','Trainings Complete - Post Implementation':'Post-Impl',
  '3P Service In Progress':'3P Service','Task In Progress':'Task In Progress',
  '1st Q&A Completed':'1st Q&A','2nd Q&A Completed':'2nd Q&A','On Hold':'On Hold'}};

function health(ds){{if(ds==null)return'green';if(ds>14)return'red';if(ds>7)return'yellow';return'green';}}

// ============================================================
// FILTERING
// ============================================================
function getFiltered(){{
  var teamVal=document.getElementById('teamFilter').value;
  var repVal=document.getElementById('repFilter').value;
  var maxS=parseInt(document.getElementById('maxStale').value||'0',10);
  var search=(document.getElementById('searchBox').value||'').toLowerCase();

  var facts=DSR_FACTS.filter(function(f){{return ROSTER.has(f.rep)&&f.category!=='draft';}});

  if(teamVal){{
    var teamReps=new Set([teamVal].concat(TEAMS[teamVal]||[]));
    facts=facts.filter(function(f){{return teamReps.has(f.rep);}});
  }}
  if(repVal)facts=facts.filter(function(f){{return f.rep===repVal;}});
  if(maxS>0)facts=facts.filter(function(f){{return(f.daysStale||0)<=maxS;}});
  if(search)facts=facts.filter(function(f){{
    return(f.seller||'').toLowerCase().includes(search)||(f.rep||'').toLowerCase().includes(search)||(f.oppOwner||'').toLowerCase().includes(search);
  }});
  return facts;
}}

function getActive(){{return getFiltered().filter(function(f){{return f.category==='active'||f.category==='onHold';}});}}
function getCompleted(){{
  var d90=new Date();d90.setDate(d90.getDate()-90);var cutoff=d90.toISOString().substring(0,10);
  return getFiltered().filter(function(f){{return f.category==='completed'&&f.completedDate>=cutoff;}});
}}

// ============================================================
// RENDER: TABS
// ============================================================
document.querySelectorAll('.tab-btn').forEach(function(btn){{
  btn.addEventListener('click',function(){{
    document.querySelectorAll('.tab-btn').forEach(function(b){{b.classList.remove('active');}});
    document.querySelectorAll('.tab-content').forEach(function(c){{c.classList.remove('active');}});
    btn.classList.add('active');
    document.getElementById('tab-'+btn.dataset.tab).classList.add('active');
    renderAll();
  }});
}});

// ============================================================
// RENDER: EVERYTHING
// ============================================================
function renderAll(){{
  var active=getActive();
  var completed=getCompleted();
  var allFiltered=getFiltered();

  // Populate team dropdown
  var teamSel=document.getElementById('teamFilter');
  var curTeam=teamSel.value;
  teamSel.innerHTML='<option value="">All Teams</option>';
  Object.keys(TEAMS).filter(function(l){{return l!=='Vendor Ops';}}).sort().forEach(function(l){{
    var cnt=DSR_FACTS.filter(function(f){{var tr=new Set([l].concat(TEAMS[l]||[]));return tr.has(f.rep)&&(f.category==='active'||f.category==='onHold');}}).length;
    if(cnt>0){{var o=document.createElement('option');o.value=l;o.textContent=l+"'s Team ("+cnt+')';teamSel.appendChild(o);}}
  }});
  if(curTeam)teamSel.value=curTeam;

  // Populate rep dropdown (scoped to team)
  var repSel=document.getElementById('repFilter');
  var curRep=repSel.value;
  var scopedFacts=DSR_FACTS.filter(function(f){{return ROSTER.has(f.rep)&&(f.category==='active'||f.category==='onHold');}});
  if(curTeam){{var tr=new Set([curTeam].concat(TEAMS[curTeam]||[]));scopedFacts=scopedFacts.filter(function(f){{return tr.has(f.rep);}});}}
  var reps=[...new Set(scopedFacts.map(function(f){{return f.rep;}}).filter(Boolean))].sort();
  repSel.innerHTML='<option value="">All Reps ('+scopedFacts.length+')</option>';
  reps.forEach(function(r){{
    var cnt=scopedFacts.filter(function(f){{return f.rep===r;}}).length;
    var o=document.createElement('option');o.value=r;o.textContent=r+' ('+cnt+')';repSel.appendChild(o);
  }});
  if(curRep&&reps.includes(curRep))repSel.value=curRep;

  // KPI row
  var kpiEl=document.getElementById('kpiRow');
  var onTrack=0,atRisk=0,offTrack=0,totalGpv=0;
  active.forEach(function(f){{
    var r=readinessScore(f);f._rs=r;
    if(r.risk==='on-track')onTrack++;else if(r.risk==='at-risk')atRisk++;else offTrack++;
    totalGpv+=(f.gpvUsd||0);
  }});
  kpiEl.innerHTML=
    '<div class="kpi"><div class="kpi-val blue">'+active.length+'</div><div class="kpi-label">Active Pipeline</div></div>'+
    '<div class="kpi"><div class="kpi-val green">'+onTrack+'</div><div class="kpi-label">On Track</div></div>'+
    '<div class="kpi"><div class="kpi-val yellow">'+atRisk+'</div><div class="kpi-label">At Risk</div></div>'+
    '<div class="kpi"><div class="kpi-val red">'+offTrack+'</div><div class="kpi-label">Off Track</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+fmtUSD(totalGpv)+'</div><div class="kpi-label">Pipeline GPV</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+completed.length+'</div><div class="kpi-label">Completed (90d)</div></div>';

  // Readiness gauge
  var rPanel=document.getElementById('readinessPanel');
  if(active.length>0){{
    var avg=Math.round(active.reduce(function(s,f){{return s+(f._rs||readinessScore(f)).score;}},0)/active.length);
    var pOn=Math.round(onTrack/active.length*100),pAt=Math.round(atRisk/active.length*100),pOff=100-pOn-pAt;
    rPanel.innerHTML='<div class="card-title">🎯 14-Day Readiness Score: '+avg+'</div>'+
      '<div class="r-gauge"><div class="r-gauge-seg" style="width:'+pOn+'%;background:#22c55e;"></div>'+
      '<div class="r-gauge-seg" style="width:'+pAt+'%;background:#eab308;"></div>'+
      '<div class="r-gauge-seg" style="width:'+pOff+'%;background:#ef4444;"></div></div>'+
      '<div style="display:flex;justify-content:space-between;font-size:0.65rem;color:#94a3b8;margin-top:4px;">'+
      '<span>🟢 On Track ('+pOn+'%)</span><span>🟡 At Risk ('+pAt+'%)</span><span>🔴 Off Track ('+pOff+'%)</span></div>';
    rPanel.style.display='block';
  }}else{{rPanel.style.display='none';}}

  // Stale alerts
  var aPanel=document.getElementById('staleAlerts');
  var scored=active.map(function(f){{var r=f._rs||readinessScore(f);return{{fact:f,score:r.score,risk:r.risk}};}})
    .filter(function(s){{return s.risk!=='on-track';}}).sort(function(a,b){{return a.score-b.score;}});
  if(scored.length>0){{
    var h='<div class="card-title">🚨 Needs Attention ('+scored.length+')</div><div class="alert-list">';
    scored.slice(0,12).forEach(function(s){{
      var f=s.fact;var cc=s.risk==='off-track'?'alert-card-red':'alert-card-yellow';
      var sc=s.risk==='off-track'?'alert-score-red':'alert-score-yellow';
      var stC=(f.daysStale||0)>14?'color:#ef4444':(f.daysStale||0)>7?'color:#ca8a04':'';
      h+='<div class="alert-card '+cc+'" onclick="openSellerDetail(\\''+esc(f.id)+'\\')">'+
        '<div style="flex:1;min-width:0;"><div class="alert-seller">'+esc(f.seller||'Unknown')+
        ' <a href="'+sfUrl(f.id)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;font-size:0.65rem;">🔗</a></div>'+
        '<div class="alert-meta">'+esc(f.rep||'')+' · '+esc(f.status||'')+' · '+(f.daysOpen||0)+'d open · <span style="'+stC+'">'+(f.daysStale||0)+'d stale</span>'+(f.gpvUsd?' · '+fmtUSD(f.gpvUsd):'')+'</div></div>'+
        '<div class="alert-score '+sc+'">'+s.score+'</div></div>';
    }});
    h+='</div>';
    aPanel.innerHTML=h;aPanel.style.display='block';
  }}else{{aPanel.style.display='none';}}

  // Tracker board
  renderTracker(active);

  // Pipeline table
  renderPipelineTab(active);

  // Completed table
  renderCompletedTab(completed);

  // Performance tab
  renderPerformanceTab(allFiltered);
}}

// ============================================================
// RENDER: TRACKER BOARD
// ============================================================
function renderTracker(active){{
  var board=document.getElementById('trackerBoard');
  var sortVal=document.getElementById('trackerSort').value;
  var sortFn={{
    stale:function(a,b){{return(b.daysStale||0)-(a.daysStale||0);}},
    open:function(a,b){{return(b.daysOpen||0)-(a.daysOpen||0);}},
    gpv:function(a,b){{return(b.gpvUsd||0)-(a.gpvUsd||0);}},
    recent:function(a,b){{return(b.createdDate||'')>(a.createdDate||'')?1:-1;}}
  }};

  var stages={{}};
  STAGES.forEach(function(st){{stages[st]=[];}});
  active.forEach(function(f){{
    var st=f.category==='onHold'?'On Hold':f.status;
    if(stages[st])stages[st].push(f);
  }});

  var html='';
  STAGES.forEach(function(st){{
    var cards=stages[st];if(!cards.length)return;
    cards.sort(sortFn[sortVal]||sortFn.stale);
    var g=0,y=0,r=0;
    cards.forEach(function(f){{var h=health(f.daysStale);if(h==='green')g++;else if(h==='yellow')y++;else r++;}});
    var total=cards.length;
    var badgeColor=r>total*0.5?'#ef4444':y+r>total*0.5?'#eab308':'#22c55e';
    html+='<div class="tracker-col"><div class="tracker-col-header"><span class="tracker-col-title">'+(STAGE_SHORT[st]||st)+'</span>';
    html+='<span class="tracker-col-badge" style="background:'+badgeColor+';">'+total+'</span></div>';
    html+='<div class="tracker-health-bar"><div style="width:'+(g/total*100)+'%;height:100%;background:#22c55e;"></div>';
    html+='<div style="width:'+(y/total*100)+'%;height:100%;background:#eab308;"></div>';
    html+='<div style="width:'+(r/total*100)+'%;height:100%;background:#ef4444;"></div></div>';
    cards.forEach(function(f){{
      var h=health(f.daysStale);
      var cc=h==='red'?'tracker-card-red':h==='yellow'?'tracker-card-yellow':'';
      var sc=h==='red'?'color:#ef4444':h==='yellow'?'color:#ca8a04':'color:#22c55e';
      html+='<div class="tracker-card '+cc+'" onclick="openSellerDetail(\\''+esc(f.id)+'\\')">'+
        '<div class="tracker-card-seller">'+esc(f.seller||'Unknown')+'</div>'+
        '<div class="tracker-card-meta">'+esc(f.rep||'')+' · AE: '+esc(f.oppOwner||'—')+'</div>'+
        '<div class="tracker-card-stale" style="'+sc+'">'+(f.daysStale||0)+'d stale</div>'+
        (f.gpvUsd?'<div style="font-size:0.65rem;color:#64748b;">'+fmtUSD(f.gpvUsd)+'</div>':'')+
        '</div>';
    }});
    html+='</div>';
  }});
  board.innerHTML=html;
  window._exportActive=active;
}}

// ============================================================
// RENDER: PIPELINE TABLE
// ============================================================
function renderPipelineTab(active){{
  var kpis=document.getElementById('pipelineKpis');
  var staleCount=active.filter(function(f){{return(f.daysStale||0)>14;}}).length;
  var medOpen=active.length?active.map(function(f){{return f.daysOpen||0;}}).sort(function(a,b){{return a-b;}})[Math.floor(active.length/2)]:0;
  kpis.innerHTML=
    '<div class="kpi"><div class="kpi-val">'+active.length+'</div><div class="kpi-label">Active</div></div>'+
    '<div class="kpi"><div class="kpi-val red">'+staleCount+'</div><div class="kpi-label">Stale (&gt;14d)</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+medOpen+'</div><div class="kpi-label">Median Days Open</div></div>';

  var table=document.getElementById('pipelineTable');
  var cols=['Seller','Rep','Status','Work Type','Days Open','Days Stale','GPV','AE',''];
  table.querySelector('thead').innerHTML='<tr>'+cols.map(function(c){{return'<th>'+c+'</th>';}}).join('')+'</tr>';
  var tbody=table.querySelector('tbody');
  tbody.innerHTML='';
  active.sort(function(a,b){{return(b.daysStale||0)-(a.daysStale||0);}}).forEach(function(f){{
    var h=health(f.daysStale);var sc=h==='red'?'color:#ef4444':h==='yellow'?'color:#ca8a04':'';
    var cat=f.category;var bc=cat==='onHold'?'badge-onhold':'badge-active';
    var tr=document.createElement('tr');
    tr.onclick=function(){{openSellerDetail(f.id);}};
    tr.innerHTML='<td><strong>'+esc(f.seller||'—')+'</strong></td><td>'+esc(f.rep)+'</td>'+
      '<td><span class="badge '+bc+'">'+esc(f.status)+'</span></td><td>'+esc(f.workType)+'</td>'+
      '<td>'+(f.daysOpen||0)+'</td><td style="'+sc+';font-weight:600;">'+(f.daysStale||0)+'</td>'+
      '<td>'+fmtUSD(f.gpvUsd)+'</td><td>'+esc(f.oppOwner)+'</td>'+
      '<td><a href="'+sfUrl(f.id)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;">🔗</a></td>';
    tbody.appendChild(tr);
  }});
}}

// ============================================================
// RENDER: COMPLETED TABLE
// ============================================================
function renderCompletedTab(completed){{
  var kpis=document.getElementById('completedKpis');
  var dtcVals=completed.filter(function(f){{return f.daysToComplete!=null;}}).map(function(f){{return f.daysToComplete;}}).sort(function(a,b){{return a-b;}});
  var medDtc=dtcVals.length?dtcVals[Math.floor(dtcVals.length/2)]:0;
  var under14=dtcVals.filter(function(d){{return d<=14;}}).length;
  var pct14=dtcVals.length?Math.round(under14/dtcVals.length*100):0;
  var totalGpv=completed.reduce(function(s,f){{return s+(f.gpvUsd||0);}},0);
  kpis.innerHTML=
    '<div class="kpi"><div class="kpi-val green">'+completed.length+'</div><div class="kpi-label">Completed (90d)</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+medDtc+'d</div><div class="kpi-label">Median Days</div></div>'+
    '<div class="kpi"><div class="kpi-val '+(pct14>=40?'green':pct14>=25?'yellow':'red')+'">'+pct14+'%</div><div class="kpi-label">≤14 Days</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+fmtUSD(totalGpv)+'</div><div class="kpi-label">GPV Completed</div></div>';

  var table=document.getElementById('completedTable');
  var cols=['Seller','Rep','Work Type','Days to Complete','Completed','GPV',''];
  table.querySelector('thead').innerHTML='<tr>'+cols.map(function(c){{return'<th>'+c+'</th>';}}).join('')+'</tr>';
  var tbody=table.querySelector('tbody');tbody.innerHTML='';
  completed.sort(function(a,b){{return(b.completedDate||'')>(a.completedDate||'')?1:-1;}}).forEach(function(f){{
    var tr=document.createElement('tr');
    tr.onclick=function(){{openSellerDetail(f.id);}};
    tr.innerHTML='<td><strong>'+esc(f.seller||'—')+'</strong></td><td>'+esc(f.rep)+'</td>'+
      '<td>'+esc(f.workType)+'</td><td>'+(f.daysToComplete!=null?f.daysToComplete+'d':'—')+'</td>'+
      '<td>'+esc(f.completedDate||'—')+'</td><td>'+fmtUSD(f.gpvUsd)+'</td>'+
      '<td><a href="'+sfUrl(f.id)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;">🔗</a></td>';
    tbody.appendChild(tr);
  }});
}}

// ============================================================
// RENDER: PERFORMANCE TAB
// ============================================================
function renderPerformanceTab(allFacts){{
  var completed=allFacts.filter(function(f){{return f.category==='completed'&&ROSTER.has(f.rep);}});
  var now=new Date();

  // Performance KPIs (all time for this filter)
  var last90=new Date();last90.setDate(last90.getDate()-90);var cut90=last90.toISOString().substring(0,10);
  var recent=completed.filter(function(f){{return f.completedDate>=cut90;}});
  var dtcAll=recent.filter(function(f){{return f.daysToComplete!=null;}}).map(function(f){{return f.daysToComplete;}}).sort(function(a,b){{return a-b;}});
  var medAll=dtcAll.length?dtcAll[Math.floor(dtcAll.length/2)]:0;
  var u14=dtcAll.filter(function(d){{return d<=14;}}).length;
  var p14=dtcAll.length?Math.round(u14/dtcAll.length*100):0;

  var kpis=document.getElementById('perfKpis');
  kpis.innerHTML=
    '<div class="kpi"><div class="kpi-val">'+recent.length+'</div><div class="kpi-label">Completed (90d)</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+medAll+'d</div><div class="kpi-label">Median Days</div></div>'+
    '<div class="kpi"><div class="kpi-val '+(p14>=40?'green':p14>=25?'yellow':'red')+'">'+p14+'%</div><div class="kpi-label">≤14d Rate</div></div>'+
    '<div class="kpi"><div class="kpi-val">'+completed.length+'</div><div class="kpi-label">All-Time Completions</div></div>';

  // Weekly trend
  var trendEl=document.getElementById('weeklyTrend');
  var weeks=[];
  for(var w=12;w>=1;w--){{
    var wS=new Date(now);wS.setDate(wS.getDate()-w*7);
    var wE=new Date(now);wE.setDate(wE.getDate()-(w-1)*7);
    var ws=wS.toISOString().substring(0,10),we=wE.toISOString().substring(0,10);
    var wf=completed.filter(function(f){{return f.completedDate>=ws&&f.completedDate<we;}});
    var dv=wf.filter(function(f){{return f.daysToComplete!=null;}}).map(function(f){{return f.daysToComplete;}}).sort(function(a,b){{return a-b;}});
    var md=dv.length?dv[Math.floor(dv.length/2)]:0;
    var u=dv.filter(function(d){{return d<=14;}}).length;
    var p=dv.length?Math.round(u/dv.length*100):0;
    weeks.push({{label:ws.substring(5),count:wf.length,med:md,pct14:p}});
  }}
  var maxC=Math.max.apply(null,weeks.map(function(w){{return w.count;}})||[1])||1;
  var th='<div class="trend-bars">';
  weeks.forEach(function(w){{
    var h=Math.max(4,Math.round(w.count/maxC*90));
    var c=w.pct14>=40?'#22c55e':w.pct14>=25?'#eab308':'#ef4444';
    th+='<div class="trend-bar" style="height:'+h+'px;background:'+c+';opacity:0.85;" title="'+w.label+': '+w.count+' completed, '+w.med+'d median, '+w.pct14+'% ≤14d"></div>';
  }});
  th+='</div><div class="trend-labels">';
  weeks.forEach(function(w){{th+='<span>'+w.label+'</span>';}});
  th+='</div><div class="trend-labels">';
  weeks.forEach(function(w){{th+='<span style="font-weight:600;">'+w.count+'</span>';}});
  th+='</div><div class="trend-labels">';
  weeks.forEach(function(w){{
    var c=w.pct14>=40?'#16a34a':w.pct14>=25?'#ca8a04':'#dc2626';
    th+='<span style="color:'+c+';font-weight:600;">'+w.pct14+'%</span>';
  }});
  th+='</div><div style="display:flex;justify-content:center;gap:16px;margin-top:6px;font-size:0.6rem;color:#94a3b8;">';
  th+='<span>Count</span><span>% ≤14d</span><span style="color:#22c55e;">■ ≥40%</span><span style="color:#eab308;">■ 25-39%</span><span style="color:#ef4444;">■ &lt;25%</span></div>';
  trendEl.innerHTML=th;

  // Work type breakdown
  var wtTable=document.getElementById('wtTable');
  var wts={{}};
  recent.forEach(function(f){{
    var wt=f.workType||'Other';
    if(!wts[wt])wts[wt]={{count:0,dtc:[]}};
    wts[wt].count++;
    if(f.daysToComplete!=null)wts[wt].dtc.push(f.daysToComplete);
  }});
  wtTable.querySelector('thead').innerHTML='<tr><th>Work Type</th><th>Count</th><th>Median Days</th><th>≤14d</th></tr>';
  var tbody=wtTable.querySelector('tbody');tbody.innerHTML='';
  Object.keys(wts).sort(function(a,b){{return wts[b].count-wts[a].count;}}).forEach(function(wt){{
    var s=wts[wt];var d=s.dtc.sort(function(a,b){{return a-b;}});
    var med=d.length?d[Math.floor(d.length/2)]:0;
    var u=d.filter(function(v){{return v<=14;}}).length;
    var p=d.length?Math.round(u/d.length*100):0;
    var tr=document.createElement('tr');
    tr.innerHTML='<td><strong>'+esc(wt)+'</strong></td><td>'+s.count+'</td><td>'+med+'d</td><td style="color:'+(p>=40?'#16a34a':p>=25?'#ca8a04':'#dc2626')+';font-weight:600;">'+p+'%</td>';
    tbody.appendChild(tr);
  }});
}}

// ============================================================
// SELLER DETAIL MODAL (same as main dashboard)
// ============================================================
const SD_STAGES=['Submitted','Assigned','Seller Outreach Complete','Consultation Complete',
  'First Call Complete','Dashboard Training Complete','App Training Complete',
  'SO Training Complete','Implementation Complete'];

function openSellerDetail(dsrId){{
  var fact=DSR_FACTS.find(function(f){{return f.id===dsrId;}});
  if(!fact)return;
  var overlay=document.getElementById('sellerDetailOverlay');
  var panel=document.getElementById('sellerDetailPanel');
  overlay.style.display='flex';document.body.style.overflow='hidden';

  var cat=fact.category||'active';
  var bc=cat==='completed'?'sd-badge-completed':cat==='cancelled'?'sd-badge-cancelled':cat==='onHold'?'sd-badge-onhold':'sd-badge-active';
  var now=new Date();
  var lastUp=fact.daysStale!=null?new Date(now-fact.daysStale*86400000).toISOString().substring(0,10):'—';
  var staleC=(fact.daysStale||0)>14?'red':(fact.daysStale||0)>7?'yellow':'green';

  var h='<button class="sd-close" onclick="closeSellerDetail()">&times;</button>';
  h+='<div class="sd-hero"><h2>'+esc(fact.seller||'Unknown')+' <a href="'+sfUrl(fact.id)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;font-size:0.7rem;font-weight:600;">🔗 Salesforce</a></h2>';
  h+='<div class="sd-hero-sub">'+esc(fact.rep||'')+' · '+esc(fact.teamLead||'')+' · '+esc(fact.country||'')+'</div>';
  h+='<span class="sd-badge '+bc+'">'+esc(fact.status)+'</span>';
  if(fact.subStatus&&fact.subStatus!=='None')h+=' <span class="sd-badge" style="background:#f1f5f9;color:#475569;">'+esc(fact.subStatus)+'</span>';
  h+='<div class="sd-kpis">';
  h+='<div class="sd-kpi"><div class="sd-kpi-val">'+fmtUSD(fact.gpvUsd)+'</div><div class="sd-kpi-label">Annual GPV</div></div>';
  h+='<div class="sd-kpi"><div class="sd-kpi-val">'+(fact.daysOpen||0)+'</div><div class="sd-kpi-label">Days Open</div></div>';
  h+='<div class="sd-kpi"><div class="sd-kpi-val '+staleC+'">'+(fact.daysStale||0)+'</div><div class="sd-kpi-label">Days Stale</div></div>';
  h+='<div class="sd-kpi"><div class="sd-kpi-val">'+lastUp+'</div><div class="sd-kpi-label">Last Updated</div></div>';
  h+='</div></div>';

  // Timeline
  h+='<div class="sd-section"><div class="sd-section-title">📍 Onboarding Journey</div><div class="sd-timeline">';
  var curIdx=SD_STAGES.indexOf(fact.status);
  if(curIdx===-1&&cat==='completed')curIdx=SD_STAGES.length;
  SD_STAGES.forEach(function(st,i){{
    if(i>0)h+='<div class="sd-tl-line'+(i<=curIdx?' done':'')+'"></div>';
    var dc=i<curIdx?'done':i===curIdx?'current':'';
    h+='<div class="sd-tl-stage"><div class="sd-tl-dot '+dc+'"></div>';
    h+='<div class="sd-tl-label'+(i===curIdx?' current':'')+'">'+st.replace(' Complete','').replace(' Completed','')+'</div>';
    if(i===curIdx&&fact.daysStale!=null)h+='<div class="sd-tl-days">'+fact.daysStale+'d in stage</div>';
    h+='</div>';
  }});
  h+='</div></div>';

  // Project details
  h+='<div class="sd-section"><div class="sd-section-title">📋 Project Details</div><div class="sd-field-grid">';
  [['GSO Rep',fact.rep],['Team Lead',fact.teamLead],['Work Type',fact.workType],['AE',fact.oppOwner],
   ['Country',fact.country],['Created',fact.createdDate],['Last Updated',lastUp],['Channel',fact.channel||'GSO'],
   ['DSR ID',null,'<a href="'+sfUrl(fact.id)+'" target="_blank" style="color:#4f46e5;text-decoration:none;font-weight:600;">'+esc(fact.id)+' 🔗</a>']
  ].forEach(function(p){{
    var val=p[1],raw=p[2];
    if(!raw&&(val==null||val===''||val==='None'))return;
    h+='<div class="sd-field"><div class="sd-field-label">'+esc(p[0])+'</div><div class="sd-field-value">'+(raw||esc(String(val)))+'</div></div>';
  }});
  h+='</div></div>';

  // Activities
  var acts=[];var seen=new Set();
  (GSO_DATA.dsaRecords||[]).forEach(function(d){{
    if(d.dr===fact.id){{var k=d.at+'|'+d.cd+'|'+d.p;if(!seen.has(k)){{seen.add(k);acts.push(d);}}}}
  }});
  (GSO_DATA.dsaRecords||[]).forEach(function(d){{
    if(d.sl&&fact.seller&&d.sl.toLowerCase()===fact.seller.toLowerCase()&&d.dr!==fact.id){{
      var k=d.at+'|'+d.cd+'|'+d.p;if(!seen.has(k)){{seen.add(k);acts.push(d);}}
    }}
  }});
  (GSO_DATA.bpoActivities||[]).forEach(function(d){{
    if(d.sl&&fact.seller&&d.sl.toLowerCase()===fact.seller.toLowerCase()){{
      var k=d.at+'|'+d.cd+'|BPO';if(!seen.has(k)){{seen.add(k);acts.push(d);}}
    }}
  }});
  acts.sort(function(a,b){{return(b.cd||'')>(a.cd||'')?1:-1;}});

  h+='<div class="sd-section"><div class="sd-section-title">🔧 Activities ('+acts.length+')</div>';
  if(acts.length>0){{
    var comp=0,sched=0,canc=0;
    acts.forEach(function(d){{var st=(d.st||'').toLowerCase();if(st.includes('completed')||st.includes('complete'))comp++;else if(st.includes('scheduled')||st.includes('confirmed'))sched++;else if(st.includes('cancel'))canc++;}});
    h+='<div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap;">';
    if(comp)h+='<span style="font-size:0.7rem;font-weight:600;color:#166534;background:#dcfce7;padding:2px 8px;border-radius:4px;">✓ '+comp+'</span>';
    if(sched)h+='<span style="font-size:0.7rem;font-weight:600;color:#1d4ed8;background:#dbeafe;padding:2px 8px;border-radius:4px;">📅 '+sched+'</span>';
    if(canc)h+='<span style="font-size:0.7rem;font-weight:600;color:#991b1b;background:#fee2e2;padding:2px 8px;border-radius:4px;">✕ '+canc+'</span>';
    h+='</div>';
    acts.forEach(function(d){{
      var st=(d.st||'').toLowerCase();
      var sc=(st.includes('completed')||st.includes('complete'))?'sd-dsa-completed':(st.includes('scheduled')||st.includes('confirmed'))?'sd-dsa-scheduled':st.includes('cancel')?'sd-dsa-cancelled':'sd-dsa-other';
      h+='<div class="sd-dsa-card"><div style="flex:1;min-width:0;"><div class="sd-dsa-type">'+esc(d.at||'Unknown');
      if(d.dr)h+=' <a href="'+sfUrl(d.dr)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;font-size:0.65rem;">🔗</a>';
      h+='</div><div class="sd-dsa-meta">'+[d.p,d.cd,d.cpd?'Done: '+d.cpd:''].filter(Boolean).join(' · ')+'</div></div>';
      h+='<div class="sd-dsa-status '+sc+'">'+esc(d.st||'Unknown')+'</div></div>';
    }});
  }}else{{h+='<div class="sd-empty">No activities found</div>';}}
  h+='</div>';

  // CSAT
  var csats=(GSO_DATA.csatResponses||[]).filter(function(c){{
    var cs=(c.sl||c.seller||'').toLowerCase();return cs&&fact.seller&&cs===fact.seller.toLowerCase();
  }});
  if(csats.length>0){{
    h+='<div class="sd-section"><div class="sd-section-title">⭐ Customer Feedback ('+csats.length+')</div>';
    csats.forEach(function(c){{
      h+='<div class="sd-csat-card">';
      if(c.r)h+='<div class="sd-csat-stars">'+'★'.repeat(Math.round(c.r))+'☆'.repeat(5-Math.round(c.r))+' '+c.r+'/5</div>';
      if(c.c)h+='<div class="sd-csat-comment">"'+esc(c.c)+'"</div>';
      h+='<div class="sd-csat-meta">'+[c.d,c.at].filter(Boolean).join(' · ')+'</div></div>';
    }});
    h+='</div>';
  }}

  // Seller history
  var others=DSR_FACTS.filter(function(f){{return f.seller&&fact.seller&&f.seller.toLowerCase()===fact.seller.toLowerCase()&&f.id!==fact.id;}});
  if(others.length>0){{
    h+='<div class="sd-section"><div class="sd-section-title">📁 Seller History ('+others.length+')</div>';
    others.slice(0,10).forEach(function(f){{
      var oc=f.category||'active';var ob=oc==='completed'?'sd-badge-completed':oc==='cancelled'?'sd-badge-cancelled':oc==='onHold'?'sd-badge-onhold':'sd-badge-active';
      h+='<div class="sd-dsa-card" style="cursor:pointer;" onclick="openSellerDetail(\\''+esc(f.id)+'\\')">'+
        '<div style="flex:1;min-width:0;"><div class="sd-dsa-type">'+esc(f.status||'Unknown')+' <a href="'+sfUrl(f.id)+'" target="_blank" rel="noopener" onclick="event.stopPropagation()" style="color:#4f46e5;text-decoration:none;font-size:0.65rem;">🔗</a></div>'+
        '<div class="sd-dsa-meta">'+esc(f.rep||'')+' · '+esc(f.createdDate||'')+(f.gpvUsd?' · '+fmtUSD(f.gpvUsd):'')+'</div></div>'+
        '<span class="sd-badge '+ob+'">'+esc(oc)+'</span></div>';
    }});
    h+='</div>';
  }}

  panel.innerHTML=h;
}}

function closeSellerDetail(){{
  document.getElementById('sellerDetailOverlay').style.display='none';
  document.body.style.overflow='';
}}
window.openSellerDetail=openSellerDetail;
window.closeSellerDetail=closeSellerDetail;

// ============================================================
// EVENT LISTENERS
// ============================================================
document.getElementById('teamFilter').addEventListener('change',function(){{
  document.getElementById('repFilter').value='';renderAll();
}});
document.getElementById('repFilter').addEventListener('change',renderAll);
document.getElementById('maxStale').addEventListener('change',renderAll);
var _debounce;
document.getElementById('searchBox').addEventListener('input',function(){{
  clearTimeout(_debounce);_debounce=setTimeout(renderAll,200);
}});
document.getElementById('trackerSort').addEventListener('change',function(){{renderTracker(getActive());}});
document.addEventListener('keydown',function(e){{if(e.key==='Escape')closeSellerDetail();}});

// ============================================================
// EXPORT ENGINE (CSV, Excel, PDF)
// ============================================================
function toggleMenu(id){{
  document.querySelectorAll('.export-menu').forEach(function(m){{if(m.id!==id)m.classList.remove('show');}});
  document.getElementById(id).classList.toggle('show');
}}
document.addEventListener('click',function(e){{
  if(!e.target.closest('.export-group'))document.querySelectorAll('.export-menu').forEach(function(m){{m.classList.remove('show');}});
}});

function getExportData(source){{
  var cols,rows;
  if(source==='tracker'||source==='pipeline'){{
    var facts=window._exportActive||[];
    cols=['Seller','Rep','Team Lead','Status','Work Type','Days Open','Days Stale','GPV (USD)','AE','Country','Created','Salesforce Link'];
    rows=facts.map(function(f){{return[f.seller,f.rep,f.teamLead,f.status,f.workType,f.daysOpen,f.daysStale,f.gpvUsd,f.oppOwner,f.country,f.createdDate,sfUrl(f.id)];}});
  }}else if(source==='completed'){{
    var facts=getCompleted();
    cols=['Seller','Rep','Work Type','Days to Complete','Completed Date','GPV (USD)','AE','Country','Salesforce Link'];
    rows=facts.map(function(f){{return[f.seller,f.rep,f.workType,f.daysToComplete,f.completedDate,f.gpvUsd,f.oppOwner,f.country,sfUrl(f.id)];}});
  }}else if(source==='performance'){{
    var allFacts=getFiltered().filter(function(f){{return f.category==='completed'&&ROSTER.has(f.rep);}});
    var d90=new Date();d90.setDate(d90.getDate()-90);var cut=d90.toISOString().substring(0,10);
    var recent=allFacts.filter(function(f){{return f.completedDate>=cut;}});
    cols=['Seller','Rep','Work Type','Days to Complete','Completed Date','GPV (USD)','AE','Salesforce Link'];
    rows=recent.map(function(f){{return[f.seller,f.rep,f.workType,f.daysToComplete,f.completedDate,f.gpvUsd,f.oppOwner,sfUrl(f.id)];}});
  }}
  return{{cols:cols,rows:rows}};
}}

function exportData(source,format){{
  var data=getExportData(source);
  if(!data.rows||!data.rows.length)return alert('No data to export');
  document.querySelectorAll('.export-menu').forEach(function(m){{m.classList.remove('show');}});

  var repVal=document.getElementById('repFilter').value;
  var teamVal=document.getElementById('teamFilter').value;
  var label=repVal||teamVal||'all';
  var safeName='gso-'+source+'-'+label.replace(/[^a-zA-Z0-9]/g,'-').toLowerCase();

  if(format==='csv'){{
    var csvRows=[data.cols.join(',')];
    data.rows.forEach(function(r){{
      csvRows.push(r.map(function(v){{return'"'+String(v==null?'':v).replace(/"/g,'""')+'"';}}).join(','));
    }});
    downloadBlob(csvRows.join('\\n'),'text/csv;charset=utf-8;',safeName+'.csv');
  }}
  else if(format==='excel'){{
    // Build Excel XML (SpreadsheetML) — works in Excel without libraries
    var xml='<?xml version="1.0"?>\\n<?mso-application progid="Excel.Sheet"?>\\n';
    xml+='<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\\n';
    xml+='<Styles><Style ss:ID="hdr"><Font ss:Bold="1" ss:Size="11"/><Interior ss:Color="#E2E8F0" ss:Pattern="Solid"/></Style>';
    xml+='<Style ss:ID="num"><NumberFormat ss:Format="#,##0"/></Style>';
    xml+='<Style ss:ID="usd"><NumberFormat ss:Format="$#,##0"/></Style></Styles>\\n';
    xml+='<Worksheet ss:Name="'+source+'"><Table>\\n';
    // Header
    xml+='<Row>';
    data.cols.forEach(function(c){{xml+='<Cell ss:StyleID="hdr"><Data ss:Type="String">'+escXml(c)+'</Data></Cell>';}});
    xml+='</Row>\\n';
    // Data rows
    data.rows.forEach(function(r){{
      xml+='<Row>';
      r.forEach(function(v,i){{
        var col=data.cols[i]||'';
        if(v==null)v='';
        if(typeof v==='number'&&!isNaN(v)){{
          var style=col.includes('GPV')||col.includes('USD')?'usd':'num';
          xml+='<Cell ss:StyleID="'+style+'"><Data ss:Type="Number">'+v+'</Data></Cell>';
        }}else{{
          xml+='<Cell><Data ss:Type="String">'+escXml(String(v))+'</Data></Cell>';
        }}
      }});
      xml+='</Row>\\n';
    }});
    xml+='</Table></Worksheet></Workbook>';
    downloadBlob(xml,'application/vnd.ms-excel',safeName+'.xls');
  }}
  else if(format==='pdf'){{
    // Build printable HTML and trigger print dialog
    var w=window.open('','_blank','width=1000,height=700');
    var h='<!DOCTYPE html><html><head><title>'+escXml(safeName)+'</title>';
    h+='<style>body{{font-family:Inter,-apple-system,sans-serif;padding:24px;color:#1e293b;}}';
    h+='h1{{font-size:16px;margin-bottom:4px;}}p{{font-size:11px;color:#64748b;margin-bottom:12px;}}';
    h+='table{{width:100%;border-collapse:collapse;font-size:10px;}}';
    h+='th{{text-align:left;padding:6px 8px;background:#f1f5f9;border-bottom:2px solid #cbd5e1;font-weight:700;font-size:9px;text-transform:uppercase;}}';
    h+='td{{padding:5px 8px;border-bottom:1px solid #f1f5f9;}}';
    h+='tr:nth-child(even){{background:#fafafa;}}';
    h+='.footer{{margin-top:16px;font-size:9px;color:#94a3b8;text-align:center;}}';
    h+='@media print{{body{{padding:12px;}}@page{{margin:0.5in;size:landscape;}}}}</style></head><body>';
    var filterDesc=[];
    if(teamVal)filterDesc.push('Team: '+teamVal);
    if(repVal)filterDesc.push('Rep: '+repVal);
    var maxS=document.getElementById('maxStale').value;
    if(maxS)filterDesc.push('Max stale: '+maxS+'d');
    h+='<h1>GSO '+source.charAt(0).toUpperCase()+source.slice(1)+' Report</h1>';
    h+='<p>'+(filterDesc.length?filterDesc.join(' · ')+' · ':'')+data.rows.length+' records · Generated '+new Date().toLocaleDateString()+'</p>';
    h+='<table><thead><tr>';
    data.cols.forEach(function(c){{if(c!=='Salesforce Link')h+='<th>'+escXml(c)+'</th>';}});
    h+='</tr></thead><tbody>';
    data.rows.forEach(function(r){{
      h+='<tr>';
      r.forEach(function(v,i){{
        if(data.cols[i]==='Salesforce Link')return;
        var val=v==null?'':typeof v==='number'&&data.cols[i].includes('GPV')?fmtUSD(v):String(v);
        h+='<td>'+escXml(val)+'</td>';
      }});
      h+='</tr>';
    }});
    h+='</tbody></table>';
    h+='<div class="footer">GSO Rep Dashboard · '+new Date().toLocaleString()+'</div>';
    h+='<script>setTimeout(function(){{window.print();}},300);</'+'script></body></html>';
    w.document.write(h);w.document.close();
  }}
}}

function downloadBlob(content,type,filename){{
  var blob=new Blob([content],{{type:type}});
  var a=document.createElement('a');a.href=URL.createObjectURL(blob);
  a.download=filename;a.click();URL.revokeObjectURL(a.href);
}}

function escXml(s){{return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}}

// Initial render
renderAll();
</script>
</body>
</html>'''

    # Write output
    with open(OUTFILE, 'w') as f:
        f.write(html)
    
    size = os.path.getsize(OUTFILE)
    print(f"\n✅ Generated {OUTFILE}: {size/1024/1024:.1f} MB")

if __name__ == '__main__':
    main()
