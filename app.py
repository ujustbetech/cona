from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask_caching import Cache


from logic.component1_transfers import run_component1
from logic.component2_inventory import run_component2
from logic.component4_sales_invoice import run_component4
from logic.component5_po_sla import run_component5
from logic.component6_short_closed_so import run_component6
from logic.component7_cost_optimization import run_component7
from logic.component3a_vendor_ontime import run_component3a
from logic.component3b_order_delivery import run_component3b
from logic.component3c_vendor_performance import run_component3c
from logic.component5a_rm_quarterly import run_component5a_rm




# --------------------------------------------------
# APP INIT
# --------------------------------------------------
app = Flask(__name__)
app.secret_key = "kt-secret-key"

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",  # memory cache
    "CACHE_DEFAULT_TIMEOUT": 300  # 5 minutes
})
# --------------------------------------------------
# USERS
# --------------------------------------------------
USERS = {
    "admin": "admin123"
}

# --------------------------------------------------
# LOGIN
# --------------------------------------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if USERS.get(request.form["username"]) == request.form["password"]:
            session["user"] = request.form["username"]
            return redirect(url_for("departments"))
        return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")

# --------------------------------------------------
# DEPARTMENTS
# --------------------------------------------------
@app.route("/departments")
def departments():
    if "user" not in session:
        return redirect(url_for("login"))

    departments = ["Purchase", "Sales & Marketing"]
    return render_template("departments.html", departments=departments)

# --------------------------------------------------
# SUB-DEPARTMENTS
# --------------------------------------------------
@app.route("/subdepartments/<department>")
def subdepartments(department):
    if "user" not in session:
        return redirect(url_for("login"))

    department = department.strip()

    if department == "Purchase":
        return redirect(url_for("kras", department=department))

    subdeps = ["LED", "Marketing", "Packaging", "Procurement & Vendor Management" ]
    return render_template(
        "subdepartments.html",
        department=department,
        subdepartments=subdeps
    )

# --------------------------------------------------
# KRAs
# --------------------------------------------------
@app.route("/kras/<department>")
@app.route("/kras/<department>/<subdepartment>")
def kras(department, subdepartment=None):
    if "user" not in session:
        return redirect(url_for("login"))

    department = department.strip()
    subdepartment = subdepartment.strip() if subdepartment else None

    if department == "Purchase":
        kras = [
            "Internal Raw Material Transfer",
            "Sales Order & Invoice Management",
            "Sales Order & Invoice Management – Short Closure",
            "Order Delivery Tracking"
        ]

    elif department == "Sales & Marketing" and subdepartment == "LED":
        kras = [
            "Inventory and Supply Chain Mgmt"
        ]

    elif department == "Sales & Marketing" and subdepartment == "Marketing":
        kras = [
            "Seasonal Campaign Execution",
            "Vendor Management"
        ]
    elif department == "Sales & Marketing" and subdepartment == "Packaging":
        kras = [
            "Cost Optimization"   # ✅ COMPONENT 7 KRA
        ]
    elif department == "Sales & Marketing" and subdepartment == "Procurement & Vendor Management":
        kras = [
            "Cost Optimization",
            "Business Development"  # ✅ COMPONENT 7 KRA
        ] 
          
 
    else:
        kras = []

    return render_template(
        "kras.html",
        department=department,
        subdepartment=subdepartment,
        kras=kras
    )

