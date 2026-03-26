# GSO Dashboard

A real-time analytics dashboard for the GSO (Global Support Operations) organization, deployed on [Blockcell](https://blockcell.sqprod.co/sites/gso-dashboard/).

## 🚀 Live URL

**https://blockcell.sqprod.co/sites/gso-dashboard/**

## Overview

The GSO Dashboard provides a unified view of team and individual performance metrics, pulling data from multiple sources into a single, interactive interface. It features three levels of drill-down navigation:

1. **GSO Overview** — Organization-wide KPIs, trends, and team comparisons
2. **Team View** — Team-specific metrics, case categories, and member performance
3. **User View** — Individual agent performance, daily trends, and recent activity

## Features

### Visual Components
- **KPI Summary Cards** — Large-format metrics with trend indicators (↑/↓ with %)
- **Line Charts** — Cases over time (new vs. resolved)
- **Donut Charts** — Case distribution by channel/category
- **Horizontal Bar Charts** — Team and member performance comparisons
- **Data Tables** — Searchable, sortable tables with clickable drill-down rows
- **Source Integration Cards** — Color-coded status cards for each data source

### Data Sources (Planned Integrations)
| Source | Status | Description |
|--------|--------|-------------|
| Looker | 🔲 Planned | Dashboard metrics, scheduled reports |
| Salesforce | 🔲 Planned | Case data, account information |
| Slack | 🔲 Planned | Escalation threads, response times |
| JIRA | 🔲 Planned | Ticket tracking, sprint velocity |
| Knowledge Base | 🔲 Planned | Article usage, helpfulness ratings |

> Currently using structured mock data (`GSO_DATA` object) designed to be swapped with live API calls.

### Teams Tracked
- Payments Support
- Account Services
- Developer Relations
- Merchant Success
- Risk & Compliance
- Hardware Support

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  GSO Dashboard                   │
│              (Static SPA on Blockcell)           │
├─────────────────────────────────────────────────┤
│  UI Layer: Tailwind CSS + Chart.js              │
│  Navigation: 3-level drill-down (SPA routing)   │
│  Data Layer: GSO_DATA object (mock → live APIs) │
├─────────────────────────────────────────────────┤
│  Data Sources (future integration):             │
│  ┌─────────┐ ┌────────────┐ ┌───────┐          │
│  │ Looker  │ │ Salesforce │ │ Slack │          │
│  └─────────┘ └────────────┘ └───────┘          │
│  ┌─────────┐ ┌────────────────────┐             │
│  │  JIRA   │ │  Knowledge Base    │             │
│  └─────────┘ └────────────────────┘             │
└─────────────────────────────────────────────────┘
```

## Tech Stack

- **HTML5** — Single-file SPA
- **Tailwind CSS** (CDN) — Utility-first styling
- **Chart.js** (CDN) — Interactive charts with animations
- **Vanilla JavaScript** — No build step required
- **Blockcell** — Static site hosting

## Local Development

Simply open `index.html` in a browser:

```bash
open index.html
```

Or serve locally:

```bash
python3 -m http.server 8080
# Then visit http://localhost:8080
```

## Deployment

Deploy to Blockcell via goose:

```
Upload /Users/mhofer/gso-dashboard to Blockcell site "gso-dashboard"
```

## Roadmap

- [ ] Connect Looker API for live dashboard metrics
- [ ] Connect Salesforce API for real case data
- [ ] Add Slack integration for escalation tracking
- [ ] Add JIRA integration for ticket data
- [ ] Implement date range filtering (currently visual only)
- [ ] Add export/download functionality for reports
- [ ] Add real-time WebSocket updates
- [ ] Implement Teams and Analytics tabs
- [ ] Add user authentication / SSO
- [ ] Mobile-responsive improvements

## Contributing

1. Clone this repo
2. Make changes to `index.html`
3. Test locally by opening in browser
4. Deploy to Blockcell

## License

Internal — Block, Inc.
