import pandas as pd


def run_component6(df: pd.DataFrame):
    """
    Component 6 — Short-Closed Sales Orders
    Serverless-safe (Vercel compatible)
    Logic preserved exactly
    """

    # ---------------- COPY & CLEAN ----------------
    df = df.copy()
    df.columns = df.columns.str.strip()

    # ---------------- RENAME (SAFE) ----------------
    df = df.rename(columns={
        "No.": "SO_No",
        "Document Date": "Document_Date",
        "Completely Shipped": "Completely_Shipped",
        "Short Closed": "Short_Closed"
    })

    # ---------------- FILTER NON-SHIPPED ----------------
    df = df[df["Completely_Shipped"] == False]

    # ---------------- DATE CLEANING ----------------
    df["Document_Date"] = pd.to_datetime(
        df["Document_Date"], errors="coerce"
    )

    df = df.dropna(subset=["Document_Date"])

    # ---------------- MONTH EXTRACTION ----------------
    df["Month"] = (
        df["Document_Date"]
        .dt.to_period("M")
        .astype(str)
    )

    # ---------------- MONTHLY METRICS ----------------
    monthly = (
        df.groupby("Month")
        .agg(
            Total_Non_Shipped=("SO_No", "count"),
            Short_Closed=("Short_Closed", lambda x: (x == True).sum())
        )
        .reset_index()
    )

    monthly["Not_Short_Closed"] = (
        monthly["Total_Non_Shipped"] -
        monthly["Short_Closed"]
    )

    # ---------------- OVERALL METRICS ----------------
    total_non_shipped = int(len(df))
    total_short_closed = int(
        (df["Short_Closed"] == True).sum()
    )

    metrics = {
        "Total_Non_Shipped": total_non_shipped,
        "Short_Closed": total_short_closed,
        "Not_Short_Closed": total_non_shipped - total_short_closed,
        "Short_Closed_Pct": round(
            (total_short_closed / total_non_shipped) * 100,
            2
        ) if total_non_shipped else 0
    }

    return metrics, monthly