# --------------------------------------------------
# KPI LIST (FIXED & CLEAN)
# --------------------------------------------------
@app.route("/kpis/<department>/<kra>")
@app.route("/kpis/<department>/<subdepartment>/<kra>")
def kpis(department, kra, subdepartment=None):
    if "user" not in session:
        return redirect(url_for("login"))

    kra = kra.strip()
    subdepartment = subdepartment.strip() if subdepartment else None
    kpis = []

    # ---------------- PURCHASE ----------------
    if kra == "Internal Raw Material Transfer":
        kpis = ["% of Transfers Completed on Schedule"]

    elif kra == "Inventory and Supply Chain Mgmt":
        kpis = ["% of Slow Stock & Dead Stock"]

    elif kra == "Sales Order & Invoice Management":
        kpis = ["% SO to Shipment Completion & O2C Cycle"]

    elif kra == "Sales Order & Invoice Management – Short Closure":
        kpis = ["% Short-Closed for Non-Shipped SOs"]

    elif kra == "Order Delivery Tracking":
        kpis = ["% of deliveries received on time"]

    # ---------------- SALES & MARKETING ----------------
    elif kra == "Seasonal Campaign Execution":
        kpis = ["100% RM requisitions fulfilled within defined SLA"]

    elif kra == "Vendor Management":
        kpis = ["95% on-time delivery rate from vendors"]

    elif kra == "Business Development":
        kpis = ["Track and evaluate vendor performance regularly"]

    elif kra == "Cost Optimization":
        if subdepartment == "Packaging":
            kpis = ["100% Supply Availability"]

        elif subdepartment == "Procurement & Vendor Management":
            kpis = ["Zero Production Stoppages due to Packaging Shortages"]

    return render_template(
        "kpis.html",
        department=department,
        subdepartment=subdepartment,
        kra=kra,
        kpis=kpis
    )


# --------------------------------------------------
# KPI → DASHBOARD REDIRECT
# --------------------------------------------------
@app.route("/kpi-redirect/<department>/<kra>/<kpi>")
@app.route("/kpi-redirect/<department>/<subdepartment>/<kra>/<kpi>")
def kpi_redirect(department, kra, kpi, subdepartment=None):
    if "user" not in session:
        return redirect(url_for("login"))

    if kpi == "% of Transfers Completed on Schedule":
        return redirect(url_for("component1_dashboard"))

    if kpi == "% of Slow Stock & Dead Stock":
        return redirect(url_for("component2_dashboard"))

    if kpi == "% SO to Shipment Completion & O2C Cycle":
        return redirect(url_for("component4_dashboard"))

    if kpi == "100% RM requisitions fulfilled within defined SLA":
        return redirect(url_for("component5a_rm_dashboard"))

    if kpi == "% Short-Closed for Non-Shipped SOs":
        return redirect(url_for("component6_dashboard"))

    if kpi == "100% Supply Availability":
        return redirect(url_for("component7a_dashboard"))

    if kpi == "Zero Production Stoppages due to Packaging Shortages":
        return redirect(url_for("component7b_dashboard"))
    
    if kpi == "95% on-time delivery rate from vendors":
        return redirect(url_for("component3a_dashboard"))

    if kpi == "% of deliveries received on time":
        return redirect(url_for("component3b_dashboard"))

    if kpi == "Track and evaluate vendor performance regularly":
        return redirect(url_for("component3c_dashboard"))


    return "Dashboard not implemented"

@app.route("/dashboard/component1")
def component1_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    summary, df = run_component1()

    # ---------------- KPI ----------------
    total = sum(summary.values())
    completed = summary.get("Completed", 0)
    on_time_pct = round((completed / total) * 100, 2) if total else 0

    # ---------------- STATUS BAR ----------------
    status_df = (
        df["Status"]
        .value_counts()
        .reset_index()
    )
    status_df.columns = ["Status", "Count"]

    status_bar = px.bar(
        status_df,
        x="Status",
        y="Count",
        text="Count",
        title="Transfer Orders by Status"
    )

    # ---------------- MoM PENDING TRANSFERS ----------------
    pending_df = df[df["Status"] == "Pending"]

    if not pending_df.empty:
        mom_df = (
            pending_df.groupby("Month")
            .size()
            .reset_index(name="Pending Orders")
        )

        mom_bar = px.bar(
            mom_df,
            x="Month",
            y="Pending Orders",
            text="Pending Orders",
            title="Month-on-Month Pending Transfers"
        )
        mom_bar_html = pio.to_html(mom_bar, full_html=False)
    else:
        mom_bar_html = "<p>No pending transfers found.</p>"

    return render_template(
        "component1.html",
        summary=summary,
        on_time_pct=on_time_pct,
        status_bar=pio.to_html(status_bar, full_html=False),
        mom_bar=mom_bar_html
    )



