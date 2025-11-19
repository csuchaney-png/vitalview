# app_vitalview.py — VitalView (Login + Plans + Forgot Password + Stripe-ready)
# Run: pip install streamlit pandas numpy altair bcrypt
# Optional: pip install stripe reportlab

import os, time, secrets, sqlite3, bcrypt
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

# ---- Optional Stripe (safe if not installed) ----
try:
    import stripe
    stripe.api_key = os.getenv("STRIPE_TEST_KEY", "")
except Exception:
    stripe = None

STRIPE_PRICE_PRO = os.getenv("STRIPE_PRICE_PRO", "")
STRIPE_PRICE_ENT = os.getenv("STRIPE_PRICE_ENT", "")

# ---- Optional PDF export (safe if not installed) ----
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.utils import simpleSplit
except Exception:
    canvas = None
# ---- Altair theme (optional) ----
import altair as alt

def vitalview_altair_theme():
    return {
        "config": {
            "view": {"stroke": "transparent"},
            "background": THEME["bg"],
            "axis": {
                "labelColor": THEME["text"],
                "titleColor": THEME["text"],
                "gridColor": THEME["muted"]
            },
            "legend": {
                "labelColor": THEME["text"],
                "titleColor": THEME["text"]
            },
            "title": {"color": THEME["text"]},
            "range": {
                "category": [THEME["primary"], THEME["accent"], THEME["good"], THEME["warn"], THEME["danger"]],
            }
        }
    }

# Register/enable each run (safe to call multiple times)
alt.themes.register('vitalview', vitalview_altair_theme)
alt.themes.enable('vitalview')

# ----------------------------
# Page + basic style
# ----------------------------

