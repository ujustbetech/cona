import pandas as pd


def run_component3c(df: pd.DataFrame):
    """
    Component 3C — Vendor Performance (Bucket-wise)
    Serverless-safe (Vercel compatible)
    Logic preserved exactly
    """

    # ---------------- COPY & CLEAN ----------------
    df = df.copy()
    df.columns = df.columns.str.strip()

    # ---------------- RENAME (SAFE NORMALIZATION) ----------------
    df = df.rename(columns={
        "Vendor Name": "Vendor",
        "Performance Bucket": "Bucket"
    })

    # ---------------- CLEAN ----------------
    df = df.dropna(subset=["Vendor", "Bucket"])

    df["Vendor"] = df["Vendor"].astype(str).str.strip()
    df["Bucket"] = df["Bucket"].astype(str).str.strip()

    # ---------------- BUCKET SUMMARY ----------------
    bucket_summary = (
        df["Bucket"]
        .value_counts()
        .reset_index()
    )

    bucket_summary.columns = [
        "Bucket",
        "Vendor_Count"
    ]

    total_vendors = int(
        bucket_summary["Vendor_Count"].sum()
    )

    bucket_summary["Percentage"] = (
        bucket_summary["Vendor_Count"] /
        total_vendors * 100
    ).round(2)

    # ---------------- METRICS ----------------
    metrics = {
        "Total_Vendors": total_vendors
    }

    return metrics, df, bucket_summary
