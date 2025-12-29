import pandas as pd
import numpy as np
import os

DATA_DIR = "data"
OUTPUT_FILE = "outputs/component4_sales_invoice.xlsx"

# --------------------------------------------------
# HELPER: FIND FILE
# --------------------------------------------------
def find_file(keyword):
    for f in os.listdir(DATA_DIR):
        if keyword.lower() in f.lower() and f.endswith(".xlsx"):
            return os.path.join(DATA_DIR, f)
    raise FileNotFoundError(f"File containing '{keyword}' not found")

# --------------------------------------------------
# MAIN FUNCTION
# --------------------------------------------------
def run_component4():

    # ---------------- FILES ----------------
    so_file = find_file("sales order")
    inv_file = find_file("posted sales invoice")

    # ---------------- SALES ORDER ----------------
    df_so = pd.read_excel(so_file)
    df_so.columns = df_so.columns.str.strip()

    # Detect SO number column
    if "No." in df_so.columns:
        so_col = "No."
    elif "No" in df_so.columns:
        so_col = "No"
    elif "Document No." in df_so.columns:
        so_col = "Document No."
    else:
        raise KeyError(f"SO number column not found. Found: {df_so.columns.tolist()}")

    df_so = df_so[
        [so_col, "Document Date", "Completely Shipped"]
    ].copy()

    df_so.columns = ["SO_No", "SO_Date", "Completely_Shipped"]

    df_so["SO_No"] = df_so["SO_No"].astype(str).str.strip().str.upper()
    df_so["SO_Date"] = pd.to_datetime(df_so["SO_Date"], errors="coerce")
    df_so["Completely_Shipped"] = df_so["Completely_Shipped"].fillna(0).astype(int)

    df_so = df_so.dropna(subset=["SO_Date"])

    # ---------------- PART A: SHIPMENT COMPLETION ----------------
    total_sos = len(df_so)
    shipped_sos = df_so["Completely_Shipped"].sum()
    shipment_pct = round((shipped_sos / total_sos) * 100, 2) if total_sos else 0

    # ---------------- INVOICE FILE ----------------
    df_inv = pd.read_excel(inv_file)
    df_inv.columns = df_inv.columns.str.strip()

    # Detect Order No column
    if "Order No." in df_inv.columns:
        inv_so_col = "Order No."
    elif "Order No" in df_inv.columns:
        inv_so_col = "Order No"
    else:
        raise KeyError(
            f"Invoice Order No column not found. Found: {df_inv.columns.tolist()}"
        )

    df_inv = df_inv[[inv_so_col, "Posting Date"]].copy()
    df_inv.columns = ["SO_No", "Invoice_Date"]

    df_inv["SO_No"] = df_inv["SO_No"].astype(str).str.strip().str.upper()
    df_inv["Invoice_Date"] = pd.to_datetime(df_inv["Invoice_Date"], errors="coerce")
    df_inv = df_inv.dropna(subset=["Invoice_Date"])

    # ---------------- PART B: O2C CYCLE ----------------
    latest_invoice = (
        df_inv.groupby("SO_No")["Invoice_Date"]
        .max()
        .reset_index()
    )

    df_main = df_so.merge(latest_invoice, on="SO_No", how="left")

    df_main["O2C_Days"] = (
        df_main["Invoice_Date"] - df_main["SO_Date"]
    ).dt.days

    # Valid KT range
    df_valid = df_main[
        (df_main["O2C_Days"] >= 0) &
        (df_main["O2C_Days"] <= 365)
    ].copy()

    # ---------------- METRICS ----------------
    avg_cycle = round(df_valid["O2C_Days"].mean(), 2)
    median_cycle = round(df_valid["O2C_Days"].median(), 2)
    p95_cycle = round(np.percentile(df_valid["O2C_Days"], 95), 2)

    metrics = {
        "total_sos": total_sos,
        "shipment_pct": shipment_pct,
        "avg_cycle": avg_cycle,
        "median_cycle": median_cycle,
        "pct_7": round((df_valid["O2C_Days"] <= 7).mean() * 100, 2),
        "pct_14": round((df_valid["O2C_Days"] <= 14).mean() * 100, 2),
        "pct_30": round((df_valid["O2C_Days"] <= 30).mean() * 100, 2),
        "pct_60": round((df_valid["O2C_Days"] <= 60).mean() * 100, 2),
        "p95_cycle": p95_cycle
    }

    # ---------------- SAVE OUTPUT ----------------
    os.makedirs("outputs", exist_ok=True)
    with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:
        df_main.to_excel(writer, "SO_Invoice_Detail", index=False)
        df_valid.to_excel(writer, "Valid_O2C_Records", index=False)

    return metrics, df_valid
