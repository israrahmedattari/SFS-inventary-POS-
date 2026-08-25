import io
import hmac
from datetime import datetime, date, timedelta

import pandas as pd
import streamlit as st
import barcode
from barcode.writer import ImageWriter

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
)

from supabase import create_client, Client

# ============================================================
# SFS ENTERPRISES
# Laptop Spare Parts Inventory + POS Billing
# Dedicated Streamlit Web Application
# ============================================================

st.set_page_config(
    page_title="SFS Enterprises | Inventory & POS",
    page_icon="💻",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ============================================================
# OWNER LOGIN
# ============================================================

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def show_login():

    st.markdown(
        """
        <div style="
            max-width:480px;
            margin:120px auto 20px auto;
            padding:35px;
            background:#101c30;
            border:1px solid #243653;
            border-radius:20px;
            text-align:center;
        ">
            <h1 style="color:white;">  💻 SFS ENTERPRISES</h1>
            <p style="color:#91a3be;">
                SIGN IN
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    password = st.text_input(
        "🔑 Enter Password",
        type="password",
        placeholder="Enter owner password"
    )

    if st.button(
        "🔓 Login",
        type="primary",
        use_container_width=True
    ):
        correct_password = st.secrets["OWNER_PASSWORD"]

        if hmac.compare_digest(password, correct_password):
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")


# Show login before the application
if not st.session_state.authenticated:
    show_login()
    st.stop()

CURRENCY = "PKR"

# Updated Categories & Brands list
CATEGORIES = [
    "Laptop Charger",
    "Laptop Screen",
    "Laptop Keyboard",
    "DC Jack",
    "Cooling Fan"
]

BRANDS = ["HP", "Dell", "Lenovo", "Acer", "Asus", "Apple", "Toshiba", "Other"]

# ------------------------- SUPABASE CONNECTION --------------------------

@st.cache_resource
def init_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase: Client = init_supabase()

# ------------------------- UI THEME --------------------------

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg:#07111f;
    --sidebar:#091525;
    --panel:#0e1a2d;
    --panel2:#12213a;
    --border:#243653;
    --text:#edf4ff;
    --muted:#91a3be;
    --primary:#3b82f6;
    --cyan:#06b6d4;
    --green:#22c55e;
    --yellow:#f59e0b;
    --red:#ef4444;
}

html, body, [class*="css"] {
    font-family: Inter, sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 90% 0%, rgba(37,99,235,.18), transparent 28%),
        radial-gradient(circle at 10% 20%, rgba(6,182,212,.08), transparent 25%),
        var(--bg);
    color:var(--text);
}

.block-container {
    max-width:1500px;
    padding-top:1rem;
    padding-bottom:2rem;
}

[data-testid="stHeader"] {
    background:rgba(7,17,31,.92);
}

[data-testid="stSidebar"] {
    background:linear-gradient(180deg,#07111f,#0b1729 55%,#0c1930);
    border-right:1px solid var(--border);
}

[data-testid="stSidebar"] * {
    color:#dbe8ff !important;
}

.brand {
    background:linear-gradient(135deg,#0d1b32,#1d4ed8 62%,#0891b2);
    border:1px solid rgba(147,197,253,.22);
    border-radius:22px;
    padding:25px 28px;
    box-shadow:0 20px 50px rgba(0,0,0,.28);
    margin-bottom:20px;
}

.brand h1 {
    color:white !important;
    margin:0;
    font-size:2rem;
    font-weight:800;
}

.brand p {
    color:#dbeafe !important;
    margin:5px 0 0;
    opacity:.9;
}

.page-title {
    color:#f8fbff !important;
    font-size:1.55rem;
    font-weight:800;
    margin:5px 0 15px;
}

.card {
    background:linear-gradient(145deg,#101c30,#0c1729);
    border:1px solid var(--border);
    border-radius:18px;
    padding:20px;
    box-shadow:0 12px 35px rgba(0,0,0,.18);
}

.kpi {
    background:linear-gradient(145deg,#111f35,#0c1728);
    border:1px solid var(--border);
    border-radius:17px;
    padding:18px;
    min-height:125px;
    box-shadow:0 12px 30px rgba(0,0,0,.18);
}

.kpi-icon {
    font-size:1.35rem;
}

.kpi-label {
    color:var(--muted);
    font-size:.78rem;
    font-weight:600;
    margin-top:6px;
}

.kpi-value {
    color:#fff;
    font-size:1.55rem;
    font-weight:800;
    margin-top:3px;
}

.stButton > button,
.stDownloadButton > button {
    min-height:42px;
    border-radius:10px !important;
    font-weight:700 !important;
    background:#172640 !important;
    color:#edf4ff !important;
    border:1px solid #304665 !important;
}

.stButton > button[kind="primary"] {
    background:linear-gradient(135deg,#2563eb,#0891b2) !important;
    color:white !important;
    border:0 !important;
}

.stButton > button:hover,
.stDownloadButton > button:hover {
    transform:translateY(-1px);
    border-color:#60a5fa !important;
    box-shadow:0 8px 22px rgba(37,99,235,.2);
}

div[data-baseweb="input"] > div,
div[data-baseweb="select"] > div,
div[data-baseweb="textarea"] > div {
    background:#0b1729 !important;
    border:1px solid #304665 !important;
    border-radius:10px !important;
}

input, textarea {
    color:#edf4ff !important;
}

input::placeholder, textarea::placeholder {
    color:#657993 !important;
}

div[data-baseweb="select"] * {
    color:#edf4ff !important;
}

.stTabs [data-baseweb="tab-list"] {
    background:#0a1526;
    border:1px solid var(--border);
    padding:7px;
    border-radius:14px;
    gap:7px;
    overflow-x:auto !important;
}

.stTabs [data-baseweb="tab"] {
    min-width:max-content;
    white-space:nowrap !important;
    padding:10px 15px;
    background:#14223a;
    border:1px solid #293e5e;
    border-radius:10px;
    color:#aebed6 !important;
    font-weight:700;
}

.stTabs [aria-selected="true"] {
    background:linear-gradient(135deg,#2563eb,#0891b2) !important;
    color:white !important;
    border-color:transparent !important;
}

.stTabs [aria-selected="true"] * {
    color:white !important;
}

.alert-red {
    background:#321622;
    border:1px solid #7f1d1d;
    color:#fecaca;
    padding:13px 16px;
    border-radius:13px;
}

.alert-green {
    background:#0e2a1d;
    border:1px solid #166534;
    color:#bbf7d0;
    padding:13px 16px;
    border-radius:13px;
}

.alert-yellow {
    background:#33260d;
    border:1px solid #92400e;
    color:#fde68a;
    padding:13px 16px;
    border-radius:13px;
}
</style>
""",
    unsafe_allow_html=True,
)

st.markdown(
    """
<div class="brand">
    <h1>💻 SFS ENTERPRISES</h1>
    <p>Laptop Spare Parts • Inventory Management • POS Billing</p>
</div>
""",
    unsafe_allow_html=True,
)

# ------------------------- BARCODE GENERATOR --------------------------

def generate_barcode_image(code_text):
    """Generates barcode images in memory as PNG Bytes."""
    rv = io.BytesIO()
    Code128 = barcode.get_barcode_class('code128')
    barcode_instance = Code128(str(code_text), writer=ImageWriter())
    barcode_instance.write(rv)
    rv.seek(0)
    return rv


@st.cache_data(ttl=2)
def products_df():
    res = supabase.table("products").select("*").order("name").execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=[
        "id", "name", "sku", "brand", "model", "category", "supplier",
        "cost_price", "sale_price", "stock", "min_stock", "location", "created_at", "updated_at"
    ])

