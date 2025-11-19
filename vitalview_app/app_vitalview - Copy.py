# app_vitalview.py  — VitalView (clean reset)
# One-file demo-ready app: header, demo mode, upload, filters, tabs (Overview/Trends/Priority/Reports), footer

import streamlit as st
import pandas as pd

# ----------------------------
# Page & simple theme header
# ----------------------------
st.set_page_config(page_title="VitalView by Christopher Chaney", layout="wide")

# (optional) small CSS polish
st.markdown(
    """
    <style>
      .stTabs [data-baseweb="tab"] { font-weight: 600; }
      .stMetric { background: #F6FAFF; border-radius: 10px; padding: 6px 10px; }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <div style='background-color:#0A74DA;padding:15px;border-radius:12px;'>
        <h1 style='text-align:center;color:white;margin:0;'>VitalView</h1>
        <p style='text-align:center;color:white;margin:0;font-size:1.05em;'>
            by Christopher Chaney — Empowering communities through data-driven health insights
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# Plans (Free / Pro / Enterprise)
# ----------------------------
PLAN_FEATURES = {
    "free":       {"exports": False},
    "pro":        {"exports": True},
    "enterprise": {"exports": True},
}
if "plan" not in st.session_state:
    st.session_state.plan = "free"

def set_plan(name: str):
    st.session_state.plan = name.lower()

def current_features():
    return PLAN_FEATURES.get(st.session_state.plan, PLAN_FEATURES["free"])
with st.sidebar.expander("📖 Data Dictionary", expanded=False):
    st.markdown("""
- **Obesity (%)** — Estimated adult obesity prevalence.
- **Food Desert (%)** — % of residents with limited access to affordable/healthy foods.
- **PM2.5 (µg/m³)** — Fine particulate air pollution concentration.
- **Uninsured (%)** — % of residents without health insurance.
- **No Car Households (%)** — % of households without a personal vehicle.

_Note:_ Higher values often signal greater need or barriers, but always interpret within local context.
    """)

# ----------------------------
# Sidebar: About + Plan + Demo Mode
# ----------------------------
with st.sidebar.expander("ℹ️ About VitalView", expanded=True):
    st.write("""**VitalView** helps community leaders, educators, and organizations
visualize local health data, identify disparities, and generate
grant-ready narratives for real-world action.""")

with st.sidebar.expander("💳 Plan"):
    plan_choice = st.radio("Choose plan", ["free", "pro", "enterprise"],
                           index=["free","pro","enterprise"].index(st.session_state.plan))
    if plan_choice != st.session_state.plan:
        set_plan(plan_choice)
        st.success(f"Plan set to: {st.session_state.plan.title()}")
FEATURES = current_features()
st.markdown(
    f"<div style='text-align:center;color:#555;font-size:0.95em;'>"
    f"Active Plan: <b>{st.session_state.plan.title()}</b> — Exports: "
    f"<b>{'ON' if FEATURES['exports'] else 'OFF'}</b></div>",
    unsafe_allow_html=True
)

demo_mode = st.sidebar.checkbox("🧪 Demo Mode (use sample data)", value=True, key="demo_mode")
if demo_mode:
    st.sidebar.success("Demo Mode is ON — sample data will be used.")

st.sidebar.markdown("---")
st.sidebar.markdown("**Upgrade options**")
col_u1, col_u2 = st.sidebar.columns(2)
with col_u1:
    if st.button("Upgrade to Pro"):
        st.info("Stripe Checkout (Pro) would open here. (Placeholder)")
with col_u2:
    if st.button("Enterprise demo call"):
        st.info("Schedule link or contact form would open here. (Placeholder)")

# ----------------------------
# Sample data + schema helpers
# ----------------------------
def _make_sample_simple():
    return pd.DataFrame(
        [
            ["Illinois","Cook","17031",2020,"Obesity (%)",31.2,"percent"],
            ["Illinois","Cook","17031",2021,"Obesity (%)",31.7,"percent"],
            ["Illinois","Cook","17031",2022,"Obesity (%)",32.1,"percent"],
            ["Illinois","Cook","17031",2020,"PM2.5 (µg/m³)",9.8,"ugm3"],
            ["Illinois","Lake","17097",2020,"Food Desert (%)",10.2,"percent"],
            ["Illinois","Will","17197",2020,"No Car Households (%)",6.1,"percent"],
            ["Illinois","Will","17197",2021,"No Car Households (%)",6.0,"percent"],
        ],
        columns=["state","county","fips","year","indicator","value","unit"]
    )

def enforce_schema(df: pd.DataFrame) -> pd.DataFrame:
    req = {"state","county","fips","year","indicator","value","unit"}
    df = df.copy()
    df.columns = [c.strip().lower() for c in df.columns]
    missing = req - set(df.columns)
    if missing:
        st.error(f"Missing columns: {missing}")
        st.stop()
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["year","value"])
    for col in ("state","county","indicator","unit"):
        df[col] = df[col].astype(str).str.strip()
        if col in ("state","county"):
            df[col] = df[col].str.title()
    return df

def update_indicators(dataframe: pd.DataFrame) -> list:
    if dataframe is not None and not dataframe.empty and "indicator" in dataframe.columns:
        return sorted(dataframe["indicator"].dropna().unique().tolist())
    return []

# ----------------------------
# Data load (upload OR sample)
# ----------------------------
uploaded = st.sidebar.file_uploader(
    "Upload CSV (state, county, fips, year, indicator, value, unit)",
    type=["csv"], accept_multiple_files=False, key="data_upload_main"
)

use_sample = demo_mode or (uploaded is None)
if use_sample:
    df = enforce_schema(_make_sample_simple())
else:
    df = enforce_schema(pd.read_csv(uploaded))

# ----------------------------
# Sidebar filters (State/County)
# ----------------------------
# ---------- Full U.S. State List ----------
ALL_STATES = [
    "Alabama","Alaska","Arizona","Arkansas","California","Colorado","Connecticut","Delaware",
    "Florida","Georgia","Hawaii","Idaho","Illinois","Indiana","Iowa","Kansas","Kentucky","Louisiana",
    "Maine","Maryland","Massachusetts","Michigan","Minnesota","Mississippi","Missouri","Montana",
    "Nebraska","Nevada","New Hampshire","New Jersey","New Mexico","New York","North Carolina",
    "North Dakota","Ohio","Oklahoma","Oregon","Pennsylvania","Rhode Island","South Carolina",
    "South Dakota","Tennessee","Texas","Utah","Vermont","Virginia","Washington","West Virginia",
    "Wisconsin","Wyoming"
]

# ---------- Filters ----------
left, right = st.columns([1,3])

with left:
    st.subheader("Filters")
    state_sel = st.multiselect("Select State(s)", ALL_STATES, default=["Illinois"])
    dfx = df[df["state"].isin(state_sel)] if state_sel else df.copy()

    counties = sorted(dfx["county"].unique()) if "county" in dfx.columns else []
    county_sel = st.multiselect("Select County", counties)
    if county_sel:
        dfx = dfx[dfx["county"].isin(county_sel)]

dfx = df[df["state"].isin(state_sel)] if state_sel else df.copy()
counties = sorted(dfx["county"].unique().tolist())
county_sel = st.sidebar.multiselect("Select County(ies)", counties)

if county_sel:
    dfx = dfx[dfx["county"].isin(county_sel)]

# Safe year handling
y_min, y_max = (int(dfx["year"].min()), int(dfx["year"].max())) if not dfx.empty else (0, 0)
if y_min and y_max and y_min != y_max:
    yr_from, yr_to = st.sidebar.slider("Year range", y_min, y_max, (y_min, y_max), key="year_range")
    dfx = dfx[(dfx["year"] >= yr_from) & (dfx["year"] <= yr_to)]
elif y_min == y_max and y_min != 0:
    st.sidebar.caption(f"Year: **{y_min}** (only one year available)")

INDICATORS = update_indicators(dfx)

# ----------------------------
# Tabs
# ----------------------------
tab_overview, tab_trends, tab_priority, tab_reports, tab_resources = st.tabs(
    ["🏠 Overview", "📈 Trends", "🎯 Priority", "📝 Reports", "🌍 Resources"]
)

# ----------------------------
# Overview
# ----------------------------
with tab_overview:
    st.subheader("Welcome")
    st.write("Use the filters in the left sidebar to explore. Switch tabs to view trends, compute priorities, and generate a grant-ready narrative.")

    # KPI row
    cA,cB,cC = st.columns(3)
    cA.metric("Rows available", f"{len(dfx):,}")
    if not dfx.empty:
        cB.metric("Year span", f"{int(dfx['year'].min())}–{int(dfx['year'].max())}")
        cC.metric("Counties", f"{dfx['county'].nunique():,}")
    else:
        cB.metric("Year span","—")
        cC.metric("Counties","—")

    st.divider()
    st.subheader("VitalView Focus Pillars")

    # Build a simple pillar score (latest year avg, normalized 0–1)
    import numpy as np
    latest_over = int(dfx["year"].max()) if not dfx.empty else None
    df_latest_over = dfx[dfx["year"]==latest_over] if latest_over else dfx
    pillars = ["Obesity (%)","Food Desert (%)","PM2.5 (µg/m³)","Uninsured (%)","No Car Households (%)"]
    vals=[]
    for p in pillars:
        v = df_latest_over[df_latest_over["indicator"]==p]["value"]
        if v.empty: score = 0.0
        else:
            # normalize by pillar mean (demo-friendly)
            score = float(v.mean())
        vals.append(score)
    # rescale to positive and normalize
    arr = np.array(vals, dtype=float)
    if arr.max() > 0:
        arr = arr / arr.max()
    data = pd.DataFrame({"pillar": pillars, "score": arr})

    # Donut chart with Altair
    import altair as alt
    base = alt.Chart(data).encode(
        theta="score:Q",
        color=alt.Color("pillar:N", legend=None),
        tooltip=["pillar:N","score:Q"]
    )
    donut = base.mark_arc(innerRadius=70, outerRadius=110)
    text = base.mark_text(radius=0, size=14).encode(text=alt.value(""))

    st.altair_chart(donut, use_container_width=True)
    st.caption("Visual emphasis of VitalView’s five pillars (scaled within the selected filters).")
    st.divider()
    st.subheader("County × Indicator Heatmap")

    # latest-year matrix for quick scanning
    if not dfx.empty:
        latest_ov = int(dfx["year"].max())
        df_heat = dfx[dfx["year"] == latest_ov][["county","indicator","value"]].copy()
        if df_heat.empty:
            st.info("No latest-year slice available for the heatmap.")
        else:
            heat_piv = df_heat.pivot_table(index="county", columns="indicator", values="value", aggfunc="mean").reset_index()
            # Show as a colored dataframe (simple, fast)
            st.dataframe(heat_piv, use_container_width=True)
            st.caption(f"Heatmap-style table for {latest_ov}. Higher values indicate greater need for many indicators.")
    else:
        st.info("Upload data or enable Demo Mode to populate the heatmap.")

# ----------------------------
# Trends
# ----------------------------
with tab_trends:
    st.subheader("Trends & Comparisons")
    ind_sel = st.selectbox(
        "Indicator (for charts)",
        INDICATORS if INDICATORS else ["(none)"],
        key="trend_indicator"
    )

    dfi = dfx[dfx["indicator"] == ind_sel] if ind_sel != "(none)" else pd.DataFrame()
    if dfi.empty:
        st.info("No rows for this indicator with current filters.")
    else:
        try:
            st.line_chart(dfi.sort_values("year").set_index("year")["value"])
        except Exception:
            st.line_chart(dfi[["year","value"]].groupby("year").mean())
        st.caption(f"{len(dfi):,} rows after filters")

# ----------------------------
# Priority (equity-weighted)
# ----------------------------
def zscore(s: pd.Series) -> pd.Series:
    s = s.astype(float)
    std = s.std(ddof=0) or 1.0
    return (s - s.mean()) / std

def derive_pivot(df_latest: pd.DataFrame) -> pd.DataFrame:
    return df_latest.pivot_table(index=["state","county","fips"], columns="indicator", values="value", aggfunc="mean")

def compute_priority_df(pivot: pd.DataFrame, weights: dict) -> pd.DataFrame:
    z = pivot.apply(zscore, axis=0)
    score = 0
    used = []
    for label, w in weights.items():
        col = next((c for c in z.columns if c.lower().startswith(label.lower())), None)
        if col is not None:
            score = score + w * z[col]
            used.append(col)
    out = z.copy()
    out["E_Score"] = score
    out["__used__"] = ", ".join(used) if used else "(none)"
    return out.reset_index().sort_values("E_Score", ascending=False)
# --- BHRI: Behavioral Health Risk Index (non-diagnostic) ---
def compute_bhri(pivot: pd.DataFrame) -> pd.DataFrame:
    # map indicator prefixes to columns
    def find(prefix):
        return next((c for c in pivot.columns if c.lower().startswith(prefix.lower())), None)

    cols = {
        "obesity": find("Obesity"),
        "food_desert": find("Food Desert"),
        "pm25": find("PM2.5"),
        "uninsured": find("Uninsured"),
        "no_car": find("No Car"),
    }

    # z-score available columns
    z = pivot.copy()
    for c in [v for v in cols.values() if v]:
        z[c] = zscore(pivot[c].astype(float))

    # weighted sum → 0–100
    w = {
        cols["food_desert"]: 0.30 if cols["food_desert"] else 0.0,
        cols["pm25"]:        0.25 if cols["pm25"] else 0.0,
        cols["uninsured"]:   0.20 if cols["uninsured"] else 0.0,
        cols["no_car"]:      0.15 if cols["no_car"] else 0.0,
        cols["obesity"]:     0.10 if cols["obesity"] else 0.0,
    }
    score = 0
    for c, wt in w.items():
        if c: score = score + wt * z[c]
    smin, smax = float(score.min()), float(score.max())
    bhri = (score - smin) / (smax - smin) * 100 if smax > smin else score*0 + 50

    out = pivot.copy()
    out["BHRI"] = bhri

    # human-readable flags (top quartile by driver)
    def flags_row(r):
        f=[]
        if cols["food_desert"] and r[cols["food_desert"]] >= pivot[cols["food_desert"]].quantile(0.75): f.append("Food access stress")
        if cols["pm25"] and r[cols["pm25"]] >= pivot[cols["pm25"]].quantile(0.75): f.append("Environmental stress (air)")
        if cols["uninsured"] and r[cols["uninsured"]] >= pivot[cols["uninsured"]].quantile(0.75): f.append("Access barrier (uninsured)")
        if cols["no_car"] and r[cols["no_car"]] >= pivot[cols["no_car"]].quantile(0.75): f.append("Mobility barrier (no vehicle)")
        if cols["obesity"] and r[cols["obesity"]] >= pivot[cols["obesity"]].quantile(0.75): f.append("Lifestyle risk proxy")
        return ", ".join(f) if f else "No elevated flags"
    out["BHRI Flags"] = pivot.apply(flags_row, axis=1)
    return out[["BHRI","BHRI Flags"]]

# --- Actions/Recommender (rule-based to start) ---
DEFAULT_RULES = {
    "rules": [
        {"if": {"Food Desert (%)": {">=": 15}}, "then": [
            "Mobile produce markets", "SNAP/WIC retailer enrollment", "Healthy corner store conversions"]},
        {"if": {"PM2.5 (µg/m³)": {">=": 10}}, "then": [
            "Indoor walking programs", "AQI alert education", "Home air-purifier pilot"]},
        {"if": {"Obesity (%)": {">=": 30}}, "then": [
            "Lifestyle coaching (12 weeks)", "Nutrition counseling", "Community walking groups"]},
        {"if": {"Uninsured (%)": {">=": 10}}, "then": [
            "Insurance enrollment navigators", "Bilingual eligibility screening", "CHW referral pathways"]},
        {"if": {"No Car Households (%)": {">=": 12}}, "then": [
            "Transit-accessible siting", "Mobile clinics on bus lines", "Travel voucher partnerships"]},
        {"if": {"Food Desert (%)": {">=": 15}, "Obesity (%)": {">=": 30}}, "then": [
            "Produce prescription + nutrition classes", "Mobile produce bundle", "Grocer discount days"]},
        {"if": {"PM2.5 (µg/m³)": {">=": 10}, "No Car Households (%)": {">=": 12}}, "then": [
            "Indoor rec access passes", "Air-quality safe-space days", "Active transport safety advocacy"]},
    ]
}

def match_rules(values_by_indicator: dict, rules_json: dict) -> list:
    recs=[]
    for rule in rules_json.get("rules", []):
        cond = rule.get("if", {})
        ok=True
        for ind, comp in cond.items():
            v = values_by_indicator.get(ind)
            if v is None:
                ok=False; break
            for op,thr in comp.items():
                if op==">=" and not (v>=thr): ok=False
                if op=="<=" and not (v<=thr): ok=False
                if op==">"  and not (v> thr): ok=False
                if op=="<"  and not (v< thr): ok=False
                if op=="==" and not (v==thr): ok=False
            if not ok: break
        if ok: recs.extend(rule.get("then", []))
    # unique, preserve order
    seen=set(); uniq=[]
    for r in recs:
        if r not in seen: seen.add(r); uniq.append(r)
    return uniq

# ---------- Equity-Weighted Priority Scoring ----------
st.divider()
st.subheader("Equity-Weighted Priority Scoring")

# Dynamically detect indicators
if "indicator" in dfx.columns:
    indicators_found = sorted(dfx["indicator"].dropna().unique().tolist())
else:
    indicators_found = []

# Define default weights for common indicators
default_weights = {
    "Obesity (%)": 1.0,
    "Food Desert (%)": 1.0,
    "PM2.5 (µg/m³)": 1.0,
    "Uninsured (%)": 0.5,
    "No Car Households (%)": 0.5,
    "Low Income (%)": 1.0,
    "Unemployment (%)": 0.8,
    "Rent Burden (%)": 0.7,
    "High School Grad (%)": 0.5,
    "Food Insecurity (%)": 1.2
}

# Create sliders automatically for indicators found
weights = {}
for ind in indicators_found:
    label = ind.split("(")[0].strip()
    w = st.slider(f"{label}", 0.0, 2.0, default_weights.get(ind, 1.0), 0.1)
    weights[ind] = w

latest = int(df["year"].max()) if not df.empty else None
df_latest = df[df["year"] == latest] if latest else df
pivot = derive_pivot(df_latest) if not df_latest.empty else pd.DataFrame()
priority_df = compute_priority_df(pivot, weights) if not pivot.empty else pd.DataFrame()

# ===== Priority Table =====
if not priority_df.empty:
    st.dataframe(priority_df.head(15), use_container_width=True)
    if FEATURES["exports"]:
        st.download_button(
            "⬇️ Download Priority (CSV)",
            data=safe_csv_bytes(priority_df),
            file_name="priority_list.csv",
            mime="text/csv"
        )
else:
    st.info("No priority table available. Adjust filters or weights.")
# ----------------------------
# Actions (rule-based recommender)
# ----------------------------
with tab_actions:
    st.subheader("Intervention Recommender")

    if dfx.empty:
        st.info("No data available. Upload a CSV or enable Demo Mode.")
    else:
        latest_year = int(dfx["year"].max())
        df_latest = dfx[dfx["year"] == latest_year]

        # pick a county to show recommendations
        pool = sorted(df_latest["county"].unique()) if not df_latest.empty else []
        sel_county = st.selectbox("Select county", pool, key="actions_county") if pool else None

        if not sel_county:
            st.info("Choose a county to see tailored recommendations.")
        else:
            vals = df_latest[df_latest["county"] == sel_county].set_index("indicator")["value"].to_dict()
            recs = match_rules(vals, DEFAULT_RULES)
            st.write("Latest values:", vals)
            if recs:
                st.success("Recommended actions: " + "; ".join(recs))
            else:
                st.warning("No matching actions under current thresholds. Try adjusting weights or review other indicators.")
# ----------------------------
# Reports (grant/board narrative)
# ----------------------------
with tab_reports:
    st.subheader("Grant / Board Narrative")
    # Rebuild priority table in this scope if needed
    try:
        latest_year = int(dfx["year"].max())
        df_latest = dfx[dfx["year"] == latest_year]
        pivot = derive_pivot(df_latest) if not df_latest.empty else pd.DataFrame()
        weights = {"Obesity": w_ob, "Food Desert": w_fd, "PM2.5": w_pm, "Uninsured": w_un, "No Car": w_nc}
        priority_df = compute_priority_df(pivot, weights) if not pivot.empty else pd.DataFrame()
    except Exception:
        priority_df = pd.DataFrame()

    if not priority_df.empty:
        top3 = priority_df.head(3)
        region = ", ".join(state_sel) if state_sel else "the selected region"
        bullets = (
            ", ".join([f"{r.county} (score {r.E_Score:.2f})" for _, r in top3.iterrows()])
            if not top3.empty else "priority areas identified"
        )
        nar = (
            f"In {latest_year}, VitalView’s equity-weighted scoring for {region} highlights top-need areas: {bullets}. "
            "Key drivers include food access, air quality, insurance coverage, mobility barriers, and lifestyle risks. "
            "These insights support targeted outreach, program design, and funding allocation with measurable objectives."
        )
        st.text(nar)

        if FEATURES.get("exports", False):
            st.download_button(
                "⬇️ Download Narrative (TXT)",
                data=nar.encode("utf-8"),
                file_name=f"VitalView_Narrative_{latest_year}.txt",
                mime="text/plain",
                key="download_narrative_txt"
            )
        else:
            st.warning("Export is a Pro feature. Upgrade in the sidebar to enable downloads.")
    else:
        st.info("Generate your Priority table (🎯 tab) to create a narrative.")
# ---------- Resources Tab ----------
with tab_resources:
    st.subheader("🌍 Community Health Resources")

    st.markdown("### 🏥 Health Access")
    st.markdown("- [FindHealthCenters.gov](https://findahealthcenter.hrsa.gov) — Free or low-cost community clinics")
    st.markdown("- [211.org](https://211.org) — Local social services (food, housing, health, transportation)")

    st.markdown("### 🌱 Food & Nutrition")
    st.markdown("- [Feeding America Food Bank Locator](https://www.feedingamerica.org/find-your-local-foodbank)")
    st.markdown("- [USDA SNAP Retailer Locator](https://www.fns.usda.gov/snap/retailer-locator)")

    st.markdown("### 💰 Funding & Grants")
    st.markdown("- [HRSA Grants](https://www.hrsa.gov/grants)")
    st.markdown("- [CDC REACH Program](https://www.cdc.gov/reach/)")
    st.markdown("- [NIH Community Health Grants](https://grants.nih.gov/grants/oer.htm)")

    st.markdown("### 📚 Education & Data")
    st.markdown("- [CDC Data Portal](https://data.cdc.gov)")
    st.markdown("- [County Health Rankings](https://www.countyhealthrankings.org)")
    st.markdown("- [US Census Data API](https://www.census.gov/data/developers/data-sets.html)")

    st.caption("VitalView connects users with real resources that improve outcomes — turning insight into action.")
# ----------------------------
# Footer
# ----------------------------
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center; color:gray; font-size:0.9em;'>
        © 2025 <b>VitalView</b> — A Community Health Platform by <b>Christopher Chaney</b><br>
        <i>Empowering data-driven wellness and equity-based action.</i>
    </div>
    """,
    unsafe_allow_html=True
)
