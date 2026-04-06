# Document Rewrite Plan — GSO Operations Review Q1 FY26

**Google Doc:** `1sXN-hXx6ANd5dfDeWTbvdQMSabQkoGqM9SwRMDZoTWw`
[Open Doc](https://docs.google.com/document/d/1sXN-hXx6ANd5dfDeWTbvdQMSabQkoGqM9SwRMDZoTWw/edit)

---

## Spreadsheet Links & Where They Go

| # | Spreadsheet | ID | Link |
|---|---|---|---|
| 1 | **Lead Time Detail** | `1JYVZh_DqJNRxFGpNK-f3VXvpMJB4VLkJSQMgxHE8Nqk` | [Open](https://docs.google.com/spreadsheets/d/1JYVZh_DqJNRxFGpNK-f3VXvpMJB4VLkJSQMgxHE8Nqk/edit) |
| 2 | **Throughput & Rep Performance** | `1yTeAYV2wlv3AknaQHErCM-6YDMY1mR7cyMcbV72aT4w` | [Open](https://docs.google.com/spreadsheets/d/1yTeAYV2wlv3AknaQHErCM-6YDMY1mR7cyMcbV72aT4w/edit) |
| 3 | **Pipeline & Bottlenecks** | `1IjTJMjcMVWlBGxVUuBFLFnNMqNjhKpzVfqoVVIi2jHg` | [Open](https://docs.google.com/spreadsheets/d/1IjTJMjcMVWlBGxVUuBFLFnNMqNjhKpzVfqoVVIi2jHg/edit) |
| 4 | **3P Partners & Vendor Spend** | `1Q4R1xmmO1LeEQGGSpf3lbZL5NFl0znB-vhtKqcYPwuM` | [Open](https://docs.google.com/spreadsheets/d/1Q4R1xmmO1LeEQGGSpf3lbZL5NFl0znB-vhtKqcYPwuM/edit) |
| 5 | **Capacity Model & BPO Activities** | `1Dh_uiErM1rttItHF5ht-9Jfko3B0cMsdq2uRFqWpiBs` | [Open](https://docs.google.com/spreadsheets/d/1Dh_uiErM1rttItHF5ht-9Jfko3B0cMsdq2uRFqWpiBs/edit) |

### Where each spreadsheet gets cited in the doc:

**Lead Time Detail** → cited in:
- Section 1 (Lead Times) — after the section header
- The lead time by work type bullets
- The lead time by region bullets
- Tabs: "Completed DSRs (3,956)" has every DSR with its DTC; "Monthly Summary" has the trend; "By Work Type" and "By Region" have the cuts

**Throughput & Rep Performance** → cited in:
- Section 2 (Throughput) — after the section header
- The monthly trend table (Nov–Apr)
- Regional throughput bullets
- "What We Did Well" section — Top 10 leaderboard, Austin's numbers
- CSAT subsection
- Tabs: "Monthly Throughput" has the trend; "Rep Performance (Q1)" has every rep; "By Region Monthly" has regional cuts; "CSAT Responses" has the raw survey data

**Pipeline & Bottlenecks** → cited in:
- Section 3 (Bottlenecks) — after the section header
- "What the 997 consists of" breakdown
- Pipeline aging buckets
- Stale DSRs (30+ days)
- Legacy DSRs (180+ days)
- Missing Info blockers
- US West gap detail
- Tabs: "Active Pipeline (997 DSRs)" has every active DSR; "Stale 30+ Days" has the stuck ones; "Legacy 180+ Days" has the audit candidates; "Missing Info Blockers" has the 102 blocked DSRs; "Status Summary" has the rollup

**3P Partners & Vendor Spend** → cited in:
- Section 5 (3P Partner Scaling) — partner turnaround speed
- Partner speed ranking
- Late cancellations detail
- Vendor spend totals
- Tabs: "Partner DSA Records (5,034)" has every DSA; "Partner Monthly Volume" has the trend; "Late Cancellations (132)" has the detail; "Vendor Spend Invoices (929)" has the invoices

**Capacity Model & BPO Activities** → cited in:
- Section 5 (Hiring & 3P) — structural deficit, hiring scenarios, combined path
- BPO speed comparison
- Tabs: "Capacity Model" has the scenario math; "BPO Activities (13,322)" has the raw data; "BPO Monthly Summary" has the trend

---

## Tab GIDs for Deep Links

### Lead Time Detail (1JYVZh_DqJNRxFGpNK-f3VXvpMJB4VLkJSQMgxHE8Nqk)
- Completed DSRs (3,956): gid=0
- Monthly Summary: gid=1825498335
- By Work Type Monthly: gid=1063498042
- By Region Monthly: gid=1419498729

### Throughput & Rep Performance (1yTeAYV2wlv3AknaQHErCM-6YDMY1mR7cyMcbV72aT4w)
- Monthly Throughput: gid=0
- Rep Performance (Q1): gid=1069498232
- By Region Monthly: gid=1402498919
- CSAT Responses: gid=1735499606

### Pipeline & Bottlenecks (1IjTJMjcMVWlBGxVUuBFLFnNMqNjhKpzVfqoVVIi2jHg)
- Active Pipeline (997 DSRs): gid=0
- Stale 30+ Days: gid=varies
- Legacy 180+ Days: gid=varies
- Missing Info Blockers: gid=varies
- Status Summary: gid=varies

### 3P Partners & Vendor Spend (1Q4R1xmmO1LeEQGGSpf3lbZL5NFl0znB-vhtKqcYPwuM)
- Partner DSA Records (5,034): gid=0
- Partner Monthly Volume: gid=varies
- Late Cancellations (132): gid=varies
- Vendor Spend Invoices (929): gid=varies

### Capacity Model & BPO Activities (1Dh_uiErM1rttItHF5ht-9Jfko3B0cMsdq2uRFqWpiBs)
- Capacity Model: gid=0
- BPO Activities (13,322): gid=varies
- BPO Monthly Summary: gid=varies

Note: "gid=varies" means the exact GID needs to be looked up at runtime via sheetsTool list_sheets.
The gid=0 entries are confirmed (default first sheet). Others should be verified.

---

## Formatting & Structure Changes

### 1. Title Block
- **Title:** "GSO Operations Review — Q1 FY26" as Heading 1
- **Subtitle:** "Data as of April 2, 2026" as italic subtitle
- **Confidential** tag

### 2. Executive Summary (new — add at top)
- 4-5 bullet TL;DR of the entire doc
- "Operating at 74% capacity, gap closing via 17 hires + 3P scaling, quality holding at 4.73 CSAT"
- This doesn't exist yet — needs to be added

### 3. Section Numbering & Headings
Current structure is fine but needs consistent formatting:
- **Section headers** → Heading 2 (1. Lead Times, 2. Throughput, etc.)
- **Sub-headers** → Heading 3 (3a. The Pipeline Problem, etc.)
- **"What We Did Well"** should become a numbered section (move to Section 3, shift Bottlenecks to 4)

Proposed final order:
1. Lead Times
2. Throughput
3. What We Did Well ← promote to full section
4. Bottlenecks (was 3)
5. Quality Metrics (was 4)
6. How Hiring & 3P Changes the Math (was 5)
7. Recommendations (was 6)
8. Methodology & Data Notes (appendix)

### 4. Citation Format
Every data claim gets an inline parenthetical link to the specific spreadsheet + tab. Format:

> "76 DSRs completed (25.3/month)" ([Rep Performance Q1](link))

Or:
> "March completions recovered to 680..." ([Monthly Throughput](link))

**Remove all 📊 emoji lines** — replace with proper inline citations.

### 5. Specific Formatting Fixes
- **Bullet lists** should use actual bullet formatting, not plain text with dashes
- **Key metrics** (the big numbers) should be **bold**
- **Status tags** (In Progress Already, Completed Already, Will Look Into) → bold + green (already done, preserve)
- **Tables** — convert these to actual Google Docs tables:
  - Monthly throughput trend (Nov–Apr)
  - Top 10 leaderboard
  - Regional throughput
  - Partner speed ranking
  - Combined path timeline
  - Australia current state metrics
- **Block quotes** for key callouts (e.g., "The gap is not a staffing shortfall...")
- **Horizontal rules** between major sections

### 6. Content Cleanup
- Remove duplicate/redundant phrasing
- Tighten the late cancellations paragraph (break into bullets)
- Methodology section — clean up into a proper appendix format with a horizontal rule separator

### 7. Things to Add
- **Executive Summary** at top (doesn't exist yet)
- **Table of Contents** (Google Docs native — just needs heading styles applied)
- **"Document prepared by"** line at bottom
- **Version/date** in header or footer

---

## Execution Plan for New Session

**Step 1:** Look up exact tab GIDs for all spreadsheets using `sheetsTool list_sheets`

**Step 2:** Write the complete new document as markdown to `/tmp/gso_doc_rewrite.md` with all inline citation links

**Step 3:** Use `Googledrive.upsert` with `file_id: "1sXN-hXx6ANd5dfDeWTbvdQMSabQkoGqM9SwRMDZoTWw"` and the markdown body to replace the entire doc content

**Step 4:** Apply formatting that markdown can't handle:
- `format_existing_text` for green status tags (In Progress Already, Completed Already, Will Look Into)
- `format_existing_text` for any color highlights
- Heading levels via `format_existing_text` with heading_level

**Step 5:** Insert proper tables using `insert_table` + `update_table_cell` for:
- Monthly throughput trend
- Top 10 leaderboard
- Partner speed ranking
- Combined path timeline

**Step 6:** Verify the final doc renders correctly

---

## Prompt for New Session

Copy-paste this to kick off the new session:

```
Continue the GSO Dashboard project. The Google Doc 1sXN-hXx6ANd5dfDeWTbvdQMSabQkoGqM9SwRMDZoTWw ("GSO Operations Review — Q1 FY26") needs a professional formatting rewrite. The full plan is saved at /Users/mhofer/gso-dashboard/doc_rewrite_plan.md — read that file first. All data is already in the doc — this is purely a formatting, structure, and citation pass. The 5 supporting spreadsheets need to be hyperlinked inline as citations. Do NOT change any numbers or analysis — only improve presentation. Work section by section to avoid timeouts.
```

---

## Current Document Content (for reference)

The full current document text is saved at `/tmp/doc_text.txt` (22,735 chars, 354 lines).
A backup should be made before any changes.

---

## ✅ COMPLETED — April 3, 2026

**All formatting changes applied successfully.**

### What was done:
1. **Full document rewrite via markdown upsert** — replaced entire doc content with properly structured markdown
2. **Executive Summary added** — 5-bullet TL;DR at top (did not exist before)
3. **Section renumbered** — "What We Did Well" promoted to Section 3; Bottlenecks → 4, Quality → 5, Hiring → 6, Recommendations → 7
4. **8 tables created** — Monthly Trend, Regional Throughput, Top 10 Leaderboard, Pipeline Aging, AU Current State, Hiring Pipeline, Partner Speed Ranking, Combined Path Timeline
5. **35 spreadsheet hyperlinks** — inline citations linking to specific tabs across all 5 supporting spreadsheets
6. **12 source citation lines** — formatted as italic with hyperlinked spreadsheet tab names
7. **Status tags colored** — "In Progress Already" (×3) and "Completed Already" (×2) in green; "Will Look Into" (×1) in amber
8. **Key callout labels bolded** — Key Insight, Critical context, Key takeaway, Recommendation, The bottom line
9. **CONFIDENTIAL tag** — bolded in subtitle
10. **Heading hierarchy fixed** — H1 title, H2 sections, H3 subsections, H4 for partner detail
11. **📊 emoji lines removed** — replaced with proper italic "Source:" citation lines
12. **Appendix created** — Methodology & Data Notes reformatted with What's Included / What's Excluded / Data Sources subsections
13. **Footer added** — "Last refreshed" and "Document prepared by GSO Operations"

### Verification: 28/28 checks passed
- All 7 sections + appendix present
- All 8 tables rendered
- All 5 spreadsheet IDs linked (35 total hyperlinks)
- All 3 status tag types formatted with color
- No data or numbers changed

### Note on spreadsheet access:
- Lead Time Detail (1JYVZh...) and Pipeline & Bottlenecks (1IjTJMjc...) returned 404 from the Sheets API — links use the GIDs from the plan file. If these spreadsheets were moved or permissions changed, the links may need updating.

---

## One-Pager Created — April 3, 2026

**Google Doc:** `1pXyfhEp6F7LVvHrOleh5x0dr4kvA_3uxdHx4kgY3--U`
[Open One-Pager](https://docs.google.com/document/d/1pXyfhEp6F7LVvHrOleh5x0dr4kvA_3uxdHx4kgY3--U/edit)

**Format:** 4 sections (Lead Times, Throughput, Bottlenecks, How Hiring & 3P Close the Gap), 7 tables, ~4,000 chars. Links back to full report and all 5 supporting spreadsheets. No fluff.

---

## 🔗 Link Audit — Completed

**Problem found:** 2 of 5 spreadsheet IDs in the original plan were stale/deleted:
- Lead Time Detail: `1JYVZh_DqJNRxFGpNK-f3VXvpMJB4VLkJSQMgxHE8Nqk` → 404
- Pipeline & Bottlenecks: `1IjTJMjcMVWlBGxVUuBFLFnNMqNjhKpzVfqoVVIi2jHg` → 404

**Corrected IDs (found via Drive search):**
- Lead Time Detail: `1Vlb4hQs0IttDxxQeoZWhZJ9TOP3YcVRkoJJ-lFtwTiY`
- Pipeline & Bottlenecks: `1rYdOySRc_oZ8jmbMXSXBBFaei4_eV0Z1B6vUbCNVfnw`

**All 16 hyperlinks in both documents verified:**
- 5 spreadsheets accessible ✅
- 16 tab GIDs cross-referenced against actual sheet listings ✅
- 0 broken links remaining ✅
- Both docs re-upserted with corrected URLs
- Formatting (green/amber status tags, bold) re-applied