@st.cache_data(ttl=2)
def sales_df():
    res = supabase.table("sales").select("*").order("sale_date", desc=True).order("id", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=[
        "id", "invoice_no", "customer_id", "customer_name", "customer_phone",
        "subtotal", "discount", "grand_total", "payment_method", "sale_date"
    ])


@st.cache_data(ttl=2)
def sale_items_df():
    res = supabase.table("sale_items").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=[
        "id", "sale_id", "product_id", "product_name", "model", "quantity", "unit_price", "cost_price", "total"
    ])


@st.cache_data(ttl=2)
def movements_df():
    res = supabase.table("stock_movements").select("*").order("movement_date", desc=True).order("id", desc=True).execute()
    return pd.DataFrame(res.data) if res.data else pd.DataFrame(columns=[
        "id", "product_id", "product_name", "movement_type", "quantity", "note", "movement_date"
    ])


def refresh():
    st.cache_data.clear()


def money(x):
    return f"{CURRENCY} {float(x):,.2f}"


def record_movement(product_id, name, kind, qty, note=""):
    supabase.table("stock_movements").insert({
        "product_id": product_id,
        "product_name": name,
        "movement_type": kind,
        "quantity": int(qty),
        "note": note,
        "movement_date": datetime.now().isoformat(),
    }).execute()


