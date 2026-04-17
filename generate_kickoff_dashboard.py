#!/usr/bin/env python3
"""Generate standalone Kickoff Call Tracker Dashboard.

Reads kickoff_data.json (per-DSR time from creation to first consultation/kickoff call,
sourced from Snowflake stage history) and produces a single-file HTML dashboard with:
  - Time range and market filters
  - KPI summary cards per market
  - Grouped bar chart (weekly median by market)
  - Collapsible weekly detail table
  - Distribution histogram
  - Trend sparklines
"""

import json, os
from datetime import datetime

DASH_DIR = os.path.dirname(os.path.abspath(__file__))


def build_kickoff_dashboard():
    print("📊 Building Kickoff Call Tracker Dashboard...")

    kickoff_path = os.path.join(DASH_DIR, 'kickoff_data.json')
    with open(kickoff_path) as f:
        kickoff_data = json.load(f)
    print(f"   Kickoff records: {len(kickoff_data)}")

    kickoff_json = json.dumps(kickoff_data, separators=(',', ':'))
    data_kb = len(kickoff_json) / 1024
    print(f"   Data size: {data_kb:.1f} KB")

    now = datetime.now()
    refresh_date = now.strftime('%B %d, %Y at %I:%M %p')

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Time to Kickoff Call — GSO Tracker</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: 'Inter', system-ui, -apple-system, sans-serif; background: #f8fafc; }}
  .kpi-card {{ transition: transform 0.15s, box-shadow 0.15s; }}
  .kpi-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.08); }}
  details summary {{ list-style: none; }}
  details summary::-webkit-details-marker {{ display: none; }}
  @media print {{ .no-print {{ display: none !important; }} }}
</style>
</head>
<body class="min-h-screen">

<!-- Header -->
<div class="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-50">
  <div class="max-w-6xl mx-auto px-4 py-3">
    <div class="flex items-center justify-between flex-wrap gap-3">
      <div>
        <h1 class="text-lg font-bold text-gray-900">⏱️ Time to Kickoff Call</h1>
        <p class="text-xs text-gray-500">Median days from DSR creation to first consultation/kickoff call · Source: Snowflake stage history</p>
      </div>
      <div class="flex items-center gap-3 flex-wrap no-print">
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500">Time Range:</label>
          <select id="filterTimeRange" onchange="render()" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-blue-200 focus:border-blue-400 outline-none">
            <option value="last_90" selected>Last 90 Days</option>
            <option value="this_month">This Month</option>
            <option value="last_month">Last Month</option>
            <option value="this_quarter">This Quarter</option>
            <option value="last_quarter">Last Quarter</option>
            <option value="last_180">Last 6 Months</option>
            <option value="ytd">Year to Date</option>
            <option value="last_365">Last 12 Months</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div class="flex items-center gap-2">
          <label class="text-xs font-medium text-gray-500">Market:</label>
          <select id="filterMarket" onchange="render()" class="border border-gray-200 rounded-lg px-3 py-1.5 text-sm text-gray-700 bg-white focus:ring-2 focus:ring-blue-200 focus:border-blue-400 outline-none">
            <option value="all">All Markets</option>
            <option value="US/CA">🇺🇸 US/CA</option>
            <option value="AU">🇦🇺 Australia</option>
            <option value="GB">🇬🇧 UK</option>
            <option value="IE">🇮🇪 Ireland</option>
            <option value="FR">🇫🇷 France</option>
            <option value="ES">🇪🇸 Spain</option>
            <option value="JP">🇯🇵 Japan</option>
          </select>
        </div>
        <button onclick="render()" class="text-xs text-blue-600 hover:text-blue-800 font-medium">↻ Refresh</button>
      </div>
    </div>
  </div>
</div>

