#!/bin/bash
# ============================================================
# GSO Dashboard — Full Data Refresh
# ============================================================
# Usage:  ./refresh.sh
#
# Pipeline:
#   1. Pull DSR facts from Airtable (source of truth, synced from Snowflake)
#   2. Enrich with Opp Owner data from Snowflake
#   3. Build slim JSON for embedding
#   4. Re-embed dsrFacts into index.html
#   5. Deploy to Blockcell
#   6. Push to GitHub
#
# Prerequisites:
#   - goose CLI with Airtable, Snowflake, and Blockcell extensions
#   - Or run the steps manually via goose session
#
# This script is a reference for the refresh pipeline.
# In practice, run these steps via a goose session:
#
#   goose "Refresh the GSO Dashboard:
#     1. Pull all records from Airtable DSR Facts (appsnfWWzptN9cwD0 / tblqfqKMvmdufvRjD)
#     2. Pull Opp Owner data from Snowflake FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C
#     3. Merge Opp Owner into the facts
#     4. Build slim JSON and re-embed into index.html
#     5. Deploy to Blockcell site gso-dashboard
#     6. Git commit and push"
# ============================================================

set -euo pipefail
cd "$(dirname "$0")"

echo "=== GSO Dashboard Refresh ==="
echo "This script documents the refresh pipeline."
echo "Run the steps via a goose session for full automation."
echo ""
echo "Steps:"
echo "  1. Pull DSR Facts from Airtable (13K+ records)"
echo "  2. Pull Opp Owner from Snowflake (100K+ records)"
echo "  3. Merge and build dsr_facts_slim.json"
echo "  4. Re-embed into index.html"
echo "  5. Deploy to Blockcell"
echo "  6. Git commit + push"
echo ""
echo "To run: open a goose session and ask it to refresh the dashboard."
