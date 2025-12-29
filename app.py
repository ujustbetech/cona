from flask import Flask, render_template, request, redirect, url_for, session
import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask_caching import Cache

print("=== LOADING app.py FROM:", __file__)


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
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = "kt-secret-key"

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 1800
})

# --------------------------------------------------
# USERS
# --------------------------------------------------
USERS = {"admin": "admin123"}
KPI_FILES = {
    "component1": [
        ("transfer_file", "Transfer Lines.xlsx")
    ],
    "component2": [
        ("ledger_file", "sept_oct_nov_item_ledgers.xlsx")
    ],
    "component3a": [
        ("po_file", "Purchase Order.xlsx"),
        ("receipt_file", "Posted Purchase Receipts.xlsx"),
        ("lines_file", "Purchase Lines.xlsx")
    ],
    "component3b": [
        ("po_file", "Purchase Order.xlsx"),
        ("receipt_file", "Posted Purchase Receipts.xlsx"),
        ("lines_file", "Purchase Lines.xlsx")
    ],
    "component4": [
        ("sales_order_file", "Sales Order.xlsx"),
        ("sales_invoice_file", "Posted Sales Invoice.xlsx")
    ],
    "component5a": [
        ("items_file", "Items.xlsx"),
        ("po_file", "Purchase Order.xlsx"),
        ("receipt_file", "Posted Purchase Receipts.xlsx"),
        ("lines_file", "Purchase Lines.xlsx")
    ],
    "component6": [
        ("sales_order_file", "Sales Order.xlsx")
    ],
    "component7a": [
        ("items_file", "Items.xlsx"),
        ("ledger_file", "sept_oct_nov_item_ledgers.xlsx")
    ],
    "component7b": [
        ("items_file", "Items.xlsx"),
        ("ledger_file", "sept_oct_nov_item_ledgers.xlsx")
    ],
}

KRA_KPI_MAP = {

    # -------- PURCHASE --------
    "Internal Raw Material Transfer": [
        ("component1", "% of Transfers Completed on Schedule")
    ],

    "Sales Order & Invoice Management": [
        ("component4", "% SO to Shipment Completion & O2C Cycle")
    ],

    "Sales Order & Invoice Management – Short Closure": [
        ("component6", "% Short-Closed for Non-Shipped SOs")
    ],

    "Order Delivery Tracking": [
        ("component3b", "% of deliveries received on time")
    ],

    # -------- SALES & MARKETING --------
    "Inventory and Supply Chain Mgmt": [
        ("component2", "% of Slow Stock & Dead Stock")
    ],

    "Seasonal Campaign Execution": [
        ("component5a", "100% RM requisitions fulfilled within defined SLA")
    ],

    "Vendor Management": [
        ("component3a", "95% on-time delivery rate from vendors")
    ],

    "Business Development": [
        ("component3c", "Track and evaluate vendor performance regularly")
    ],

    "Cost Optimization": [
        ("component7a", "100% Supply Availability"),
        ("component7b", "Zero Production Stoppages due to Packaging Shortages")
    ]
}


# --------------------------------------------------
# KPI UPLOAD ROUTE  ✅ MUST COME AFTER KPI_FILES
# --------------------------------------------------
@app.route("/upload/<component>", methods=["GET", "POST"])
def upload_component(component):
    if "user" not in session:
        return redirect(url_for("login"))

    files_needed = KPI_FILES.get(component)
    if not files_needed:
        return f"Invalid component: {component}", 404

    if request.method == "POST":
        for field, _ in files_needed:
            file = request.files.get(field)
            if not file:
                return f"Missing file: {field}", 400
            cache.set(field.replace("_file", "_df"), pd.read_excel(file))

        return redirect(url_for(f"{component}_dashboard"))

    return render_template(
        "upload_kpi.html",
        component=component,
        files=files_needed
    )


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
    return render_template("departments.html")