<!-- Main Content -->
<div class="max-w-6xl mx-auto px-4 py-6">
  <!-- KPI Cards -->
  <div id="kpiCards" class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3 mb-6"></div>

  <!-- Bar Chart -->
  <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
    <div class="flex items-center justify-between mb-3">
      <h2 class="text-sm font-semibold text-gray-700">📊 Weekly Median by Market</h2>
      <span id="chartSubtitle" class="text-xs text-gray-400"></span>
    </div>
    <div style="height:320px;"><canvas id="chartKickoff"></canvas></div>
  </div>

  <!-- Distribution + Trend Row -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
    <!-- Distribution Histogram -->
    <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-700 mb-3">📈 Distribution of Days to Kickoff</h2>
      <div style="height:240px;"><canvas id="chartDistribution"></canvas></div>
    </div>
    <!-- Monthly Trend -->
    <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm">
      <h2 class="text-sm font-semibold text-gray-700 mb-3">📉 Monthly Trend (Median)</h2>
      <div style="height:240px;"><canvas id="chartMonthly"></canvas></div>
    </div>
  </div>

  <!-- Weekly Detail Table -->
  <div class="bg-white rounded-xl border border-gray-200 p-5 shadow-sm mb-6">
    <details open>
      <summary class="text-sm font-semibold text-gray-700 cursor-pointer hover:text-blue-600 mb-3 flex items-center gap-2">
        <svg class="w-4 h-4 text-gray-400 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"/></svg>
        📋 Weekly Detail Table
      </summary>
      <div id="weeklyTable" class="overflow-x-auto"></div>
    </details>
  </div>

  <!-- Footer -->
  <div class="text-center text-xs text-gray-400 py-4">
    GSO Kickoff Call Tracker · Data refreshed {refresh_date} · Source: Snowflake DEAL_SUPPORT_REQUEST_HISTORY
  </div>
</div>

<script>
// ═══════════════════════════════════════════════════════
// DATA
// ═══════════════════════════════════════════════════════
const KICKOFF_RAW = {kickoff_json};

// ═══════════════════════════════════════════════════════
// MARKET DEFINITIONS
// ═══════════════════════════════════════════════════════
const MARKETS = {{
  'US/CA': {{ codes: new Set(['US','CA','United States','us','Us']), color: '#3b82f6', label: '🇺🇸 US/CA' }},
  'AU':    {{ codes: new Set(['AU','Au','au','Australia']),          color: '#f59e0b', label: '🇦🇺 AU' }},
  'GB':    {{ codes: new Set(['GB','UK','uk','Uk','United Kingdom']),color: '#10b981', label: '🇬🇧 UK' }},
  'IE':    {{ codes: new Set(['IE','Ie']),                          color: '#8b5cf6', label: '🇮🇪 IE' }},
  'FR':    {{ codes: new Set(['FR','Fr','fr']),                      color: '#ec4899', label: '🇫🇷 FR' }},
  'ES':    {{ codes: new Set(['ES','es']),                          color: '#f97316', label: '🇪🇸 ES' }},
  'JP':    {{ codes: new Set(['JP']),                               color: '#06b6d4', label: '🇯🇵 JP' }}
}};
const MARKET_KEYS = Object.keys(MARKETS);

function toMarket(country) {{
  const c = country || '';
  for (const [mk, def] of Object.entries(MARKETS)) {{
    if (def.codes.has(c)) return mk;
  }}
  return null;
}}

// ═══════════════════════════════════════════════════════
// HELPERS
// ═══════════════════════════════════════════════════════
function nMed(arr) {{ if (!arr.length) return null; const s = [...arr].sort((a,b)=>a-b); const m = Math.floor(s.length/2); return s.length%2 ? s[m] : (s[m-1]+s[m])/2; }}
function nP25(arr) {{ if (!arr.length) return null; const s = [...arr].sort((a,b)=>a-b); return s[Math.floor(s.length*0.25)]; }}
function nP75(arr) {{ if (!arr.length) return null; const s = [...arr].sort((a,b)=>a-b); return s[Math.floor(s.length*0.75)]; }}
function nP90(arr) {{ if (!arr.length) return null; const s = [...arr].sort((a,b)=>a-b); return s[Math.floor(s.length*0.90)]; }}
function kickoffColor(med) {{ return med <= 10 ? '#059669' : med <= 20 ? '#d97706' : '#dc2626'; }}
function round1(v) {{ return Math.round(v * 10) / 10; }}

