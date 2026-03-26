Pull fresh data from Looker dashboard 39532 (GSO Go Live Metrics) with these filters:
- Completed Date: 90 day
- Created Date: 365 day
- Seller Country: US,CA,GB,JP,ES,FR,AU,IE

Use Blockdata.runDashboard to first get the dashboard metadata (no query_ids), then execute ALL query_ids to get the latest data.

Then regenerate the index.html file in the current working directory with the updated data. Keep the same visual layout, tabs, charts, and design — only update the numbers and data values in the GSO_DATA JavaScript object.

Finally, upload the current working directory to Blockcell site 'gso-dashboard'.
