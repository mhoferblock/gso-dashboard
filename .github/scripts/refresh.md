# Dashboard Refresh Runbook

## Quick Refresh (tell goose)

> Refresh the GSO Dashboard. Pull delta from Snowflake, upsert to Airtable, rebuild and publish.

## What happens

1. **Delta query** — Snowflake for DSRs modified since last sync
2. **Upsert** — New records → create in Airtable, existing → update
3. **Read** — Pull all data from Airtable tables
4. **Build** — `python3 .github/scripts/build_dashboard_data.py`
5. **Embed** — `python3 .github/scripts/embed_data.py`
6. **Publish** — Git commit + push + Blockcell upload

## Key IDs

- Airtable base: `appsnfWWzptN9cwD0`
- DSR Facts table: `tblqfqKMvmdufvRjD`
- Snowflake: `FIVETRAN.APP_SALES_SFDC.DEAL_SUPPORT_REQUEST_C`
- Record Type: `0124W0000011dFnQAI`
- Team filter: `DEAL_SUPPORT_TEAM_C = 'GSO Global Seller Onboarding'`