function getTimeRange() {{
  const now = new Date();
  const val = document.getElementById('filterTimeRange').value;
  const y = now.getFullYear(), m = now.getMonth(), d = now.getDate();
  const todayStr = now.toISOString().split('T')[0];
  let start, end, label;
  switch (val) {{
    case 'this_month':
      start = new Date(y, m, 1).toISOString().split('T')[0]; end = todayStr;
      label = now.toLocaleDateString('en-US', {{ month: 'long', year: 'numeric' }}); break;
    case 'last_month': {{
      const lm = new Date(y, m-1, 1); const lmEnd = new Date(y, m, 0);
      start = lm.toISOString().split('T')[0]; end = lmEnd.toISOString().split('T')[0];
      label = lm.toLocaleDateString('en-US', {{ month: 'long', year: 'numeric' }}); break;
    }}
    case 'this_quarter': {{
      start = new Date(y, Math.floor(m/3)*3, 1).toISOString().split('T')[0]; end = todayStr;
      label = 'Q' + (Math.floor(m/3)+1) + ' ' + y; break;
    }}
    case 'last_quarter': {{
      const lqs = new Date(y, Math.floor(m/3)*3-3, 1); const lqe = new Date(y, Math.floor(m/3)*3, 0);
      start = lqs.toISOString().split('T')[0]; end = lqe.toISOString().split('T')[0];
      label = 'Q' + (Math.floor(lqs.getMonth()/3)+1) + ' ' + lqs.getFullYear(); break;
    }}
    case 'last_90':
      start = new Date(now - 90*86400000).toISOString().split('T')[0]; end = todayStr; label = 'Last 90 Days'; break;
    case 'last_180':
      start = new Date(now - 180*86400000).toISOString().split('T')[0]; end = todayStr; label = 'Last 6 Months'; break;
    case 'ytd':
      start = y + '-01-01'; end = todayStr; label = 'Year to Date (' + y + ')'; break;
    case 'last_365':
      start = new Date(now - 365*86400000).toISOString().split('T')[0]; end = todayStr; label = 'Last 12 Months'; break;
    case 'all':
      start = '2000-01-01'; end = todayStr; label = 'All Time'; break;
    default:
      start = new Date(now - 90*86400000).toISOString().split('T')[0]; end = todayStr; label = 'Last 90 Days';
  }}
  return {{ start, end, label }};
}}

// ═══════════════════════════════════════════════════════
// CHARTS (persistent references for destroy/recreate)
// ═══════════════════════════════════════════════════════
let chartKickoff = null, chartDist = null, chartMonthly = null;

