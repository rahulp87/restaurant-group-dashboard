import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Meridian Restaurant Group Dashboard", page_icon="🍽️", layout="wide")

# ---------------------------------------------------------------------------
# Design system — matches the "Rowley's Pass" artifact (warm neutrals,
# Fraunces/Public Sans pairing, violet accent, blue=lunch / orange=dinner).
# ---------------------------------------------------------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&family=Public+Sans:wght@400;500;600;700&display=swap');

:root{
  --page:#f7f3ea; --surface:#fffdf8; --surface-2:#f1ebdd;
  --text-1:#211d15; --text-2:#5c5646; --text-muted:#8f8879;
  --border:rgba(33,29,21,0.12); --gridline:#e6e0d0;
  --accent:#4a3aa7; --accent-soft:rgba(74,58,167,0.10);
  --good:#0ca30c; --good-ink:#006300;
  --serious:#eb6834; --serious-ink:#a83f13;
  --shadow-card:0 1px 2px rgba(33,29,21,0.05), 0 8px 24px -16px rgba(33,29,21,0.18);
}

html, body, [class*="css"]{ font-family:"Public Sans", system-ui, sans-serif; }
.stApp{ background:var(--page); }
h1, h2, h3{ font-family:"Fraunces", Georgia, serif !important; letter-spacing:-0.01em; color:var(--text-1); }

[data-testid="stSidebar"]{ background:var(--surface-2); border-right:1px solid var(--border); }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3{ font-family:"Public Sans",sans-serif !important; }

[data-testid="stTabs"] button[role="tab"]{ font-weight:600; color:var(--text-2); font-size:14px; }
[data-testid="stTabs"] button[aria-selected="true"]{ color:var(--accent); }
[data-baseweb="tab-highlight"]{ background-color:var(--accent) !important; }

[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--surface); border:1px solid var(--border) !important; border-radius:16px !important;
  box-shadow:var(--shadow-card);
}

