#!/usr/bin/env python3
"""Load DSA vendor records from CSV into Airtable DSA Activities table."""

import csv
import json
import sys
import os

CSV_PATH = os.path.expanduser("~/dsa_vendor_records_2yr.csv")
OUTPUT_PATH = os.path.expanduser("~/dsa_airtable_records.json")

def parse_csv():
    """Parse the CSV and return list of Airtable-ready records."""
    records = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Map CSV columns to Airtable fields
            rec = {
                "DSA ID": row.get("DSA_ID", "").strip(),
                "DSA Name": row.get("DSA_NAME", "").strip(),
                "Activity Type": row.get("ACTIVITY_TYPE_C", "").strip() or None,
                "Status": row.get("STATUS_C", "").strip() or None,
                "Partner": row.get("PARTNER_NAME", "").strip(),
                "Partner Account ID": row.get("PARTNER_ACCOUNT_ID", "").strip(),
                "Seller": row.get("SELLER", "").strip(),
                "DSR ID": row.get("DSR_ID", "").strip(),
                "Created Date": row.get("CREATED_DATE", "").strip() or None,
                "Scheduled Date": row.get("SCHEDULED_DATE", "").strip() or None,
                "Completed Date": row.get("COMPLETED_DATE", "").strip() or None,
                "Rush": row.get("RUSH", "").strip().lower() == "true",
                "Technician": row.get("TECHNICIAN", "").strip() or None,
                "Owner": row.get("OWNER_NAME", "").strip() or None,
                "Region": row.get("REGION_CURRENCY", "").strip() or None,
                "Difficulty": row.get("DIFFICULTY_C", "").strip() or None,
                "Notes": (row.get("NOTES", "") or "").strip()[:1000] or None,
                "Source": "Snowflake DSA",
            }
            
            # Parse CSAT score
            csat = row.get("CSAT_SCORE_C", "").strip()
            if csat and csat not in ("", "None", "null"):
                try:
                    rec["CSAT Score"] = float(csat)
                except ValueError:
                    pass
            
            # Parse price
            price = row.get("PRICE", "").strip()
            if price and price not in ("", "None", "null"):
                try:
                    rec["Price"] = float(price)
                except ValueError:
                    pass
            
            # Clean up None values
            rec = {k: v for k, v in rec.items() if v is not None and v != ""}
            
            if rec.get("DSA ID"):
                records.append(rec)
    
    return records

def main():
    print(f"Reading CSV from {CSV_PATH}...")
    records = parse_csv()
    print(f"Parsed {len(records)} records")
    
    # Deduplicate by DSA ID
    seen = set()
    unique = []
    for r in records:
        dsa_id = r["DSA ID"]
        if dsa_id not in seen:
            seen.add(dsa_id)
            unique.append(r)
    
    print(f"Unique records: {len(unique)} (removed {len(records) - len(unique)} duplicates)")
    
    # Get activity type and status distributions
    activity_types = {}
    statuses = {}
    partners = {}
    for r in unique:
        at = r.get("Activity Type", "Unknown")
        activity_types[at] = activity_types.get(at, 0) + 1
        st = r.get("Status", "Unknown")
        statuses[st] = statuses.get(st, 0) + 1
        p = r.get("Partner", "Unknown")
        partners[p] = partners.get(p, 0) + 1
    
    print(f"\nActivity Types ({len(activity_types)}):")
    for k, v in sorted(activity_types.items(), key=lambda x: -x[1])[:20]:
        print(f"  {k}: {v}")
    
    print(f"\nStatuses ({len(statuses)}):")
    for k, v in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    
    print(f"\nPartners ({len(partners)}):")
    for k, v in sorted(partners.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")
    
    # Save as JSON for loading
    # Format as Airtable batch records
    batches = []
    batch = []
    for r in unique:
        batch.append({"fields": r})
        if len(batch) == 10:
            batches.append(batch)
            batch = []
    if batch:
        batches.append(batch)
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(batches, f)
    
    print(f"\nSaved {len(batches)} batches ({len(unique)} records) to {OUTPUT_PATH}")
    print(f"Ready for Airtable upload")

if __name__ == "__main__":
    main()