# --------------------------------------------------
# COMPONENT 2
# --------------------------------------------------
@app.route("/dashboard/component2")
def component2_dashboard():
    summary, df = run_component2()

    status_df = pd.DataFrame({
        "Status": ["Active", "Slow-Moving", "Dead"],
        "Count": [
            summary.get("Active Items", 0),
            summary.get("Slow-Moving Items", 0),
            summary.get("Dead Items", 0)
        ]
    })

    bar = px.bar(
        status_df,
        x="Status",
        y="Count",
        text="Count",
        title="Inventory Classification"
    )

    bar.update_traces(textposition="outside")
    bar.update_layout(yaxis_title="Count", xaxis_title="Status")

    return render_template(
        "component2.html",
        bar_chart=pio.to_html(bar, full_html=False)
    )


# --------------------------------------------------
# COMPONENT 3A — Vendor Management
# --------------------------------------------------
# --------------------------------------------------
# COMPONENT 3A — Vendor Management
# --------------------------------------------------
@app.route("/dashboard/component3a")
def component3a_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    metrics, vendor_df = run_component3a()

    # -------- BAR CHART: ON-TIME % BY VENDOR --------
    bar_fig = px.bar(
        vendor_df,
        x="Vendor",
        y="On_Time_Pct",
        text="On_Time_Pct",
        color=vendor_df["On_Time_Pct"] < 95,
        color_discrete_map={
            True: "#e74c3c",   # Red → below SLA
            False: "#2ecc71"  # Green → meets SLA
        },
        title="Vendor On-Time Delivery Performance (%)"
    )

    bar_fig.update_layout(
        yaxis_title="On-Time Delivery %",
        xaxis_title="Vendor",
        showlegend=False
    )

    bar_fig.update_traces(texttemplate="%{text}%", textposition="outside")

    return render_template(
        "component3a_vendor_management.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar_fig, full_html=False)
    )


# --------------------------------------------------
# COMPONENT 3B — Order Delivery Tracking
# --------------------------------------------------
@app.route("/dashboard/component3b")
def component3b_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    metrics, df = run_component3b()

    # -------- PIE CHART --------
    pie_df = pd.DataFrame({
        "Status": ["On-Time", "Delayed"],
        "Count": [metrics["On_Time"], metrics["Delayed"]]
    })

    pie_fig = px.pie(
        pie_df,
        names="Status",
        values="Count",
        title="% Deliveries Received On Time",
        color="Status",
        color_discrete_map={
            "On-Time": "#2ecc71",
            "Delayed": "#e74c3c"
        }
    )

    # -------- MONTHLY TREND --------
    trend_df = (
        df.groupby(["Month", "Delivery_Status"])
        .size()
        .reset_index(name="Count")
    )

    bar_fig = px.bar(
        trend_df,
        x="Month",
        y="Count",
        color="Delivery_Status",
        barmode="stack",
        title="Monthly Delivery Performance Trend"
    )

    return render_template(
        "component3b_order_delivery.html",
        metrics=metrics,
        pie_chart=pio.to_html(pie_fig, full_html=False),
        bar_chart=pio.to_html(bar_fig, full_html=False)
    )


# --------------------------------------------------
# COMPONENT 3C — Vendor Performance (Business Dev)
# --------------------------------------------------
@app.route("/dashboard/component3c")
def component3c_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    metrics, df, bucket_df = run_component3c()

    bar_fig = px.bar(
        bucket_df,
        x="Bucket",
        y="Vendor_Count",
        text="Vendor_Count",
        color="Bucket",
        title="Vendor Performance Distribution"
    )

    pie_fig = px.pie(
        bucket_df,
        names="Bucket",
        values="Vendor_Count",
        title="Vendor Performance Share (%)"
    )

    return render_template(
        "component3c_vendor_performance.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar_fig, full_html=False),
        pie_chart=pio.to_html(pie_fig, full_html=False)
    )


