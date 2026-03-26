# Date-Accurate Overview KPI Plan

## Goal

Make the top Overview KPI cards respond accurately to the selected date range:

- `Total DSRs`
- `Completed`
- `Active Pipeline`
- `On Hold`
- `Cancelled`
- `Median Days`

## Current State

The dashboard currently mixes:

- row-level active pipeline data
- row-level completed seller data
- pre-aggregated totals and summaries

This is why date filters can be accurate for some tabs but not for the top Overview cards.

### Current source files

- `q5_active_pipeline.json`
  - row-level active records
  - current shape: `REP`, `STAGE`, `SELLER`, `WORK_TYPE`, `CREATED`, `GO_LIVE`, `GPV`, `DAYS_OPEN`, `DAYS_STALE`
- `q6_completed_sellers.json`
  - row-level completed records
  - current shape: `REP`, `SELLER`, `WORK_TYPE`, `GPV`, `COUNTRY`, `COMPLETED_DATE`, `DAYS_TO_COMPLETE`
- `q2_monthly_trend.json`
  - monthly aggregate counts by status
- `q1_rep_status_worktype.json`
  - aggregate counts by rep/status/work type
- `processed_data.json`
  - final embedded dashboard object

### Important mismatch

- `processed_data.json -> totals.completed = 4894`
- `q6_completed_sellers.json -> 1642 rows`

That means the current completed feed is not a full lifetime completed fact table, so any date-filtered `Completed` KPI built from it will undercount.

## Recommended Source Of Truth

Add one canonical fact dataset that contains one row per DSR.

Suggested file:

- `q0_dsr_facts.json`

Suggested final embedded property:

- `GSO_DATA.dsrFacts`

## Required Row Schema

Each DSR row should include:

```json
{
  "dsrId": "SFDC_OR_INTERNAL_ID",
  "rep": "Alexandre Garreau",
  "teamLead": "Caleb Cunningham",
  "seller": "Miami Cafe",
  "workType": "Onsite",
  "gpv": 700000,
  "country": "US",
  "createdDate": "2026-02-23",
  "currentStatus": "active",
  "currentStage": "App Training Complete",
  "completedDate": null,
  "cancelledDate": null,
  "isOnHold": false,
  "onHoldStartDate": null,
  "goLiveDate": "2026-03-09",
  "daysToComplete": null,
  "daysOpen": 31
}
```

## Minimum Fields Needed For Accurate Overview KPIs

### Required

- `dsrId`
- `rep`
- `teamLead`
- `workType`
- `gpv`
- `createdDate`
- `currentStatus`
- `currentStage`
- `completedDate`
- `cancelledDate`
- `isOnHold`

### Strongly recommended

- `country`
- `goLiveDate`
- `onHoldStartDate`
- `daysToComplete`
- `daysOpen`

## KPI Definitions

These definitions will make the top cards consistent and explainable.

### Flow metrics

These use an event date inside the selected range.

- `Total DSRs`
  - count rows where `createdDate` is in range
- `Completed`
  - count rows where `completedDate` is in range
- `Cancelled`
  - count rows where `cancelledDate` is in range
- `Median Days`
  - median `daysToComplete` for rows where `completedDate` is in range

### Snapshot metrics

These use the current row state, optionally filtered by created date.

- `Active Pipeline`
  - count rows where `currentStatus = "active"`
- `On Hold`
  - count rows where `isOnHold = true` or `currentStage = "On Hold"`

## Recommended UI Behavior

For date filters, use this interpretation:

- `Total DSRs`, `Completed`, `Cancelled`, `Median Days`
  - flow/event metrics tied to the selected range
- `Active Pipeline`, `On Hold`
  - current-state snapshot metrics

This keeps the dashboard intuitive:

- "Last 30 Days Completed" means completions that happened in the last 30 days
- "Active Pipeline" still means what is active now

If you want snapshot metrics to also be period-based, that requires status history, not just current status.

## If Period-Accurate Snapshot Metrics Are Needed

