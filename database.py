import os
import csv
import pandas as pd
from datetime import datetime

RESULTS_FILE = "data/call_results.csv"
FIELDNAMES = ["id", "account", "name", "status", "next_payment_date", "conversation", "called_at"]

def init_db():
    """Create CSV file with headers if it doesn't exist."""
    os.makedirs("data", exist_ok=True)
    if not os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        print(f"✅ Created {RESULTS_FILE}")

def _get_next_id():
    """Auto-increment ID based on existing rows."""
    if not os.path.exists(RESULTS_FILE):
        return 1
    df = pd.read_csv(RESULTS_FILE)
    if df.empty:
        return 1
    return int(df["id"].max()) + 1

def save_call_result(account, name, status, next_payment_date=None, conversation=None):
    """Append a new result row to the CSV."""
    init_db()
    row = {
        "id": _get_next_id(),
        "account": account,
        "name": name,
        "status": status,
        "next_payment_date": next_payment_date or "",
        "conversation": (conversation or "").replace("\n", " "),  # flatten for CSV
        "called_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    with open(RESULTS_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
    print(f"💾 Saved result for {name} ({account}) → {status}")

def get_all_results():
    """Read all results from CSV as a DataFrame."""
    init_db()
    if not os.path.exists(RESULTS_FILE):
        return pd.DataFrame(columns=FIELDNAMES)
    return pd.read_csv(RESULTS_FILE)

def update_input_file(input_file="data/input.xlsx"):
    """
    After calls, merge call results back into input Excel
    so you can see call status alongside original data.
    Saves updated file to data/input_with_results.xlsx
    """
    results_df = get_all_results()
    if results_df.empty:
        print("⚠️  No call results to merge yet.")
        return

    input_df = pd.read_excel(input_file)
    input_df["Account"] = input_df["Account"].astype(str)
    results_df["account"] = results_df["account"].astype(str)

    merged = input_df.merge(
        results_df[["account", "status", "next_payment_date", "called_at"]],
        left_on="Account",
        right_on="account",
        how="left"
    ).drop(columns=["account"])

    merged.rename(columns={
        "status": "Call_Status",
        "next_payment_date": "Next_Payment_Date",
        "called_at": "Last_Called_At"
    }, inplace=True)

    out_path = "data/input_with_results.xlsx"
    merged.to_excel(out_path, index=False)
    print(f"✅ Updated input file saved → {out_path}")
    return merged

# Auto-init on import
init_db()