# --------------------------------------------------
# SUB-DEPARTMENTS
# --------------------------------------------------
@app.route("/subdepartments/<department>")
def subdepartments(department):
    if "user" not in session:
        return redirect(url_for("login"))

    department = department.lower()

    # ONLY Sales has sub-departments
    if department == "sales":
        return render_template(
            "subdepartments.html",
            department="Sales & Marketing",
            subdepartments=[
                ("led", "LED"),
                ("marketing", "Marketing"),
                ("packaging", "Packaging"),
                ("procurement", "Procurement & Vendor Management"),
            ]
        )

    # Anything else → back
    return redirect(url_for("departments"))


# --------------------------------------------------
# KRAs
# --------------------------------------------------
@app.route("/kras/<department>")
@app.route("/kras/<department>/<subdepartment>")
def kras(department, subdepartment=None):
    if "user" not in session:
        return redirect(url_for("login"))

    # PURCHASE
    if department == "purchase":
        kras = [
            "Internal Raw Material Transfer",
            "Sales Order & Invoice Management",
            "Sales Order & Invoice Management – Short Closure",
            "Order Delivery Tracking"
        ]

        return render_template(
            "kras.html",
            department="Purchase",
            subdepartment=None,
            kras=kras
        )

    # SALES & MARKETING
    if department == "sales":
        kra_map = {
            "led": ["Inventory and Supply Chain Mgmt"],
            "marketing": ["Seasonal Campaign Execution", "Vendor Management"],
            "packaging": ["Cost Optimization"],
            "procurement": ["Cost Optimization", "Business Development"]
        }

        kras = kra_map.get(subdepartment, [])

        return render_template(
            "kras.html",
            department="Sales & Marketing",
            subdepartment=subdepartment,
            kras=kras
        )

    return redirect(url_for("departments"))

# --------------------------------------------------
# KPIs (STEP 3 – FINAL & CORRECT)
# --------------------------------------------------
@app.route("/kpis/<department>/<kra>")
@app.route("/kpis/<department>/<subdepartment>/<kra>")
def kpis(department, kra, subdepartment=None):
    if "user" not in session:
        return redirect(url_for("login"))

    # Decode names safely
    department = department.lower()
    kra = kra

    kpis = KRA_KPI_MAP.get(kra)

    if not kpis:
        return f"No KPIs configured for KRA: {kra}", 404

    return render_template(
        "kpis.html",
        department=department,
        subdepartment=subdepartment,
        kra=kra,
        kpis=kpis
    )



