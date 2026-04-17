#!/usr/bin/env python3
"""Generate standalone Lead Time Story Dashboard.

Extracts the full Lead Time Story tab from the main GSO Dashboard into a
self-contained HTML file that can be shared independently via Blockcell.

Data embedded:
  - DSR facts (GSO channel only, slim format)
  - Kickoff data (Snowflake stage history)
  - Journey timing (pre-aggregated)
  - Teams / roster

All rendering logic from the main dashboard's renderNarrative() is included.
"""

import json, os, re
from datetime import datetime

DASH_DIR = os.path.dirname(os.path.abspath(__file__))


def build_leadtime_dashboard():
    print("📊 Building Lead Time Story Dashboard...")

    # ── Load data ──
    with open(os.path.join(DASH_DIR, 'dashboard.html'), 'r') as f:
        main_html = f.read()

    # Extract GSO_DATA block from main dashboard (line starting with "const GSO_DATA = ")
    # We need: teams, journeyTiming, stageDuration
    m = re.search(r'const GSO_DATA = (\{.*?\});', main_html, re.DOTALL)
    if not m:
        print("❌ Could not find GSO_DATA block in dashboard.html")
        return
    gso_data_str = m.group(1)

    # Extract dsrFacts
    m2 = re.search(r'GSO_DATA\.dsrFacts = (\[.*?\]);\s*\n', main_html, re.DOTALL)
    if not m2:
        print("❌ Could not find GSO_DATA.dsrFacts in dashboard.html")
        return
    dsr_facts_str = m2.group(1)
    # Count records
    dsr_count = dsr_facts_str.count('"i":')
    print(f"   DSR Facts: ~{dsr_count} records")

    # Extract kickoffData
    m3 = re.search(r'GSO_DATA\.kickoffData = (\[.*?\]);\s*\n', main_html, re.DOTALL)
    kickoff_str = m3.group(1) if m3 else '[]'
    kickoff_count = kickoff_str.count('"k":')
    print(f"   Kickoff records: ~{kickoff_count}")

    # Extract the full renderNarrative JS block (lines 17652-18885 equivalent)
    # Find from "// LEAD TIME STORY TAB" to "// FORECAST TAB"
    js_start = main_html.index('// LEAD TIME STORY TAB')
    js_end = main_html.index('// FORECAST TAB', js_start)
    # Back up to include the full line
    js_start = main_html.rfind('\n', 0, js_start) + 1
    js_end = main_html.rfind('\n', 0, js_end) + 1
    narrative_js = main_html[js_start:js_end].strip()

    # Remove the tab-show listener (not needed in standalone)
    narrative_js = narrative_js.replace(
        "document.querySelectorAll('.tab-btn[data-tab=\"narrative\"]').forEach(function(btn) {\n      btn.addEventListener('click', function() { setTimeout(renderNarrative, 50); });\n    });",
        "// (tab listener removed — standalone dashboard)"
    )

    print(f"   Narrative JS: {len(narrative_js)} chars")

    now = datetime.now()
    refresh_date = now.strftime('%B %d, %Y at %I:%M %p')

    # ── Build HTML ──
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Lead Time Story — GSO Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; }}
  body {{ background: #f8fafc; }}
  .prose p {{ margin-bottom: 0.75em; }}
  .prose strong {{ color: #1e293b; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ background: white; }}
  }}
</style>
</head>
<body class="min-h-screen">

<!-- Sticky Header -->
<div class="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50 no-print">
  <div class="max-w-4xl mx-auto px-4 py-3">
    <div class="flex items-start justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-xl font-bold text-gray-900">📋 Lead Time Story</h1>
        <p class="text-sm text-gray-500 mt-1">What's driving onboarding lead time, where the opportunities are, and what we're doing about it.</p>
        <p class="text-xs text-gray-400 mt-1">Data auto-computed from live DSR records. Narrative sections are editable — click ✏️ to customize. <span id="narrativeRefreshDate"></span></p>
      </div>
      <div class="flex items-center gap-3 mt-1 flex-wrap">
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500">Time Range:</label>
          <select id="narrativeTimeRange" onchange="renderNarrative()" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-blue-200 focus:border-blue-400 outline-none">
            <option value="this_week">This Week</option>
            <option value="this_month">This Month</option>
            <option value="last_month">Last Month</option>
            <option value="this_quarter">This Quarter</option>
            <option value="last_quarter">Last Quarter</option>
            <option value="last_90" selected>Last 90 Days</option>
            <option value="last_180">Last 6 Months</option>
            <option value="ytd">Year to Date</option>
            <option value="last_365">Last 12 Months</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500">Region:</label>
          <select id="narrativeRegion" onchange="renderNarrative()" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-blue-200 focus:border-blue-400 outline-none">
            <option value="all">All Regions</option>
            <option value="na">North America</option>
            <option value="au">Australia</option>
            <option value="eu">Europe</option>
            <option value="jp">Japan</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500">Country:</label>
          <select id="narrativeCountry" onchange="renderNarrative()" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-blue-200 focus:border-blue-400 outline-none">
            <option value="all">All Countries</option>
            <option value="US">US</option>
            <option value="AU">Australia</option>
            <option value="GB">UK</option>
            <option value="CA">Canada</option>
            <option value="IE">Ireland</option>
            <option value="FR">France</option>
            <option value="ES">Spain</option>
            <option value="JP">Japan</option>
          </select>
        </div>
        <div class="flex items-center gap-2 relative">
          <label class="text-xs font-medium text-gray-500">Package:</label>
          <button id="narrativePkgBtn" onclick="document.getElementById('narrativePkgDrop').classList.toggle('hidden')" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white hover:border-blue-300 focus:ring-2 focus:ring-blue-200 outline-none flex items-center gap-1">
            <span id="narrativePkgLabel">All Packages</span>
            <svg class="w-3 h-3 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/></svg>
          </button>
          <div id="narrativePkgDrop" class="hidden absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 p-2 min-w-[200px]">
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="all" checked onchange="toggleNarrativePkgAll(this)"><span class="font-medium text-gray-700">Select All</span></label>
            <div class="border-t border-gray-100 my-1"></div>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Onsite" checked onchange="updateNarrativePkg()"><span>Onsite</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Premium" checked onchange="updateNarrativePkg()"><span>Premium</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Plus" checked onchange="updateNarrativePkg()"><span>Plus</span></label>
            <div class="border-t border-gray-100 my-1"></div>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Tasks Only" checked onchange="updateNarrativePkg()"><span>Tasks Only</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Optimization Call" checked onchange="updateNarrativePkg()"><span>Optimization Call</span></label>
            <div class="border-t border-gray-100 my-1"></div>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Payroll" checked onchange="updateNarrativePkg()"><span>Payroll</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Half-day 3rd Party Vendor Install" checked onchange="updateNarrativePkg()"><span>Half-day Vendor Install</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Full-day 3rd Party Vendor Install" checked onchange="updateNarrativePkg()"><span>Full-day Vendor Install</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="In-Person Refresh" checked onchange="updateNarrativePkg()"><span>In-Person Refresh</span></label>
            <label class="flex items-center gap-2 px-2 py-1 hover:bg-gray-50 rounded text-xs cursor-pointer"><input type="checkbox" class="narrative-pkg-cb" value="Appointments Migration + Training" checked onchange="updateNarrativePkg()"><span>Appts Migration + Training</span></label>
            <div class="border-t border-gray-100 my-1"></div>
            <div class="flex gap-2 px-2 pt-1">
              <button onclick="setNarrativePkgPreset('handsOn')" class="text-[10px] px-2 py-0.5 bg-blue-50 text-blue-700 rounded hover:bg-blue-100">Hands-On</button>
              <button onclick="setNarrativePkgPreset('fastTurn')" class="text-[10px] px-2 py-0.5 bg-green-50 text-green-700 rounded hover:bg-green-100">Fast-Turn</button>
              <button onclick="setNarrativePkgPreset('all')" class="text-[10px] px-2 py-0.5 bg-gray-50 text-gray-700 rounded hover:bg-gray-100">All</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Main Content -->
<div class="max-w-4xl mx-auto px-4 py-6">

  <!-- Section 1: What is driving lead time today -->
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-4">
    <h3 class="text-base font-bold text-gray-900 mb-1 flex items-center gap-2">
      <span class="text-lg">1</span> What is driving lead time today
    </h3>
    <p class="text-xs text-gray-400 mb-4">Current blended median and the factors behind it</p>
    <div id="narrativeS1Data" class="mb-4"></div>
    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200 relative group">
      <button onclick="editNarrative('s1')" class="absolute top-2 right-2 text-gray-300 hover:text-blue-500 text-sm opacity-0 group-hover:opacity-100 transition-opacity no-print" title="Edit">✏️</button>
      <div id="narrativeS1Text" class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none"></div>
    </div>
  </div>

  <!-- Section 2: Which parts of the flow are the biggest opportunities -->
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-4">
    <h3 class="text-base font-bold text-gray-900 mb-1 flex items-center gap-2">
      <span class="text-lg">2</span> Which parts of the flow are the biggest opportunities
    </h3>
    <p class="text-xs text-gray-400 mb-4">Ranked by potential impact on overall lead time</p>
    <div id="narrativeS2Data" class="mb-4"></div>
    <div class="bg-slate-50 rounded-lg p-4 border border-slate-200 relative group">
      <button onclick="editNarrative('s2')" class="absolute top-2 right-2 text-gray-300 hover:text-blue-500 text-sm opacity-0 group-hover:opacity-100 transition-opacity no-print" title="Edit">✏️</button>
      <div id="narrativeS2Text" class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none"></div>
    </div>
  </div>

  <!-- Section 3: Actions underway & expected impact -->
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-4">
    <h3 class="text-base font-bold text-gray-900 mb-1 flex items-center gap-2">
      <span class="text-lg">3</span> Actions underway & expected impact
    </h3>
    <p class="text-xs text-gray-400 mb-4">Initiatives mapped to each opportunity with quantified impact — <em>click ✏️ to update</em></p>
    <div id="narrativeS34Data" class="mb-4"></div>
    <div class="bg-amber-50 rounded-lg p-4 border border-amber-200 relative group">
      <button onclick="editNarrative('s3')" class="absolute top-2 right-2 text-gray-300 hover:text-blue-500 text-sm opacity-0 group-hover:opacity-100 transition-opacity no-print" title="Edit">✏️</button>
      <div id="narrativeS3Text" class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none"></div>
    </div>
  </div>

  <!-- Section 4: What this means for overall lead time -->
  <div class="bg-white rounded-xl border border-gray-200 p-6 shadow-sm mb-4">
    <h3 class="text-base font-bold text-gray-900 mb-1 flex items-center gap-2">
      <span class="text-lg">4</span> What this means for overall lead time
    </h3>
    <p class="text-xs text-gray-400 mb-4">The synthesis — where we are, where we're headed</p>
    <div id="narrativeS5Data" class="mb-4"></div>
    <div class="bg-emerald-50 rounded-lg p-4 border border-emerald-200 relative group">
      <button onclick="editNarrative('s5')" class="absolute top-2 right-2 text-gray-300 hover:text-blue-500 text-sm opacity-0 group-hover:opacity-100 transition-opacity no-print" title="Edit">✏️</button>
      <div id="narrativeS5Text" class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none"></div>
    </div>
  </div>

  <!-- Export -->
  <div class="flex items-center gap-3 mt-6 mb-8 no-print">
    <button onclick="exportNarrative()" class="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors">📥 Export Report</button>
    <button onclick="window.print()" class="border border-gray-200 hover:bg-gray-50 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors">🖨️ Print</button>
    <button onclick="resetNarrativeEdits()" class="text-xs text-gray-400 hover:text-red-500 transition-colors">Reset edits to defaults</button>
  </div>

  <!-- Footer -->
  <div class="text-center text-xs text-gray-400 py-4 border-t border-gray-200">
    GSO Lead Time Story · Data refreshed {refresh_date} · Source: Snowflake DSR records + stage history
  </div>
</div>

<script>
// ═══════════════════════════════════════════════════════
// EMBEDDED DATA
// ═══════════════════════════════════════════════════════
const GSO_DATA = {gso_data_str};
GSO_DATA.dsrFacts = {dsr_facts_str};
GSO_DATA.kickoffData = {kickoff_str};

// ═══════════════════════════════════════════════════════
// DATA EXPANSION (from main dashboard)
// ═══════════════════════════════════════════════════════
const COMPLETED_STATUSES = new Set(['Implementation Complete', 'Completed', 'Transitioned']);
const CANCELLED_STATUSES = new Set(['Rejected', 'Lost - No Seller Contact', 'Lost - Churn', 'Lost']);
const ON_HOLD_STATUSES = new Set(['On Hold']);
const DRAFT_STATUSES = new Set(['Draft']);

function classifyStatus(status) {{
  if (COMPLETED_STATUSES.has(status)) return 'completed';
  if (CANCELLED_STATUSES.has(status)) return 'cancelled';
  if (ON_HOLD_STATUSES.has(status)) return 'onHold';
  if (DRAFT_STATUSES.has(status)) return 'draft';
  return 'active';
}}

const FX_TO_USD = {{
  'JP': 0.0067, 'AU': 0.63, 'GB': 1.26, 'IE': 1.08, 'ES': 1.08, 'FR': 1.08, 'CA': 0.72
}};

function expandFact(f) {{
  const country = f.co || '';
  const rawGpv = f.g || 0;
  const fxRate = FX_TO_USD[country];
  const gpvUsd = fxRate ? Math.round(rawGpv * fxRate) : rawGpv;
  return {{
    id: f.i || '', rep: f.r || '', teamLead: f.tl || '', seller: f.s || '',
    workType: f.w || '', status: f.st || '', subStatus: f.ss || '',
    requestReason: f.rr || '', country: country, gpvUsd: gpvUsd,
    createdDate: f.cd || null, completedDate: f.cpd || null,
    goLiveDate: f.gl || null, daysToComplete: f.dtc ?? null,
    daysOpen: f.do ?? null, daysStale: f.ds ?? null,
    oppOwner: f.ao || '', oppOwnerRole: f.ar || '',
    channel: f.ch || 'other', nextStep: f.ns || '',
    nextStepDate: f.nsd || '', desiredGoLiveDate: f.dgl || '',
    numLocations: f.nl || null, complexityScore: f.cx || null,
    competitorPos: f.cp || '', assignedDate: f.ad || null,
    holdDays: f.hd ?? 0, daysAssignedExclHold: f.dae ?? null,
    category: classifyStatus(f.st || '')
  }};
}}

const DSR_FACTS = GSO_DATA.dsrFacts.map(expandFact);
const GSO_FACTS = DSR_FACTS.filter(f => f.channel !== 'bpo' && f.channel !== 'vendorops');

const ROSTER_SET = new Set();
Object.values(GSO_DATA.teams).forEach(reps => reps.forEach(r => ROSTER_SET.add(r)));
['Meaghan Biederman', 'Ben Pomeroy', 'Caleb Cunningham', 'Kamilla Warr'].forEach(r => ROSTER_SET.add(r));

// ═══════════════════════════════════════════════════════
// LEAD TIME STORY LOGIC (extracted from main dashboard)
// ═══════════════════════════════════════════════════════
{narrative_js}

// ═══════════════════════════════════════════════════════
// AUTO-RENDER ON LOAD
// ═══════════════════════════════════════════════════════
renderNarrative();
</script>
</body>
</html>'''

    out_path = os.path.join(DASH_DIR, 'leadtime_dashboard.html')
    with open(out_path, 'w') as f:
        f.write(html)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n✅ Generated leadtime_dashboard.html: {size_mb:.1f} MB")
    return out_path


if __name__ == '__main__':
    build_leadtime_dashboard()
