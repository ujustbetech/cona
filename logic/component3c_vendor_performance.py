import pandas as pd

FILE_PATH = "data/Vendor_Performance.xlsx"


def run_component3c():

    # ---------------- LOAD FILE ----------------
    df = pd.read_excel(FILE_PATH)
    df.columns = df.columns.str.strip()

    # ---------------- RENAME (SAFE NORMALIZATION) ----------------
    df = df.rename(columns={
        "Vendor Name": "Vendor",
        "Performance Bucket": "Bucket"
    })

    # ---------------- CLEAN ----------------
    df = df.dropna(subset=["Vendor", "Bucket"])

    # ---------------- BUCKET SUMMARY ----------------
    bucket_summary = (
        df["Bucket"]
        .value_counts()
        .reset_index()
    )
    bucket_summary.columns = ["Bucket", "Vendor_Count"]

    total_vendors = bucket_summary["Vendor_Count"].sum()

    bucket_summary["Percentage"] = (
        bucket_summary["Vendor_Count"] / total_vendors * 100
    ).round(2)

    metrics = {
        "Total_Vendors": total_vendors
    }

    return metrics, df, bucket_summary
