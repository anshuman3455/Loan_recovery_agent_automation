import pandas as pd
import os

def reconcile(base_file, compare_file):
    os.makedirs("output", exist_ok=True)
    base = pd.read_excel(base_file)
    comp = pd.read_excel(compare_file)

    # Merge on Account
    merged = base.merge(comp, on="Account", how="outer", suffixes=("_base", "_compare"), indicator=True)

    merged["Status"] = merged["_merge"].map({
        "both": "MATCH",
        "left_only": "MISSING_IN_COMPARE",
        "right_only": "MISSING_IN_BASE"
    })

    # Check for amount/name mismatches in matched rows
    if "Amount_base" in merged.columns and "Amount_compare" in merged.columns:
        merged.loc[
            (merged["Status"] == "MATCH") & 
            (merged["Amount_base"] != merged["Amount_compare"]),
            "Status"
        ] = "AMOUNT_MISMATCH"

    # AI suggested next steps
    merged["Suggested_Action"] = merged["Status"].map({
        "MATCH": "No action needed",
        "MISSING_IN_COMPARE": "Investigate: Record exists in base but not in compare file",
        "MISSING_IN_BASE": "Investigate: Record exists in compare but not in base file — possible new entry",
        "AMOUNT_MISMATCH": "URGENT: Amount differs between files — verify transaction records",
    })

    # Save differences file (non-matches only)
    differences = merged[merged["Status"] != "MATCH"].copy()
    differences.drop(columns=["_merge"], inplace=True, errors="ignore")
    differences.to_excel("output/differences_with_comments.xlsx", index=False)

    # Save full base data
    base.to_excel("output/base_data.xlsx", index=False)

    print(f"✅ Reconciliation complete!")
    print(f"   Total records: {len(merged)}")
    print(f"   Matches: {(merged['Status'] == 'MATCH').sum()}")
    print(f"   Differences: {(merged['Status'] != 'MATCH').sum()}")

    return merged