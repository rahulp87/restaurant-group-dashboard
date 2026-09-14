import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import date, timedelta

st.set_page_config(page_title="Meridian Restaurant Group Dashboard", layout="wide")

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
# Header + executive summary
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

c1, c2, c3, c4 = st.columns(4)
d1 = _delta_pct(total_net_sales, prev_net_sales)
c1.metric("Net sales", f"${total_net_sales:,.0f}", None if d1 is None else f"{d1:+.1f}% vs prior period")

d2 = _delta_pct(total_covers, prev_covers)
c2.metric("Total covers", f"{total_covers:,.0f}", None if d2 is None else f"{d2:+.1f}% vs prior period")

d3 = _delta_pct(avg_spend_cover, prev_spend_cover)
c3.metric(
    "Avg spend / cover", f"${avg_spend_cover:,.2f}",
    None if d3 is None else f"{d3:+.1f}% vs prior period",
    delta_color="normal" if avg_spend_cover >= target_spend_cover else "inverse",
)

d4 = _delta_pct(dinner_share, prev_dinner_share)
c4.metric(
    "Dinner share", f"{dinner_share:.1f}%",
    None if d4 is None else f"{d4:+.1f} pts vs prior period",
)

gap_spend = avg_spend_cover - target_spend_cover
gap_daily = (total_net_sales / period_days) - target_daily_net_sales
t1, t2 = st.columns(2)
t1.caption(
    f"Avg spend/cover is {'above' if gap_spend >= 0 else 'below'} target "
    f"by ${abs(gap_spend):,.2f} (target ${target_spend_cover:,.2f})."
)
t2.caption(
    f"Avg daily net sales is {'above' if gap_daily >= 0 else 'below'} target "
    f"by ${abs(gap_daily):,.0f} (target ${target_daily_net_sales:,.0f}/day)."
)

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_trends, tab_mix, tab_items, tab_data = st.tabs(
    ["Trends", "Revenue mix", "Top items", "Raw data"]
)

with tab_trends:
    by_date = daily.groupby("date", as_index=False)[["lunch_net", "dinner_net", "net_sales"]].sum()

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=by_date["date"], y=by_date["lunch_net"], name="Lunch",
                              mode="lines", line=dict(color="#2a78d6", width=2),
                              fill="tozeroy", fillcolor="rgba(42,120,214,0.10)"))
    fig.add_trace(go.Scatter(x=by_date["date"], y=by_date["dinner_net"], name="Dinner",
                              mode="lines", line=dict(color="#eb6834", width=2),
                              fill="tozeroy", fillcolor="rgba(235,104,52,0.10)"))
    fig.update_layout(title="Net sales over time (lunch vs dinner)", height=380,
                       legend=dict(orientation="h", yanchor="bottom", y=1.02),
                       margin=dict(t=60, b=10, l=10, r=10))
    st.plotly_chart(fig, width="stretch")

    col_a, col_b = st.columns(2)
    with col_a:
        dow_avg = (
            daily.groupby("dow", as_index=False)["net_sales"].mean()
            .assign(day=lambda d: d["dow"].map(lambda i: DOW_NAMES[i]))
            .sort_values("dow")
        )
        fig_dow = px.bar(dow_avg, x="day", y="net_sales", title="Average net sales by weekday")
        fig_dow.update_traces(marker_color="#4a3aa7")
        fig_dow.update_layout(height=340, margin=dict(t=50, b=10, l=10, r=10), xaxis_title=None, yaxis_title="Avg net sales")
        st.plotly_chart(fig_dow, width="stretch")

    with col_b:
        share_by_date = daily.groupby("date", as_index=False).apply(
            lambda g: pd.Series({"dinner_share": g["dinner_net"].sum() / g["net_sales"].sum() * 100}),
            include_groups=False,
        )
        fig_share = go.Figure()
        fig_share.add_trace(go.Scatter(x=share_by_date["date"], y=share_by_date["dinner_share"],
                                        mode="lines", line=dict(color="#eb6834", width=2), name="Dinner share"))
        fig_share.add_hline(y=target_dinner_share, line_dash="dash", line_color="#8f8879",
                             annotation_text="Target", annotation_position="top left")
        fig_share.update_layout(title="Dinner share of net sales, over time", height=340,
                                 margin=dict(t=50, b=10, l=10, r=10), yaxis_title="Dinner share (%)")
        st.plotly_chart(fig_share, width="stretch")

    if len(selected_locations) > 1:
        by_loc_date = daily.groupby(["date", "location"], as_index=False)["net_sales"].sum()
        fig_loc = px.line(by_loc_date, x="date", y="net_sales", color="location",
                           title="Net sales by location")
        fig_loc.update_layout(height=380, margin=dict(t=50, b=10, l=10, r=10), legend_title=None)
        st.plotly_chart(fig_loc, width="stretch")