# --------------------------------------------------
# COMPONENT 1 — TRANSFER
# --------------------------------------------------
@app.route("/dashboard/component1")
def component1_dashboard():
    df = cache.get("transfer_df")
    if df is None:
        return redirect(url_for("upload_component", component="component1"))

    summary, df = run_component1(df)

    bar = px.bar(
        df["Status"].value_counts().reset_index(),
        x="index", y="Status", text="Status"
    )

    return render_template("component1.html",
                           summary=summary,
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 2 — INVENTORY (NEW LEDGER)
# --------------------------------------------------
@app.route("/dashboard/component2")
def component2_dashboard():
    df = cache.get("ledger_df")
    if df is None:
        return redirect(url_for("upload_component", component="component2"))

    summary, _ = run_component2(df)

    bar = px.bar(
        pd.DataFrame({
            "Status": ["Active", "Slow-Moving", "Dead"],
            "Count": [
                summary["Active Items"],
                summary["Slow-Moving Items"],
                summary["Dead Items"]
            ]
        }),
        x="Status", y="Count", text="Count"
    )

    return render_template("component2.html",
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 3A — VENDOR ON-TIME
# --------------------------------------------------
@app.route("/dashboard/component3a")
def component3a_dashboard():
    if not all([cache.get("po_df"), cache.get("receipt_df"), cache.get("lines_df")]):
        return redirect(url_for("upload_component", component="component3"))

    metrics, vendor_df = run_component3a(
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )

    bar = px.bar(vendor_df, x="Vendor", y="On_Time_Pct", text="On_Time_Pct")

    return render_template("component3a_vendor_management.html",
                           metrics=metrics,
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 3B — ORDER DELIVERY
# --------------------------------------------------
@app.route("/dashboard/component3b")
def component3b_dashboard():
    metrics, df = run_component3b(
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )
    return redirect(url_for("upload_component", component="component3b"))

    metrics, df = run_component3b(
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )

    pie = px.pie(
        pd.DataFrame({
            "Status": ["On-Time", "Delayed"],
            "Count": [metrics["On_Time"], metrics["Delayed"]]
        }),
        names="Status", values="Count"
    )

    return render_template("component3b_order_delivery.html",
                           metrics=metrics,
                           pie_chart=pio.to_html(pie, full_html=False))

# --------------------------------------------------
# COMPONENT 4 — SALES O2C
# --------------------------------------------------
@app.route("/dashboard/component4")
def component4_dashboard():
   if not all([cache.get("sales_order_df"), cache.get("sales_invoice_df")]):
        return redirect(url_for("upload_component", component="component4"))

        metrics, _ = run_component4(
            cache.get("sales_order_df"),
            cache.get("sales_invoice_df")
    )

        return render_template("component4.html", metrics=metrics)

# --------------------------------------------------
# COMPONENT 5 — PO SLA
# --------------------------------------------------
@app.route("/dashboard/component5")
def component5_dashboard():
    metrics, df = run_component5(
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )

    return redirect(url_for("upload_component", component="component5"))

    metrics, df = run_component5(
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )


    bar = px.bar(
        df.groupby("Month").size().reset_index(name="Completed POs"),
        x="Month", y="Completed POs"
    )

    return render_template("component5.html",
                           metrics=metrics,
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 5A — RM SLA
# --------------------------------------------------
@app.route("/dashboard/component5a")
def component5a_dashboard():
    metrics, df_monthly = run_component5a_rm(
        cache.get("items_df"),
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )
    return redirect(url_for("upload_component", component="component5a"))

    metrics, df_monthly = run_component5a_rm(
        cache.get("items_df"),
        cache.get("po_df"),
        cache.get("receipt_df"),
        cache.get("lines_df")
    )

    bar = px.bar(df_monthly, x="Month", y="PO_Count", color="SLA_Status")

    return render_template("component5a_rm.html",
                           metrics=metrics,
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 6 — SHORT CLOSURE
# --------------------------------------------------
@app.route("/dashboard/component6")
def component6_dashboard():
    if not cache.get("sales_order_df"):
        return redirect(url_for("upload_component", component="component6"))
    metrics, df_monthly = run_component6(cache.get("sales_order_df"))

    bar = px.bar(df_monthly,
                 x="Month",
                 y=["Short_Closed", "Not_Short_Closed"],
                 barmode="stack")

    return render_template("component6.html",
                           metrics=metrics,
                           bar_chart=pio.to_html(bar, full_html=False))

# --------------------------------------------------
# COMPONENT 7 — COST OPTIMIZATION
# --------------------------------------------------
@app.route("/dashboard/component7a")
@app.route("/dashboard/component7b")
def component7_dashboard():
    if not all([cache.get("items_df"), cache.get("ledger_df")]):
        return redirect(url_for("upload_component", component="component7a"))


    bar = px.bar(
        company_view.groupby("Stock_Status")["Total_Qty"].sum().reset_index(),
        x="Stock_Status", y="Total_Qty"
    )

    template = (
        "component7a_supply_availability.html"
        if request.path.endswith("7a")
        else "component7b_packaging_stoppage.html"
    )

    return render_template(template,
                           bar_chart=pio.to_html(bar, full_html=False))

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
# --------------------------------------------------
# RUN
# --------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True)