Add a second event-history table:

- `q0_dsr_status_events.json`

Suggested shape:

```json
{
  "dsrId": "SFDC_OR_INTERNAL_ID",
  "eventDate": "2026-03-05",
  "eventType": "status_change",
  "fromStatus": "active",
  "toStatus": "on_hold",
  "fromStage": "Assigned",
  "toStage": "On Hold"
}
```

That would allow:

- "how many DSRs were on hold during last month"
- "how many were active at the end of Q1"

Without status history, only current-state snapshot metrics are reliable.

## Journey Flow Requirements

The current Journey tab is built from:

- `journeyTiming`
- `stageDuration`

Those are aggregate summaries, so they cannot be recalculated accurately for:

- team filters
- rep filters
- work type filters
- date filters

To make the Journey Flow truly filterable, add a row-level journey event dataset.

### Suggested file

- `q0_dsr_journey_events.json`

### Suggested embedded property

- `GSO_DATA.journeyEvents`

### Required row schema

```json
{
  "dsrId": "SFDC_OR_INTERNAL_ID",
  "rep": "Alexandre Garreau",
  "teamLead": "Caleb Cunningham",
  "seller": "Miami Cafe",
  "workType": "Onsite",
  "createdDate": "2026-02-23",
  "stageName": "Assigned",
  "enteredStageAt": "2026-02-24",
  "exitedStageAt": "2026-02-26",
  "daysInStage": 2,
  "milestoneReachedAt": "2026-02-26",
  "sequence": 2,
  "goLiveDate": "2026-03-09",
  "completedDate": null
}
```

### Minimum fields needed

- `dsrId`
- `rep`
- `teamLead`
- `workType`
- `createdDate`
- `stageName`
- `enteredStageAt`
- `exitedStageAt`
- `daysInStage`
- `milestoneReachedAt`

### Strongly recommended

- `seller`
- `sequence`
- `goLiveDate`
- `completedDate`

### Metrics derived from `journeyEvents`

With filtered journey events, the Journey tab can accurately compute:

- median time in each stage
- median time to reach each stage
- median time between stages
- median time from implementation complete to go live
- median time from go live to 1st Q&A
- median time from 1st Q&A to 2nd Q&A
- median total time in GSO

### Rendering rule

The Journey Flow should be derived from filtered events using the same top-level filters:

- team
- rep
- work type
- date range

Recommended date interpretation:

- include DSRs whose `createdDate` falls in the selected range

Alternative interpretation if needed later:

- include DSRs whose milestone timestamp falls in the selected range

The first option is simpler and easier to explain.

## Refresh Pipeline Changes

### New output

Produce a row-level fact file:

- `.github/data/q0_dsr_facts.json`

Example wrapper:

```json
{
  "result": {
    "status": "success",
    "data": [
      {
        "DSR_ID": "123",
        "REP": "Alexandre Garreau",
        "TEAM_LEAD": "Caleb Cunningham",
        "SELLER": "Miami Cafe",
        "WORK_TYPE": "Onsite",
        "GPV": 700000,
        "COUNTRY": "US",
        "CREATED_DATE": "2026-02-23",
        "CURRENT_STATUS": "active",
        "CURRENT_STAGE": "App Training Complete",
        "COMPLETED_DATE": null,
        "CANCELLED_DATE": null,
        "IS_ON_HOLD": false,
        "ON_HOLD_START_DATE": null,
        "GO_LIVE_DATE": "2026-03-09",
        "DAYS_TO_COMPLETE": null,
        "DAYS_OPEN": 31
      }
    ]
  }
}
```

### Data generation rule

Everything in `processed_data.json` should be derived from `q0_dsr_facts.json`.

That includes:

- `totals`
- `monthly`
- `repSummary`
- `workTypeSummary`
- `activePipeline`
- `completedSellers`
- `weeklyCompletions`

This removes the current mismatch between aggregated totals and row-level subsets.

## `index.html` Changes Needed

### 1. Add `dsrFacts` to embedded data