# --------------------------------------------------
# COMPONENT 4
# --------------------------------------------------
@app.route("/dashboard/component4")
def component4_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    metrics, df = run_component4()

    # ==================================================
    # SHIPMENT COMPLETION PIE CHART
    # ==================================================
    shipped_pct = metrics["shipment_pct"]
    not_shipped_pct = 100 - shipped_pct

    shipment_df = pd.DataFrame({
        "Status": ["Fully Shipped", "Not Fully Shipped"],
        "Percentage": [shipped_pct, not_shipped_pct]
    })

    shipment_pie = px.pie(
        shipment_df,
        names="Status",
        values="Percentage",
        title="Shipment Completion Status",
        hole=0.4
    )

    # ==================================================
    # O2C BUCKETING
    # ==================================================
    df["O2C_Bucket"] = pd.cut(
        df["O2C_Days"],
        bins=[0, 7, 14, 30, 60, 365],
        labels=["0–7", "8–14", "15–30", "31–60", "60+"],
        include_lowest=True
    )

    o2c_df = (
        df["O2C_Bucket"]
        .value_counts()
        .sort_index()
        .reset_index()
    )
    o2c_df.columns = ["Cycle Days", "SO Count"]

    # ==================================================
    # O2C BAR CHART
    # ==================================================
    o2c_bar = px.bar(
        o2c_df,
        x="Cycle Days",
        y="SO Count",
        text="SO Count",
        title="Order-to-Cash Cycle Time Distribution"
    )

    # ==================================================
    # RENDER TEMPLATE
    # ==================================================
    return render_template(
        "component4.html",
        metrics=metrics,
        shipment_chart=pio.to_html(
            shipment_pie,
            full_html=False,
            include_plotlyjs="cdn"
        ),
        o2c_chart=pio.to_html(
            o2c_bar,
            full_html=False
        )
    )


# --------------------------------------------------
# COMPONENT 5
# --------------------------------------------------
@app.route("/dashboard/component5")
def component5_dashboard():
    metrics, df = run_component5()

    bar = px.bar(
        df.groupby("Month").size().reset_index(name="Completed POs"),
        x="Month", y="Completed POs"
    )

    return render_template(
        "component5.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )
# --------------------------------------------------
# COMPONENT 5A — RM SLA (Quarterly / Monthly)
# --------------------------------------------------
@app.route("/dashboard/component5a_rm")
def component5a_rm_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    metrics, df_monthly = run_component5a_rm()

    bar = px.bar(
        df_monthly,
        x="Month",
        y="PO_Count",
        color="SLA_Status",
        barmode="stack",
        title="RM Purchase Orders – On-Time vs Late"
    )

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
    metrics, df_monthly = run_component6()

    bar = px.bar(
        df_monthly,
        x="Month",
        y=["Short_Closed", "Not_Short_Closed"],
        barmode="stack"
    )

    return render_template(
        "component6.html",
        metrics=metrics,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 7A
# --------------------------------------------------
@app.route("/dashboard/component7a")
def component7a_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    df, location_view, company_view = run_component7()

    summary = df["Stock_Status"].value_counts().to_dict()

    bar_df = (
        company_view.groupby("Stock_Status")["Total_Qty"]
        .sum()
        .reset_index()
    )

    bar = px.bar(
        bar_df,
        x="Stock_Status",
        y="Total_Qty",
        color="Stock_Status",
        title="Overall Stock Health (All Items)",
        text="Total_Qty"
    )

    return render_template(
        "component7a_supply_availability.html",
        summary=summary,
        bar_chart=pio.to_html(bar, full_html=False)
    )

# --------------------------------------------------
# COMPONENT 7B
# --------------------------------------------------
@app.route("/dashboard/component7b")
def component7b_dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    df, location_view, company_view = run_component7()

    df_pm = df[df["Product_Group"] == "PM"]

    summary = df_pm["Stock_Status"].value_counts().to_dict()

    bar_df = (
        df_pm.groupby("Stock_Status")["Remaining_Qty"]
        .sum()
        .reset_index()
    )

    bar = px.bar(
        bar_df,
        x="Stock_Status",
        y="Remaining_Qty",
        color="Stock_Status",
        title="Packaging Material Stock Health",
        text="Remaining_Qty"
    )

    return render_template(
        "component7b_packaging_stoppage.html",
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




