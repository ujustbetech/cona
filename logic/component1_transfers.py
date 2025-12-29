import pandas as pd

INPUT_FILE = "data/Transfer Lines.xlsx"
OUTPUT_FILE = "outputs/component1_transfer_report.xlsx"

def run_component1():
    df = pd.read_excel(INPUT_FILE)
    df.columns = df.columns.str.strip()

    # Required columns only
    df = df[
        [
            "Document No.",
            "Transfer-from Code",
            "Transfer-to Code",
            "Quantity",
            "Quantity Shipped",
            "Quantity Received",
            "Created At"
        ]
    ]

    # Cleaning
    df = df.dropna(subset=["Document No.", "Created At"])
    for col in ["Quantity", "Quantity Shipped", "Quantity Received"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["Transfer-from Code"] = df["Transfer-from Code"].astype(str)
    df["Transfer-to Code"] = df["Transfer-to Code"].astype(str)
    df["Created At"] = pd.to_datetime(df["Created At"], errors="coerce")
    df = df.dropna(subset=["Created At"])

    # LF → LF filter
    df = df[
        df["Transfer-from Code"].str.startswith("LF-") &
        df["Transfer-to Code"].str.startswith("LF-")
    ]

    records = []

    for doc, g in df.groupby("Document No."):
        total_qty = g["Quantity"].sum()
        shipped = g["Quantity Shipped"].sum()
        received = g["Quantity Received"].sum()

        if received >= shipped:
            status = "Completed"
        elif shipped >= total_qty:
            status = "In Transit"
        else:
            status = "Partially Shipped"

        created_at = g["Created At"].min()

        records.append({
            "Document No": doc,
            "Total Qty": total_qty,
            "Shipped Qty": shipped,
            "Received Qty": received,
            "In Transit Qty": shipped - received,
            "Status": status,
            "Month": created_at.strftime("%Y-%m")
        })

    df_orders = pd.DataFrame(records)

    # Save output
    df_orders.to_excel(OUTPUT_FILE, index=False)

    summary = {
        "Total": len(df_orders),
        "Completed": int((df_orders["Status"] == "Completed").sum()),
        "In Transit": int((df_orders["Status"] == "In Transit").sum()),
        "Partially Shipped": int((df_orders["Status"] == "Partially Shipped").sum())
    }

    return summary, df_orders