Current dashboard object:

- `GSO_DATA.totals`
- `GSO_DATA.monthly`
- `GSO_DATA.activePipeline`
- `GSO_DATA.completedSellers`

Add:

- `GSO_DATA.dsrFacts`

### 2. Add a reusable fact-table range helper

Suggested helpers:

```js
function getFilteredFacts() {
  let facts = [...GSO_DATA.dsrFacts];

  const selTeam = filterTeam.value;
  const selRep = filterRep.value;
  const selWT = filterWorkType.value;
  const range = getTimeframeRange();

  if (selTeam) {
    const teamReps = GSO_DATA.teams[selTeam] || [];
    facts = facts.filter(f => teamReps.includes(f.rep));
  }
  if (selRep) facts = facts.filter(f => f.rep === selRep);
  if (selWT) facts = facts.filter(f => f.workType === selWT);

  return { facts, range };
}

function isFactDateInRange(dateStr, range) {
  if (!range) return true;
  return isDateInRange(dateStr, range.start, range.end);
}
```

### 3. Replace Overview KPI calculations

Current Overview logic in [index.html](/Users/mhofer/Documents/New project/gso-dashboard/index.html#L1067) uses:

- `const T = GSO_DATA.totals;`

Replace with derived values:

```js
const { facts, range } = getFilteredFacts();

const createdFacts = facts.filter(f => isFactDateInRange(f.createdDate, range));
const completedFacts = facts.filter(f => isFactDateInRange(f.completedDate, range));
const cancelledFacts = facts.filter(f => isFactDateInRange(f.cancelledDate, range));

const totalDsrs = createdFacts.length;
const completed = completedFacts.length;
const cancelled = cancelledFacts.length;
const activePipeline = facts.filter(f => f.currentStatus === 'active').length;
const onHold = facts.filter(f => f.isOnHold || f.currentStage === 'On Hold').length;

const daysList = completedFacts
  .map(f => f.daysToComplete)
  .filter(d => d != null && d >= 0)
  .sort((a, b) => a - b);
const medianDays = daysList.length ? daysList[Math.floor(daysList.length / 2)] : 0;
```

### 4. Replace Overview card labels/subtext

```js
const completionRate = totalDsrs ? (completed / totalDsrs * 100) : 0;
const cancelRate = totalDsrs ? (cancelled / totalDsrs * 100) : 0;
```

Then render:

- `Total DSRs` -> `totalDsrs`
- `Completed` -> `completed`
- `Active Pipeline` -> `activePipeline`
- `On Hold` -> `onHold`
- `Cancelled` -> `cancelled`
- `Median Days` -> `medianDays`

### 5. Keep current Pipeline and Completed tabs

Those tabs already use row-level datasets and can stay mostly as-is until the fact table is added.

Later, they can also be refactored to derive from `GSO_DATA.dsrFacts`.

## Variance By Metric

### Accurate now with current row-level sources

- `Median Days`
- `Active Pipeline`
- `On Hold`

### Not accurate enough now

- `Total DSRs`
- `Completed`
- `Cancelled`
- completion rate
- cancel rate

## Lowest-Risk Rollout Plan

1. Add `q0_dsr_facts.json` to the refresh pipeline.
2. Embed `dsrFacts` into `processed_data.json`.
3. Update only the top Overview cards first.
4. Verify that derived lifetime totals equal current snapshot values.
5. Then, if desired, migrate the other aggregates to derive from `dsrFacts` too.

## Validation Checklist

- Lifetime `Total DSRs` from `dsrFacts` matches current `6467`
- Lifetime `Completed` from `dsrFacts` matches current `4894`
- Lifetime `Cancelled` from `dsrFacts` matches current `583`
- Current `Active Pipeline` matches current `1093`
- Current `On Hold` matches current `243`
- Date filters produce stable results across:
  - `Last 30 Days`
  - `Last 60 Days`
  - `Last 90 Days`
  - `This Month`
  - `Last Month`
  - `Quarter`
  - `Year`
