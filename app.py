from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask_caching import Cache

# ---------------- COMPONENT IMPORTS ----------------
from logic.component1_transfers import run_component1
from logic.component2_inventory import run_component2
from logic.component3a_vendor_ontime import run_component3a
from logic.component3b_order_delivery import run_component3b
from logic.component3c_vendor_performance import run_component3c
from logic.component4_sales_invoice import run_component4
from logic.component5_po_sla import run_component5
from logic.component5a_rm_quarterly import run_component5a_rm
from logic.component6_short_closed_so import run_component6
from logic.component7_cost_optimization import run_component7

# --------------------------------------------------
# APP INIT
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = "kt-secret-key"

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1800  # 30 mins
})

# --------------------------------------------------
# USERS (TEMP)
# --------------------------------------------------
USERS = {"admin": "admin123"}

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if USERS.get(request.form["username"]) == request.form["password"]:
            session["user"] = request.form["username"]
            return redirect(url_for("upload"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# --------------------------------------------------
# UPLOAD (GENERIC – ALL FILES)
# --------------------------------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            files = request.files

            # ---- MASTER DATA ----
            if "transfer_file" in files:
                cache.set("transfer_df", pd.read_excel(files["transfer_file"]))

            if "ledger_file" in files:
                cache.set("ledger_df", pd.read_excel(files["ledger_file"]))

            if "items_file" in files:
                cache.set("items_df", pd.read_excel(files["items_file"]))

            # ---- PURCHASE ----
            if "po_file" in files:
                cache.set("po_df", pd.read_excel(files["po_file"]))

            if "receipt_file" in files:
                cache.set("receipt_df", pd.read_excel(files["receipt_file"]))

            if "lines_file" in files:
                cache.set("lines_df", pd.read_excel(files["lines_file"]))

            # ---- SALES ----
            if "sales_order_file" in files:
                cache.set("sales_order_df", pd.read_excel(files["sales_order_file"]))

            if "sales_invoice_file" in files:
                cache.set("sales_invoice_df", pd.read_excel(files["sales_invoice_file"]))

            # ---- VENDOR PERFORMANCE ----
            if "vendor_perf_file" in files:
                cache.set("vendor_performance_df", pd.read_excel(files["vendor_perf_file"]))

        except Exception as e:
            return f"Upload failed: {e}", 500

        return redirect(url_for("departments"))

    return render_template("upload.html")

# --------------------------------------------------
# DEPARTMENTS
# --------------------------------------------------
@app.route("/departments")
def departments():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("departments.html", departments=["Purchase", "Sales & Marketing"])

# --------------------------------------------------
# COMPONENT 1
# --------------------------------------------------
@app.route("/dashboard/component1")
def component1_dashboard():
    df = cache.get("transfer_df")
    if df is None:
        return redirect(url_for("upload"))

    summary, df = run_component1(df)

    total = sum(summary.values())
    completed = summary.get("Completed", 0)
    on_time_pct = round((completed / total) * 100, 2) if total else 0

    status_df = df["Status"].value_counts().reset_index()
    status_df.columns = ["Status", "Count"]

    status_bar = px.bar(status_df, x="Status", y="Count", text="Count")

    return render_template(
        "component1.html",
        summary=summary,
        on_time_pct=on_time_pct,
        status_bar=pio.to_html(status_bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 2
# --------------------------------------------------
@app.route("/dashboard/component2")
def component2_dashboard():
    df = cache.get("ledger_df")
    if df is None:
        return redirect(url_for("upload"))

    summary, _ = run_component2(df)

    bar_df = pd.DataFrame({
        "Status": ["Active", "Slow-Moving", "Dead"],
        "Count": [
            summary["Active Items"],
            summary["Slow-Moving Items"],
            summary["Dead Items"]
        ]
    })

    bar = px.bar(bar_df, x="Status", y="Count", text="Count")

    return render_template(
        "component2.html",
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 3A
# --------------------------------------------------
@app.route("/dashboard/component3a")
def component3a_dashboard():
    df_po = cache.get("po_df")
    df_rcpt = cache.get("receipt_df")
    df_lines = cache.get("lines_df")

    if not all([df_po, df_rcpt, df_lines]):
        return redirect(url_for("upload"))

    metrics, vendor_df = run_component3a(df_po, df_rcpt, df_lines)

    bar = px.bar(vendor_df, x="Vendor", y="On_Time_Pct", text="On_Time_Pct")

    return render_template(
        "component3a_vendor_management.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 3B
# --------------------------------------------------
@app.route("/dashboard/component3b")
def component3b_dashboard():
    df_po = cache.get("po_df")
    df_rcpt = cache.get("receipt_df")
    df_lines = cache.get("lines_df")

    if not all([df_po, df_rcpt, df_lines]):
        return redirect(url_for("upload"))

    metrics, df = run_component3b(df_po, df_rcpt, df_lines)

    pie_df = pd.DataFrame({
        "Status": ["On-Time", "Delayed"],
        "Count": [metrics["On_Time"], metrics["Delayed"]]
    })

    pie = px.pie(pie_df, names="Status", values="Count")

    trend_df = df.groupby(["Month", "Delivery_Status"]).size().reset_index(name="Count")
    bar = px.bar(trend_df, x="Month", y="Count", color="Delivery_Status")

    return render_template(
        "component3b_order_delivery.html",
        metrics=metrics,
        pie_chart=pio.to_html(pie, full_html=False),
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 3C
# --------------------------------------------------
@app.route("/dashboard/component3c")
def component3c_dashboard():
    df = cache.get("vendor_performance_df")
    if df is None:
        return redirect(url_for("upload"))

    metrics, _, bucket_df = run_component3c(df)

    bar = px.bar(bucket_df, x="Bucket", y="Vendor_Count", text="Vendor_Count")
    pie = px.pie(bucket_df, names="Bucket", values="Vendor_Count")

    return render_template(
        "component3c_vendor_performance.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False),
        pie_chart=pio.to_html(pie, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 4
# --------------------------------------------------
@app.route("/dashboard/component4")
def component4_dashboard():
    df_so = cache.get("sales_order_df")
    df_inv = cache.get("sales_invoice_df")

    if not all([df_so, df_inv]):
        return redirect(url_for("upload"))

    metrics, df = run_component4(df_so, df_inv)

    return render_template(
        "component4.html",
        metrics=metrics
    )

# --------------------------------------------------
# COMPONENT 5
# --------------------------------------------------
@app.route("/dashboard/component5")
def component5_dashboard():
    df_po = cache.get("po_df")
    df_rcpt = cache.get("receipt_df")
    df_lines = cache.get("lines_df")

    if not all([df_po, df_rcpt, df_lines]):
        return redirect(url_for("upload"))

    metrics, df = run_component5(df_po, df_rcpt, df_lines)

    bar = px.bar(df.groupby("Month").size().reset_index(name="Completed POs"),
                 x="Month", y="Completed POs")

    return render_template(
        "component5.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 5A
# --------------------------------------------------
@app.route("/dashboard/component5a_rm")
def component5a_rm_dashboard():
    df_items = cache.get("items_df")
    df_po = cache.get("po_df")
    df_rcpt = cache.get("receipt_df")
    df_lines = cache.get("lines_df")

    if not all([df_items, df_po, df_rcpt, df_lines]):
        return redirect(url_for("upload"))

    metrics, df_monthly = run_component5a_rm(df_items, df_po, df_rcpt, df_lines)

    bar = px.bar(df_monthly, x="Month", y="PO_Count", color="SLA_Status")

    return render_template(
        "component5a_rm.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 6
# --------------------------------------------------
@app.route("/dashboard/component6")
def component6_dashboard():
    df = cache.get("sales_order_df")
    if df is None:
        return redirect(url_for("upload"))

    metrics, df_monthly = run_component6(df)

    bar = px.bar(df_monthly, x="Month",
                 y=["Short_Closed", "Not_Short_Closed"],
                 barmode="stack")

    return render_template(
        "component6.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 7A / 7B
# --------------------------------------------------
@app.route("/dashboard/component7a")
@app.route("/dashboard/component7b")
def component7_dashboard():
    df_items = cache.get("items_df")
    df_ledger = cache.get("ledger_df")

    if not all([df_items, df_ledger]):
        return redirect(url_for("upload"))

    df, _, company_view = run_component7(df_items, df_ledger)

    summary = df["Stock_Status"].value_counts().to_dict()

    bar = px.bar(
        company_view.groupby("Stock_Status")["Total_Qty"].sum().reset_index(),
        x="Stock_Status",
        y="Total_Qty"
    )

    template = (
        "component7a_supply_availability.html"
        if request.path.endswith("7a")
        else "component7b_packaging_stoppage.html"
    )

    return render_template(
        template,
        summary=summary,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# LOGOUT
# --------------------------------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --------------------------------------------------
# RUN
# --------------------------------------------------
app = app
