#!/bin/bash
# ============================================================
# GSO Dashboard — Full Data Refresh
# ============================================================
# Usage:  Run via a goose session (not directly)
#
# Pipeline:
#   1. Pull DSR facts from Snowflake (delta) → upsert to Airtable → pull all → embed
#   2. Pull DSA records from Snowflake → embed
#   3. Pull late cancellations from Snowflake → embed
#   4. Pull CSAT from GetFeedback API → embed
#   5. Pull Vendor Spend from Airtable → embed
#   6. Pull Goaling from Airtable → embed
#   7. Embed all into dashboard.html (with backup + validation)
#   8. Deploy to Blockcell
#   9. Git commit and push
#
# To run:
#   goose "Refresh the GSO Dashboard using the refresh-dashboard recipe"
#
# Or load the recipe directly:
#   goose session --recipe refresh-dashboard.yaml
#
# Key files:
#   dashboard.html      — the single-file SPA (NOT index.html)
#   refresh-dashboard.yaml — the goose recipe with full instructions
#   refresh_all.py      — the embed script (Step 7)
#
# Data sources:
#   Snowflake: FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C (DSR facts)
#   Snowflake: FIVETRAN.APP_PARTNERSHIPS.DEAL_SUPPORT_ACTIVITY_C (DSA + late cancels)
#   Airtable:  appsnfWWzptN9cwD0 (DSR Facts, Vendor Spend, Goaling, Sync Log)
#   GetFeedback: sc.getfeedback.com/data (CSAT responses)
# ============================================================

set -euo pipefail
cd "$(dirname "$0")"

echo "=== GSO Dashboard Refresh ==="
echo "Working directory: $(pwd)"
echo "Main file: dashboard.html"
echo ""
echo "This script documents the refresh pipeline."
echo "Run via goose session for full automation:"
echo ""
echo "  goose \"Refresh the GSO Dashboard using refresh-dashboard.yaml\""
echo ""
echo "Or for just the embed step (after data is pulled):"
echo "  python3 refresh_all.py"
