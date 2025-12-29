import pandas as pd

def run_component1(df: pd.DataFrame):
    """
    Serverless-safe version
    Expects a DataFrame (already loaded from Excel in app.py)
    """

    # -------------------------
    # CLEAN COLUMN NAMES
    # -------------------------
    df = df.copy()
    df.columns = df.columns.str.strip()

    # -------------------------
    # REQUIRED COLUMNS
    # -------------------------
    required_cols = [
        "Document No.",
        "Transfer-from Code",
        "Transfer-to Code",
        "Quantity",
        "Quantity Shipped",
        "Quantity Received",
        "Created At"
    ]

    df = df[required_cols]

    # -------------------------
    # BASIC CLEANING
    # -------------------------
    df = df.dropna(subset=["Document No.", "Created At"])

    for col in ["Quantity", "Quantity Shipped", "Quantity Received"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Transfer-from Code"] = df["Transfer-from Code"].astype(str)
    df["Transfer-to Code"] = df["Transfer-to Code"].astype(str)

    df["Created At"] = pd.to_datetime(df["Created At"], errors="coerce")
    df = df.dropna(subset=["Created At"])

    # -------------------------
    # LF → LF FILTER
    # -------------------------
    df = df[
        df["Transfer-from Code"].str.startswith("LF-") &
        df["Transfer-to Code"].str.startswith("LF-")
    ]

    # -------------------------
    # AGGREGATION LOGIC
    # -------------------------
    records = []

    for doc_no, g in df.groupby("Document No."):
        total_qty = g["Quantity"].sum()
        shipped_qty = g["Quantity Shipped"].sum()
        received_qty = g["Quantity Received"].sum()

        if received_qty >= shipped_qty:
            status = "Completed"
        elif shipped_qty >= total_qty:
            status = "In Transit"
        else:
            status = "Partially Shipped"

        created_at = g["Created At"].min()

        records.append({
            "Document No": doc_no,
            "Total Qty": total_qty,
            "Shipped Qty": shipped_qty,
            "Received Qty": received_qty,
            "In Transit Qty": shipped_qty - received_qty,
            "Status": status,
            "Month": created_at.strftime("%Y-%m")
        })

    df_orders = pd.DataFrame(records)

    # -------------------------
    # SUMMARY
    # -------------------------
    summary = {
        "Total": len(df_orders),
        "Completed": int((df_orders["Status"] == "Completed").sum()),
        "In Transit": int((df_orders["Status"] == "In Transit").sum()),
        "Partially Shipped": int((df_orders["Status"] == "Partially Shipped").sum())
    }

    return summary, df_orders