def invoice_number():
    return "SFS-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f")[-8:]


# ------------------------- PDF GENERATION -------------------------------

def receipt_pdf(invoice, customer, phone, cart, subtotal, discount, total, payment, sale_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=35,
        leftMargin=35,
        topMargin=35,
        bottomMargin=35,
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=styles["Title"], alignment=TA_CENTER, fontSize=20, textColor=colors.HexColor("#173b75"))
    center = ParagraphStyle("CenterX", parent=styles["Normal"], alignment=TA_CENTER, fontSize=9, textColor=colors.HexColor("#475569"))
    right = ParagraphStyle("RightX", parent=styles["Normal"], alignment=TA_RIGHT, fontSize=10)

    # Generated Barcode PDF Element
    barcode_img_bytes = generate_barcode_image(invoice)
    rl_barcode = RLImage(barcode_img_bytes, width=150, height=40)

    story = [
        Paragraph("SFS ENTERPRISES", title),
        Paragraph("Laptop Spare Parts & Services", center),
        Spacer(1, 8),
        rl_barcode,
        Spacer(1, 8),
        Paragraph(f"<b>Invoice:</b> {invoice}", styles["Normal"]),
        Paragraph(f"<b>Date:</b> {sale_date}", styles["Normal"]),
        Paragraph(f"<b>Customer:</b> {customer or 'Walk-in Customer'}", styles["Normal"]),
        Paragraph(f"<b>Phone:</b> {phone or 'N/A'}", styles["Normal"]),
        Spacer(1, 15),
    ]

    data = [["Product", "Brand/Model", "Qty", "Unit Price", "Total"]]
    for item in cart:
        b_mod = f"{item.get('brand','') or ''} {item.get('model','') or ''}".strip() or "N/A"
        data.append([
            item["name"],
            b_mod,
            str(item["qty"]),
            money(item["price"]),
            money(item["qty"] * item["price"]),
        ])

    table = Table(data, colWidths=[150, 100, 45, 85, 85], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173b75")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
        ("ALIGN", (2,1), (-1,-1), "RIGHT"),
    ]))

    story += [
        table,
        Spacer(1, 15),
        Paragraph(f"Subtotal: {money(subtotal)}", right),
        Paragraph(f"Discount: {money(discount)}", right),
        Paragraph(f"<b>Grand Total: {money(total)}</b>", right),
        Paragraph(f"Payment Method: {payment}", right),
        Spacer(1, 30),
        Paragraph("Thank you for shopping with SFS ENTERPRISES!", center),
    ]

    doc.build(story)
    buffer.seek(0)
    return buffer


