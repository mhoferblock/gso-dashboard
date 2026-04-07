# GSO Dashboard — Resume Prompt

Copy everything below this line and paste it to start a new session:

---

## Context

I'm working on the **GSO Dashboard**, a single-file SPA (~14MB) with embedded data that tracks Global Seller Onboarding metrics. It's deployed to Blockcell at:

- **Dashboard:** https://blockcell.sqprod.co/sites/gso-dashboard/
- **14-Day Go-Live Guide:** https://blockcell.sqprod.co/sites/gso-14day-guide/

### Working Directory
`/Users/mhofer/gso-dashboard/`

### Key Files
| File | Purpose |
|------|---------|
| `dashboard.html` | Main SPA dashboard (~14MB, all data embedded as JSON) |
| `index.html` | Redirect to dashboard.html |
| `14-day-go-live-guide.html` | Standalone playbook for 14-day go-live process |
| `dsr_facts.json` | DSR cache (~40,852 records, 24MB) |
| `dsa_records.json` | Partner activity records (5,145 records) |
| `bpo_activities.json` | BPO activities (12,292 records) |
| `csat_data.json` | CSAT survey responses (192 records) |
| `late_cancels.json` | Late cancellation records (76 records) |
| `vendor_spend.json` | Vendor spend data |
| `goaling.json` | Rep goaling targets |
| `refresh_all.py` | Embed script — validates JSON, applies channel tagging, embeds into dashboard.html |

### Architecture
- **Single-file SPA** — all HTML, CSS, JS, and data in one `dashboard.html`
- **Data is embedded** as `GSO_DATA.dsrFacts`, `GSO_DATA.dsaRecords`, `GSO_DATA.bpoActivities`, `GSO_DATA.csatResponses`, etc.
- **DSR facts** use compressed keys that get expanded by `expandFact()` at runtime
- **Roster filtering** — `ROSTER_SET` built from `GSO_DATA.teams` at runtime, filters out departed reps from pipeline
- **Channel tagging** — DSRs tagged as GSO, BPO, or Vendor Ops; `GSO_FACTS`, `BPO_FACTS`, `VO_FACTS` are pre-filtered arrays
- **Drilldown system** — `openDrilldown()` for table modals, `openSellerDetail()` for rich seller cards, `openRepDetail()`, `openTeamDetail()`, `openPartnerScorecard()`, `openBpoDetail()`

### Recent Additions (April 6, 2026)
1. **Project Stage Tracker** — Kanban board in the Journey tab showing every active DSR in its current onboarding stage with color-coded staleness (green <7d, yellow 7-14d, red >14d)
2. **GSO Rep dropdown filter** — Filter the tracker board by rep
3. **Seller Detail Modal** (`openSellerDetail(dsrId)`) — Click any tracker card to see:
   - Hero section with status badge, GPV, days open, days stale, last updated date, activity count, CSAT rating
   - Onboarding journey timeline (visual dot progression)
   - Project details grid
   - Associated activities (DSAs matched by DSR ID + seller name + BPO activities) with status summary bar
   - CSAT feedback
   - Seller history (other DSRs for same seller, clickable)
4. **14-Day Go-Live Guide** — Standalone HTML playbook deployed separately

### Deployment Process
1. Edit `dashboard.html` directly (or edit JSON files + run `python3 refresh_all.py`)
2. Create deploy directory: `mkdir -p /tmp/gso-deploy && cp dashboard.html index.html /tmp/gso-deploy/`
3. Upload via `Blockcell.manageSite({ site_name: "gso-dashboard", action: "upload", directory_path: "/tmp/gso-deploy" })`
4. Promote if needed via `Blockcell.manageSite({ site_name: "gso-dashboard", action: "promote", version_id: "..." })`
5. For the guide: deploy to `gso-14day-guide` site with the guide as `index.html`
6. Always verify with download after deploy — checksums must match
7. Git commit: `cd /Users/mhofer/gso-dashboard && git add -A && git commit -m "message" && git push`

### Critical Rules
- **Always backup** before editing: `cp dashboard.html .backups/dashboard_pre_CHANGE_$(date +%Y%m%d_%H%M%S).html`
- **Check brace balance** after JS edits — the file has ~14MB of embedded JSON so overall brace count will be off, but check the specific section you edited
- **Functions called from inline onclick** must be exposed on `window` (e.g., `window.openSellerDetail = openSellerDetail;`)
- **Never deploy without verifying** the deployed file matches the source (MD5 check)
- Inline `onclick` handlers must escape special characters in seller names (use `esc()`)

### Data Refresh (Recipe)
The full data refresh follows `/Users/mhofer/.config/goose/recipes/refresh-gso-dashboard.yaml` — a 7-step pipeline:
1. Setup Snowflake config (limit=50K, warehouse=ADHOC__LARGE)
2. DSR Facts — 90-day incremental merge from Snowflake
3. DSA Records — Partner activities from Snowflake
4. BPO Activities — From Snowflake
5. CSAT + Late Cancels — GetFeedback API + Snowflake
6. Embed — `python3 refresh_all.py` (validates, tags channels, embeds)
7. Deploy to Blockcell + git commit

### What I'd Like to Work On
[DESCRIBE YOUR NEXT IMPROVEMENT HERE]

---
