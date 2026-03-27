# GSO Dashboard

Real-time analytics dashboard for Global Support Operations, deployed on [Blockcell](https://blockcell.sqprod.co/sites/gso-dashboard/).

## 🚀 Live URL

**https://blockcell.sqprod.co/sites/gso-dashboard/**

## Architecture

```
Snowflake (FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C)
    │  delta sync
    ▼
Airtable (appsnfWWzptN9cwD0 — DSR Facts, Team Roster, Goaling, Sync Log)
    │  pull all records
    ▼
dsr_facts.json → dsr_facts_slim.json → embedded in index.html
    │
    ▼
Blockcell (static SPA) ← Looker 41359 (goaling points)
```

### Data Sources
| Source | Table/ID | Purpose |
|--------|----------|---------|
| Snowflake | `FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C` | Source of truth for DSRs |
| Airtable | Base `appsnfWWzptN9cwD0` | Persistent store (DSR Facts, Team Roster, Goaling) |
| Looker | Dashboard 41359 | Goaling points data |

### Embedded Data (`GSO_DATA`)
| Property | Source | Records |
|----------|--------|---------|
| `dsrFacts` | Airtable DSR Facts | 13,304 row-level facts |
| `teams` | Airtable Team Roster | 4 teams, 51 reps |
| `goaling` | Looker 41359 | Per-rep quarterly goals |
| `activePipeline` | Legacy (kept for Journey tab) | ~970 active items |
| `completedSellers` | Legacy (kept for Journey tab) | ~1,645 recent completions |
| `repSummary` | Legacy (kept for Journey tab) | 39 rep aggregates |

## Dashboard Tabs

| Tab | Data Source | Filterable |
|-----|------------|------------|
| 📊 Overview | `dsrFacts` | ✅ Team, Rep, Work Type, Status, Date |
| 👥 Team Performance | `dsrFacts` | ✅ All filters |
| 🔄 Active Pipeline | `dsrFacts` | ✅ All filters + Stage |
| 🗺️ Onboarding Journey | `journeyTiming` (aggregate) | ⚠️ Limited (needs row-level events) |
| ✅ Completed | `dsrFacts` | ✅ All filters |
| 🚀 Sellers Launched | `dsrFacts` (launch work types only) | ✅ All filters |
| 🚫 Cancelled / Rejected | `dsrFacts` | ✅ All filters + AE, AE Leader |
| 🎯 GSO Goaling | `goaling` + `goalingMeta` | ✅ Team filter |

### Sellers Launched Work Types
Only implementation-based work types count as "launches":
- Onsite, Premium, Plus, Full-day 3rd Party Vendor Install, Half-day 3rd Party Vendor Install

## Refresh Pipeline

To refresh dashboard data:

```
# Via goose session (recommended):
goose "Refresh the GSO Dashboard — pull from Airtable, enrich from Snowflake, embed, deploy"

# Or step by step:
1. Pull DSR Facts from Airtable → dsr_facts.json
2. Pull Opp Owner from Snowflake → merge into dsr_facts.json
3. python3 rebuild_embed.py  (builds slim JSON, embeds into index.html)
4. Deploy to Blockcell: upload /Users/mhofer/gso-dashboard as gso-dashboard
5. git commit + push
```

### Scripts
| Script | Purpose |
|--------|---------|
| `rebuild_embed.py` | Build slim JSON from dsr_facts.json, embed into index.html |
| `embed_dsr_facts.py` | Original embedding script (used for initial migration) |
| `refresh.sh` | Reference docs for the full refresh pipeline |

## Tech Stack

- **HTML5** — Single-file SPA (`index.html`, ~3.5 MB with embedded data)
- **Tailwind CSS** (CDN) — Utility-first styling
- **Chart.js** (CDN) — Interactive charts
- **Vanilla JavaScript** — No build step required
- **Blockcell** — Static site hosting

## Local Development

```bash
open index.html
# or
python3 -m http.server 8080
```

## Deployment

```bash
# Via goose Blockcell extension:
# Upload /Users/mhofer/gso-dashboard to Blockcell site "gso-dashboard"
```
