You are refreshing the GSO Dashboard. Follow these steps EXACTLY and QUICKLY:

STEP 1: Pull data from Looker dashboard 39532 using Blockdata.runDashboard.
- First call with dashboard_id="39532", platform="looker" (no query_ids) to get metadata.
- Then call with ALL query_ids and filters: {"Completed Date": "90 day", "Created Date": "365 day", "Seller Country": "US,CA,GB,JP,ES,FR,AU,IE"}

STEP 2: Write the raw query results as JSON to .github/latest-data.json in the current working directory.

STEP 3: Read the current index.html file. Update ONLY the GSO_DATA JavaScript object with the fresh numbers from the Looker data. Do NOT change the HTML structure, CSS, chart configurations, or layout. Only update data values.

STEP 4: Write the updated index.html.

STEP 5: Upload the current working directory to Blockcell site "gso-dashboard" using Blockcell.manageSite with action "upload".

Be fast. Do not explain. Just execute.