with tab_mix:
    col_a, col_b = st.columns(2)

    with col_a:
        def revenue_centre(row):
            if row["kind"] == "Food":
                return "Food"
            return "Alcoholic beverage" if row["alc"] else "Non-alcoholic beverage"

        rc = items.assign(centre=items.apply(revenue_centre, axis=1)).groupby("centre", as_index=False)["net_sales"].sum()
        rc = rc.sort_values("net_sales", ascending=True)
        fig_rc = px.bar(rc, x="net_sales", y="centre", orientation="h", title="Net sales by revenue centre")
        fig_rc.update_traces(marker_color="#4a3aa7")
        fig_rc.update_layout(height=360, margin=dict(t=50, b=10, l=10, r=10), yaxis_title=None, xaxis_title="Net sales")
        st.plotly_chart(fig_rc, width="stretch")

    with col_b:
        cat = items.groupby(["category", "cls"], as_index=False)["net_sales"].sum()
        cat["label"] = cat["category"] + " / " + cat["cls"]
        cat = cat.sort_values("net_sales", ascending=False).head(8).sort_values("net_sales")
        fig_cat = px.bar(cat, x="net_sales", y="label", orientation="h", title="Top menu categories")
        fig_cat.update_traces(marker_color="#2a78d6")
        fig_cat.update_layout(height=360, margin=dict(t=50, b=10, l=10, r=10), yaxis_title=None, xaxis_title="Net sales")
        st.plotly_chart(fig_cat, width="stretch")

    with st.expander("Show full menu category breakdown"):
        full_cat = items.groupby(["category", "cls"], as_index=False)["net_sales"].sum().sort_values("net_sales", ascending=False)
        full_cat["share %"] = (full_cat["net_sales"] / full_cat["net_sales"].sum() * 100).round(1)
        st.dataframe(full_cat.rename(columns={"category": "Category", "cls": "Class", "net_sales": "Net sales"}),
                     width="stretch", hide_index=True)

with tab_items:
    def top_items_panel(col, meal, kind, color):
        sub = items[(items["meal"] == meal) & (items["kind"] == kind)]
        agg = sub.groupby("item", as_index=False)[["net_sales", "qty"]].sum().sort_values("net_sales", ascending=False)
        col.markdown(f"**{meal} · {kind.lower()}**")
        top = agg.head(6).sort_values("net_sales")
        fig = px.bar(top, x="net_sales", y="item", orientation="h")
        fig.update_traces(marker_color=color)
        fig.update_layout(height=260, margin=dict(t=10, b=10, l=10, r=10), yaxis_title=None, xaxis_title="Net sales")
        col.plotly_chart(fig, width="stretch")

    r1c1, r1c2 = st.columns(2)
    top_items_panel(r1c1, "Lunch", "Food", "#2a78d6")
    top_items_panel(r1c2, "Dinner", "Food", "#eb6834")
    r2c1, r2c2 = st.columns(2)
    top_items_panel(r2c1, "Lunch", "Beverage", "#2a78d6")
    top_items_panel(r2c2, "Dinner", "Beverage", "#eb6834")

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