st.set_page_config(page_title="VitalView", layout="wide")
# ===== VitalView Split-Word Animated Hero =====
st.markdown(
    """
    <style>
        .vv-container {
            text-align: center;
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .vv-word {
            font-size: 60px;
            font-weight: 900;
            letter-spacing: 1px;
        }

        .vv-vital {
            color: #00d4ff;
            animation: vvFadeInVital 1.4s forwards;
            opacity: 0;
        }

        .vv-view {
            color: #00ffa3;
            animation: vvFadeInView 2.4s forwards;
            opacity: 0;
        }

        @keyframes vvFadeInVital {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0px); }
        }

        @keyframes vvFadeInView {
            from { opacity: 0; transform: translateY(10px); }
            to   { opacity: 1; transform: translateY(0px); }
        }

        .vv-sub {
            font-size: 20px;
            color: #444;
            margin-top: -8px;
            animation: vvFadeInSub 3.0s forwards;
            opacity: 0;
        }

        @keyframes vvFadeInSub {
            from { opacity: 0; transform: translateY(6px); }
            to   { opacity: 1; transform: translateY(0px); }
        }

        .vv-tagline-bar {
            display: inline-block;
            margin-top: 6px;
            padding: 6px 14px;
            border-radius: 999px;
            background: linear-gradient(90deg, #0A74DA, #00c2ff, #00ffa3);
            color: white;
            font-size: 13px;
            font-weight: 600;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
    </style>

    <div class="vv-container">
        <div>
            <span class="vv-word vv-vital">Vital</span>
            <span class="vv-word vv-view">View</span>
        </div>
        <p class="vv-sub">
            Vital = what truly matters. View = how you see it.<br/>
            Together, VitalView shows where health equity needs action first.
        </p>
        <div class="vv-tagline-bar">
            Community Health • Equity Signals • Grant-Ready Insights
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# ===== VitalView polished theme (colors + tab highlight) =====
PRIMARY = "#0A74DA"      # Vital blue
ACCENT  = "#00E3A8"      # Aqua
INK     = "#0F172A"      # Slate-900
PAPER   = "#FFFFFF"      # White
MUTED   = "#64748B"      # Slate-500
# ===== THEME PRESETS =====
THEMES = {
    "Vital (Bright)": {
        "bg": "#ffffff",
        "panel": "#F6FAFF",
        "text": "#0A1B2E",
        "muted": "#6A7A8C",
        "primary": "#0A74DA",
        "primaryGradLeft": "#0A74DA",
        "primaryGradRight": "#00E3A8",
        "accent": "#00C2FF",
        "good": "#18A957",
        "warn": "#F6A800",
        "danger": "#E84D4D",
        "tabSelected": "#0A74DA",
        "tabHover": "#E9F4FF",
        "chip": "#EAF6FF",
    },
    "Midnight (Dark)": {
        "bg": "#0E1117",
        "panel": "#111827",
        "text": "#E5E7EB",
        "muted": "#9CA3AF",
        "primary": "#22D3EE",
        "primaryGradLeft": "#22D3EE",
        "primaryGradRight": "#34D399",
        "accent": "#60A5FA",
        "good": "#34D399",
        "warn": "#FBBF24",
        "danger": "#F87171",
        "tabSelected": "#111827",
        "tabHover": "#1F2937",
        "chip": "#0B1220",
    },
    "High Contrast": {
        "bg": "#ffffff",
        "panel": "#ffffff",
        "text": "#000000",
        "muted": "#222222",
        "primary": "#000000",
        "primaryGradLeft": "#000000",
        "primaryGradRight": "#FFB703",
        "accent": "#FB8500",
        "good": "#007200",
        "warn": "#C98400",
        "danger": "#B00020",
        "tabSelected": "#000000",
        "tabHover": "#F2F2F2",
        "chip": "#F5F5F5",
    },
}

if "theme_name" not in st.session_state:
    st.session_state.theme_name = "Vital (Bright)"
THEME = THEMES[st.session_state.theme_name]

st.markdown(
    """
    <style>
      @keyframes vitalPulse {
        0%   { letter-spacing: 0.05em; opacity: 0.9; }
        50%  { letter-spacing: 0.15em; opacity: 1.0; }
        100% { letter-spacing: 0.05em; opacity: 0.9; }
      }
      @keyframes glowSweep {
        0%   { box-shadow: 0 0 0px #00E3A8; }
        50%  { box-shadow: 0 0 18px #00E3A8; }
        100% { box-shadow: 0 0 0px #00E3A8; }
      }
    </style>
    <div style="
        background: radial-gradient(circle at 0% 0%, #00E3A8 0%, #0A74DA 40%, #041B3A 100%);
        padding: 18px;
        border-radius: 14px;
        margin-bottom: 12px;
        animation: glowSweep 4s ease-in-out infinite;
    ">
        <h1 style="
            text-align:center;
            color:white;
            margin:0;
            font-size:2.1em;
            font-weight:800;
            letter-spacing:0.12em;
            text-transform:uppercase;
            animation: vitalPulse 5s ease-in-out infinite;
        ">
            <span style="opacity:0.92;">VITAL</span>
            <span style="opacity:1.0;">VIEW</span>
        </h1>
        <p style="text-align:center;color:#ECF7FF;margin:4px 0 0;font-size:0.95em;">
            by <b>Christopher Chaney</b> — Turning community data into action, grants, and accountability.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)
# ===== GLOBAL CSS USING CURRENT THEME =====
st.markdown(
    f"""
    <style>
      :root {{
        --bg: {THEME['bg']};
        --panel: {THEME['panel']};
        --text: {THEME['text']};
        --muted: {THEME['muted']};
        --primary: {THEME['primary']};
        --gradL: {THEME['primaryGradLeft']};
        --gradR: {THEME['primaryGradRight']};
        --accent: {THEME['accent']};
        --good: {THEME['good']};
        --warn: {THEME['warn']};
        --danger: {THEME['danger']};
        --tabSelected: {THEME['tabSelected']};
        --tabHover: {THEME['tabHover']};
        --chip: {THEME['chip']};
      }}

      /* App background + text */
      .stApp {{
        background: var(--bg);
        color: var(--text);
      }}

      /* Top hero header (if you have a header div) */
      .vv-hero {{
        background: linear-gradient(90deg, var(--gradL), var(--gradR));
        border-radius: 14px;
        padding: 16px 18px;
        color: white;
        margin-bottom: 8px;
      }}

      /* Panels / containers */
      .stMarkdown, .stDataFrame, .stAlert, .stTabs, .stMetric {{
        color: var(--text);
      }}

      /* Buttons */
      .stButton>button, .stDownloadButton>button {{
        border-radius: 10px;
        font-weight: 600;
        border: none;
        background: linear-gradient(90deg, var(--gradL), var(--gradR));
        color: white;
      }}
      .stButton>button:hover, .stDownloadButton>button:hover {{
        filter: brightness(0.95);
        transform: translateY(-1px);
      }}

      /* Tabs: selected + hover styles */
      .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
        border-bottom: 3px solid var(--primary);
        color: var(--text) !important;
        font-weight: 700;
        background: var(--tabHover);
      }}
      .stTabs [data-baseweb="tab-list"] button:hover {{
        background: var(--tabHover);
      }}

      /* Chips / small badges */
      .vv-chip {{
        display: inline-block;
        background: var(--chip);
        color: var(--text);
        border-radius: 999px;
        padding: 2px 10px;
        font-size: 0.85rem;
        margin-right: 6px;
      }}

      /* Metrics card background hint */
      .stMetric {{
        background: var(--panel);
      }}

      /* Sidebar headings */
      section[data-testid="stSidebar"] .stMarkdown h3, 
      section[data-testid="stSidebar"] .stMarkdown h4 {{
        color: var(--text);
      }}
    </style>
    """,
    unsafe_allow_html=True
)



THEME = THEMES[st.session_state.theme_name]  # refresh after possible change

# ----------------------------
# Session defaults (MUST be early)
# ----------------------------
if "user" not in st.session_state:
    st.session_state.user = None      # dict: {name,email,plan}
if "plan" not in st.session_state:
    st.session_state.plan = "free"    # demo fallback when logged out

# ----------------------------
# Plans & features
# ----------------------------
PLAN_FEATURES = {
    "free":       {"exports": False},
    "pro":        {"exports": True},
    "enterprise": {"exports": True},
}

# ----------------------------
# Auth: SQLite + bcrypt
# ----------------------------
DB_PATH = "vitalview_users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT UNIQUE,
            password TEXT,
            plan TEXT DEFAULT 'free'
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS password_resets(
            email TEXT,
            code TEXT,
            expires INTEGER
        )
    """)
    conn.commit(); conn.close()

def add_user(name, email, password, plan="free"):
    if not (name and email and password):
        st.error("Enter name, email, and password.")
        return
    conn = sqlite3.connect(DB_PATH)
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    try:
        conn.execute("INSERT INTO users(name,email,password,plan) VALUES(?,?,?,?)",
                     (name.strip(), email.strip(), hashed, plan))
        conn.commit()
        st.success("✅ Account created. Please log in.")
    except sqlite3.IntegrityError:
        st.error("❌ That email is already registered.")
    finally:
        conn.close()

def login_user(email, password):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT name,email,password,plan FROM users WHERE email=?", (email.strip(),))
    row = cur.fetchone()
    conn.close()
    if row and bcrypt.checkpw(password.encode(), row[2].encode()):
        st.session_state.user = {"name": row[0], "email": row[1], "plan": row[3]}
        st.success(f"👋 Welcome back, {row[0]}!")
        st.experimental_rerun()
    else:
        st.error("❌ Incorrect email or password.")

def logout_user():
    st.session_state.user = None
    st.success("Logged out.")
    st.experimental_rerun()

def update_plan(email, plan):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE users SET plan=? WHERE email=?", (plan, email))
    conn.commit(); conn.close()

def start_reset(email, ttl_minutes=15):
    email = (email or "").strip()
    if not email:
        return False, "Enter your account email."
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT email FROM users WHERE email=?", (email,))
    if not cur.fetchone():
        conn.close()
        return False, "No user with that email."
    code = secrets.token_hex(3).upper()      # e.g. A1B2C3
    exp = int(time.time()) + ttl_minutes*60
    conn.execute("DELETE FROM password_resets WHERE email=?", (email,))
    conn.execute("INSERT INTO password_resets(email,code,expires) VALUES(?,?,?)",
                 (email, code, exp))
    conn.commit(); conn.close()
    return True, code

def finish_reset(email, code, newpwd):
    email = (email or "").strip()
    code  = (code or "").strip().upper()
    if not (email and code and newpwd):
        return False, "Provide email, code, and new password."
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT code,expires FROM password_resets WHERE email=?", (email,))
    row = cur.fetchone()
    if not row:
        conn.close(); return False, "No reset request found."
    saved, exp = row
    if code != saved:
        conn.close(); return False, "Invalid code."
    if time.time() > int(exp):
        conn.close(); return False, "Code expired."

    hashed = bcrypt.hashpw(newpwd.encode(), bcrypt.gensalt()).decode()
    conn.execute("UPDATE users SET password=? WHERE email=?", (hashed, email))
    conn.execute("DELETE FROM password_resets WHERE email=?", (email,))
    conn.commit(); conn.close()
    return True, "Password updated. Please log in."

init_db()

# ----------------------------
# Sidebar: Account
# ----------------------------
st.sidebar.header("🔑 Account")
if not st.session_state.user:
    auth_mode = st.sidebar.radio("Select option", ["Log In", "Sign Up"], horizontal=True, key="auth_mode")
    if auth_mode == "Log In":
        li_email = st.sidebar.text_input("Email")
        li_pwd   = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Log In"):
            login_user(li_email, li_pwd)
    else:
        su_name  = st.sidebar.text_input("Full Name")
        su_email = st.sidebar.text_input("Email")
        su_pwd   = st.sidebar.text_input("Password", type="password")
        su_plan  = st.sidebar.selectbox("Choose Plan", ["free","pro","enterprise"])
        if st.sidebar.button("Create Account"):
            add_user(su_name, su_email, su_pwd, su_plan)
# ----------------------------
# Sample data helper (VitalView Demo Mode)
# ----------------------------
def _make_sample_simple():
    """Tiny built-in sample so VitalView always has data in Demo Mode."""
    return pd.DataFrame(
        [
            ["Illinois","Cook","17031",2020,"Obesity (%)",31.2,"percent"],
            ["Illinois","Cook","17031",2021,"Obesity (%)",31.7,"percent"],
            ["Illinois","Cook","17031",2022,"Obesity (%)",32.1,"percent"],

            ["Illinois","Cook","17031",2020,"PM2.5 (µg/m³)",9.8,"ugm3"],

            ["Illinois","Lake","17097",2020,"Food Desert (%)",10.2,"percent"],

            ["Illinois","Will","17197",2020,"No Car Households (%)",6.1,"percent"],
            ["Illinois","Will","17197",2021,"No Car Households (%)",6.0,"percent"]
        ],
        columns=["state","county","fips","year","indicator","value","unit"]
    )

# ===== Local Resources CSV (optional upload) =====
st.sidebar.markdown("### 📂 Local Resources (CSV)")
# ===== Local Resources CSV template helper =====
def resources_csv_template_bytes() -> bytes:
    import pandas as pd
    cols = ["state", "county", "section", "label", "url"]
    sample_rows = [
        ["Illinois", "Cook", "Health Access", "Cook County Health — Clinics", "https://cookcountyhealth.org/locations/"],
        ["Illinois", "Cook", "Food & Nutrition", "Greater Chicago Food Depository — Find Food", "https://www.chicagosfoodbank.org/find-food/"],
        ["Illinois", "Cook", "Behavioral Health", "NAMI Chicago Helpline", "https://www.namichicago.org/helpline"],
        ["Illinois", "Cook", "Housing", "Chicago 311 — Homeless Services", "https://www.chicago.gov/city/en/depts/fss/provdrs/emerg/svcs/emergency-shelter.html"],
        ["Illinois", "Cook", "Transportation", "CTA Reduced/Free Ride Programs", "https://www.transitchicago.com/reduced-fare/"],
    ]
    df = pd.DataFrame(sample_rows, columns=cols)
    return df.to_csv(index=False).encode("utf-8")
res_csv = st.sidebar.file_uploader(
    "Upload local resources CSV",
    type=["csv"],
    help="Columns required: state, county, section, label, url"
)# Quick template download (so folks get the right headers)
st.sidebar.download_button(
    "⬇️ Download Resources CSV Template",
    data=resources_csv_template_bytes(),
    file_name="vitalview_local_resources_template.csv",
    mime="text/csv",
    help="Get a starter CSV with the correct headers: state, county, section, label, url"
)
# --- Forgot Password ---
with st.sidebar.expander("🔁 Forgot password?"):
    st.info("If you forgot your password, enter your email below to request a reset link.")
    with st.form("reset_request_form"):
        email_reset = st.text_input("Email address")
        submit_reset = st.form_submit_button("Send reset link")
        if submit_reset:
            if email_reset:
                st.success("A password reset link will be sent to your email (demo placeholder).")
            else:
                st.warning("Please enter your email address first.")
# ----------------------------
# Plan selection (demo override when logged out)
# ----------------------------
with st.sidebar.expander("💳 Plan (demo selector when logged out)"):
    st.session_state.plan = st.radio("Choose plan (demo only)", ["free","pro","enterprise"],
                                     index=["free","pro","enterprise"].index(st.session_state.plan))

# Determine active plan
active_plan = st.session_state.user["plan"] if st.session_state.user else st.session_state.plan
FEATURES = PLAN_FEATURES.get(active_plan, PLAN_FEATURES["free"])
st.markdown(
    f"<div style='text-align:center;color:#555;font-size:0.95em;'>"
    f"Active Plan: <b>{active_plan.title()}</b> — Exports: <b>{'ON' if FEATURES['exports'] else 'OFF'}</b></div>",
    unsafe_allow_html=True
)

# ----------------------------
# Upgrade via Stripe (test mode)
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Upgrade (Stripe Test)")
def start_checkout(price_id: str, user_email: str, success_plan: str):
    if stripe is None or not getattr(stripe, "api_key", ""):
        st.sidebar.error("Stripe not configured. Set STRIPE_TEST_KEY / PRICE env vars.")
        return
    if not user_email:
        st.sidebar.error("Log in first.")
        return
    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://example.com/success",
            cancel_url="https://example.com/cancel",
            customer_email=user_email
        )
        st.sidebar.success("Checkout session created.")
        st.sidebar.link_button("Open Stripe Checkout", session.url)
        # DEMO: instantly flip plan (real apps: use Stripe webhooks)
        if st.sidebar.button("Simulate success (demo)"):
            update_plan(user_email, success_plan)
            if st.session_state.user and st.session_state.user["email"] == user_email:
                st.session_state.user["plan"] = success_plan
            st.sidebar.success(f"Plan upgraded to {success_plan.title()}. Reload the page.")
    except Exception as e:
        st.sidebar.error(f"Stripe error: {e}")

col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("Upgrade to Pro"):
        if not STRIPE_PRICE_PRO: st.sidebar.error("Missing STRIPE_PRICE_PRO"); 
        else: start_checkout(STRIPE_PRICE_PRO, st.session_state.user["email"] if st.session_state.user else None, "pro")
with col2:
    if st.button("Enterprise"):
        if not STRIPE_PRICE_ENT: st.sidebar.error("Missing STRIPE_PRICE_ENT"); 
        else: start_checkout(STRIPE_PRICE_ENT, st.session_state.user["email"] if st.session_state.user else None, "enterprise")

# ----------------------------
# Data helpers & demo
# ----------------------------
# ===== Public Health Resource Catalog + Builders =====
from urllib.parse import quote_plus

NEED_CATALOG = {
    "Food Access": [
        ("Find a Food Bank (Feeding America)", "https://www.feedingamerica.org/find-your-local-foodbank"),
        ("SNAP Retailer Locator (USDA)", "https://www.fns.usda.gov/snap/retailer-locator"),
        ("WIC Program Finder", "https://www.fns.usda.gov/wic/wic-how-apply"),
    ],
    "Housing & Utilities": [
        ("HUD Resource Locator", "https://resources.hud.gov/"),
        ("Low Income Home Energy Assistance (LIHEAP)", "https://www.acf.hhs.gov/ocs/low-income-home-energy-assistance-program-liheap"),
        ("Emergency Rental Assistance (by state)", "https://www.consumerfinance.gov/coronavirus/mortgage-and-housing-assistance/renter-protections/find-help-with-rent-and-utilities/"),
    ],
    "Mental/Behavioral Health": [
        ("SAMHSA Treatment Locator", "https://findtreatment.gov"),
        ("988 Suicide & Crisis Lifeline", "https://988lifeline.org"),
        ("NAMI HelpLine", "https://www.nami.org/help"),
    ],
    "Healthcare Access": [
        ("Find a Community Health Center (HRSA)", "https://findahealthcenter.hrsa.gov"),
        ("Medicaid by State", "https://www.medicaid.gov/about-us/beneficiary-resources/index.html"),
        ("Marketplace (Healthcare.gov)", "https://www.healthcare.gov"),
    ],
    "Transportation": [
        ("211.org – Transportation Help", "https://www.211.org"),
        ("Medicaid NEMT (info)", "https://www.medicaid.gov/medicaid/benefits/downloads/transportation.pdf"),
    ],
    "Income/Employment": [
        ("Benefits.gov – Eligibility Finder", "https://www.benefits.gov/"),
        ("American Job Centers", "https://www.dol.gov/agencies/eta/american-job-centers"),
    ],
    "Legal & Safety": [
        ("Find Legal Aid (LSC)", "https://www.lsc.gov/about-lsc/what-legal-aid/find-legal-aid"),
        ("National DV Hotline", "https://www.thehotline.org/"),
        ("Disaster Assistance (FEMA)", "https://www.disasterassistance.gov/"),
    ],
    "Education & Data": [
        ("CDC Data Portal", "https://data.cdc.gov"),
        ("County Health Rankings", "https://www.countyhealthrankings.org"),
        ("U.S. Census Data", "https://data.census.gov"),
    ],
}
# ===== Local Resources CSV template =====
def resources_csv_template_bytes() -> bytes:
    import pandas as pd
    cols = ["state","county","section","label","url"]
    sample_rows = [
        ["Illinois","Cook","Health Access","Cook County Health — Clinics","https://cookcountyhealth.org/locations/"],
        ["Illinois","Cook","Food & Nutrition","Greater Chicago Food Depository — Find Food","https://www.chicagosfoodbank.org/find-food/"],
        ["Illinois","Cook","Behavioral Health","NAMI Chicago Helpline","https://www.namichicago.org/helpline"],
        ["Illinois","Cook","Housing","Chicago 311 — Homeless Services","https://www.chicago.gov/city/en/depts/fss/provdrs/emerg/svcs/emergency-shelter.html"],
        ["Illinois","Cook","Transportation","CTA Reduced/Free Ride Programs","https://www.transitchicago.com/reduced-fare/"],
    ]
    df = pd.DataFrame(sample_rows, columns=cols)
    return df.to_csv(index=False).encode("utf-8")
# optional: your Chicagoland local directory (extend as you grow)
LOCAL_DIR_IL = {
    "Cook": [
        ("Cook County Health — Clinics", "https://cookcountyhealth.org/locations/"),
        ("Greater Chicago Food Depository — Find Food", "https://www.chicagosfoodbank.org/find-food/"),
        ("NAMI Chicago Helpline", "https://www.namichicago.org/helpline"),
        ("Chicago 311 — Homeless Services", "https://www.chicago.gov/city/en/depts/fss/provdrs/emerg/svcs/emergency-shelter.html"),
        ("CTA Reduced/Free Ride Programs", "https://www.transitchicago.com/reduced-fare/"),
    ],
    "Lake": [
        ("Lake County Health Dept. — Services", "https://www.lakecountyil.gov/2313/"),
        ("Northern IL Food Bank — Find Food", "https://solvehungertoday.org/get-help/"),
        ("Lake County Crisis Care", "https://www.lakecountyil.gov/2399/Crisis-Care-Program"),
    ],
    "Will": [
        ("Will County Health Dept. — Clinics", "https://willcountyhealth.org/"),
        ("Northern IL Food Bank — Find Food", "https://solvehungertoday.org/get-help/"),
        ("Will County Behavioral Health", "https://willcountyhealth.org/programs/behavioral-health/"),
    ],
}

def local_resources(state: str, county: str) -> list[tuple[str, str]]:
    """Return prioritized local links if we know the region; else national defaults."""
    state = (state or "").title()
    county = (county or "").title()
    if state == "Illinois" and county in LOCAL_DIR_IL:
        return LOCAL_DIR_IL[county]
    # national fallbacks that help in any location
    return [
        ("Find a Community Health Center (HRSA)", "https://findahealthcenter.hrsa.gov"),
        ("Find a Food Bank (Feeding America)", "https://www.feedingamerica.org/find-your-local-foodbank"),
        ("SAMHSA Treatment Locator", "https://findtreatment.gov"),
        ("HUD Resource Locator", "https://resources.hud.gov/"),
        ("211.org – Local Services", "https://www.211.org"),
        ("Benefits.gov – Eligibility Finder", "https://www.benefits.gov/"),
    ]
# ===== Load & index local resources from CSV =====
def local_resources(state: str, county: str) -> list[tuple[str, str]]:
    """
    Priority:
      1) Uploaded CSV entries for (state, county)
      2) Built-in Chicagoland directory (LOCAL_DIR_IL)
      3) National defaults
    """
    state = (state or "").title()
    county = (county or "").title()

    # 1) uploaded CSV
    if "UPLOADED_RESOURCES" in globals():
        entries = UPLOADED_RESOURCES.get((state, county), [])
        if entries:
            # return as (label, url) but keep section later in the tab for grouping
            return entries  # this is list of (section, label, url)

    # 2) built-in IL directory
    if state == "Illinois" and county in LOCAL_DIR_IL:
        return [("Local", label, url) for (label, url) in LOCAL_DIR_IL[county]]

    # 3) national fallbacks
    return [
        ("National", "Find a Community Health Center (HRSA)", "https://findahealthcenter.hrsa.gov"),
        ("National", "Find a Food Bank (Feeding America)", "https://www.feedingamerica.org/find-your-local-foodbank"),
        ("National", "SAMHSA Treatment Locator", "https://findtreatment.gov"),
        ("National", "HUD Resource Locator", "https://resources.hud.gov/"),
        ("National", "211.org – Local Services", "https://www.211.org"),
        ("National", "Benefits.gov – Eligibility Finder", "https://www.benefits.gov/"),
    ]
    # normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"state", "county", "section", "label", "url"}
    if not required.issubset(set(df.columns)):
        st.warning(f"Resources CSV missing columns: {required - set(df.columns)}")
        return {}

    # clean
    for c in ["state", "county", "section", "label", "url"]:
        df[c] = df[c].astype(str).str.strip()

    # title-case state & county to match your filters
    df["state"] = df["state"].str.title()
    df["county"] = df["county"].str.title()

    # build index
    resources = {}
    for (_, row) in df.iterrows():
        key = (row["state"], row["county"])
        resources.setdefault(key, []).append((row["section"], row["label"], row["url"]))
    return resources

# hold parsed resources in memory
# ===== Load & index local resources from CSV =====
def load_local_resources_csv(file) -> dict:
    """
    CSV schema (headers, case-insensitive):
      state, county, section, label, url
    Returns: dict[(State, County)] -> list of (section, label, url)
    """
    if file is None:
        return {}

    try:
        df = pd.read_csv(file)
    except Exception:
        try:
            df = pd.read_csv(file, encoding="utf-8-sig")
        except Exception as e:
            st.warning(f"Could not read resources CSV: {e}")
            return {}

    # normalize columns
    df.columns = [c.strip().lower() for c in df.columns]
    required = {"state", "county", "section", "label", "url"}
    if not required.issubset(set(df.columns)):
        st.warning(f"Resources CSV missing columns: {required - set(df.columns)}")
        return {}

    # clean up text
    for c in ["state", "county", "section", "label", "url"]:
        df[c] = df[c].astype(str).str.strip()

    # title-case state & county to match your filters
    df["state"] = df["state"].str.title()
    df["county"] = df["county"].str.title()

    # build lookup dictionary
    resources = {}
    for _, row in df.iterrows():
        key = (row["state"], row["county"])
        resources.setdefault(key, []).append((row["section"], row["label"], row["url"]))

    return resources
UPLOADED_RESOURCES = load_local_resources_csv(res_csv)

def need_search_links(need: str, state: str, county: str) -> list[tuple[str, str]]:
    """
    Build 'active' search links for the selected need + user’s state/county:
      - 211 deep-link query
      - Google 'site:' queries for official sources
    """
    q_parts = [need]
    if county: q_parts.append(county)
    if state:  q_parts.append(state)
    q = " ".join(q_parts)

    links = []
    # 211 deep-link
    links.append(("Search 211 for this need", f"https://www.211.org/search?search={quote_plus(q)}"))

    # Google site: helpers (favor .gov/.org and local)
    g = quote_plus(q)
    links.extend([
        (f"Search .gov for {need}", f"https://www.google.com/search?q=site%3A.gov+{g}"),
        (f"Search .org for {need}", f"https://www.google.com/search?q=site%3A.org+{g}"),
        (f"{state} government help (Google)", f"https://www.google.com/search?q={quote_plus(state + ' ' + need)}") if state else None,
    ])
    return [x for x in links if x]
def _make_sample():
    counties = [("Illinois","Cook","17031"),("Illinois","Lake","17097"),("Illinois","Will","17197")]
    years = list(range(2019, 2025))
    rows=[]
    def trend(a,b,n): return [round(a+(b-a)*i/(n-1),2) for i in range(n)]
    ob={"Cook":trend(29,33,len(years)),"Lake":trend(25,29,len(years)),"Will":trend(26,31,len(years))}
    pm={"Cook":trend(11.5,9.2,len(years)),"Lake":trend(10.8,8.9,len(years)),"Will":trend(11.2,9.1,len(years))}
    un={"Cook":trend(15,11,len(years)),"Lake":trend(12,9,len(years)),"Will":trend(13,9.5,len(years))}
    nc={"Cook":trend(16,15,len(years)),"Lake":trend(7,6.5,len(years)),"Will":trend(6.3,5.9,len(years))}
    fd={"Cook":{2019:17.6,2022:16.8,2024:16.2},"Lake":{2019:10.6,2022:10.1,2024:9.8},"Will":{2019:12.7,2022:12.1,2024:11.9}}
    for (s,c,f) in counties:
        for i,y in enumerate(years):
            rows.append([s,c,f,y,"Obesity (%)",ob[c][i],"percent"])
            rows.append([s,c,f,y,"PM2.5 (µg/m³)",pm[c][i],"ugm3"])
            rows.append([s,c,f,y,"Uninsured (%)",un[c][i],"percent"])
            rows.append([s,c,f,y,"No Car Households (%)",nc[c][i],"percent"])
        for y in fd[c]:
            rows.append([s,c,f,y,"Food Desert (%)",fd[c][y],"percent"])
    return pd.DataFrame(rows, columns=["state","county","fips","year","indicator","value","unit"])
from datetime import datetime

def _save_narrative(text: str, state_list, county_list):
    if "narratives" not in st.session_state:
        st.session_state.narratives = []
    st.session_state.narratives.append({
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "states": list(state_list) if state_list else [],
        "counties": list(county_list) if county_list else [],
        "text": text,
    })
def enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    req = {"state","county","fips","year","indicator","value","unit"}
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    missing = req - set(df.columns)
    if missing:
        st.error(f"Missing columns: {missing}"); st.stop()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year","value"])
    for col in ("state","county","indicator","unit"):
        df[col] = df[col].astype(str).str.strip()
        if col in ("state","county"): df[col] = df[col].str.title()
    return df
# ===== Local resource linker =====
def local_resources(state: str, county: str) -> list[tuple[str,str,str]]:
    """
    returns a list of (section, label, url) tuples for the given state/county.
    expand this table over time with your most common regions.
    """
    state = (state or "").title()
    county = (county or "").title()

    # known Chicagoland examples
    IL = {
        "Cook": [
            ("🏥 Health Access", "Cook County Health — Clinics", "https://cookcountyhealth.org/locations/"),
            ("🏥 Health Access", "Find a FQHC (HRSA)", "https://findahealthcenter.hrsa.gov"),
            ("🌱 Food & Nutrition", "Greater Chicago Food Depository — Find Food", "https://www.chicagosfoodbank.org/find-food/"),
            ("🌱 Food & Nutrition", "Illinois SNAP (ABE) Application", "https://abe.illinois.gov/abe/access/"),
            ("💬 Behavioral Health", "NAMI Chicago Helpline", "https://www.namichicago.org/helpline"),
            ("🏠 Housing", "Chicago 311 — Homeless Services", "https://www.chicago.gov/city/en/depts/fss/provdrs/emerg/svcs/emergency-shelter.html"),
            ("🚍 Transportation", "CTA Reduced/Free Ride Programs", "https://www.transitchicago.com/reduced-fare/"),
        ],
        "Lake": [
            ("🏥 Health Access", "Lake County Health Dept. — Services", "https://www.lakecountyil.gov/2313/"),
            ("🌱 Food & Nutrition", "Northern IL Food Bank — Find Food", "https://solvehungertoday.org/get-help/"),
            ("💬 Behavioral Health", "Lake County Crisis Care", "https://www.lakecountyil.gov/2399/Crisis-Care-Program"),
        ],
        "Will": [
            ("🏥 Health Access", "Will County Health Dept. — Clinics", "https://willcountyhealth.org/"),
            ("🌱 Food & Nutrition", "Northern IL Food Bank — Find Food", "https://solvehungertoday.org/get-help/"),
            ("💬 Behavioral Health", "Will County Behavioral Health", "https://willcountyhealth.org/programs/behavioral-health/"),
        ],
    }

    if state == "Illinois" and county in IL:
        return IL[county]

    # sensible national defaults
    return [
        ("🏥 Health Access", "Find a Community Health Center (HRSA)", "https://findahealthcenter.hrsa.gov"),
        ("🌱 Food & Nutrition", "Feeding America — Food Bank Locator", "https://www.feedingamerica.org/find-your-local-foodbank"),
        ("💬 Behavioral Health", "SAMHSA Treatment Locator", "https://findtreatment.gov"),
        ("🏠 Housing", "HUD Resource Locator", "https://resources.hud.gov/"),
        ("🚍 Transportation", "211.org — Local transportation help", "https://www.211.org"),
        ("💼 Benefits", "Benefits.gov — Eligibility Finder", "https://www.benefits.gov/"),
    ]
def safe_csv_bytes(df: pd.DataFrame) -> bytes:
    def esc(x):
        if isinstance(x,str) and x and x[0] in ("=","+","-","@"): return "'"+x
        return x
    return df.applymap(esc).to_csv(index=False).encode("utf-8")

def zscore(s: pd.Series) -> pd.Series:
    s = pd.to_numeric(s, errors="coerce").astype(float)
    std = s.std(ddof=0) or 1.0
    return (s - s.mean()) / std

def derive_pivot(df_latest: pd.DataFrame) -> pd.DataFrame:
    if df_latest is None or df_latest.empty: return pd.DataFrame()
    return df_latest.pivot_table(index=["state","county","fips"],
                                 columns="indicator", values="value", aggfunc="mean")

def to_pdf_bytes(text: str, title="VitalView Report") -> bytes:
    if canvas is None: return b""
    buf = __import__("io").BytesIO()
    c = canvas.Canvas(buf, pagesize=letter); w,h = letter
    margin = 0.75*inch; y = h - margin
    c.setTitle(title); c.setFont("Helvetica-Bold", 14); c.drawString(margin,y,title); y -= 0.35*inch
    c.setFont("Helvetica",10); maxw = w-2*margin
    for raw in text.replace("\r","").split("\n"):
        if not raw.strip(): y -= 0.18*inch; continue
        for line in simpleSplit(raw,"Helvetica",10,maxw):
            if y < margin: c.showPage(); y = h-margin; c.setFont("Helvetica",10)
            c.drawString(margin,y,line); y -= 0.16*inch
    c.showPage(); c.save(); pdf = buf.getvalue(); buf.close(); return pdf

# ----------------------------
# Sidebar: About + Data
# ----------------------------
with st.sidebar.expander("ℹ️ About VitalView", expanded=True):
    st.write("Visualize local health data, identify disparities, and export grant-ready narratives.")

demo_mode = st.sidebar.checkbox("🧪 Demo Mode (sample data)", value=True)
# ----------------------------
# Data load (CSV / Excel / JSON) + sample
# ----------------------------
uploaded = st.sidebar.file_uploader(
    "Upload data file (CSV, Excel, or JSON: state, county, fips, year, indicator, value, unit)",
    type=["csv", "xlsx", "xls", "json"],
    accept_multiple_files=False,
    key="data_upload_main"
)

def load_any_file(uploaded_file):
    """Load CSV, Excel, or JSON and enforce VitalView schema."""
    if uploaded_file is None:
        # safety fallback, shouldn't normally get here
        return enforce_schema(_make_sample_simple())

    name = uploaded_file.name.lower()

    try:
        if name.endswith(".csv"):
            df_raw = pd.read_csv(uploaded_file)
        elif name.endswith(".xlsx") or name.endswith(".xls"):
            df_raw = pd.read_excel(uploaded_file)
        elif name.endswith(".json"):
            df_raw = pd.read_json(uploaded_file)
        else:
            st.error("Unsupported file type. Please upload CSV, Excel (.xlsx/.xls), or JSON.")
            st.stop()
    except Exception as e:
        st.error(f"Could not read file: {e}")
        st.stop()

    return enforce_schema(df_raw)

# If demo mode is on and no file uploaded → use the sample data
use_sample = demo_mode and (uploaded is None)

if use_sample:
    df = enforce_schema(_make_sample_simple())
else:
    df = load_any_file(uploaded) if uploaded is not None else enforce_schema(_make_sample_simple())
# ---------- Data summary & quality checks ----------
def summarize_data(df: pd.DataFrame) -> dict:
    """Quick summary for the homepage."""
    if df is None or df.empty:
        return {
            "rows": 0,
            "years": (None, None),
            "n_counties": 0,
            "n_indicators": 0,
            "missing_values": 0,
        }

    years = df["year"].dropna() if "year" in df.columns else pd.Series([], dtype="float")
    years_min = int(years.min()) if not years.empty else None
    years_max = int(years.max()) if not years.empty else None

    return {
        "rows": int(len(df)),
        "years": (years_min, years_max),
        "n_counties": int(df["county"].nunique()) if "county" in df.columns else 0,
        "n_indicators": int(df["indicator"].nunique()) if "indicator" in df.columns else 0,
        "missing_values": int(df.isna().sum().sum()),
    }


def find_data_issues(df: pd.DataFrame) -> list:
    """Return human-readable data quality issues / cleaning tips."""
    issues = []

    if df is None or df.empty:
        issues.append("No data loaded. Turn on Demo Mode or upload a file to begin exploring.")
        return issues

    # Required columns present?
    required = ["state", "county", "fips", "year", "indicator", "value", "unit"]
    missing_cols = [c for c in required if c not in df.columns]
    if missing_cols:
        issues.append(
            "Missing required columns: "
            + ", ".join(missing_cols)
            + ". Make sure your file includes all standard VitalView fields."
        )

    # Duplicate rows
    dup_count = int(df.duplicated().sum())
    if dup_count > 0:
        issues.append(
            f"{dup_count:,} duplicate row(s) detected. Consider removing duplicates before final analysis."
        )

    # Negative values (often suspicious for these indicators)
    if "value" in df.columns and (df["value"] < 0).any():
        issues.append(
            "Some indicator values are negative. Check those rows to confirm they’re valid (e.g., not a coding error)."
        )

    # Narrow year span
    if "year" in df.columns:
        years = df["year"].dropna()
        if not years.empty and years.max() - years.min() < 3:
            issues.append(
                "Year range is very narrow. Trend lines may be less meaningful; consider adding more years if available."
            )

    # Missing values by indicator
    if "indicator" in df.columns and "value" in df.columns:
        null_by_ind = df[df["value"].isna()].groupby("indicator").size()
        for ind, cnt in null_by_ind.items():
            issues.append(
                f"{cnt} record(s) for '{ind}' are missing values. You may want to impute or drop these before exporting."
            )

    return issues


# Pre-computed summary + issues, reused on the homepage
DATA_SUMMARY = summarize_data(df)
DATA_ISSUES = find_data_issues(df)
# ---------- Flagged rows + schema / documentation helpers ----------

def compute_flagged_rows(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a small table of 'flagged' rows:
    - missing values
    - negative values
    - duplicate rows
    - weird years
    """
    if df is None or df.empty:
        return pd.DataFrame()

    work = df.copy()
    work["flag_reason"] = ""

    # Missing numeric value
    if "value" in work.columns:
        mask_missing = work["value"].isna()
        work.loc[mask_missing, "flag_reason"] += "Missing value; "

        # Negative values (often suspicious)
        mask_neg = work["value"] < 0
        work.loc[mask_neg, "flag_reason"] += "Negative value; "

    # Year issues
    if "year" in work.columns:
        bad_year = work["year"].isna()
        work.loc[bad_year, "flag_reason"] += "Missing year; "

    # Duplicate rows
    dup_mask = work.duplicated()
    work.loc[dup_mask, "flag_reason"] += "Duplicate row; "

    flagged = work[work["flag_reason"] != ""].copy()
    flagged["flag_reason"] = flagged["flag_reason"].str.rstrip("; ").str.strip()

    # Only show a subset of columns so it’s readable
    keep_cols = [c for c in ["state", "county", "fips", "year", "indicator", "value", "unit", "flag_reason"] if c in flagged.columns]
    return flagged[keep_cols] if not flagged.empty else pd.DataFrame()


def analyze_structure_hints(df: pd.DataFrame) -> list:
    """
    Return 'variable finder' style hints about how the dataset is structured.
    Not AI, but very helpful.
    """
    hints = []
    if df is None or df.empty:
        hints.append("No data loaded yet. Turn on Demo Mode or upload a file to see structure hints.")
        return hints

    required = {"state","county","fips","year","indicator","value","unit"}
    extra_cols = [c for c in df.columns if c not in required]
    missing_cols = [c for c in required if c not in df.columns]

    if extra_cols:
        hints.append("Extra columns detected: " + ", ".join(extra_cols) + ". These can be useful but may need documentation.")
    if missing_cols:
        hints.append("Missing standard VitalView columns: " + ", ".join(missing_cols) + ".")

    # Indicator overview
    if "indicator" in df.columns:
        inds = sorted(df["indicator"].dropna().unique().tolist())
        n_inds = len(inds)
        if n_inds == 0:
            hints.append("No indicator names found. Check that your 'indicator' column is populated.")
        else:
            sample_inds = inds[:8]
            hints.append(f"{n_inds} unique indicators found. Examples: " + "; ".join(sample_inds) + ("..." if n_inds > 8 else ""))

    # Year coverage
    if "year" in df.columns:
        years = df["year"].dropna().unique().tolist()
        if years:
            hints.append(f"Year coverage: {int(min(years))}–{int(max(years))} ({len(years)} distinct year(s)).")
        else:
            hints.append("No valid year values found. Make sure 'year' is numeric.")

    return hints


def build_data_doc(df: pd.DataFrame, summary: dict, issues: list, schema_hints: list) -> str:
    """
    Build a plain-text 'dataset documentation' note that can be downloaded or pasted into a grant.
    """
    lines = []
    lines.append("VitalView Dataset Documentation")
    lines.append("--------------------------------")
    lines.append("")
    lines.append(f"Rows loaded: {summary.get('rows', 0):,}")

    yr_min, yr_max = summary.get("years", (None, None))
    if yr_min and yr_max:
        lines.append(f"Year range: {yr_min}–{yr_max}")
    else:
        lines.append("Year range: (not available)")

    lines.append(f"Unique counties: {summary.get('n_counties', 0):,}")
    lines.append(f"Unique indicators: {summary.get('n_indicators', 0):,}")
    lines.append(f"Total missing values: {summary.get('missing_values', 0):,}")
    lines.append("")

    # Columns
    if df is not None and not df.empty:
        lines.append("Columns:")
        for c in df.columns:
            lines.append(f"  - {c}")
    else:
        lines.append("Columns: (no data)")

    lines.append("")
    lines.append("Schema / Structure hints:")
    if schema_hints:
        for h in schema_hints:
            lines.append(f"  - {h}")
    else:
        lines.append("  - None found.")

    lines.append("")
    lines.append("Data quality notes:")
    if issues:
        for i in issues:
            lines.append(f"  - {i}")
    else:
        lines.append("  - No major issues detected.")

    lines.append("")
    lines.append("Generated by VitalView (v1.0 demo).")
    return "\n".join(lines)


# Pre-computed objects reused on the homepage & reports
FLAGGED_ROWS = compute_flagged_rows(df)
DATA_SCHEMA_HINTS = analyze_structure_hints(df)


# ----------------------------
# Filters
# ----------------------------
left, right = st.columns([1,3])
with left:
    st.subheader("Filters")
    states = sorted(df["state"].unique().tolist())
    state_sel = st.multiselect("Select State(s)", states, default=states[:1])
    dfx = df[df["state"].isin(state_sel)] if state_sel else df.copy()
    counties = sorted(dfx["county"].unique().tolist())
    county_sel = st.multiselect("Select County(ies)", counties)
    if county_sel: dfx = dfx[dfx["county"].isin(county_sel)]
    years = sorted(dfx["year"].unique().tolist())
    if years:
        y_min, y_max = int(min(years)), int(max(years))
        if y_min != y_max:
            yr_from, yr_to = st.slider("Year range", y_min, y_max, (y_min, y_max))
            dfx = dfx[(dfx["year"]>=yr_from)&(dfx["year"]<=yr_to)]
        else:
            st.caption(f"Year: {y_min}")

# ----------------------------
# Tabs
# ----------------------------
tab_overview, tab_trends, tab_priority, tab_reports, tab_resources, tab_actions, tab_map = st.tabs(
    ["🏠 Overview","📈 Trends","🎯 Priority","📝 Reports","🌍 Resources","🤝 Community Actions","🗺️ Map"]
)

# Overview
with tab_overview:
    # --- Big visual upload/status card ---
    st.subheader("Welcome to VitalView 1.0")

    st.markdown(
        """
        <div style="
            border-radius: 12px;
            padding: 16px;
            background: linear-gradient(90deg,#0A74DA11,#00E3A822);
            border: 1px solid #0A74DA33;
            margin-bottom: 14px;">
            <span style="font-weight:600;">Step 1 — Add your data.</span><br>
            • Drag & drop a <b>CSV, Excel, or JSON</b> file into the uploader in the left sidebar<br>
            • Or turn on <b>Demo Mode</b> in the sidebar to explore sample data for Cook, Lake, and Will Counties<br><br>
            <span style="font-size:0.9em;opacity:0.85;">
            VitalView automatically checks your file for required columns, missing values, and basic issues.
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Data Snapshot ---
    st.subheader("Data Snapshot")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows loaded", f"{DATA_SUMMARY['rows']:,}")

    yr_min, yr_max = DATA_SUMMARY["years"]
    if yr_min and yr_max:
        c2.metric("Year range", f"{yr_min}–{yr_max}")
    else:
        c2.metric("Year range", "—")

    c3.metric("Counties", f"{DATA_SUMMARY['n_counties']:,}")
    c4.metric("Indicators", f"{DATA_SUMMARY['n_indicators']:,}")

    st.caption(f"Total missing values detected: {DATA_SUMMARY['missing_values']:,}")

    st.divider()

    # --- Data Quality Check / Cleaning Suggestions ---
    st.subheader("Data Quality Check")

    if not DATA_ISSUES:
        st.success("✅ No major data issues detected. You’re ready to explore trends, priorities, and maps.")
    else:
        st.markdown("VitalView found some things you may want to clean before using this data in a grant or report:")
        for issue in DATA_ISSUES[:8]:
            st.warning("• " + issue)

        if len(DATA_ISSUES) > 8:
            st.info(f"...and {len(DATA_ISSUES) - 8} more potential issues. Consider reviewing those rows in your source file.")

    # --- Flagged Rows Preview ---
    st.subheader("Flagged Rows Preview")

    if FLAGGED_ROWS is None or FLAGGED_ROWS.empty:
        st.info("No specific rows flagged. That’s a good sign — or your file is very clean.")
    else:
        st.caption("Sample of rows with missing, negative, duplicate, or otherwise flagged values.")
        st.dataframe(FLAGGED_ROWS.head(50), use_container_width=True)

    st.divider()

    # --- Variable Finder / Schema Hints ---
    st.subheader("Variable Finder & Schema Hints")

    if DATA_SCHEMA_HINTS:
        for h in DATA_SCHEMA_HINTS:
            st.write("• " + h)
    else:
        st.info("No schema hints available yet. Upload a dataset or enable Demo Mode.")

    st.divider()

    # --- Download cleaned version (simple demo cleaner) ---
    st.subheader("Download Cleaned Data (Demo)")

    def _clean_for_export(df_clean: pd.DataFrame) -> pd.DataFrame:
        if df_clean is None or df_clean.empty:
            return pd.DataFrame()
        work = df_clean.copy()
        # Drop duplicate rows
        work = work.drop_duplicates()
        # Drop rows with missing year or value
        if "year" in work.columns:
            work = work[work["year"].notna()]
        if "value" in work.columns:
            work = work[work["value"].notna()]
        # Drop negative values for these common indicators
        if "indicator" in work.columns and "value" in work.columns:
            neg_mask = (work["value"] < 0)
            work = work[~neg_mask]
        return work

    CLEANED_EXPORT = _clean_for_export(df)

    if CLEANED_EXPORT is None or CLEANED_EXPORT.empty:
        st.info("No cleaned data available to download yet.")
    else:
        st.caption("This cleaned file removes duplicate rows, missing year/value rows, and negative values in common indicators.")
        if 'safe_csv_bytes' in globals():
            st.download_button(
                "⬇️ Download Cleaned Data (CSV)",
                data=safe_csv_bytes(CLEANED_EXPORT),
                file_name="vitalview_cleaned_data.csv",
                mime="text/csv",
                key="download_cleaned_csv"
            )
        else:
            st.warning("`safe_csv_bytes` is not available. You can still export using df.to_csv() directly in a future update.")

    st.divider()
    st.markdown(
        """
        **Next steps**

        - Go to the **📈 Trends** tab to see indicator trends over time  
        - Use **🎯 Priority** to compute equity-weighted scores and export priority lists  
        - Open **🗺️ Map** to see where needs are most concentrated across states  
        - Use **📝 Reports** and the AI Grant Writer to generate narrative language for proposals
        """
    )

# Trends
with tab_trends:
    st.subheader("Trends & Comparisons")
    indicators = sorted(dfx["indicator"].dropna().unique().tolist()) if not dfx.empty else []
    ind_sel = st.selectbox("Indicator", indicators if indicators else ["(none)"])
    dfi = dfx[dfx["indicator"]==ind_sel] if ind_sel!="(none)" else pd.DataFrame()
    if dfi.empty:
        st.info("No rows for this indicator with current filters.")
    else:
        st.line_chart(dfi.sort_values("year").set_index("year")["value"])
        st.caption(f"{len(dfi):,} rows after filters")

# Priority (equity-weighted)
def compute_priority_df(pivot: pd.DataFrame, weights: dict) -> pd.DataFrame:
    if pivot is None or pivot.empty: return pd.DataFrame()
    z = pivot.apply(zscore, axis=0)
    score = 0; used=[]
    for lbl, w in weights.items():
        col = next((c for c in z.columns if c.lower().startswith(lbl.lower())), None)
        if col is not None:
            score = score + w * z[col]; used.append(col)
    out = z.copy(); out["E_Score"] = score; out["__used__"]=", ".join(used) if used else "(none)"
    return out.reset_index().sort_values("E_Score", ascending=False)

with tab_priority:
    st.subheader("Equity-Weighted Priority Scoring")
    if dfx.empty:
        st.info("Upload data or enable Demo Mode.")
    else:
        latest = int(dfx["year"].max())
        df_latest = dfx[dfx["year"]==latest]
        pivot = derive_pivot(df_latest)

        # auto sliders for found indicators
        weights = {}
        for ind in sorted(pivot.columns.tolist()):
            label = ind.split("(")[0].strip()
            default = 1.0 if "Food Desert" in ind or "PM2.5" in ind else 0.8
            weights[ind] = st.slider(f"{label}", 0.0, 2.0, float(default), 0.1, key=f"w_{ind}")

        priority_df = compute_priority_df(pivot, weights) if not pivot.empty else pd.DataFrame()
        if priority_df.empty:
            st.info("No priority table available. Adjust weights or data.")
        else:
            st.dataframe(priority_df.head(15), use_container_width=True)
            if FEATURES["exports"]:
                st.download_button("⬇️ Download Priority (CSV)",
                                   data=safe_csv_bytes(priority_df),
                                   file_name="priority_list.csv", mime="text/csv")

# Reports (narrative + PDF)
with tab_reports:
    st.subheader("Grant / Board Narrative")
    try:
        latest = int(dfx["year"].max())
        df_latest = dfx[dfx["year"]==latest]
        pivot = derive_pivot(df_latest)
        if 'weights' not in locals() or not pivot.columns.tolist():
            weights = {c:1.0 for c in pivot.columns}
        pr = compute_priority_df(pivot, weights) if not pivot.empty else pd.DataFrame()
    except Exception:
        pr = pd.DataFrame()
    st.divider()
    st.subheader("📄 Dataset Documentation Builder")

    if st.button("Generate Dataset Documentation", key="build_data_doc_btn"):
        doc_text = build_data_doc(df, DATA_SUMMARY, DATA_ISSUES, DATA_SCHEMA_HINTS)
        st.text(doc_text)

        if 'safe_csv_bytes' in globals():
            # We don't actually need CSV here, but we’ll provide TXT download:
            st.download_button(
                "⬇️ Download Documentation (TXT)",
                data=doc_text.encode("utf-8"),
                file_name="vitalview_dataset_documentation.txt",
                mime="text/plain",
                key="download_data_doc_txt"
            )
        else:
            st.info("TXT documentation shown above. You can copy & paste it into your grant or Word/Pages.")

# ----------------------------
# U.S. Map (State-level choropleth by equity score)
# ----------------------------
with tab_map:
    st.subheader("U.S. Equity Score Map (Latest Year)")

    if 'dfx' not in locals() or dfx.empty:
        st.info("Upload data or enable Demo Mode to see the map.")
    else:
        try:
            latest_year = int(dfx["year"].max())
            df_latest_map = dfx[dfx["year"] == latest_year]

            # Pivot (wide) for scoring
            pivot_map = derive_pivot(df_latest_map)

            # Weights: use current ones if they exist, else fallback to 1.0 each
            if 'weights' not in locals() or not weights:
                weights = {col: 1.0 for col in (pivot_map.columns if not pivot_map.empty else [])}

            # Compute equity scores (E_Score) per county
            priority_map = compute_priority_df(pivot_map, weights) if not pivot_map.empty else pd.DataFrame()

            if priority_map.empty:
                st.info("Not enough data to compute scores for the map.")
            else:
                # Average E_Score per state for choropleth
                state_scores = (
                    priority_map.groupby("state", as_index=False)["E_Score"]
                    .mean()
                    .rename(columns={"E_Score": "equity_score"})
                )

                import altair as alt
                us_states_url = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json"
                states = alt.topo_feature(us_states_url, feature="states")

                # VitalView gradient
                vitalview_range = ["#0A74DA", "#00C2FF", "#00E3A8", "#7CF29A"]

                map_chart = (
                    alt.Chart(states)
                    .mark_geoshape(stroke="white", strokeWidth=0.5)
                    .transform_lookup(
                        lookup="properties.name",
                        from_=alt.LookupData(state_scores, "state", ["equity_score"])
                    )
                    .encode(
                        color=alt.Color("equity_score:Q",
                                        title="Avg Equity Score",
                                        scale=alt.Scale(range=vitalview_range)),
                        tooltip=[
                            alt.Tooltip("properties.name:N", title="State"),
                            alt.Tooltip("equity_score:Q", title="Avg Equity Score", format=".2f"),
                        ],
                    )
                    .properties(height=520)
                    .project(type="albersUsa")
                )

                st.altair_chart(map_chart, use_container_width=True)
                st.caption(f"Latest year mapped: {latest_year}. Equity score = z-scored & weighted indicator mix averaged by state.")

                # simple drilldown: pick a state to show top counties
                st.markdown("### State details")
                states_available = sorted(state_scores["state"].dropna().unique().tolist())
                state_pick = st.selectbox("Choose a state", options=states_available) if states_available else None

                if state_pick:
                    state_detail = priority_map[priority_map["state"] == state_pick].copy()
                    if state_detail.empty:
                        st.info("No county rows for this state under current filters/weights.")
                    else:
                        top_n = st.slider("Show top N counties", 5, 30, 10, 1, key="map_topn")
                        top_view = state_detail.head(top_n)[["state","county","E_Score","__used__"]].rename(
                            columns={"E_Score": "Equity Score", "__used__": "Weighted Indicators"}
                        )
                        st.dataframe(top_view, use_container_width=True)
        except Exception as e:
            st.error(f"Map error: {e}")
# =========================
# 🧠 AI Grant Writer (Data-Aware Draft) + 1-Click Polisher
# =========================
st.divider()
st.subheader("🧠 AI Grant Writer (Data-Aware Draft)")

# tiny helper to make quick trend blurbs
def _trend_blurbs(df_scope: pd.DataFrame) -> list:
    blurbs = []
    if df_scope is None or df_scope.empty: 
        return blurbs
    years_sorted = sorted(pd.to_numeric(df_scope["year"], errors="coerce").dropna().unique().tolist())
    slice_years = years_sorted[-3:] if len(years_sorted) >= 3 else years_sorted
    d3 = df_scope[df_scope["year"].isin(slice_years)].copy()
    for ind, sub in d3.groupby("indicator"):
        try:
            sub = sub.groupby("year", as_index=False)["value"].mean().sort_values("year")
            if len(sub) >= 2:
                delta = float(sub["value"].iloc[-1]) - float(sub["value"].iloc[0])
                dirw = "increased" if delta > 0 else ("decreased" if delta < 0 else "held steady")
                blurbs.append(f"{ind} {dirw} by {abs(delta):.1f} over {len(sub)} year(s).")
        except Exception:
            pass
    return blurbs[:6]

with st.form("ai_grant_writer_form"):
    program_name = st.text_input("Program/Initiative Name", value="VitalView Community Health Initiative")
    target_pop   = st.text_input("Target Population", value="Low-income residents in identified priority counties")
    timeframe    = st.text_input("Timeframe", value="12 months")
    geog_scope   = st.text_input("Geographic focus (optional)", value="")
    focus_domains = st.multiselect(
        "Focus Domains",
        ["Food Access", "Environmental Health", "Healthcare Access", "Housing & Transportation", "Education & Outreach", "Behavioral Health"],
        default=["Food Access","Healthcare Access","Housing & Transportation"]
    )
    outcomes_txt = st.text_area("SMART Outcomes (one per line)", value="Increase SNAP enrollment by 10%\nLaunch weekly mobile market in 2 neighborhoods\nEnroll 100 residents in lifestyle coaching")
    include_stories = st.checkbox("Include recent Community Actions (stories)", value=True)
    tone = st.selectbox("Tone", ["Neutral professional", "Equity-forward", "Impact-focused"], index=1)
    build_ai = st.form_submit_button("🧠 Generate Draft")

draft = ""
if build_ai:
    try:
        # scope & latest
        df_scope = dfx.copy() if ('dfx' in locals() and not dfx.empty) else df.copy()
        latest_year = int(df_scope["year"].max()) if not df_scope.empty else None
        piv = derive_pivot(df_scope[df_scope["year"] == latest_year]) if latest_year else derive_pivot(df_scope)

        # weights fallback if none exist
        if 'weights' not in locals() or not weights:
            weights = {col: 1.0 for col in (piv.columns if not piv.empty else [])}

        pr_df = compute_priority_df(piv, weights) if not piv.empty else pd.DataFrame()
        top_list = ", ".join([f"{r.county} ({r.state})" for _, r in pr_df.head(3).iterrows()]) if not pr_df.empty else "priority areas identified"

        used_cols = []
        if "__used__" in pr_df.columns and not pr_df.empty and isinstance(pr_df["__used__"].iloc[0], str):
            used_cols = [c.strip() for c in pr_df["__used__"].iloc[0].split(",") if c.strip()]
        if not used_cols:
            used_cols = list(piv.columns)[:5] if not piv.empty else []
        drivers_text = ", ".join(used_cols) if used_cols else "multiple community determinants"

        trends = _trend_blurbs(df_scope)
        # (Optional) pull community actions from session storage
        story_lines = []
        if include_stories and "community_actions" in st.session_state and st.session_state.community_actions:
            for s in st.session_state.community_actions[-3:]:
                snippet = (s["story"][:220] + "…") if len(s["story"]) > 220 else s["story"]
                story_lines.append(f"- {s['location']}: {snippet}")
        if not story_lines:
            story_lines = ["- (No community stories submitted yet)"]

        outcomes_lines = [o.strip() for o in outcomes_txt.splitlines() if o.strip()]
        domains_text = ", ".join(focus_domains) if focus_domains else "core equity domains"

        if tone == "Neutral professional":
            tone_intro = "This proposal presents a practical, data-driven plan to improve community health outcomes."
        elif tone == "Impact-focused":
            tone_intro = "This initiative is designed to deliver measurable improvements where the need is greatest."
        else:  # Equity-forward
            tone_intro = "Grounded in equity, this proposal centers communities experiencing disproportionate barriers."

        draft = f"""
{program_name} — Grant Draft

Executive Summary
{tone_intro} Using VitalView’s equity-weighted analysis, we identified top-need areas: {top_list}.
We will deploy targeted interventions across {domains_text} with measurable outcomes over {timeframe}.

Statement of Need
VitalView synthesizes local indicators (e.g., {drivers_text}) to surface where resources can do the most good.
{'Geographic scope: ' + geog_scope if geog_scope else ''}

Recent Indicator Trends
{chr(10).join(['- ' + t for t in trends]) if trends else '- Insufficient trend data; baseline profiles available.'}

Community Voice
{chr(10).join(story_lines)}

Target Population
{target_pop}

Proposed Strategies
- Data-informed outreach and enrollment navigation
- Food access supports (mobile markets, produce prescription, grocer partnerships)
- Indoor activity & air-quality awareness where environmental burdens are higher
- Transportation-aware siting and voucher coordination
- Culturally relevant lifestyle coaching & education

Partnerships
- Local health department
- Community clinic
- Food bank
- Transit/municipal partners
(Add/replace with named partners as appropriate.)

SMART Outcomes
{chr(10).join(['- ' + o for o in outcomes_lines]) if outcomes_lines else '- Add SMART outcomes here'}

Implementation Timeline ({timeframe})
- Phase 1: Launch outreach; finalize partners; baseline metrics
- Phase 2: Program activation; midpoint evaluation; adjust targeting
- Phase 3: Scale to additional neighborhoods; deepen case management
- Phase 4: Summative evaluation; sustainability plan

Evaluation & Equity Monitoring
- Quarterly equity-weighted priority tracking
- Outcome indicators by ZIP/tract; transparent reporting to stakeholders
- Use of VitalView dashboard for shared accountability

Budget & Sustainability (outline)
- Personnel (navigators, coordinators)
- Program operations (markets, vouchers, comms)
- Data/evaluation (hosting, analytics, reporting)
- Sustainability via payer/city partnerships and philanthropy

Powered by VitalView — Community Health Dashboard (© {latest_year if latest_year else ''})
"""
        st.text(draft)

        # downloads (Pro feature)
        if FEATURES.get("exports", False):
            st.download_button(
                "⬇️ Download Draft (TXT)",
                data=draft.encode("utf-8"),
                file_name="VitalView_Grant_Draft.txt",
                mime="text/plain",
                key="download_ai_draft_txt"
            )
            pdf_ai = to_pdf_bytes(draft, title="VitalView — Grant Draft")
            if pdf_ai:
                st.download_button(
                    "⬇️ Download Draft (PDF)",
                    data=pdf_ai,
                    file_name="VitalView_Grant_Draft.pdf",
                    mime="application/pdf",
                    key="download_ai_draft_pdf"
                )
            else:
                st.info("Install ReportLab to enable PDF export:  \n`pip install reportlab`")
        else:
            st.info("Exports are a Pro feature. Upgrade in the sidebar to download.")
    except Exception as e:
        st.error(f"Grant Writer error: {e}")

# -------- 1-Click Polisher --------
st.subheader("🪄 Polish This Draft (1-Click Formatter)")

def _summarize_lines(text: str, max_chars: int = 1400) -> str:
    if not text: return ""
    t = " ".join(line.strip() for line in text.splitlines())
    return (t[:max_chars].rstrip() + "…") if len(t) > max_chars else t

def _to_bullets(text: str, max_lines: int = 14) -> str:
    out=[]
    for line in (text or "").splitlines():
        s=line.strip()
        if not s: continue
        if s.endswith(":"): out.append(f"- **{s[:-1]}**")
        elif not s.startswith("- "): out.append(f"- {s}")
        else: out.append(s)
        if len(out) >= max_lines:
            out.append("…"); break
    return "\n".join(out)

def _sectionize(text: str) -> dict:
    sections, current = {}, None
    for line in (text or "").splitlines():
        if line.strip() and not line.startswith(" "):
            if any(h in line for h in ["Executive Summary","Statement of Need","Recent Indicator Trends",
                                       "Community Voice","Target Population","Proposed Strategies",
                                       "Partnerships","SMART Outcomes","Implementation Timeline",
                                       "Evaluation & Equity Monitoring","Budget & Sustainability"]):
                current = line.strip(); sections[current] = []; continue
        if current: sections[current].append(line)
    return {k:"\n".join(v).strip() for k,v in sections.items()}

polish_mode = st.selectbox(
    "Audience / Style",
    ["Board-ready Executive Summary","Clinic/Implementation Summary","Funder Narrative (Concise)","Bulleted Talking Points"],
    index=0
)
polish_btn = st.button("✨ Polish Current Draft")

if polish_btn:
    if not draft:
        st.warning("Generate a draft above first, then polish it.")
    else:
        secs = _sectionize(draft)
        exsum = secs.get("Executive Summary","")
        need  = secs.get("Statement of Need","")
        strategies = secs.get("Proposed Strategies","")
        outcomes  = secs.get("SMART Outcomes","")
        timeline  = secs.get("Implementation Timeline","")
        evalmon   = secs.get("Evaluation & Equity Monitoring","")

        if polish_mode == "Board-ready Executive Summary":
            polished = f"""Executive Summary (Board-ready)

{_summarize_lines(exsum, 600)}

Key Drivers & Need
{_summarize_lines(need, 500)}

Planned Actions
{_to_bullets(strategies, 8)}

SMART Outcomes
{_to_bullets(outcomes, 6)}
"""
        elif polish_mode == "Clinic/Implementation Summary":
            polished = f"""Clinic / Implementation Summary

What We’ll Do (Action Steps)
{_to_bullets(strategies, 10)}

12-Month Timeline
{_to_bullets(timeline, 8)}

Evaluation & Reporting
{_summarize_lines(evalmon, 400)}
"""
        elif polish_mode == "Funder Narrative (Concise)":
            polished = f"""Funder Narrative (Concise)

Need & Equity Rationale
{_summarize_lines(need, 500)}

Approach
{_summarize_lines(strategies, 500)}

Measurable Outcomes
{_to_bullets(outcomes, 8)}
"""
        else:
            polished = f"""Talking Points

{_to_bullets(exsum, 6)}

Need
{_to_bullets(need, 6)}

Actions
{_to_bullets(strategies, 8)}

Outcomes
{_to_bullets(outcomes, 6)}
"""

        st.text(polished)
        if FEATURES.get("exports", False):
            st.download_button(
                "⬇️ Download Polished Draft (TXT)",
                data=polished.encode("utf-8"),
                file_name="VitalView_Polished_Draft.txt",
                mime="text/plain",
                key="download_polished_draft_txt"
            )
            pdf_polished = to_pdf_bytes(polished, title="VitalView — Polished Draft")
            if pdf_polished:
                st.download_button(
                    "⬇️ Download Polished Draft (PDF)",
                    data=pdf_polished,
                    file_name="VitalView_Polished_Draft.pdf",
                    mime="application/pdf",
                    key="download_polished_draft_pdf"
                )
            else:
                st.info("Install ReportLab to enable PDF export:  \n`pip install reportlab`")
        else:
            st.info("Exports are a Pro feature. Upgrade in the sidebar to download.")
# ---------- Resources Tab (Smart, Need-Based) ----------
# Local directory (uploaded CSV first, then built-in, then national)
st.markdown("### 📍 Local Programs (based on your State/County)")
# ---------- Helper: local resource lookup ----------
def local_resources(state: str, county: str) -> list:
    """
    Returns a list of tuples (section, label, url) for a given state/county.
    Pulls from UPLOADED_RESOURCES (if available) or built-in fallbacks.
    """
    results = []

    # 1️⃣ Try uploaded CSV resources
    if "UPLOADED_RESOURCES" in globals() and UPLOADED_RESOURCES:
        key_exact = (state.title(), county.title())
        key_state = (state.title(), "")
        if key_exact in UPLOADED_RESOURCES:
            results.extend(UPLOADED_RESOURCES[key_exact])
        elif key_state in UPLOADED_RESOURCES:
            results.extend(UPLOADED_RESOURCES[key_state])

    # 2️⃣ Built-in fallback examples (if CSV not found)
    if not results:
        if state.lower() == "illinois":
            if county.lower() == "cook":
                results = [
                    ("Food Access", "Greater Chicago Food Depository", "https://www.chicagosfoodbank.org/find-food/"),
                    ("Housing", "Chicago Housing Authority", "https://www.thecha.org"),
                    ("Healthcare", "Cook County Health Clinics", "https://cookcountyhealth.org/locations/"),
                    ("Mental Health", "NAMI Chicago Helpline", "https://www.namichicago.org/help"),
                ]
            elif county.lower() == "lake":
                results = [
                    ("Healthcare", "Lake County Health Department", "https://lakecountyil.gov/2318/Health-Department"),
                    ("Food Access", "Northern Illinois Food Bank", "https://solvehungertoday.org/get-help/"),
                ]
            elif county.lower() == "will":
                results = [
                    ("Housing", "Will County Center for Community Concerns", "https://wcccc.net/"),
                    ("Food Access", "Northern Illinois Food Bank — Will County", "https://solvehungertoday.org/get-help/"),
                ]
        else:
            results = [
                ("National", "FindHelp.org — National Directory", "https://www.findhelp.org/"),
                ("National", "211.org — Community Resources", "https://211.org"),
            ]

    return results

# ---------- Resources Tab (Smart, Need-Based) ----------
with tab_resources:
    st.subheader("🌍 Community Health Resources")

    # --- Emergency banner ---
    st.warning("If you or someone else is in immediate danger, call **911**. For mental health crises, call **988** (24/7).")

    # --- Define state/county safely ---
    def _first_or_none(x):
        if isinstance(x, list) and len(x) > 0:
            return x[0]
        if isinstance(x, str) and x.strip():
            return x
        return None

    sel_state = _first_or_none(globals().get("state_sel")) or "Illinois"
    sel_county = _first_or_none(globals().get("county_sel")) or ("Cook" if sel_state == "Illinois" else "")

    st.caption(f"Location context: **{sel_county or '(county not set)'}**, **{sel_state}**")

    # --- Need picker + optional keywords ---
    colr1, colr2 = st.columns([1, 1])

    with colr1:
        need_sel = st.selectbox(
            "What do you need right now?",
            list(NEED_CATALOG.keys()),
            index=list(NEED_CATALOG.keys()).index("Food Access"),
            key=f"resources_need_{sel_state}_{sel_county}_v1"
        )

    with colr2:
        custom_need = st.text_input(
            "(Optional) Add keywords (e.g., 'shelter', 'diabetes', 'prenatal')",
            value="",
            key=f"resources_keywords_{sel_state}_{sel_county}_v1"
        )

    # --- Directory header ---
    st.markdown(f"### 🔎 {need_sel} — Trusted Directories")

    # Local directory (uploaded CSV first, then built-in, then national)
    st.markdown("### 📍 Local Programs (based on your State/County)")
    entries = local_resources(sel_state, sel_county)

    from collections import defaultdict
    groups = defaultdict(list)
    for item in entries:
        if len(item) == 3:
            section, label, url = item
        else:
            section, (label, url) = "Local", item
        groups[section].append((label, url))

    for section, items in groups.items():
        st.markdown(f"#### {section}")
        for label, url in items:
            st.markdown(f"- [{label}]({url})")

    # Active search launchers (211 + .gov/.org + state)
    st.markdown("### 🚀 Active Search")
    q_need = (custom_need or need_sel).strip()
    for label, url in need_search_links(q_need, sel_state, sel_county):
        st.markdown(f"- [{label}]({url})")

    st.info("Tip: adjust **State/County** filters to update local links. Use the keywords box to refine searches (e.g., 'utility shutoff', 'opioid', 'dental clinic').")
# ---------- Community Actions Tab ----------
with tab_actions:
    st.subheader("🤝 Community Actions & Local Insights")
    st.markdown("Share real projects or observations that match what you see in the data.")

    # in-memory store (resets on app restart)
    if "community_actions" not in st.session_state:
        st.session_state.community_actions = []

    with st.form("community_action_form"):
        name = st.text_input("Your Name or Organization")
        location = st.text_input("Community / City")
        category = st.selectbox("Focus Area", [
            "Food Access","Environmental Health","Healthcare Access",
            "Housing & Transportation","Education & Outreach","Other"
        ])
        story = st.text_area("Describe your initiative or observation")
        submitted = st.form_submit_button("📤 Submit Story")
    if submitted and story.strip():
        st.session_state.community_actions.append({
            "name": name or "Anonymous",
            "location": location or "Unknown",
            "category": category,
            "story": story.strip()
        })
        st.success("✅ Added. Thank you for sharing!")

    if st.session_state.community_actions:
        st.markdown("### 🌟 Latest Stories")
        for entry in reversed(st.session_state.community_actions[-12:]):
            st.markdown(f"""
**{entry['name']}** — *{entry['location']}*  
_Category:_ **{entry['category']}**

> {entry['story']}

---
""")
    else:
        st.info("No community stories yet. Be the first to contribute!")
    st.caption("VitalView connects insight to action — share these with clients, students, or partners.")
    if pr.empty:
        st.info("Generate a Priority table first to draft a narrative.")
    else:
        top3 = ", ".join([f"{r.county} ({r.state})" for _, r in pr.head(3).iterrows()])
        region = ", ".join(sorted(dfx['state'].unique().tolist()))
        nar = (
            f"In {latest}, VitalView’s equity-weighted scoring for {region} highlights top-need areas: {top3}. "
            "Key drivers include food access, air quality, insurance coverage, mobility barriers, and lifestyle risks. "
            "These insights support targeted outreach, program design, and funding allocation with measurable outcomes."
        )
        st.text(nar)

        if FEATURES["exports"]:
            st.download_button("⬇️ Download Narrative (TXT)", data=nar.encode("utf-8"),
                               file_name=f"VitalView_Narrative_{latest}.txt", mime="text/plain")
            pdf_bytes = to_pdf_bytes(nar, title="VitalView Narrative")
            if pdf_bytes:
                st.download_button("⬇️ Download Narrative (PDF)", data=pdf_bytes,
                                   file_name=f"VitalView_Narrative_{latest}.pdf", mime="application/pdf")
            else:
                st.info("Install ReportLab for PDF export:  \n`pip install reportlab`")
        else:
            st.info("Exports are a Pro feature. Upgrade in the sidebar.")
# --- Save narrative to library ---
col_s1, col_s2 = st.columns([1,1])
with col_s1:
    if st.button("💾 Save to Library", key="save_narrative"):
        try:
            _save_narrative(nar, state_sel if 'state_sel' in locals() else [], county_sel if 'county_sel' in locals() else [])
            st.success("Saved! See it in 'Saved Narratives' below.")
        except Exception as e:
            st.error(f"Could not save: {e}")
with col_s2:
    if FEATURES.get("exports", False):
        st.download_button(
            "⬇️ Download Narrative (TXT)",
            data=nar.encode("utf-8"),
            file_name="VitalView_Narrative.txt",
            mime="text/plain",
            key="download_narrative_reports"
        )

st.markdown("---")
st.subheader("🗂️ Saved Narratives")
if "narratives" in st.session_state and st.session_state.narratives:
    # newest first
    for i, entry in enumerate(reversed(st.session_state.narratives)):
        idx = len(st.session_state.narratives) - 1 - i
        st.markdown(f"**{entry['ts']}** — {', '.join(entry['counties']) or '(all counties)'}; {', '.join(entry['states']) or '(all states)'}")
        st.text(entry["text"])

        cc1, cc2, cc3 = st.columns([1,1,2])
        with cc1:
            st.download_button(
                "⬇️ Download TXT",
                data=entry["text"].encode("utf-8"),
                file_name=f"VitalView_Narrative_{entry['ts'].replace(':','-')}.txt",
                mime="text/plain",
                key=f"dl_saved_{idx}"
            )
        with cc2:
            if st.button("🗑️ Delete", key=f"del_saved_{idx}"):
                try:
                    del st.session_state.narratives[idx]
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Delete failed: {e}")
        st.markdown("---")
else:
    st.info("No saved narratives yet. Generate one above and click **Save to Library**.")
# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:gray;font-size:0.9em;'>
© 2025 <b>VitalView</b> — A Community Health Platform by <b>Christopher Chaney</b><br>
<i>Empowering data-driven wellness and equity-based action.</i>
</div>
""", unsafe_allow_html=True)