// ═══════════════════════════════════════════════════════
// MAIN RENDER
// ═══════════════════════════════════════════════════════
function render() {{
  const {{ start, end, label }} = getTimeRange();
  const marketFilter = document.getElementById('filterMarket').value;

  // Filter data
  const filtered = KICKOFF_RAW.filter(r => {{
    if (!r.k || r.d == null) return false;
    if (r.k < start || r.k > end) return false;
    if (marketFilter !== 'all') {{
      const mk = toMarket(r.co);
      if (mk !== marketFilter) return false;
    }}
    return true;
  }});

  // ── Weekly buckets by market ──
  const weeklyBuckets = {{}};
  const allWeeks = new Set();
  filtered.forEach(r => {{
    const mk = toMarket(r.co);
    if (!mk) return;
    const kDate = new Date(r.k);
    const dow = (kDate.getDay() + 6) % 7;
    const mon = new Date(kDate); mon.setDate(kDate.getDate() - dow);
    const wk = mon.toISOString().split('T')[0];
    allWeeks.add(wk);
    if (!weeklyBuckets[wk]) weeklyBuckets[wk] = {{}};
    if (!weeklyBuckets[wk][mk]) weeklyBuckets[wk][mk] = [];
    weeklyBuckets[wk][mk].push(r.d);
    if (!weeklyBuckets[wk]['All']) weeklyBuckets[wk]['All'] = [];
    weeklyBuckets[wk]['All'].push(r.d);
  }});

  // Exclude current partial week
  const now = new Date();
  const curDow = (now.getDay() + 6) % 7;
  const curMon = new Date(now); curMon.setDate(now.getDate() - curDow);
  const curWeekStr = curMon.toISOString().split('T')[0];
  const weeks = [...allWeeks].sort().filter(w => w < curWeekStr);

  // ── Per-market summary ──
  const marketSummary = {{}};
  const allDays = filtered.map(r => r.d).filter(d => d != null && d >= 0 && d <= 365);
  if (allDays.length) {{
    marketSummary['All'] = {{ med: round1(nMed(allDays)), avg: round1(allDays.reduce((s,v)=>s+v,0)/allDays.length), n: allDays.length, p25: round1(nP25(allDays)), p75: round1(nP75(allDays)), p90: round1(nP90(allDays)) }};
  }}
  MARKET_KEYS.forEach(mk => {{
    const days = filtered.filter(r => toMarket(r.co) === mk).map(r => r.d).filter(d => d != null && d >= 0 && d <= 365);
    if (days.length >= 3) {{
      marketSummary[mk] = {{ med: round1(nMed(days)), avg: round1(days.reduce((s,v)=>s+v,0)/days.length), n: days.length, p25: round1(nP25(days)), p75: round1(nP75(days)), p90: round1(nP90(days)) }};
    }}
  }});

  // ── KPI Cards ──
  let kpiHtml = '';
  const sa = marketSummary['All'];
  if (sa) {{
    kpiHtml += '<div class="kpi-card bg-blue-50 rounded-xl p-4 border border-blue-100 text-center col-span-2 md:col-span-1 lg:col-span-2">' +
      '<div class="text-[10px] text-blue-600 font-semibold uppercase tracking-wider mb-1">All Markets</div>' +
      '<div class="text-3xl font-bold" style="color:' + kickoffColor(sa.med) + '">' + sa.med + 'd</div>' +
      '<div class="text-[10px] text-gray-500 mt-1">P25 ' + sa.p25 + 'd · P75 ' + sa.p75 + 'd · P90 ' + sa.p90 + 'd</div>' +
      '<div class="text-[10px] text-gray-400">' + sa.n.toLocaleString() + ' kickoff calls · avg ' + sa.avg + 'd</div>' +
      '</div>';
  }}
  const activeMarkets = MARKET_KEYS.filter(mk => marketSummary[mk]);
  activeMarkets.sort((a,b) => marketSummary[b].n - marketSummary[a].n);
  activeMarkets.forEach(mk => {{
    const s = marketSummary[mk];
    const def = MARKETS[mk];
    kpiHtml += '<div class="kpi-card bg-white rounded-xl p-3 border border-gray-200 text-center">' +
      '<div class="text-[10px] text-gray-500 font-semibold uppercase tracking-wider mb-1">' + def.label + '</div>' +
      '<div class="text-2xl font-bold" style="color:' + kickoffColor(s.med) + '">' + s.med + 'd</div>' +
      '<div class="text-[10px] text-gray-400 mt-1">avg ' + s.avg + 'd · n=' + s.n.toLocaleString() + '</div>' +
      '</div>';
  }});
  document.getElementById('kpiCards').innerHTML = kpiHtml;

  // ── Weekly chart data ──
  const chartData = {{}};
  MARKET_KEYS.forEach(mk => {{ chartData[mk] = []; }});
  weeks.forEach(wk => {{
    MARKET_KEYS.forEach(mk => {{
      const arr = (weeklyBuckets[wk] || {{}})[mk] || [];
      chartData[mk].push(arr.length >= 2 ? round1(nMed(arr)) : null);
    }});
  }});

  // ── Bar Chart ──
  if (chartKickoff) {{ chartKickoff.destroy(); chartKickoff = null; }}
  const canvas = document.getElementById('chartKickoff');
  if (canvas && weeks.length >= 1) {{
    const labels = weeks.map(w => {{
      const d = new Date(w);
      return d.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }});
    }});
    const datasets = [];
    // If a single market is selected, show just that market
    const marketsToShow = marketFilter !== 'all' ? [marketFilter] : activeMarkets;
    marketsToShow.forEach(mk => {{
      if (!marketSummary[mk]) return;
      const def = MARKETS[mk];
      datasets.push({{
        label: def.label,
        data: chartData[mk],
        backgroundColor: def.color + 'CC',
        borderColor: def.color,
        borderWidth: 1,
        borderRadius: 3,
        barPercentage: 0.85,
        categoryPercentage: marketsToShow.length <= 3 ? 0.7 : 0.85
      }});
    }});
    // Target line
    datasets.push({{
      label: 'Target (10d)',
      data: weeks.map(() => 10),
      type: 'line',
      borderColor: 'rgba(16,185,129,0.6)',
      borderWidth: 2,
      borderDash: [6, 4],
      fill: false,
      pointRadius: 0,
      pointHitRadius: 0,
      order: 0
    }});
    document.getElementById('chartSubtitle').textContent = label + ' · ' + filtered.length.toLocaleString() + ' kickoff calls';
    chartKickoff = new Chart(canvas, {{
      type: 'bar',
      data: {{ labels, datasets }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ display: true, position: 'top', labels: {{ font: {{ size: 11 }}, usePointStyle: true, padding: 10, boxWidth: 10 }} }},
          tooltip: {{ mode: 'index', intersect: false, callbacks: {{ label: ctx => ctx.raw == null ? null : ctx.dataset.label + ': ' + ctx.raw + 'd median' }} }}
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }}, maxRotation: 45 }} }},
          y: {{ beginAtZero: true, suggestedMax: 30, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }}, callback: v => v + 'd', stepSize: 5 }}, title: {{ display: true, text: 'Median Days to Kickoff', font: {{ size: 10 }} }} }}
        }}
      }}
    }});
  }}

  // ── Distribution Histogram ──
  if (chartDist) {{ chartDist.destroy(); chartDist = null; }}
  const distCanvas = document.getElementById('chartDistribution');
  if (distCanvas && allDays.length > 0) {{
    const buckets = [0,0,0,0,0,0,0,0]; // 0-3, 4-7, 8-14, 15-21, 22-30, 31-45, 46-60, 60+
    const bucketLabels = ['0-3d','4-7d','8-14d','15-21d','22-30d','31-45d','46-60d','60+d'];
    const bucketColors = ['#059669','#10b981','#34d399','#fbbf24','#f59e0b','#f97316','#ef4444','#dc2626'];
    allDays.forEach(d => {{
      if (d <= 3) buckets[0]++;
      else if (d <= 7) buckets[1]++;
      else if (d <= 14) buckets[2]++;
      else if (d <= 21) buckets[3]++;
      else if (d <= 30) buckets[4]++;
      else if (d <= 45) buckets[5]++;
      else if (d <= 60) buckets[6]++;
      else buckets[7]++;
    }});
    chartDist = new Chart(distCanvas, {{
      type: 'bar',
      data: {{
        labels: bucketLabels,
        datasets: [{{ data: buckets, backgroundColor: bucketColors, borderRadius: 4, barPercentage: 0.8 }}]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        plugins: {{
          legend: {{ display: false }},
          tooltip: {{ callbacks: {{ label: ctx => ctx.raw + ' DSRs (' + (allDays.length > 0 ? Math.round(ctx.raw/allDays.length*100) : 0) + '%)' }} }}
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 10 }} }} }},
          y: {{ beginAtZero: true, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 10 }} }}, title: {{ display: true, text: 'DSR Count', font: {{ size: 10 }} }} }}
        }}
      }},
      plugins: [{{
        id: 'barPctLabels',
        afterDatasetsDraw: function(chart) {{
          const ctx = chart.ctx;
          chart.data.datasets[0].data.forEach((val, i) => {{
            if (val === 0) return;
            const meta = chart.getDatasetMeta(0).data[i];
            const pct = allDays.length > 0 ? Math.round(val/allDays.length*100) : 0;
            ctx.save();
            ctx.fillStyle = '#374151';
            ctx.font = 'bold 10px Inter, sans-serif';
            ctx.textAlign = 'center';
            ctx.fillText(pct + '%', meta.x, meta.y - 6);
            ctx.restore();
          }});
        }}
      }}]
    }});
  }}

  // ── Monthly Trend ──
  if (chartMonthly) {{ chartMonthly.destroy(); chartMonthly = null; }}
  const monthlyCanvas = document.getElementById('chartMonthly');
  if (monthlyCanvas && filtered.length > 0) {{
    const monthlyBuckets = {{}};
    filtered.forEach(r => {{
      if (!r.k || r.d == null) return;
      const mo = r.k.substring(0, 7);
      if (!monthlyBuckets[mo]) monthlyBuckets[mo] = [];
      monthlyBuckets[mo].push(r.d);
    }});
    const months = Object.keys(monthlyBuckets).sort();
    const mLabels = months.map(mo => new Date(mo + '-15').toLocaleDateString('en-US', {{ month: 'short', year: '2-digit' }}));
    const mMedData = months.map(mo => round1(nMed(monthlyBuckets[mo])));
    const mP75Data = months.map(mo => round1(nP75(monthlyBuckets[mo])));
    const mCounts = months.map(mo => monthlyBuckets[mo].length);
    chartMonthly = new Chart(monthlyCanvas, {{
      type: 'line',
      data: {{
        labels: mLabels,
        datasets: [
          {{ label: 'Median', data: mMedData, borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.08)', borderWidth: 2.5, fill: true, tension: 0.3, pointRadius: 4, pointBackgroundColor: mMedData.map(v => kickoffColor(v)), pointBorderColor: '#fff', pointBorderWidth: 2 }},
          {{ label: 'P75', data: mP75Data, borderColor: 'rgba(245,158,11,0.5)', borderWidth: 1.5, borderDash: [5,3], fill: false, tension: 0.3, pointRadius: 3, pointBackgroundColor: 'rgba(245,158,11,0.5)' }},
          {{ label: 'Volume', data: mCounts, type: 'bar', backgroundColor: 'rgba(209,213,219,0.3)', borderRadius: 3, yAxisID: 'y1', order: 3 }},
          {{ label: 'Target (10d)', data: months.map(() => 10), borderColor: 'rgba(16,185,129,0.4)', borderWidth: 1.5, borderDash: [3,3], fill: false, pointRadius: 0, order: 4 }}
        ]
      }},
      options: {{
        responsive: true, maintainAspectRatio: false,
        interaction: {{ mode: 'index', intersect: false }},
        plugins: {{
          legend: {{ display: true, labels: {{ font: {{ size: 10 }}, usePointStyle: true, padding: 8 }} }},
          tooltip: {{ mode: 'index', intersect: false }}
        }},
        scales: {{
          x: {{ grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }} }} }},
          y: {{ beginAtZero: true, suggestedMax: 30, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ font: {{ size: 9 }}, callback: v => v + 'd' }}, title: {{ display: true, text: 'Days', font: {{ size: 9 }} }} }},
          y1: {{ position: 'right', beginAtZero: true, grid: {{ display: false }}, ticks: {{ font: {{ size: 9 }} }}, title: {{ display: true, text: 'Volume', font: {{ size: 9 }} }} }}
        }}
      }}
    }});
  }}

  // ── Weekly Detail Table ──
  let tableHtml = '';
  if (weeks.length > 0) {{
    const visibleMarkets = activeMarkets.filter(mk => marketFilter === 'all' || mk === marketFilter);
    tableHtml += '<table class="w-full text-xs border-collapse"><thead><tr class="bg-gray-50 text-gray-500 uppercase tracking-wide text-[10px]">';
    tableHtml += '<th class="text-left py-2 px-3 sticky left-0 bg-gray-50 z-10">Week</th>';
    tableHtml += '<th class="text-right py-2 px-3 font-semibold">All</th>';
    visibleMarkets.forEach(mk => {{
      tableHtml += '<th class="text-right py-2 px-3">' + MARKETS[mk].label + '</th>';
    }});
    tableHtml += '<th class="text-right py-2 px-3 text-gray-400">n</th>';
    tableHtml += '</tr></thead><tbody>';
    [...weeks].reverse().forEach(wk => {{
      const wkDate = new Date(wk);
      const wkLabel = wkDate.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }});
      const wkEnd = new Date(wkDate); wkEnd.setDate(wkDate.getDate() + 6);
      const wkEndLabel = wkEnd.toLocaleDateString('en-US', {{ month: 'short', day: 'numeric' }});
      const allArr = (weeklyBuckets[wk] || {{}})['All'] || [];
      const allMed = allArr.length >= 2 ? round1(nMed(allArr)) : (allArr.length === 1 ? allArr[0] : null);
      tableHtml += '<tr class="border-b border-gray-100 hover:bg-gray-50">';
      tableHtml += '<td class="py-1.5 px-3 text-gray-700 whitespace-nowrap sticky left-0 bg-white z-10 font-medium">' + wkLabel + ' – ' + wkEndLabel + '</td>';
      if (allMed != null) {{
        tableHtml += '<td class="text-right py-1.5 px-3 font-semibold" style="color:' + kickoffColor(allMed) + '">' + allMed + 'd</td>';
      }} else {{
        tableHtml += '<td class="text-right py-1.5 px-3 text-gray-300">—</td>';
      }}
      visibleMarkets.forEach(mk => {{
        const arr = (weeklyBuckets[wk] || {{}})[mk] || [];
        if (arr.length >= 2) {{
          const med = round1(nMed(arr));
          tableHtml += '<td class="text-right py-1.5 px-3" style="color:' + kickoffColor(med) + '">' + med + 'd <span class="text-gray-400">(' + arr.length + ')</span></td>';
        }} else if (arr.length === 1) {{
          tableHtml += '<td class="text-right py-1.5 px-3 text-gray-400">' + arr[0] + 'd (1)</td>';
        }} else {{
          tableHtml += '<td class="text-right py-1.5 px-3 text-gray-300">—</td>';
        }}
      }});
      tableHtml += '<td class="text-right py-1.5 px-3 text-gray-400">' + allArr.length + '</td>';
      tableHtml += '</tr>';
    }});
    tableHtml += '</tbody></table>';
  }} else {{
    tableHtml = '<p class="text-sm text-gray-400 text-center py-8">No data for the selected filters.</p>';
  }}
  document.getElementById('weeklyTable').innerHTML = tableHtml;
}}

// Initial render
render();
</script>
</body>
</html>"""

    out_path = os.path.join(DASH_DIR, 'kickoff_dashboard.html')
    with open(out_path, 'w') as f:
        f.write(html)

    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n✅ Generated kickoff_dashboard.html: {size_mb:.1f} MB")
    return out_path


if __name__ == '__main__':
    build_kickoff_dashboard()
