#!/usr/bin/env python3
"""Generate standalone AE Dashboard — a kanban-style project tracker for Sales AEs and leaders."""

import json, os, html as html_mod
from datetime import datetime

DASH_DIR = os.path.dirname(os.path.abspath(__file__))

def esc(s):
    return html_mod.escape(str(s)) if s else ''

def build_ae_dashboard():
    print("📊 Building AE Sales Dashboard...")

    # Load data files
    dsr_path = os.path.join(DASH_DIR, 'dsr_facts.json')
    dsa_path = os.path.join(DASH_DIR, 'dsa_records.json')
    bpo_path = os.path.join(DASH_DIR, 'bpo_activities.json')
    csat_path = os.path.join(DASH_DIR, 'csat_data.json')

    with open(dsr_path) as f:
        dsrs = json.load(f)
    print(f"   DSR Facts: {len(dsrs)}")

    dsa_data = []
    if os.path.exists(dsa_path):
        with open(dsa_path) as f:
            dsa_data = json.load(f)
    print(f"   DSA Records: {len(dsa_data)}")

    bpo_data = []
    if os.path.exists(bpo_path):
        with open(bpo_path) as f:
            bpo_data = json.load(f)
    print(f"   BPO Activities: {len(bpo_data)}")

    csat_data = []
    if os.path.exists(csat_path):
        with open(csat_path) as f:
            csat_data = json.load(f)
    print(f"   CSAT Responses: {len(csat_data)}")

    # Embed data
    dsr_json = json.dumps(dsrs, separators=(',', ':'))
    dsa_json = json.dumps(dsa_data, separators=(',', ':'))
    bpo_json = json.dumps(bpo_data, separators=(',', ':'))
    csat_json = json.dumps(csat_data, separators=(',', ':'))

    total_mb = (len(dsr_json) + len(dsa_json) + len(bpo_json) + len(csat_json)) / 1024 / 1024
    print(f"   Total embedded data: {total_mb:.1f} MB")

    today = datetime.now().strftime('%Y-%m-%d')
    nl = '\n'

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GSO Sales AE Dashboard — Project Tracker</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#f1f5f9;color:#0f172a;}}
.header{{background:linear-gradient(135deg,#1e293b 0%,#334155 100%);color:#fff;padding:16px 24px;position:sticky;top:0;z-index:100;}}
.header h1{{font-size:1.25rem;font-weight:700;}}
.header p{{font-size:0.75rem;color:#94a3b8;margin-top:2px;}}
.controls{{display:flex;gap:10px;flex-wrap:wrap;align-items:center;padding:12px 24px;background:#fff;border-bottom:1px solid #e2e8f0;position:sticky;top:56px;z-index:99;}}
.controls select,.controls input{{font-size:0.8rem;padding:6px 10px;border:1px solid #cbd5e1;border-radius:6px;background:#fff;}}
.controls select{{max-width:220px;}}
.controls input{{width:200px;}}
.legend{{margin-left:auto;font-size:0.7rem;color:#64748b;display:flex;gap:8px;align-items:center;}}
.legend span{{display:inline-flex;align-items:center;gap:3px;}}
.legend .dot{{width:8px;height:8px;border-radius:50%;}}
.tab-bar{{display:flex;gap:0;background:#fff;border-bottom:1px solid #e2e8f0;padding:0 24px;position:sticky;top:104px;z-index:98;}}
.tab-btn{{padding:10px 20px;font-size:0.8rem;font-weight:600;color:#64748b;cursor:pointer;border:none;background:none;border-bottom:2px solid transparent;}}
.tab-btn:hover{{color:#1e293b;}}
.tab-btn.active{{color:#4f46e5;border-bottom-color:#4f46e5;}}
.tab-content{{display:none;padding:20px 24px;}}
.tab-content.active{{display:block;}}
.card{{background:#fff;border-radius:10px;border:1px solid #e2e8f0;padding:16px;margin-bottom:16px;}}
.card h3{{font-size:0.9rem;font-weight:700;margin-bottom:8px;}}
.kpi-row{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;margin-bottom:16px;}}
.kpi{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px;text-align:center;}}
.kpi .val{{font-size:1.4rem;font-weight:800;color:#1e293b;}}
.kpi .label{{font-size:0.65rem;color:#64748b;text-transform:uppercase;margin-top:2px;}}
.kpi.green .val{{color:#16a34a;}}
.kpi.yellow .val{{color:#ca8a04;}}
.kpi.red .val{{color:#dc2626;}}
.kpi.blue .val{{color:#4f46e5;}}
.tracker-board{{display:flex;gap:12px;overflow-x:auto;padding-bottom:16px;min-height:400px;}}
.tracker-col{{min-width:220px;max-width:260px;flex-shrink:0;}}
.tracker-col-header{{display:flex;align-items:center;justify-content:space-between;padding:8px 10px;background:#f8fafc;border-radius:8px 8px 0 0;border:1px solid #e2e8f0;border-bottom:none;}}
.tracker-col-title{{font-size:0.72rem;font-weight:700;color:#334155;}}
.tracker-col-badge{{font-size:0.65rem;font-weight:700;color:#fff;padding:2px 8px;border-radius:10px;}}
.tracker-health-bar{{display:flex;height:3px;border-radius:2px;overflow:hidden;margin:0 1px;}}
.tracker-cards{{border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;padding:6px;max-height:600px;overflow-y:auto;background:#fafbfc;}}
.tracker-card{{background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;margin-bottom:6px;cursor:pointer;border-left:3px solid #22c55e;transition:box-shadow 0.15s;}}
.tracker-card:hover{{box-shadow:0 2px 8px rgba(0,0,0,0.1);}}
.tracker-card-yellow{{border-left-color:#eab308;}}
.tracker-card-red{{border-left-color:#ef4444;}}
.tracker-card-seller{{font-size:0.78rem;font-weight:700;color:#0f172a;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.tracker-card-meta{{font-size:0.65rem;color:#64748b;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
.tracker-card-stale{{font-size:0.65rem;font-weight:600;}}
table{{width:100%;border-collapse:collapse;font-size:0.78rem;}}
th{{background:#f8fafc;font-weight:600;text-align:left;padding:8px 10px;border-bottom:2px solid #e2e8f0;cursor:pointer;}}
td{{padding:7px 10px;border-bottom:1px solid #f1f5f9;}}
tr:hover td{{background:#f8fafc;}}
.badge{{display:inline-block;padding:2px 8px;border-radius:10px;font-size:0.65rem;font-weight:600;}}
.badge-green{{background:#dcfce7;color:#166534;}}
.badge-yellow{{background:#fef9c3;color:#854d0e;}}
.badge-red{{background:#fee2e2;color:#991b1b;}}
.badge-blue{{background:#dbeafe;color:#1e40af;}}
.badge-gray{{background:#f1f5f9;color:#475569;}}
/* Seller Detail Modal */
.sd-overlay{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;overflow-y:auto;}}
.sd-overlay.active{{display:flex;justify-content:center;padding:40px 20px;}}
.sd-panel{{background:#fff;border-radius:12px;max-width:900px;width:100%;max-height:90vh;overflow-y:auto;padding:24px;position:relative;}}
.sd-close{{position:absolute;top:12px;right:16px;font-size:1.5rem;cursor:pointer;color:#64748b;background:none;border:none;}}
.sd-hero{{display:flex;flex-wrap:wrap;gap:10px;margin:12px 0;}}
.sd-kpi{{background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 14px;text-align:center;min-width:100px;}}
.sd-kpi .val{{font-size:1.1rem;font-weight:800;}}
.sd-kpi .label{{font-size:0.6rem;color:#64748b;text-transform:uppercase;}}
.sd-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:8px;margin:12px 0;}}
.sd-field{{background:#f8fafc;border-radius:6px;padding:8px 10px;}}
.sd-field .fl{{font-size:0.6rem;color:#94a3b8;text-transform:uppercase;}}
.sd-field .fv{{font-size:0.8rem;font-weight:600;color:#1e293b;word-break:break-word;}}
.sd-timeline{{display:flex;align-items:center;gap:0;margin:16px 0;overflow-x:auto;padding:10px 0;}}
.sd-stage{{display:flex;flex-direction:column;align-items:center;min-width:70px;}}
.sd-dot{{width:14px;height:14px;border-radius:50%;border:2px solid #cbd5e1;background:#fff;}}
.sd-dot.done{{background:#22c55e;border-color:#22c55e;}}
.sd-dot.current{{background:#4f46e5;border-color:#4f46e5;animation:pulse 2s infinite;}}
.sd-line{{flex:1;height:2px;background:#e2e8f0;min-width:20px;}}
.sd-line.done{{background:#22c55e;}}
@keyframes pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.5;}}}}
.export-group{{position:relative;display:inline-block;}}
.export-btn{{font-size:0.75rem;padding:6px 12px;background:#4f46e5;color:#fff;border:none;border-radius:6px;cursor:pointer;font-weight:600;}}
.export-btn:hover{{background:#4338ca;}}
.export-menu{{display:none;position:absolute;top:100%;right:0;background:#fff;border:1px solid #e2e8f0;border-radius:8px;box-shadow:0 4px 12px rgba(0,0,0,0.1);z-index:50;min-width:140px;margin-top:4px;}}
.export-menu.show{{display:block;}}
.export-menu button{{display:block;width:100%;text-align:left;padding:8px 14px;border:none;background:none;font-size:0.78rem;cursor:pointer;}}
.export-menu button:hover{{background:#f1f5f9;}}
</style>
</head>
<body>

<div class="header">
  <h1>📊 GSO Sales AE Dashboard — Project Tracker</h1>
  <p>Where are my sellers in the onboarding journey? · Last refreshed: {today}</p>
</div>

<div class="controls">
  <select id="roleFilter"><option value="">All Sales Teams</option></select>
  <select id="aeFilter"><option value="">All AEs</option></select>
  <select id="maxStale">
    <option value="">No Stale Limit</option>
    <option value="14">Hide &gt; 14d stale</option>
    <option value="30">Hide &gt; 30d stale</option>
    <option value="60" selected>Hide &gt; 60d stale</option>
    <option value="90">Hide &gt; 90d stale</option>
    <option value="180">Hide &gt; 180d stale</option>
  </select>
  <input type="text" id="searchBox" placeholder="Search seller, AE, or rep...">
  <select id="sortBy">
    <option value="stale">Most Stale First</option>
    <option value="open">Longest Open First</option>
    <option value="gpv">Highest GPV First</option>
    <option value="recent">Most Recent First</option>
  </select>
  <div class="legend">
    <span><span class="dot" style="background:#22c55e;"></span> Fresh (&lt;7d)</span>
    <span><span class="dot" style="background:#eab308;"></span> Aging (7-14d)</span>
    <span><span class="dot" style="background:#ef4444;"></span> Stale (&gt;14d)</span>
  </div>
</div>

<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('projects')">My Projects</button>
  <button class="tab-btn" onclick="switchTab('pipeline')">Pipeline</button>
  <button class="tab-btn" onclick="switchTab('completed')">Completed</button>
</div>

<div id="tab-projects" class="tab-content active">
  <div class="kpi-row" id="kpiRow"></div>
  <div style="display:flex;justify-content:flex-end;margin-bottom:8px;">
    <div class="export-group">
      <button class="export-btn" onclick="toggleMenu('trackerMenu')">📥 Export ▾</button>
      <div class="export-menu" id="trackerMenu">
        <button onclick="exportData('tracker','csv')">📄 CSV</button>
        <button onclick="exportData('tracker','excel')">📊 Excel</button>
        <button onclick="exportData('tracker','pdf')">📑 PDF</button>
      </div>
    </div>
  </div>
  <div class="tracker-board" id="trackerBoard"></div>
</div>

<div id="tab-pipeline" class="tab-content">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <h3>Active Pipeline</h3>
      <div class="export-group">
        <button class="export-btn" onclick="toggleMenu('pipelineMenu')">📥 Export ▾</button>
        <div class="export-menu" id="pipelineMenu">
          <button onclick="exportData('pipeline','csv')">📄 CSV</button>
          <button onclick="exportData('pipeline','excel')">📊 Excel</button>
          <button onclick="exportData('pipeline','pdf')">📑 PDF</button>
        </div>
      </div>
    </div>
    <table id="pipelineTable"><thead><tr>
      <th>Seller</th><th>GSO Rep</th><th>Status</th><th>Next Step</th><th>Go-Live</th><th>Days Open</th><th>Stale</th><th>GPV</th><th>Work Type</th>
    </tr></thead><tbody></tbody></table>
  </div>
</div>

<div id="tab-completed" class="tab-content">
  <div class="card">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
      <h3>Recently Completed (Last 90 Days)</h3>
      <div class="export-group">
        <button class="export-btn" onclick="toggleMenu('completedMenu')">📥 Export ▾</button>
        <div class="export-menu" id="completedMenu">
          <button onclick="exportData('completed','csv')">📄 CSV</button>
          <button onclick="exportData('completed','excel')">📊 Excel</button>
          <button onclick="exportData('completed','pdf')">📑 PDF</button>
        </div>
      </div>
    </div>
    <table id="completedTable"><thead><tr>
      <th>Seller</th><th>GSO Rep</th><th>Completed</th><th>Days to Complete</th><th>GPV</th><th>Work Type</th>
    </tr></thead><tbody></tbody></table>
  </div>
</div>

<!-- Seller Detail Modal -->
<div class="sd-overlay" id="sellerModal">
  <div class="sd-panel" id="sellerPanel">
    <button class="sd-close" onclick="closeDetail()">&times;</button>
    <div id="sellerContent"></div>
  </div>
</div>

<script>
// ============================================================
// EMBEDDED DATA
// ============================================================
var GSO_DATA = {{}};
GSO_DATA.dsrFacts = {dsr_json};
GSO_DATA.dsaRecords = {dsa_json};
GSO_DATA.bpoActivities = {bpo_json};
GSO_DATA.csatResponses = {csat_json};

// ============================================================
// DATA PROCESSING
// ============================================================
var SF_BASE='https://squareinc.lightning.force.com/lightning/r/';
function sfUrl(id){{return SF_BASE+id+'/view';}}

var TERMINAL=new Set(['Implementation Complete','Transitioned','Completed','Rejected','Lost','Lost - No Seller Contact','Lost - Churn','Draft']);

function classify(st){{
  if(!st||st==='Draft')return 'draft';
  if(['Implementation Complete','Transitioned','Completed'].includes(st))return 'completed';
  if(['Rejected','Lost','Lost - No Seller Contact','Lost - Churn'].includes(st))return 'cancelled';
  if(st==='On Hold')return 'onHold';
  return 'active';
}}

function esc(s){{return s?String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'):'';}}
function fmtUSD(v){{if(!v)return'';v=Number(v);if(v>=1e6)return'$'+(v/1e6).toFixed(1)+'M';if(v>=1e3)return'$'+(v/1e3).toFixed(0)+'K';return'$'+v;}}

// Expand compressed facts
var ALL_FACTS=GSO_DATA.dsrFacts.map(function(r){{
  r.id=r.id||r.i||'';r.rep=r.rep||r.r||'';r.teamLead=r.teamLead||r.tl||'';
  r.seller=r.seller||r.s||'';r.workType=r.workType||r.w||'';
  r.status=r.status||r.st||'';r.subStatus=r.subStatus||r.ss||'';
  r.country=r.country||r.co||'';r.channel=r.channel||r.ch||'';
  r.createdDate=r.createdDate||r.cd||'';r.completedDate=r.completedDate||r.cpd||'';
  r.goLiveDate=r.goLiveDate||r.gl||'';
  r.nextStep=r.nextStep||r.ns||'';r.nextStepDate=r.nextStepDate||r.nsd||'';
  r.desiredGoLiveDate=r.desiredGoLiveDate||r.dgl||'';
  r.daysOpen=r.daysOpen!=null?r.daysOpen:r.do_!=null?r.do_:r['do']!=null?r['do']:null;
  r.daysToComplete=r.daysToComplete!=null?r.daysToComplete:r.dtc!=null?r.dtc:null;
  r.daysStale=r.daysStale!=null?r.daysStale:r.ds!=null?r.ds:null;
  r.gpvUsd=r.gpvUsd!=null?r.gpvUsd:r.g!=null?r.g:null;
  r.oppOwner=r.oppOwner||r.ao||r.oo||'';r.oppOwnerRole=r.oppOwnerRole||r.ar||r.oor||'';
  r.requestReason=r.requestReason||r.rr||'';r.competitorPos=r.competitorPos||r.cp||'';
  r.complexityScore=r.complexityScore!=null?r.complexityScore:r.cx!=null?r.cx:null;
  r.numLocations=r.numLocations!=null?r.numLocations:r.nl!=null?r.nl:null;
  r.category=classify(r.status);
  return r;
}});

// Build DSA lookup
var _dsaByDsr={{}};
(GSO_DATA.dsaRecords||[]).forEach(function(d){{if(d.dr){{if(!_dsaByDsr[d.dr])_dsaByDsr[d.dr]=[];_dsaByDsr[d.dr].push(d);}} }});
(GSO_DATA.bpoActivities||[]).forEach(function(d){{if(d.dr){{if(!_dsaByDsr[d.dr])_dsaByDsr[d.dr]=[];_dsaByDsr[d.dr].push(d);}} }});

// ============================================================
// NEXT STEP DETECTION
// ============================================================
var SCHED_ST=new Set(['Tech Scheduled','Dispatch Submitted','Dispatch Acknowledged','Dispatch Accepted',
  'Kickoff Call Pending','Received Seller Availability','Pending Seller Availability','In Progress','Initiating','Assigned','Reviewing']);
var NEXT_MAP={{
  'Submitted':'Assign to rep','Assigned':'Seller outreach','Seller Outreach Complete':'Schedule consultation',
  'Consultation Complete':'Schedule first call','First Call Complete':'Dashboard training',
  'Dashboard Training Complete':'App training','App Training Complete':'SO training',
  'SO Training Complete':'Post-impl training','Trainings Complete - Post Implementation':'Go live',
  '3P Service In Progress':'Awaiting partner','Task In Progress':'Complete task',
  '1st Q&A Completed':'2nd Q&A','2nd Q&A Completed':'Implementation complete'
}};

function getNextStep(f){{
  var sfNext=f.nextStep||'';
  if(sfNext)return{{text:sfNext,status:'',date:f.nextStepDate||'',type:'sfdc'}};
  var dsas=_dsaByDsr[f.id]||[];
  var upcoming=dsas.filter(function(d){{return SCHED_ST.has(d.st||'');}});
  if(upcoming.length>0){{
    upcoming.sort(function(a,b){{return(b.cd||'')>(a.cd||'')?1:-1;}});
    var nx=upcoming[0];
    return{{text:nx.at||'Activity',status:(nx.st||'').replace('Tech ','').replace('Dispatch ',''),date:nx.sd||'',type:'scheduled'}};
  }}
  var ss=f.subStatus||'';
  if(ss&&ss!=='None'){{
    if(ss.includes('Missing Info'))return{{text:'Missing info needed',status:'',date:'',type:'blocked'}};
    if(ss.includes('Non-Responsive'))return{{text:'Seller non-responsive',status:'',date:'',type:'blocked'}};
    if(ss.includes('Waiting on AE'))return{{text:'Waiting on AE',status:'',date:'',type:'blocked'}};
    if(ss.includes('Site')||ss.includes('Premise'))return{{text:'Site work needed',status:'',date:'',type:'blocked'}};
    if(ss.includes('Product Blocker'))return{{text:'Product blocker',status:'',date:'',type:'blocked'}};
    if(ss.includes('Pushed Live'))return{{text:'Seller pushed date',status:'',date:'',type:'waiting'}};
    if(ss.includes('Timeline'))return{{text:'Timeline TBD',status:'',date:'',type:'waiting'}};
    return{{text:ss,status:'',date:'',type:'info'}};
  }}
  var implied=NEXT_MAP[f.status];
  if(implied)return{{text:implied,status:'',date:'',type:'next'}};
  return null;
}}

// ============================================================
// FILTERS
// ============================================================
function getFiltered(){{
  var role=document.getElementById('roleFilter').value;
  var ae=document.getElementById('aeFilter').value;
  var maxStale=parseInt(document.getElementById('maxStale').value||'0',10);
  var search=(document.getElementById('searchBox').value||'').toLowerCase();
  
  return ALL_FACTS.filter(function(f){{
    if(role&&f.oppOwnerRole!==role)return false;
    if(ae&&f.oppOwner!==ae)return false;
    if(maxStale&&f.daysStale>maxStale)return false;
    if(search){{
      var hay=(f.seller+' '+f.oppOwner+' '+f.rep+' '+f.workType).toLowerCase();
      if(hay.indexOf(search)<0)return false;
    }}
    return true;
  }});
}}

// ============================================================
// POPULATE FILTERS
// ============================================================
function populateFilters(){{
  var active=ALL_FACTS.filter(function(f){{return f.category==='active'||f.category==='onHold';}});
  
  // Roles
  var roleCounts={{}};
  active.forEach(function(f){{var r=f.oppOwnerRole||'Unknown';roleCounts[r]=(roleCounts[r]||0)+1;}});
  var roleSelect=document.getElementById('roleFilter');
  var curRole=roleSelect.value;
  roleSelect.innerHTML='<option value="">All Sales Teams ('+active.length+')</option>';
  Object.keys(roleCounts).sort().forEach(function(r){{
    var opt=document.createElement('option');opt.value=r;opt.textContent=r+' ('+roleCounts[r]+')';
    if(r===curRole)opt.selected=true;
    roleSelect.appendChild(opt);
  }});
  
  // AEs — filtered by role
  var aeCounts={{}};
  active.forEach(function(f){{
    if(curRole&&f.oppOwnerRole!==curRole)return;
    var a=f.oppOwner||'Unknown';aeCounts[a]=(aeCounts[a]||0)+1;
  }});
  var aeSelect=document.getElementById('aeFilter');
  var curAe=aeSelect.value;
  var total=Object.values(aeCounts).reduce(function(a,b){{return a+b;}},0);
  aeSelect.innerHTML='<option value="">All AEs ('+total+')</option>';
  Object.keys(aeCounts).sort().forEach(function(a){{
    var opt=document.createElement('option');opt.value=a;opt.textContent=a+' ('+aeCounts[a]+')';
    if(a===curAe)opt.selected=true;
    aeSelect.appendChild(opt);
  }});
}}

// ============================================================
// TABS
// ============================================================
function switchTab(id){{
  document.querySelectorAll('.tab-btn').forEach(function(b){{b.classList.remove('active');}});
  document.querySelectorAll('.tab-content').forEach(function(c){{c.classList.remove('active');}});
  document.getElementById('tab-'+id).classList.add('active');
  event.target.classList.add('active');
}}

// ============================================================
// RENDER: TRACKER BOARD
// ============================================================
var STAGES=['Submitted','Assigned','Seller Outreach Complete','Consultation Complete',
  'First Call Complete','Dashboard Training Complete','App Training Complete',
  'SO Training Complete','Trainings Complete - Post Implementation',
  '3P Service In Progress','Task In Progress','1st Q&A Completed','2nd Q&A Completed','On Hold'];
var STAGE_SHORT={{'Seller Outreach Complete':'Seller Outreach','Consultation Complete':'Consultation',
  'First Call Complete':'First Call','Dashboard Training Complete':'Dash Training',
  'App Training Complete':'App Training','SO Training Complete':'SO Training',
  'Trainings Complete - Post Implementation':'Post-Impl Training',
  '3P Service In Progress':'3P Service','Task In Progress':'Task In Progress',
  '1st Q&A Completed':'1st Q&A','2nd Q&A Completed':'2nd Q&A'}};

function health(ds){{return ds>14?'red':ds>7?'yellow':'green';}}

function renderTracker(){{
  var all=getFiltered();
  var active=all.filter(function(f){{return f.category==='active'||f.category==='onHold';}});
  
  var sortBy=document.getElementById('sortBy').value;
  active.sort(function(a,b){{
    if(sortBy==='stale')return(b.daysStale||0)-(a.daysStale||0);
    if(sortBy==='open')return(b.daysOpen||0)-(a.daysOpen||0);
    if(sortBy==='gpv')return(b.gpvUsd||0)-(a.gpvUsd||0);
    return(b.createdDate||'')>(a.createdDate||'')?-1:1;
  }});
  
  // Group by stage
  var byStage={{}};
  STAGES.forEach(function(s){{byStage[s]=[];}});
  active.forEach(function(f){{
    var st=f.category==='onHold'?'On Hold':f.status;
    if(!byStage[st])byStage[st]=[];
    byStage[st].push(f);
  }});
  
  // KPIs
  var onTrack=0,atRisk=0,offTrack=0,totalGpv=0;
  active.forEach(function(f){{
    totalGpv+=(f.gpvUsd||0);
    var ds=f.daysStale||0;
    if(ds<=7)onTrack++;else if(ds<=14)atRisk++;else offTrack++;
  }});
  
  var kpiHtml='<div class="kpi"><div class="val">'+active.length+'</div><div class="label">Active Projects</div></div>';
  kpiHtml+='<div class="kpi green"><div class="val">'+onTrack+'</div><div class="label">On Track</div></div>';
  kpiHtml+='<div class="kpi yellow"><div class="val">'+atRisk+'</div><div class="label">At Risk</div></div>';
  kpiHtml+='<div class="kpi red"><div class="val">'+offTrack+'</div><div class="label">Off Track</div></div>';
  kpiHtml+='<div class="kpi blue"><div class="val">'+fmtUSD(totalGpv)+'</div><div class="label">Pipeline GPV</div></div>';
  
  var completed90=all.filter(function(f){{return f.category==='completed'&&f.daysOpen!=null&&f.daysOpen<=90;}});
  kpiHtml+='<div class="kpi"><div class="val">'+completed90.length+'</div><div class="label">Completed (90d)</div></div>';
  
  document.getElementById('kpiRow').innerHTML=kpiHtml;
  
  // Board
  var board=document.getElementById('trackerBoard');
  var html='';
  window._exportActive=active;
  
  STAGES.forEach(function(st){{
    var cards=byStage[st]||[];
    if(cards.length===0)return;
    var g=0,y=0,r=0;
    cards.forEach(function(f){{var h=health(f.daysStale);if(h==='green')g++;else if(h==='yellow')y++;else r++;}});
    var total=cards.length;
    var badgeColor=r>total*0.5?'#ef4444':y+r>total*0.5?'#eab308':'#22c55e';
    html+='<div class="tracker-col"><div class="tracker-col-header"><span class="tracker-col-title">'+(STAGE_SHORT[st]||st)+'</span>';
    html+='<span class="tracker-col-badge" style="background:'+badgeColor+';">'+total+'</span></div>';
    html+='<div class="tracker-health-bar"><div style="width:'+(g/total*100)+'%;height:100%;background:#22c55e;"></div>';
    html+='<div style="width:'+(y/total*100)+'%;height:100%;background:#eab308;"></div>';
    html+='<div style="width:'+(r/total*100)+'%;height:100%;background:#ef4444;"></div></div>';
    html+='<div class="tracker-cards">';
    cards.forEach(function(f){{
      var h=health(f.daysStale);
      var cc=h==='red'?'tracker-card-red':h==='yellow'?'tracker-card-yellow':'';
      var sc=h==='red'?'color:#ef4444':h==='yellow'?'color:#ca8a04':'color:#22c55e';
      var ns=getNextStep(f);
      var goLive=f.desiredGoLiveDate||f.goLiveDate||'';
      var glHtml='';
      if(goLive){{
        var glDate=new Date(goLive+'T00:00:00');var now=new Date();
        var daysUntil=Math.round((glDate-now)/86400000);
        var glColor=daysUntil<0?'#dc2626':daysUntil<=7?'#ca8a04':'#16a34a';
        var glLabel=daysUntil<0?Math.abs(daysUntil)+'d overdue':daysUntil===0?'Today!':daysUntil+'d away';
        glHtml='<div style="font-size:10px;font-weight:600;margin-top:2px;color:'+glColor+';white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="Go-live: '+esc(goLive)+'">🎯 '+esc(goLive)+' · '+glLabel+'</div>';
      }}
      var nsHtml='';
      if(ns){{
        var icon=ns.type==='sfdc'?'📋':ns.type==='scheduled'?'📅':ns.type==='blocked'?'🚫':ns.type==='waiting'?'⏳':'➡️';
        var nc=ns.type==='sfdc'?'#0d9488':ns.type==='scheduled'?'#1d4ed8':ns.type==='blocked'?'#dc2626':ns.type==='waiting'?'#ca8a04':'#6366f1';
        nsHtml='<div style="font-size:10px;color:'+nc+';font-weight:600;margin-top:1px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="'+esc(ns.text)+(ns.date?' · '+esc(ns.date):'')+'">'+icon+' '+esc(ns.text);
        if(ns.date)nsHtml+=' <span style="font-weight:400;opacity:0.7;">· '+esc(ns.date)+'</span>';
        nsHtml+='</div>';
      }}
      html+='<div class="tracker-card '+cc+'" onclick="openDetail(\\''+esc(f.id)+'\\')">'+
        '<div class="tracker-card-seller">'+esc(f.seller||'Unknown')+'</div>'+
        '<div class="tracker-card-meta">Rep: '+esc(f.rep||'—')+' · AE: '+esc(f.oppOwner||'—')+'</div>'+
        glHtml+nsHtml+
        '<div class="tracker-card-stale" style="'+sc+'">'+(f.daysStale||0)+'d stale</div>'+
        (f.gpvUsd?'<div style="font-size:0.65rem;color:#64748b;">'+fmtUSD(f.gpvUsd)+'</div>':'')+
        '</div>';
    }});
    html+='</div></div>';
  }});
  board.innerHTML=html;
}}

// ============================================================
// RENDER: PIPELINE TABLE
// ============================================================
function renderPipeline(){{
  var all=getFiltered();
  var active=all.filter(function(f){{return f.category==='active'||f.category==='onHold';}});
  active.sort(function(a,b){{return(b.daysStale||0)-(a.daysStale||0);}});
  
  var tbody=document.querySelector('#pipelineTable tbody');
  var html='';
  window._exportPipeline=active;
  active.forEach(function(f){{
    var ns=getNextStep(f);
    var nsText=ns?ns.text:'—';
    var nsDate=ns&&ns.date?' · '+ns.date:'';
    var gl=f.desiredGoLiveDate||f.goLiveDate||'—';
    var staleColor=f.daysStale>14?'color:#ef4444':f.daysStale>7?'color:#ca8a04':'color:#22c55e';
    html+='<tr onclick="openDetail(\\''+esc(f.id)+'\\');" style="cursor:pointer;">'+
      '<td><strong>'+esc(f.seller)+'</strong> <a href="'+sfUrl(f.id)+'" target="_blank" onclick="event.stopPropagation()" style="color:#4f46e5;font-size:0.7rem;">🔗</a></td>'+
      '<td>'+esc(f.rep)+'</td>'+
      '<td><span class="badge badge-blue">'+esc(f.status)+'</span></td>'+
      '<td>'+esc(nsText)+nsDate+'</td>'+
      '<td>'+esc(gl)+'</td>'+
      '<td>'+((f.daysOpen||0))+'d</td>'+
      '<td style="'+staleColor+';font-weight:600;">'+(f.daysStale||0)+'d</td>'+
      '<td>'+fmtUSD(f.gpvUsd)+'</td>'+
      '<td>'+esc(f.workType)+'</td></tr>';
  }});
  tbody.innerHTML=html;
}}

// ============================================================
// RENDER: COMPLETED TABLE
// ============================================================
function renderCompleted(){{
  var all=getFiltered();
  var completed=all.filter(function(f){{return f.category==='completed'&&f.completedDate;}});
  // Last 90 days
  var cutoff=new Date();cutoff.setDate(cutoff.getDate()-90);
  var cutStr=cutoff.toISOString().slice(0,10);
  completed=completed.filter(function(f){{return f.completedDate>=cutStr;}});
  completed.sort(function(a,b){{return(b.completedDate||'')>(a.completedDate||'')?-1:1;}});
  
  var tbody=document.querySelector('#completedTable tbody');
  var html='';
  window._exportCompleted=completed;
  completed.forEach(function(f){{
    html+='<tr onclick="openDetail(\\''+esc(f.id)+'\\');" style="cursor:pointer;">'+
      '<td><strong>'+esc(f.seller)+'</strong> <a href="'+sfUrl(f.id)+'" target="_blank" onclick="event.stopPropagation()" style="color:#4f46e5;font-size:0.7rem;">🔗</a></td>'+
      '<td>'+esc(f.rep)+'</td>'+
      '<td>'+esc(f.completedDate)+'</td>'+
      '<td>'+(f.daysToComplete!=null?f.daysToComplete+'d':'—')+'</td>'+
      '<td>'+fmtUSD(f.gpvUsd)+'</td>'+
      '<td>'+esc(f.workType)+'</td></tr>';
  }});
  tbody.innerHTML=html;
}}

// ============================================================
// SELLER DETAIL MODAL
// ============================================================
var SD_STAGES=['Submitted','Assigned','Seller Outreach Complete','Consultation Complete',
  'First Call Complete','Dashboard Training Complete','App Training Complete',
  'SO Training Complete','Implementation Complete'];

function openDetail(id){{
  var fact=null;
  for(var i=0;i<ALL_FACTS.length;i++){{if(ALL_FACTS[i].id===id){{fact=ALL_FACTS[i];break;}}}}
  if(!fact)return;
  
  var now=new Date();
  var lastUp=fact.daysStale!=null?new Date(now-fact.daysStale*86400000).toISOString().slice(0,10):'—';
  var goLive=fact.desiredGoLiveDate||fact.goLiveDate||'';
  
  // Timeline
  var curIdx=SD_STAGES.indexOf(fact.status);
  if(curIdx<0)curIdx=fact.category==='completed'?SD_STAGES.length-1:-1;
  var timeHtml='<div class="sd-timeline">';
  SD_STAGES.forEach(function(st,i){{
    if(i>0)timeHtml+='<div class="sd-line'+(i<=curIdx?' done':'')+'"></div>';
    var cls=i<curIdx?'done':i===curIdx?'current':'';
    var label=STAGE_SHORT[st]||st;
    timeHtml+='<div class="sd-stage"><div class="sd-dot '+cls+'"></div><div style="font-size:0.55rem;color:#64748b;margin-top:4px;text-align:center;max-width:70px;">'+label+'</div></div>';
  }});
  timeHtml+='</div>';
  
  // KPIs
  var kpiHtml='<div class="sd-hero">';
  kpiHtml+='<div class="sd-kpi"><div class="val">'+fmtUSD(fact.gpvUsd)+'</div><div class="label">Annual GPV</div></div>';
  kpiHtml+='<div class="sd-kpi"><div class="val">'+(fact.daysOpen||0)+'</div><div class="label">Days Open</div></div>';
  var staleColor=fact.daysStale>14?'color:#ef4444':fact.daysStale>7?'color:#ca8a04':'color:#22c55e';
  kpiHtml+='<div class="sd-kpi"><div class="val" style="'+staleColor+'">'+(fact.daysStale||0)+'</div><div class="label">Days Stale</div></div>';
  kpiHtml+='<div class="sd-kpi"><div class="val">'+lastUp+'</div><div class="label">Last Updated</div></div>';
  
  // DSA count
  var dsas=(_dsaByDsr[fact.id]||[]);
  var sellerDsas=[];
  if(fact.seller){{
    var sLow=fact.seller.toLowerCase();
    (GSO_DATA.dsaRecords||[]).forEach(function(d){{if(d.sl&&d.sl.toLowerCase()===sLow&&d.dr!==fact.id)sellerDsas.push(d);}});
    (GSO_DATA.bpoActivities||[]).forEach(function(d){{if(d.sl&&d.sl.toLowerCase()===sLow&&d.dr!==fact.id)sellerDsas.push(d);}});
  }}
  var allDsas=dsas.concat(sellerDsas);
  kpiHtml+='<div class="sd-kpi"><div class="val">'+allDsas.length+'</div><div class="label">Activities</div></div>';
  kpiHtml+='</div>';
  
  // Fields grid
  var fields=[
    ['GSO Rep',fact.rep],['Team Lead',fact.teamLead],['AE',fact.oppOwner],['AE Role',fact.oppOwnerRole],
    ['Work Type',fact.workType],['Request Reason',fact.requestReason],
    ['Country',fact.country],['Created',fact.createdDate],['Last Updated',lastUp],
    ['Desired Go-Live',goLive||'—'],
    ['Next Step',fact.nextStep||'—'],['Next Step Date',fact.nextStepDate||'—'],
    ['Channel',fact.channel||'GSO'],
    ['Complexity',fact.complexityScore],['Locations',fact.numLocations],
    ['Competitor POS',fact.competitorPos]
  ];
  var gridHtml='<div class="sd-grid">';
  fields.forEach(function(pair){{
    if(!pair[1]&&pair[1]!==0)return;
    gridHtml+='<div class="sd-field"><div class="fl">'+esc(pair[0])+'</div><div class="fv">'+esc(pair[1])+'</div></div>';
  }});
  gridHtml+='<div class="sd-field"><div class="fl">DSR ID</div><div class="fv"><a href="'+sfUrl(fact.id)+'" target="_blank" style="color:#4f46e5;text-decoration:none;font-weight:600;">'+esc(fact.id)+' 🔗</a></div></div>';
  gridHtml+='</div>';
  
  // Activities
  var actHtml='<h3 style="margin-top:16px;">🔧 Associated Activities ('+allDsas.length+')</h3>';
  if(allDsas.length===0){{
    actHtml+='<p style="color:#94a3b8;font-size:0.8rem;margin:8px 0;">No partner activities linked.</p>';
  }}else{{
    var comp=0,sched=0,canc=0;
    allDsas.forEach(function(d){{
      var s=(d.st||'').toLowerCase();
      if(s.includes('completed')||s.includes('complete'))comp++;
      else if(s.includes('scheduled')||s.includes('submitted')||s.includes('accepted')||s.includes('acknowledged')||s.includes('initiating'))sched++;
      else if(s.includes('cancel')||s.includes('reject'))canc++;
    }});
    actHtml+='<div style="display:flex;gap:8px;margin:8px 0;font-size:0.7rem;">';
    if(comp)actHtml+='<span class="badge badge-green">✓ '+comp+' Completed</span>';
    if(sched)actHtml+='<span class="badge badge-blue">📅 '+sched+' Scheduled</span>';
    if(canc)actHtml+='<span class="badge badge-red">✕ '+canc+' Cancelled</span>';
    actHtml+='</div>';
    allDsas.forEach(function(d){{
      var s=(d.st||'').toLowerCase();
      var bc=s.includes('completed')||s.includes('complete')?'border-left:3px solid #22c55e':
             s.includes('cancel')||s.includes('reject')?'border-left:3px solid #ef4444':
             'border-left:3px solid #3b82f6';
      actHtml+='<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;margin:4px 0;'+bc+';">';
      actHtml+='<strong style="font-size:0.78rem;">'+esc(d.at||'Activity')+'</strong>';
      if(d.p)actHtml+=' <span style="font-size:0.65rem;color:#64748b;">'+esc(d.p)+'</span>';
      actHtml+='<div style="font-size:0.65rem;color:#64748b;">'+esc(d.cd||'')+(d.sd?' · Scheduled: '+esc(d.sd):'')+'</div>';
      actHtml+='<span class="badge '+(s.includes('completed')||s.includes('complete')?'badge-green':s.includes('cancel')||s.includes('reject')?'badge-red':'badge-blue')+'">'+esc(d.st||'—')+'</span>';
      actHtml+='</div>';
    }});
  }}
  
  // Status badge
  var statusColor=fact.category==='completed'?'badge-green':fact.category==='cancelled'?'badge-red':fact.category==='onHold'?'badge-yellow':'badge-blue';
  
  var fullHtml='<h2 style="font-size:1.2rem;font-weight:800;">'+esc(fact.seller||'Unknown Seller')+
    ' <a href="'+sfUrl(fact.id)+'" target="_blank" style="color:#4f46e5;font-size:0.8rem;text-decoration:none;">🔗 Open in Salesforce</a></h2>'+
    '<p style="font-size:0.8rem;color:#64748b;">'+esc(fact.rep||'')+' · '+esc(fact.oppOwner||'')+' · '+esc(fact.country||'')+'</p>'+
    '<span class="badge '+statusColor+'" style="margin-top:4px;">'+esc(fact.status)+'</span>'+
    kpiHtml+timeHtml+'<h3 style="margin-top:16px;">📋 Project Details</h3>'+gridHtml+actHtml;
  
  // Seller history
  var others=ALL_FACTS.filter(function(o){{return o.seller&&fact.seller&&o.seller.toLowerCase()===fact.seller.toLowerCase()&&o.id!==fact.id;}});
  if(others.length>0){{
    fullHtml+='<h3 style="margin-top:16px;">📁 Seller History ('+others.length+' other DSR'+(others.length>1?'s':'')+')</h3>';
    others.forEach(function(o){{
      var oCat=o.category==='completed'?'badge-green':o.category==='cancelled'?'badge-red':'badge-blue';
      fullHtml+='<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:8px 10px;margin:4px 0;cursor:pointer;" onclick="openDetail(\\''+esc(o.id)+'\\')">'+
        '<strong style="font-size:0.78rem;">'+esc(o.status)+'</strong>'+
        '<div style="font-size:0.65rem;color:#64748b;">'+esc(o.rep||'')+' · '+esc(o.createdDate||'')+'</div>'+
        '<span class="badge '+oCat+'">'+esc(o.category)+'</span>'+
        ' <a href="'+sfUrl(o.id)+'" target="_blank" onclick="event.stopPropagation()" style="color:#4f46e5;font-size:0.65rem;">🔗</a></div>';
    }});
  }}
  
  document.getElementById('sellerContent').innerHTML=fullHtml;
  document.getElementById('sellerModal').classList.add('active');
  document.body.style.overflow='hidden';
}}

function closeDetail(){{
  document.getElementById('sellerModal').classList.remove('active');
  document.body.style.overflow='';
}}
window.openDetail=openDetail;
window.closeDetail=closeDetail;

document.getElementById('sellerModal').addEventListener('click',function(e){{
  if(e.target===this)closeDetail();
}});
document.addEventListener('keydown',function(e){{
  if(e.key==='Escape')closeDetail();
}});

// ============================================================
// EXPORT
// ============================================================
function toggleMenu(id){{
  document.querySelectorAll('.export-menu').forEach(function(m){{if(m.id!==id)m.classList.remove('show');}});
  document.getElementById(id).classList.toggle('show');
}}
document.addEventListener('click',function(e){{
  if(!e.target.closest('.export-group'))document.querySelectorAll('.export-menu').forEach(function(m){{m.classList.remove('show');}});
}});

function getExportData(source){{
  if(source==='tracker')return window._exportActive||[];
  if(source==='pipeline')return window._exportPipeline||[];
  if(source==='completed')return window._exportCompleted||[];
  return[];
}}

function exportData(source,fmt){{
  var data=getExportData(source);
  if(!data.length)return alert('No data to export');
  
  var cols=[['Seller','seller'],['AE','oppOwner'],['AE Role','oppOwnerRole'],['GSO Rep','rep'],
    ['Status','status'],['Next Step','nextStep'],['Next Step Date','nextStepDate'],
    ['Go-Live','desiredGoLiveDate'],['Work Type','workType'],['Days Open','daysOpen'],
    ['Days Stale','daysStale'],['GPV','gpvUsd'],['Country','country'],['Created','createdDate'],
    ['Completed','completedDate'],['SFDC Link','id']];
  
  var headers=cols.map(function(c){{return c[0];}});
  var rows=data.map(function(f){{
    return cols.map(function(c){{
      if(c[1]==='id')return sfUrl(f.id);
      var v=f[c[1]];
      return v!=null?String(v):'';
    }});
  }});
  
  if(fmt==='csv'){{
    var csv=headers.join(',')+String.fromCharCode(10)+rows.map(function(r){{return r.map(function(c){{return'"'+c.replace(/"/g,'""')+'"';}}).join(',');}}).join(String.fromCharCode(10));
    var blob=new Blob([csv],{{type:'text/csv'}});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='gso-ae-'+source+'.csv';a.click();
  }}else if(fmt==='excel'){{
    var xml='<?xml version="1.0"?><?mso-application progid="Excel.Sheet"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Sheet1"><Table>';
    xml+='<Row>'+headers.map(function(h){{return'<Cell><Data ss:Type="String">'+h+'</Data></Cell>';}}).join('')+'</Row>';
    rows.forEach(function(r){{xml+='<Row>'+r.map(function(c){{return'<Cell><Data ss:Type="String">'+c.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</Data></Cell>';}}).join('')+'</Row>';}});
    xml+='</Table></Worksheet></Workbook>';
    var blob=new Blob([xml],{{type:'application/vnd.ms-excel'}});
    var a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='gso-ae-'+source+'.xls';a.click();
  }}else if(fmt==='pdf'){{
    var w=window.open('','_blank');
    w.document.write('<html><head><title>GSO AE Export</title><style>body{{font-family:sans-serif;padding:20px;}}table{{width:100%;border-collapse:collapse;font-size:11px;}}th{{background:#f1f5f9;padding:6px;border:1px solid #ddd;text-align:left;}}td{{padding:5px;border:1px solid #eee;}}</style></head><body>');
    w.document.write('<h2>GSO AE Dashboard — '+source+'</h2><table><tr>'+headers.map(function(h){{return'<th>'+h+'</th>';}}).join('')+'</tr>');
    rows.forEach(function(r){{w.document.write('<tr>'+r.map(function(c){{return'<td>'+c+'</td>';}}).join('')+'</tr>');}});
    w.document.write('</table></body></html>');
    w.document.close();
    w.print();
  }}
  document.querySelectorAll('.export-menu').forEach(function(m){{m.classList.remove('show');}});
}}

// ============================================================
// RENDER ALL
// ============================================================
function renderAll(){{
  populateFilters();
  renderTracker();
  renderPipeline();
  renderCompleted();
}}

// Event listeners
var _debounce;
document.getElementById('searchBox').addEventListener('input',function(){{clearTimeout(_debounce);_debounce=setTimeout(renderAll,300);}});
document.getElementById('sortBy').addEventListener('change',renderAll);
document.getElementById('maxStale').addEventListener('change',renderAll);
document.getElementById('roleFilter').addEventListener('change',function(){{
  document.getElementById('aeFilter').value='';renderAll();
}});
document.getElementById('aeFilter').addEventListener('change',renderAll);

// Initial render
renderAll();
</script>
</body>
</html>'''

    out_path = os.path.join(DASH_DIR, 'ae_dashboard.html')
    with open(out_path, 'w') as f:
        f.write(page)
    
    size_mb = os.path.getsize(out_path) / 1024 / 1024
    print(f"\n✅ Generated ae_dashboard.html: {size_mb:.1f} MB")

if __name__ == '__main__':
    build_ae_dashboard()