span[data-baseweb="tag"]{ background-color:var(--accent) !important; border-radius:999px !important; }
span[data-baseweb="tag"] span{ color:#fff !important; }

.stButton button, .stDownloadButton button{
  background:var(--accent); color:#fff; border:none; border-radius:8px; font-weight:600;
}
.stButton button:hover, .stDownloadButton button:hover{ filter:brightness(1.1); color:#fff; }

[data-testid="stDataFrame"]{ border:1px solid var(--border); border-radius:12px; overflow:hidden; }
hr{ border-color:var(--border) !important; }
[data-testid="stCaptionContainer"], .stCaption{ color:var(--text-muted) !important; }

.kpi-card{
  background:var(--surface); border:1px solid var(--border); border-radius:14px;
  padding:16px 18px 14px; box-shadow:var(--shadow-card); display:flex; flex-direction:column; gap:4px;
}
.kpi-label{ font-size:12px; color:var(--text-2); font-weight:600; }
.kpi-value-row{ display:flex; align-items:baseline; justify-content:space-between; gap:8px; }
.kpi-value{ font-size:23px; font-weight:600; color:var(--text-1); font-variant-numeric:tabular-nums; white-space:nowrap; }
.kpi-delta{ font-size:12px; font-weight:700; white-space:nowrap; }
.kpi-foot{ font-size:11.5px; color:var(--text-muted); margin-top:2px; }

.narrative{
  display:flex; gap:16px; padding:20px 22px; border-radius:16px; background:var(--surface);
  border:1px solid var(--border); border-left:4px solid var(--accent); box-shadow:var(--shadow-card); margin:6px 0 18px;
}
.narrative-icon{
  flex:none; width:36px; height:36px; border-radius:10px; background:var(--accent-soft); color:var(--accent);
  display:flex; align-items:center; justify-content:center; font-size:17px;
}
.narrative-eyebrow{ font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; color:var(--text-muted); margin-bottom:8px; }
.narrative-lead{ font-family:"Fraunces",serif; font-style:italic; font-weight:500; font-size:16.5px; line-height:1.55; color:var(--text-1); margin-bottom:12px; }
.narrative-lead b{ font-style:normal; font-weight:600; }
.chip-row{ display:flex; flex-wrap:wrap; gap:8px; }
.chip{ display:inline-flex; align-items:center; gap:7px; background:var(--surface-2); border:1px solid var(--border); border-radius:999px; padding:6px 12px; font-size:12.5px; color:var(--text-2); }
.chip b{ color:var(--text-1); }
.chip .dot{ width:8px; height:8px; border-radius:50%; flex:none; }

.section-title{ font-family:"Fraunces",serif; font-weight:600; font-size:15.5px; color:var(--text-1); margin:4px 0 10px; }
</style>
""", unsafe_allow_html=True)

C_LUNCH, C_DINNER, C_ACCENT = "#2a78d6", "#eb6834", "#4a3aa7"
C_GOOD, C_SERIOUS = "#0ca30c", "#eb6834"


def style_fig(fig, height=None):
    updates = dict(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Public Sans, sans-serif", color="#5c5646", size=12),
        legend=dict(font=dict(color="#5c5646")),
        margin=dict(t=50, b=10, l=10, r=10),
    )
    if fig.layout.title is not None and fig.layout.title.text:
        updates["title_font"] = dict(family="Fraunces, Georgia, serif", color="#211d15", size=15)
    fig.update_layout(**updates)
    fig.update_xaxes(gridcolor="#e6e0d0", zerolinecolor="#c6bfab", tickfont=dict(color="#8f8879"))
    fig.update_yaxes(gridcolor="#e6e0d0", zerolinecolor="#c6bfab", tickfont=dict(color="#8f8879"))
    if height:
        fig.update_layout(height=height)
    return fig


def spark_svg(values, up):
    values = list(values)
    if len(values) < 2 or max(values) == min(values):
        pts = "0,15 220,15"
    else:
        vmax, vmin = max(values), min(values)
        rng = vmax - vmin
        step_x = 220 / (len(values) - 1)
        pts = " ".join(f"{i * step_x:.1f},{30 - ((v - vmin) / rng) * 30:.1f}" for i, v in enumerate(values))
    last_x, last_y = pts.split()[-1].split(",")
    dot = C_GOOD if up else C_SERIOUS
    return (
        f'<svg viewBox="0 0 220 30" width="100%" height="30" preserveAspectRatio="none" '
        f'style="display:block;margin-top:6px;">'
        f'<polyline points="{pts}" fill="none" stroke="#8f8879" stroke-width="1.6" '
        f'stroke-linecap="round" stroke-linejoin="round" opacity="0.55"/>'
        f'<circle cx="{last_x}" cy="{last_y}" r="3" fill="{dot}"/></svg>'
    )


def kpi_card(label, value, delta_pct, spark_values, foot, suffix="%"):
    if delta_pct is None:
        delta_html = ""
        up = True
    else:
        up = delta_pct >= 0
        color = "#006300" if up else "#a83f13"
        arrow = "▲" if up else "▼"
        delta_html = f'<span class="kpi-delta" style="color:{color}">{arrow} {abs(delta_pct):.1f}{suffix}</span>'
    return (
        f'<div class="kpi-card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value-row"><span class="kpi-value">{value}</span>{delta_html}</div>'
        f'{spark_svg(spark_values, up)}'
        f'<div class="kpi-foot">{foot}</div></div>'
    )


def chip(dot_color, html):
    return f'<span class="chip"><span class="dot" style="background:{dot_color}"></span>{html}</span>'


# ---------------------------------------------------------------------------
# Mock data model
# ---------------------------------------------------------------------------

LOCATION_SCALE = {
    "The Silver Spoon": 1.15,
    "Bistro V": 0.85,
    "Golden Oak Grill": 1.30,
    "Copper Kettle Kitchen": 0.70,
    "The Blue Fig Café": 1.00,
}
LOCATIONS = list(LOCATION_SCALE.keys())

# dow: Mon=0 .. Sun=6
DOW_MULT = [0.85, 0.80, 0.88, 1.05, 1.30, 1.40, 1.10]
DOW_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

FOOD_ITEMS = [
    # name, category, cls, price, lunch_w, dinner_w
    ("Chef's Ribeye", "Main Courses", "Mains", 34.0, 0.16, 0.22),
    ("Prime Cut Steak", "Main Courses", "Mains", 42.0, 0.10, 0.18),
    ("Garden Herb Chicken", "Main Courses", "Mains", 22.0, 0.18, 0.14),
    ("Wagyu-Style Burger", "Main Courses", "Mains", 19.0, 0.20, 0.12),
    ("Roasted Salmon", "Main Courses", "Mains", 26.0, 0.09, 0.13),
    ("Loaded Fries, Bowl", "Side Orders", "Sides", 9.0, 0.07, 0.06),
    ("Truffle Fries, Bowl", "Side Orders", "Sides", 10.0, 0.06, 0.06),
    ("Caesar Salad", "Side Orders", "Sides", 12.0, 0.06, 0.04),
    ("Artisan Bread Basket", "Side Orders", "Sides", 6.0, 0.03, 0.03),
    ("Molten Chocolate Cake", "Desserts", "Desserts", 11.0, 0.03, 0.05),
    ("New York Cheesecake", "Desserts", "Desserts", 10.0, 0.02, 0.03),
]

BEV_ITEMS = [
    # name, category, cls, is_alcoholic, price, lunch_w, dinner_w
    ("Cola Classic", "Bar Items", "Soft Drinks", False, 4.0, 0.20, 0.14),
    ("Diet Cola", "Bar Items", "Soft Drinks", False, 4.0, 0.16, 0.11),
    ("Lemon Soda", "Bar Items", "Soft Drinks", False, 4.0, 0.08, 0.06),
    ("Ginger Fizz", "Bar Items", "Soft Drinks", False, 4.0, 0.06, 0.06),
    ("Still Water", "Water", "Water", False, 3.5, 0.10, 0.08),
    ("Sparkling Water", "Water", "Water", False, 4.5, 0.04, 0.03),
    ("Fresh Lemonade", "Bar Items", "Soft Drinks", False, 5.0, 0.06, 0.03),
    ("Virgin Berry Mojito", "Bar Items", "Mocktails", False, 8.0, 0.04, 0.04),
    ("House Cappuccino", "Hot Drinks", "Hot Beverages", False, 5.0, 0.03, 0.02),
    ("Craft Lager", "Bar Items", "Beer", True, 7.5, 0.07, 0.05),
    ("Signature Espresso Martini", "Bar Items", "Cocktails", True, 14.0, 0.02, 0.10),
    ("Botanical Gin & Tonic", "Bar Items", "Spirits", True, 13.0, 0.01, 0.08),
    ("House Red (bottle)", "Wines", "Red Wine", True, 38.0, 0.01, 0.07),
    ("Premium Tequila (single)", "Bar Items", "Spirits", True, 12.0, 0.01, 0.06),
    ("Classic Negroni", "Bar Items", "Cocktails", True, 12.0, 0.01, 0.06),
    ("House White (glass)", "Wines", "White Wine", True, 10.0, 0.02, 0.03),
    ("Sommelier's Red (glass)", "Wines", "Red Wine", True, 11.0, 0.01, 0.02),
]

_SUM_FOOD_L = sum(i[4] for i in FOOD_ITEMS)
_SUM_FOOD_D = sum(i[5] for i in FOOD_ITEMS)
_SUM_BEV_L = sum(i[5] for i in BEV_ITEMS)
_SUM_BEV_D = sum(i[6] for i in BEV_ITEMS)


@st.cache_data(show_spinner=False)
def generate_data(n_days: int = 120, seed: int = 42):
    rng = np.random.default_rng(seed)
    end = date.today()
    dates = [end - timedelta(days=i) for i in range(n_days - 1, -1, -1)]

    daily_rows = []
    item_rows = []

    for loc, scale in LOCATION_SCALE.items():
        for d in dates:
            dow = d.weekday()
            mult = DOW_MULT[dow] * scale

            lunch_total = max(200.0, 2100 * mult * rng.uniform(0.90, 1.10))
            dinner_total = max(200.0, 3600 * mult * rng.uniform(0.90, 1.10))

            food_share_l = rng.uniform(0.82, 0.88)
            food_share_d = rng.uniform(0.82, 0.88)
            lunch_food = lunch_total * food_share_l
            lunch_bev = lunch_total - lunch_food
            dinner_food = dinner_total * food_share_d
            dinner_bev = dinner_total - dinner_food

            lunch_avg_spend = rng.uniform(24, 30)
            dinner_avg_spend = rng.uniform(34, 42)
            lunch_covers = max(1, round(lunch_total / lunch_avg_spend))
            dinner_covers = max(1, round(dinner_total / dinner_avg_spend))
            total_covers = lunch_covers + dinner_covers
            net_sales = lunch_total + dinner_total

            daily_rows.append({
                "date": d, "location": loc, "dow": dow,
                "lunch_net": lunch_total, "dinner_net": dinner_total, "net_sales": net_sales,
                "lunch_covers": lunch_covers, "dinner_covers": dinner_covers, "total_covers": total_covers,
                "avg_spend_cover": net_sales / total_covers,
                "dinner_share": dinner_total / net_sales * 100,
            })

            for name, cat, cls, price, lw, dw in FOOD_ITEMS:
                ln = lunch_food * (lw / _SUM_FOOD_L) * rng.uniform(0.75, 1.25)
                dn = dinner_food * (dw / _SUM_FOOD_D) * rng.uniform(0.75, 1.25)
                item_rows.append({
                    "date": d, "location": loc, "item": name, "category": cat, "cls": cls,
                    "kind": "Food", "alc": False, "meal": "Lunch", "net_sales": ln, "qty": max(0, round(ln / price)),
                })
                item_rows.append({
                    "date": d, "location": loc, "item": name, "category": cat, "cls": cls,
                    "kind": "Food", "alc": False, "meal": "Dinner", "net_sales": dn, "qty": max(0, round(dn / price)),
                })

            for name, cat, cls, alc, price, lw, dw in BEV_ITEMS:
                ln = lunch_bev * (lw / _SUM_BEV_L) * rng.uniform(0.70, 1.30)
                dn = dinner_bev * (dw / _SUM_BEV_D) * rng.uniform(0.70, 1.30)
                item_rows.append({
                    "date": d, "location": loc, "item": name, "category": cat, "cls": cls,
                    "kind": "Beverage", "alc": alc, "meal": "Lunch", "net_sales": ln, "qty": max(0, round(ln / price)),
                })
                item_rows.append({
                    "date": d, "location": loc, "item": name, "category": cat, "cls": cls,
                    "kind": "Beverage", "alc": alc, "meal": "Dinner", "net_sales": dn, "qty": max(0, round(dn / price)),
                })

    daily_df = pd.DataFrame(daily_rows)
    items_df = pd.DataFrame(item_rows)
    daily_df["date"] = pd.to_datetime(daily_df["date"])
    items_df["date"] = pd.to_datetime(items_df["date"])
    return daily_df, items_df


daily_df, items_df = generate_data()

# ---------------------------------------------------------------------------
# Sidebar filters
# ---------------------------------------------------------------------------

st.sidebar.header("Filters")

min_date, max_date = daily_df["date"].min().date(), daily_df["date"].max().date()
date_range = st.sidebar.date_input(
    "Date range", value=(max_date - timedelta(days=29), max_date),
    min_value=min_date, max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

selected_locations = st.sidebar.multiselect("Locations", options=LOCATIONS, default=LOCATIONS)

st.sidebar.subheader("KPI targets")
target_dinner_share = st.sidebar.slider("Dinner share target (%)", 0, 100, 62)
target_spend_cover = st.sidebar.number_input("Avg spend / cover target ($)", value=32.0, step=1.0)
target_daily_net_sales = st.sidebar.number_input("Daily net sales target ($)", value=4800.0, step=100.0)

if not selected_locations:
    st.warning("Select at least one location in the sidebar to see the dashboard.")
    st.stop()

mask = (
    (daily_df["location"].isin(selected_locations))
    & (daily_df["date"].dt.date >= start_date)
    & (daily_df["date"].dt.date <= end_date)
)
daily = daily_df.loc[mask].copy()

item_mask = (
    (items_df["location"].isin(selected_locations))
    & (items_df["date"].dt.date >= start_date)
    & (items_df["date"].dt.date <= end_date)
)
items = items_df.loc[item_mask].copy()

period_days = (end_date - start_date).days + 1
prev_end = start_date - timedelta(days=1)
prev_start = prev_end - timedelta(days=period_days - 1)
prev_mask = (
    (daily_df["location"].isin(selected_locations))
    & (daily_df["date"].dt.date >= prev_start)
    & (daily_df["date"].dt.date <= prev_end)
)
prev_daily = daily_df.loc[prev_mask].copy()

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Meridian Restaurant Group")
st.caption(
    f"Executive dashboard · {len(selected_locations)} location(s) · "
    f"{start_date:%d %b %Y} – {end_date:%d %b %Y} · demo data, not a real business"
)

if daily.empty:
    st.info("No data for the selected filters.")
    st.stop()


def _delta_pct(cur, prev):
    if prev in (0, None) or pd.isna(prev):
        return None
    return (cur - prev) / prev * 100


total_net_sales = daily["net_sales"].sum()
total_covers = daily["total_covers"].sum()
avg_spend_cover = total_net_sales / total_covers if total_covers else 0
dinner_share = daily["dinner_net"].sum() / total_net_sales * 100 if total_net_sales else 0

prev_net_sales = prev_daily["net_sales"].sum()
prev_covers = prev_daily["total_covers"].sum()
prev_spend_cover = (prev_net_sales / prev_covers) if prev_covers else None
prev_dinner_share = (prev_daily["dinner_net"].sum() / prev_net_sales * 100) if prev_net_sales else None

d1 = _delta_pct(total_net_sales, prev_net_sales)
d2 = _delta_pct(total_covers, prev_covers)
d3 = _delta_pct(avg_spend_cover, prev_spend_cover)
d4 = _delta_pct(dinner_share, prev_dinner_share)

# 14-day series (independent of date-range filter) for KPI sparklines
last14_dates = sorted(daily_df["date"].unique())[-14:]
last14 = daily_df[(daily_df["location"].isin(selected_locations)) & (daily_df["date"].isin(last14_dates))]
spark = last14.groupby("date").agg(
    net_sales=("net_sales", "sum"), total_covers=("total_covers", "sum"), dinner_net=("dinner_net", "sum"),
).reset_index()
spark["avg_spend_cover"] = spark["net_sales"] / spark["total_covers"]
spark["dinner_share"] = spark["dinner_net"] / spark["net_sales"] * 100

# ---------------------------------------------------------------------------
# KPI row
# ---------------------------------------------------------------------------

k1, k2, k3, k4 = st.columns(4)
k1.markdown(kpi_card("Net sales", f"${total_net_sales:,.0f}", d1, spark["net_sales"], "vs prior period"), unsafe_allow_html=True)
k2.markdown(kpi_card("Total covers", f"{total_covers:,.0f}", d2, spark["total_covers"], "guests served"), unsafe_allow_html=True)
k3.markdown(kpi_card("Avg spend / cover", f"${avg_spend_cover:,.2f}", d3, spark["avg_spend_cover"], "net sales per guest"), unsafe_allow_html=True)
k4.markdown(kpi_card("Dinner share", f"{dinner_share:.1f}%", d4, spark["dinner_share"], "of net sales", suffix=" pts"), unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Narrative — auto-generated commentary, recomputed on every filter change
# ---------------------------------------------------------------------------

by_date_all = daily.groupby("date", as_index=False)[["lunch_net", "dinner_net", "net_sales"]].sum()
daily_avg = by_date_all["net_sales"].mean()
best_row = by_date_all.loc[by_date_all["net_sales"].idxmax()]
best_pct = (best_row["net_sales"] - daily_avg) / daily_avg * 100 if daily_avg else 0

food_top = (
    items[items["kind"] == "Food"].groupby("item", as_index=False)[["net_sales", "qty"]].sum()
    .sort_values("net_sales", ascending=False)
)
top_item = food_top.iloc[0] if not food_top.empty else None

gap_spend = avg_spend_cover - target_spend_cover

if d1 is None:
    lead = f"Over the selected period, net sales reached <b>${total_net_sales:,.0f}</b>."
    up_overall = True
else:
    up_overall = d1 >= 0
    if up_overall:
        qualitative = "the strongest stretch in this window" if d1 > 8 else "a steady step forward"
    else:
        qualitative = "a slightly quieter patch" if d1 > -8 else "worth a closer look before next week's roster"
    lead = (
        f"Over the selected period, net sales reached <b>${total_net_sales:,.0f}</b>, "
        f"<b>{'up' if up_overall else 'down'} {abs(d1):.1f}%</b> vs the prior period &mdash; {qualitative}."
    )

chips = []
if d1 is not None:
    chips.append(chip(C_GOOD if up_overall else C_SERIOUS,
                       f"{'Trending up' if up_overall else 'Trending down'} <b>{abs(d1):.1f}%</b> vs prior period"))
chips.append(chip(C_ACCENT,
                   f"{best_row['date']:%a %d %b} was the standout &mdash; <b>${best_row['net_sales']:,.0f}</b> "
                   f"({best_pct:+.0f}% vs daily avg)"))
chips.append(chip(C_ACCENT,
                   f"Dinner carries <b>{dinner_share:.0f}%</b> of sales, lunch the remaining {100 - dinner_share:.0f}%"))
if top_item is not None:
    chips.append(chip(C_ACCENT,
                       f"<b>{top_item['item']}</b> led the kitchen &mdash; {top_item['qty']:.0f} sold, ${top_item['net_sales']:,.0f}"))
chips.append(chip(C_GOOD if gap_spend >= 0 else C_SERIOUS,
                   f"Avg spend/cover is {'above' if gap_spend >= 0 else 'below'} target by <b>${abs(gap_spend):,.2f}</b>"))

st.markdown(
    f'''<div class="narrative">
      <div class="narrative-icon">📋</div>
      <div>
        <div class="narrative-eyebrow">Shift notes · auto-generated, refreshes with your filters</div>
        <div class="narrative-lead">{lead}</div>
        <div class="chip-row">{"".join(chips)}</div>
      </div>
    </div>''',
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_trends, tab_mix, tab_items, tab_data = st.tabs(
    ["Trends", "Revenue mix", "Top items", "Raw data"]
)

with tab_trends:
    with st.container(border=True):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=by_date_all["date"], y=by_date_all["lunch_net"], name="Lunch",
                                  mode="lines", line=dict(color=C_LUNCH, width=2),
                                  fill="tozeroy", fillcolor="rgba(42,120,214,0.10)"))
        fig.add_trace(go.Scatter(x=by_date_all["date"], y=by_date_all["dinner_net"], name="Dinner",
                                  mode="lines", line=dict(color=C_DINNER, width=2),
                                  fill="tozeroy", fillcolor="rgba(235,104,52,0.10)"))
        fig.update_layout(title="Net sales over time (lunch vs dinner)",
                           legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(style_fig(fig, height=380), width="stretch")

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            dow_avg = (
                daily.groupby("dow", as_index=False)["net_sales"].mean()
                .assign(day=lambda d: d["dow"].map(lambda i: DOW_NAMES[i]))
                .sort_values("dow")
            )
            fig_dow = px.bar(dow_avg, x="day", y="net_sales", title="Average net sales by weekday")
            fig_dow.update_traces(marker_color=C_ACCENT)
            fig_dow.update_layout(xaxis_title=None, yaxis_title="Avg net sales")
            st.plotly_chart(style_fig(fig_dow, height=340), width="stretch")

    with col_b:
        with st.container(border=True):
            share_by_date = daily.groupby("date", as_index=False).apply(
                lambda g: pd.Series({"dinner_share": g["dinner_net"].sum() / g["net_sales"].sum() * 100}),
                include_groups=False,
            )
            fig_share = go.Figure()
            fig_share.add_trace(go.Scatter(x=share_by_date["date"], y=share_by_date["dinner_share"],
                                            mode="lines", line=dict(color=C_DINNER, width=2), name="Dinner share"))
            fig_share.add_hline(y=target_dinner_share, line_dash="dash", line_color="#8f8879",
                                 annotation_text="Target", annotation_position="top left")
            fig_share.update_layout(title="Dinner share of net sales, over time", yaxis_title="Dinner share (%)")
            st.plotly_chart(style_fig(fig_share, height=340), width="stretch")

    if len(selected_locations) > 1:
        with st.container(border=True):
            by_loc_date = daily.groupby(["date", "location"], as_index=False)["net_sales"].sum()
            fig_loc = px.line(by_loc_date, x="date", y="net_sales", color="location",
                               title="Net sales by location")
            fig_loc.update_layout(legend_title=None)
            st.plotly_chart(style_fig(fig_loc, height=380), width="stretch")

with tab_mix:
    col_a, col_b = st.columns(2)

    with col_a:
        with st.container(border=True):
            def revenue_centre(row):
                if row["kind"] == "Food":
                    return "Food"
                return "Alcoholic beverage" if row["alc"] else "Non-alcoholic beverage"

            rc = items.assign(centre=items.apply(revenue_centre, axis=1)).groupby("centre", as_index=False)["net_sales"].sum()
            rc = rc.sort_values("net_sales", ascending=True)
            fig_rc = px.bar(rc, x="net_sales", y="centre", orientation="h", title="Net sales by revenue centre")
            fig_rc.update_traces(marker_color=C_ACCENT)
            fig_rc.update_layout(yaxis_title=None, xaxis_title="Net sales")
            st.plotly_chart(style_fig(fig_rc, height=360), width="stretch")

    with col_b:
        with st.container(border=True):
            cat = items.groupby(["category", "cls"], as_index=False)["net_sales"].sum()
            cat["label"] = cat["category"] + " / " + cat["cls"]
            cat = cat.sort_values("net_sales", ascending=False).head(8).sort_values("net_sales")
            fig_cat = px.bar(cat, x="net_sales", y="label", orientation="h", title="Top menu categories")
            fig_cat.update_traces(marker_color=C_LUNCH)
            fig_cat.update_layout(yaxis_title=None, xaxis_title="Net sales")
            st.plotly_chart(style_fig(fig_cat, height=360), width="stretch")

    with st.expander("Show full menu category breakdown"):
        full_cat = items.groupby(["category", "cls"], as_index=False)["net_sales"].sum().sort_values("net_sales", ascending=False)
        full_cat["share %"] = (full_cat["net_sales"] / full_cat["net_sales"].sum() * 100).round(1)
        st.dataframe(full_cat.rename(columns={"category": "Category", "cls": "Class", "net_sales": "Net sales"}),
                     width="stretch", hide_index=True)

with tab_items:
    def top_items_panel(col, meal, kind, color):
        sub = items[(items["meal"] == meal) & (items["kind"] == kind)]
        agg = sub.groupby("item", as_index=False)[["net_sales", "qty"]].sum().sort_values("net_sales", ascending=False)
        with col:
            with st.container(border=True):
                st.markdown(f'<div class="section-title">{meal} · {kind.lower()}</div>', unsafe_allow_html=True)
                top = agg.head(6).sort_values("net_sales")
                fig = px.bar(top, x="net_sales", y="item", orientation="h")
                fig.update_traces(marker_color=color)
                fig.update_layout(yaxis_title=None, xaxis_title="Net sales")
                st.plotly_chart(style_fig(fig, height=260), width="stretch")

    r1c1, r1c2 = st.columns(2)
    top_items_panel(r1c1, "Lunch", "Food", C_LUNCH)
    top_items_panel(r1c2, "Dinner", "Food", C_DINNER)
    r2c1, r2c2 = st.columns(2)
    top_items_panel(r2c1, "Lunch", "Beverage", C_LUNCH)
    top_items_panel(r2c2, "Dinner", "Beverage", C_DINNER)

with tab_data:
    st.subheader("Daily sales")
    daily_display = daily.sort_values("date", ascending=False).copy()
    daily_display["day"] = daily_display["dow"].map(lambda i: DOW_NAMES[i])
    daily_display = daily_display[[
        "date", "location", "day", "lunch_net", "dinner_net", "net_sales",
        "lunch_covers", "dinner_covers", "total_covers", "avg_spend_cover", "dinner_share",
    ]].round(2)
    st.dataframe(daily_display, width="stretch", hide_index=True)
    st.download_button(
        "Download daily sales (CSV)",
        daily_display.to_csv(index=False).encode("utf-8"),
        file_name="daily_sales.csv", mime="text/csv",
    )

    st.subheader("Item-level sales")
    items_display = items.groupby(["item", "category", "cls", "kind", "meal"], as_index=False)[["net_sales", "qty"]].sum()
    items_display = items_display.sort_values("net_sales", ascending=False).round(2)
    st.dataframe(items_display, width="stretch", hide_index=True)
    st.download_button(
        "Download item sales (CSV)",
        items_display.to_csv(index=False).encode("utf-8"),
        file_name="item_sales.csv", mime="text/csv",
    )

st.divider()
st.caption("Meridian Restaurant Group is a fictional company. All names, locations and figures on this page are synthetic demo data.")
