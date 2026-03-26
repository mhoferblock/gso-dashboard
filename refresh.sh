#!/bin/bash
# GSO Dashboard Daily Refresh Script
# Scheduled to run at 6:00 AM ET via launchd
# Triggers goose to pull fresh Looker data and redeploy to Blockcell

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG_FILE="$SCRIPT_DIR/refresh.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

echo "[$TIMESTAMP] Starting GSO Dashboard refresh..." >> "$LOG_FILE"

# Run goose with the refresh instructions
/usr/local/bin/goose run --instructions "
Pull fresh data from Looker dashboard 39532 (GSO Go Live Metrics) with filters:
- Completed Date: 90 day
- Created Date: 365 day
- Seller Country: US,CA,GB,JP,ES,FR,AU,IE

Execute ALL query_ids from the dashboard to get the latest data.
Then regenerate /Users/mhofer/gso-dashboard/index.html with the updated data
(keep the same visual layout, tabs, charts, and design — only update the numbers).
Finally, upload /Users/mhofer/gso-dashboard to Blockcell site 'gso-dashboard'.
Commit the changes to git with message 'Daily refresh: [today's date]'.
" >> "$LOG_FILE" 2>&1

EXIT_CODE=$?
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S %Z')

if [ $EXIT_CODE -eq 0 ]; then
  echo "[$TIMESTAMP] ✅ Refresh completed successfully" >> "$LOG_FILE"
else
  echo "[$TIMESTAMP] ❌ Refresh failed with exit code $EXIT_CODE" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"