def daily_report_pdf(df, report_date):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle", parent=styles["Title"], alignment=TA_CENTER,
        fontSize=18, textColor=colors.HexColor("#173b75")
    )

    story = [
        Paragraph("SFS ENTERPRISES", title),
        Paragraph(f"Daily Sales Report — {report_date}", styles["Heading2"]),
        Spacer(1, 10),
    ]

    data = [["Invoice", "Customer", "Total", "Payment", "Time"]]
    for _, r in df.iterrows():
        data.append([
            str(r["invoice_no"]),
            str(r["customer_name"] or "Walk-in")[:25],
            money(r["grand_total"]),
            str(r["payment_method"]),
            str(r["sale_date"])[11:19],
        ])

    table = Table(data, colWidths=[100, 150, 90, 85, 70], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173b75")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))

    story.append(table)
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"<b>Total Sales:</b> {len(df)} &nbsp;&nbsp;&nbsp; "
        f"<b>Total Revenue:</b> {money(df['grand_total'].sum())}",
        styles["Normal"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer


# ------------------------- LOAD DATA --------------------------

products = products_df()
sales = sales_df()
sale_items = sale_items_df()

if not products.empty:
    for col in ["stock", "min_stock"]:
        products[col] = pd.to_numeric(products[col], errors="coerce").fillna(0).astype(int)
    for col in ["cost_price", "sale_price"]:
        products[col] = pd.to_numeric(products[col], errors="coerce").fillna(0.0)

if not sales.empty:
    sales["grand_total"] = pd.to_numeric(sales["grand_total"], errors="coerce").fillna(0.0)

 # ------------------------- SIDEBAR ----------------------------

with st.sidebar:

    # Business heading
    st.markdown("### 💻 SFS ENTERPRISES")
    st.caption("Our Standard Is Your Trust")

    # Owner access
    st.markdown("---")
    st.markdown("### 🔐 Owner Access")

    # Logout button
    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):
        st.session_state.authenticated = False
        st.rerun()

    st.divider()

    # Inventory statistics
    st.metric(
        "📦 Products",
        len(products)
    )

    st.metric(
        "🚨 Low Stock",
        int(
            (products["stock"] <= products["min_stock"]).sum()
        ) if not products.empty else 0
    )

    # Today's revenue
    st.metric(
        "💰 Today's Revenue",
        money(
            sales[
                pd.to_datetime(
                    sales["sale_date"],
                    errors="coerce"
                ).dt.date == date.today()
            ]["grand_total"].sum()
        ) if not sales.empty else money(0)
    )

    st.divider()

    # Helpful information
    st.markdown("### 💡 Quick Tip")

    st.caption(
        "Sell from POS or use the Barcode Scanner. "
        "Stock is automatically updated after every sale."
    )

    st.divider()

    # Application information
    st.caption("💻 SFS ENTERPRISES")
    st.caption("Inventory Management • POS Billing")
    st.caption("@sfsAll Right Reserved")
# --------------------------- NAVIGATION TABS -----------------------------

tabs = st.tabs([
    "🏠 Dashboard",
    "📦 Products",
    "🚨 Low Stock",
    "🧾 POS Billing",
    "👥 Customers",
    "📊 Sales Reports",
    "🕘 Stock History",
])

# ==============================================================
# DASHBOARD
# ==============================================================

with tabs[0]:
    st.markdown('<div class="page-title">Dashboard Overview</div>', unsafe_allow_html=True)

    today = date.today()
    today_sales = sales[pd.to_datetime(sales["sale_date"], errors="coerce").dt.date == today] if not sales.empty else pd.DataFrame()
    month_sales = sales[pd.to_datetime(sales["sale_date"], errors="coerce").dt.month == today.month] if not sales.empty else pd.DataFrame()

    stock_units = int(products["stock"].sum()) if not products.empty else 0
    stock_cost = float((products["stock"] * products["cost_price"]).sum()) if not products.empty else 0
    today_revenue = float(today_sales["grand_total"].sum()) if not today_sales.empty else 0
    low_stock = int((products["stock"] <= products["min_stock"]).sum()) if not products.empty else 0

    k1, k2, k3, k4, k5 = st.columns(5)
    metrics = [
        ("💻", "Products", len(products)),
        ("📦", "Units", f"{stock_units:,}"),
        ("💰", "Stock Cost", money(stock_cost)),
        ("🧾", "Today Sales", money(today_revenue)),
        ("🚨", "Low Stock", low_stock),
    ]

    for col, (icon, label, value) in zip([k1, k2, k3, k4, k5], metrics):
        with col:
            st.markdown(
                f"""
                <div class="kpi">
                    <div class="kpi-icon">{icon}</div>
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.write("")
    a, b = st.columns([1.35, 1])

    with a:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 📈 Revenue — Last 14 Days")
        if not sales.empty:
            temp = sales.copy()
            temp["day"] = pd.to_datetime(temp["sale_date"], errors="coerce").dt.date
            start = today - timedelta(days=13)
            recent = temp[temp["day"] >= start]
            daily = recent.groupby("day")["grand_total"].sum()
            dates = pd.date_range(start, today).date
            daily = daily.reindex(dates, fill_value=0)
            st.line_chart(daily, height=290)
        else:
            st.info("Sales chart will appear after your first sale.")
        st.markdown('</div>', unsafe_allow_html=True)

    with b:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🏆 Best Selling Parts")
        if not sale_items.empty:
            top = sale_items.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(8)
            st.bar_chart(top, height=290)
        else:
            st.info("No sales recorded yet.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.write("")
    c, d = st.columns(2)

    with c:
        st.markdown("#### 🚨 Stock Needing Attention")
        if products.empty:
            st.info("No products available.")
        else:
            alert = products[products["stock"] <= products["min_stock"]][
                ["name", "sku", "category", "stock", "min_stock", "supplier"]
            ]
            if alert.empty:
                st.markdown('<div class="alert-green">✓ All products are above minimum stock.</div>', unsafe_allow_html=True)
            else:
                st.dataframe(alert, use_container_width=True, hide_index=True)

    with d:
        st.markdown("#### 🧾 Recent Sales")
        if sales.empty:
            st.info("No sales.")
        else:
            recent = sales[["invoice_no", "customer_name", "grand_total", "payment_method", "sale_date"]].head(7).copy()
            recent["grand_total"] = recent["grand_total"].map(money)
            st.dataframe(recent, use_container_width=True, hide_index=True)


# ==============================================================
# PRODUCTS
# ==============================================================

with tabs[1]:
    st.markdown('<div class="page-title">📦 Product Inventory</div>', unsafe_allow_html=True)

    search = st.text_input("🔎 Search product / SKU / Barcode / Model / Brand", placeholder="Type or scan barcode...")

    f1, f2, f3 = st.columns(3)
    category = f1.selectbox("Category Filter", ["All"] + CATEGORIES)
    brand_filt = f2.selectbox("Brand Filter", ["All"] + BRANDS)
    status = f3.selectbox("Stock Status", ["All", "In Stock", "Low Stock", "Out of Stock"])

    view = products.copy()

    if search:
        s = search.lower()
        mask = (
            view["name"].astype(str).str.lower().str.contains(s, na=False)
            | view["sku"].astype(str).str.lower().str.contains(s, na=False)
            | view["model"].astype(str).str.lower().str.contains(s, na=False)
            | view["brand"].astype(str).str.lower().str.contains(s, na=False)
        )
        view = view[mask]

    if category != "All":
        view = view[view["category"] == category]

    if brand_filt != "All":
        view = view[view["brand"] == brand_filt]

    if status == "In Stock":
        view = view[view["stock"] > view["min_stock"]]
    elif status == "Low Stock":
        view = view[(view["stock"] <= view["min_stock"]) & (view["stock"] > 0)]
    elif status == "Out of Stock":
        view = view[view["stock"] <= 0]

    show = view[
        ["id", "sku", "name", "brand", "model", "category", "supplier",
         "stock", "min_stock", "cost_price", "sale_price", "location"]
    ].copy()

    st.caption(f"{len(show)} product(s) found")
    st.dataframe(show, use_container_width=True, hide_index=True)

    st.write("")
    add, edit = st.columns(2)

    with add:
        with st.expander("➕ Add New Product", expanded=products.empty):
            with st.form("add_product", clear_on_submit=True):
                p1, p2 = st.columns(2)
                name = p1.text_input("Product Name *")
                sku_in = p2.text_input("SKU / Barcode (Leave blank to auto-generate)")

                p3, p4 = st.columns(2)
                brand_in = p3.selectbox("Brand / Make *", BRANDS)
                model_in = p4.text_input("Model Name or Number (e.g., HP G6 / Dell E6430)")

                p5, p6, p7 = st.columns(3)
                category_new = p5.selectbox("Category *", CATEGORIES)
                supplier = p6.text_input("Supplier Name")
                location = p7.text_input("Shelf / Location")

                p8, p9, p10, p11 = st.columns(4)
                cost = p8.number_input("Purchase Cost", min_value=0.0, step=100.0)
                price = p9.number_input("Selling Price", min_value=0.0, step=100.0)
                stock = p10.number_input("Opening Stock", min_value=0, step=1)
                min_stock = p11.number_input("Min Stock Level", min_value=0, value=5, step=1)

                submit = st.form_submit_button("💾 Save Product", type="primary", use_container_width=True)

            if submit:
                name = name.strip()
                auto_sku = sku_in.strip() if sku_in.strip() else "SFS" + datetime.now().strftime("%Y%m%d%H%M%S")

                if not name:
                    st.error("Product name is required.")
                else:
                    now = datetime.now().isoformat()
                    try:
                        res = supabase.table("products").insert({
                            "name": name,
                            "sku": auto_sku,
                            "brand": brand_in,
                            "model": model_in.strip(),
                            "category": category_new,
                            "supplier": supplier.strip(),
                            "cost_price": cost,
                            "sale_price": price,
                            "stock": int(stock),
                            "min_stock": int(min_stock),
                            "location": location.strip(),
                            "created_at": now,
                            "updated_at": now
                        }).execute()

                        pid = res.data[0]["id"]

                        if stock:
                            record_movement(pid, name, "PURCHASE", int(stock), "Opening stock")

                        refresh()
                        st.success(f"Product added. Generated Barcode SKU: {auto_sku}")
                        st.rerun()

                    except Exception as e:
                        st.error("Product name or SKU already exists.")

    with edit:
        with st.expander("✏️ Update Product / Print Barcode"):
            if products.empty:
                st.info("No products available.")
            else:
                pid = st.selectbox(
                    "Select Product",
                    products["id"].tolist(),
                    format_func=lambda x: f"#{x} — {products.loc[products['id']==x,'name'].iloc[0]}"
                )
                row = products[products["id"] == pid].iloc[0]

                # Barcode Renderer
                st.markdown("**Printable Product Barcode:**")
                b_img = generate_barcode_image(row["sku"] or str(row["id"]))
                st.image(b_img, caption=f"SKU Barcode: {row['sku']}")

                with st.form("edit_product"):
                    e1, e2 = st.columns(2)
                    ename = e1.text_input("Product Name", value=row["name"])
                    esku = e2.text_input("SKU Barcode", value=row["sku"] or "")

                    e3, e4 = st.columns(2)
                    ebrand = e3.selectbox("Brand", BRANDS, index=BRANDS.index(row["brand"]) if row["brand"] in BRANDS else 0)
                    emodel = e4.text_input("Model", value=row["model"] or "")

                    e5, e6 = st.columns(2)
                    ecat = e5.selectbox("Category", CATEGORIES, index=CATEGORIES.index(row["category"]) if row["category"] in CATEGORIES else 0)
                    esupplier = e6.text_input("Supplier", value=row["supplier"] or "")

                    e7, e8, e9 = st.columns(3)
                    ecost = e7.number_input("Cost", value=float(row["cost_price"]))
                    eprice = e8.number_input("Price", value=float(row["sale_price"]))
                    estock = e9.number_input("Current Stock", value=int(row["stock"]))

                    update = st.form_submit_button("💾 Update Product", type="primary", use_container_width=True)

                if update:
                    now = datetime.now().isoformat()
                    supabase.table("products").update({
                        "name": ename.strip(),
                        "sku": esku.strip(),
                        "brand": ebrand,
                        "model": emodel.strip(),
                        "category": ecat,
                        "supplier": esupplier.strip(),
                        "cost_price": ecost,
                        "sale_price": eprice,
                        "stock": estock,
                        "updated_at": now
                    }).eq("id", pid).execute()

                    refresh()
                    st.success("Product updated.")
                    st.rerun()

 # ------------------------- SAFE DELETE PRODUCT -------------------------
 
    try:

        # Check sales history
        sale_check = (
            supabase
            .table("sale_items")
            .select("id")
            .eq("product_id", pid)
            .limit(1)
            .execute()
        )

        if sale_check.data:

            st.error(
                "❌ Cannot delete this product because "
                "it has sales history."
            )

        else:

            # Check stock movement history
            movement_check = (
                supabase
                .table("stock_movements")
                .select("id")
                .eq("product_id", pid)
                .limit(1)
                .execute()
            )

            if movement_check.data:

                st.error(
                    "❌ Cannot delete this product because "
                    "it has stock history."
                )

            else:

                # Delete product
                supabase \
                    .table("products") \
                    .delete() \
                    .eq("id", pid) \
                    .execute()

                refresh()

                st.success(
                    f"✅ Product '{row['name']}' deleted successfully."
                )

                st.rerun()

    except Exception as e:

        st.error(
            f"❌ Unable to delete product: {str(e)}"
        )

# ==============================================================
# LOW STOCK
# ==============================================================

with tabs[2]:
    st.markdown('<div class="page-title">🚨 Low Stock Center</div>', unsafe_allow_html=True)

    if products.empty:
        st.info("No products have been added yet.")
    else:
        low = products[products["stock"] <= products["min_stock"]].copy()
        out = products[products["stock"] <= 0].copy()

        a, b, c = st.columns(3)
        a.metric("Low Stock", len(low))
        b.metric("Out of Stock", len(out))

        reorder_value = float(((low["min_stock"] - low["stock"]).clip(lower=0) * low["cost_price"]).sum()) if not low.empty else 0
        c.metric("Estimated Reorder Cost", money(reorder_value))

        if out.empty and low.empty:
            st.markdown('<div class="alert-green">✓ Excellent. No product is below its minimum stock level.</div>', unsafe_allow_html=True)
        else:
            if not low.empty:
                st.dataframe(low[["id", "name", "sku", "brand", "category", "stock", "min_stock", "supplier"]], use_container_width=True, hide_index=True)

                st.markdown("#### 📥 Quick Restock")
                rid = st.selectbox("Product to Restock", low["id"].tolist(), format_func=lambda x: f"{x} — {low.loc[low['id']==x,'name'].iloc[0]}")
                qty = st.number_input("Quantity Received", min_value=1, value=5)

                if st.button("📥 Receive Stock", type="primary", use_container_width=True):
                    cur_stock = int(low.loc[low['id'] == rid, 'stock'].iloc[0])
                    supabase.table("products").update({"stock": cur_stock + int(qty)}).eq("id", rid).execute()
                    refresh()
                    st.success("Stock updated successfully!")
                    st.rerun()


# ==============================================================
# POS BILLING
# ==============================================================

with tabs[3]:
    st.markdown('<div class="page-title">🧾 Point of Sale (POS)</div>', unsafe_allow_html=True)

    if "cart" not in st.session_state:
        st.session_state.cart = []

    available = products[products["stock"] > 0].copy()

    left, right = st.columns([1.1, 1.4])

    with left:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### ⚡ Barcode Scanner Auto-Add")
        scan_val = st.text_input("📷 Scan Barcode or SKU", key="pos_barcode_scanner")

        if scan_val:
            match = available[available["sku"].astype(str) == scan_val.strip()]
            if not match.empty:
                item = match.iloc[0]
                found = False
                for cart_item in st.session_state.cart:
                    if cart_item["id"] == int(item["id"]):
                        if cart_item["qty"] < int(item["stock"]):
                            cart_item["qty"] += 1
                            st.success(f"Increased quantity for {item['name']}")
                        else:
                            st.error("Stock limit reached.")
                        found = True
                        break
                if not found:
                    st.session_state.cart.append({
                        "id": int(item["id"]),
                        "name": item["name"],
                        "brand": item.get("brand", ""),
                        "model": item.get("model", ""),
                        "qty": 1,
                        "price": float(item["sale_price"]),
                        "cost": float(item["cost_price"]),
                    })
                    st.success(f"Added: {item['name']}")
            else:
                st.error("No product found matching this barcode SKU.")

        st.divider()
        st.markdown("#### 🔎 Manual Item Selection")

        if not available.empty:
            pos_choice = st.selectbox(
                "Select Spare Part",
                available["id"].tolist(),
                format_func=lambda x: f"{available.loc[available['id']==x,'name'].iloc[0]} ({available.loc[available['id']==x,'brand'].iloc[0]}) - {money(available.loc[available['id']==x,'sale_price'].iloc[0])}"
            )
            selected_prod = available[available["id"] == pos_choice].iloc[0]
            p_qty = st.number_input("Quantity to sell", min_value=1, max_value=int(selected_prod["stock"]), value=1)

            if st.button("➕ Add to Cart", type="primary", use_container_width=True):
                found = False
                for cart_item in st.session_state.cart:
                    if cart_item["id"] == int(selected_prod["id"]):
                        if cart_item["qty"] + int(p_qty) <= int(selected_prod["stock"]):
                            cart_item["qty"] += int(p_qty)
                        found = True
                        break
                if not found:
                    st.session_state.cart.append({
                        "id": int(selected_prod["id"]),
                        "name": selected_prod["name"],
                        "brand": selected_prod.get("brand", ""),
                        "model": selected_prod.get("model", ""),
                        "qty": int(p_qty),
                        "price": float(selected_prod["sale_price"]),
                        "cost": float(selected_prod["cost_price"]),
                    })
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("#### 🛒 Current Cart")

        if st.session_state.cart:
            cart_df = pd.DataFrame(st.session_state.cart)
            cart_df["Total"] = cart_df["qty"] * cart_df["price"]
            st.dataframe(cart_df[["name", "brand", "model", "qty", "price", "Total"]], use_container_width=True, hide_index=True)

            if st.button("🗑️ Clear Cart", use_container_width=True):
                st.session_state.cart = []
                st.rerun()

            st.write("")
            c1, c2, c3 = st.columns(3)
            cname = c1.text_input("Customer Name", value="Walk-in Customer")
            cphone = c2.text_input("Customer Phone")
            payment = c3.selectbox("Payment Method", ["Cash", "Card", "Bank Transfer", "Easypaisa", "JazzCash"])

            subtotal = sum(x["qty"] * x["price"] for x in st.session_state.cart)
            discount = st.number_input("Discount (PKR)", min_value=0.0, max_value=float(subtotal), value=0.0)
            grand_total = max(0.0, subtotal - discount)

            st.metric("Grand Total", money(grand_total))

            if st.button("💳 PRINT RECEIPT & COMPLETE SALE", type="primary", use_container_width=True):
                inv = invoice_number()
                now = datetime.now().isoformat()

                sale_res = supabase.table("sales").insert({
                    "invoice_no": inv,
                    "customer_name": cname,
                    "customer_phone": cphone,
                    "subtotal": subtotal,
                    "discount": discount,
                    "grand_total": grand_total,
                    "payment_method": payment,
                    "sale_date": now
                }).execute()
                
                sale_id = sale_res.data[0]["id"]

                for item in st.session_state.cart:
                    prod_info = supabase.table("products").select("stock").eq("id", item["id"]).execute()
                    current_stk = prod_info.data[0]["stock"] if prod_info.data else 0
                    supabase.table("products").update({"stock": current_stk - item["qty"]}).eq("id", item["id"]).execute()

                    supabase.table("sale_items").insert({
                        "sale_id": sale_id,
                        "product_id": item["id"],
                        "product_name": item["name"],
                        "model": item["model"],
                        "quantity": item["qty"],
                        "unit_price": item["price"],
                        "cost_price": item["cost"],
                        "total": item["qty"] * item["price"]
                    }).execute()

                    record_movement(item["id"], item["name"], "SALE", item["qty"], f"Invoice {inv}")

                receipt = receipt_pdf(inv, cname, cphone, st.session_state.cart, subtotal, discount, grand_total, payment, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                st.session_state.cart = []
                refresh()

                st.success(f"Sale Complete! Invoice: {inv}")
                st.download_button("📄 DOWNLOAD PDF RECEIPT", data=receipt, file_name=f"{inv}.pdf", mime="application/pdf", use_container_width=True)
        else:
            st.info("Cart is currently empty.")
        st.markdown('</div>', unsafe_allow_html=True)


# ==============================================================
# CUSTOMERS
# ==============================================================

with tabs[4]:
    st.markdown('<div class="page-title">👥 Customers</div>', unsafe_allow_html=True)

    c_res = supabase.table("customers").select("*").order("name").execute()
    customers = pd.DataFrame(c_res.data) if c_res.data else pd.DataFrame(columns=["id", "name", "phone", "email", "address", "created_at"])

    add_c, show_c = st.columns(2)

    with add_c:
        with st.form("cust_form", clear_on_submit=True):
            cn = st.text_input("Customer Name *")
            cp = st.text_input("Phone")
            ce = st.text_input("Email")
            ca = st.text_area("Address")
            if st.form_submit_button("Save Customer", type="primary", use_container_width=True):
                if cn.strip():
                    supabase.table("customers").insert({
                        "name": cn.strip(),
                        "phone": cp.strip(),
                        "email": ce.strip(),
                        "address": ca.strip(),
                        "created_at": datetime.now().isoformat()
                    }).execute()
                    st.success("Customer added successfully.")
                    st.rerun()

    with show_c:
        st.dataframe(customers, use_container_width=True, hide_index=True)


# ==============================================================
# SALES REPORTS
# ==============================================================

with tabs[5]:
    st.markdown('<div class="page-title">📊 Sales Reports</div>', unsafe_allow_html=True)

    if sales.empty:
        st.info("No sales records available.")
    else:
        st.dataframe(sales[["invoice_no", "customer_name", "grand_total", "payment_method", "sale_date"]], use_container_width=True, hide_index=True)


# ==============================================================
# STOCK HISTORY
# ==============================================================

with tabs[6]:
    st.markdown('<div class="page-title">🕘 Stock History</div>', unsafe_allow_html=True)

    history = movements_df()
    if history.empty:
        st.info("No stock movements recorded yet.")
    else:
        st.dataframe(history[["id", "product_name", "movement_type", "quantity", "note", "movement_date"]], use_container_width=True, hide_index=True)
