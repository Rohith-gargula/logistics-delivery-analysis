"""
Logistics Delivery Performance Analysis (SQL + Python)

Loads the Olist e-commerce CSVs into SQLite, runs the SQL queries in /sql,
saves charts to /charts, exports tidy CSVs for Power BI to /powerbi_exports,
and writes an auto-generated findings.md with the real numbers.

Usage:
    python analysis.py                       # uses ./data  (real Olist files)
    python analysis.py --data sample_data    # uses simulated test data
"""
import argparse
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("--data", default="data", help="folder with the Olist CSV files")
args = parser.parse_args()

data_dir = Path(args.data)
IS_SAMPLE = "sample" in data_dir.name.lower()
TAG = "  [SAMPLE DATA - NOT REAL]" if IS_SAMPLE else ""

files = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
}
for name, fname in files.items():
    if not (data_dir / fname).exists():
        raise SystemExit(f"Missing {data_dir / fname}. See README for download steps.")

# ---------- Load into SQLite ----------
conn = sqlite3.connect(":memory:")
for name, fname in files.items():
    pd.read_csv(data_dir / fname).to_sql(name, conn, index=False)


def q(sql_file):
    return pd.read_sql_query(Path("sql", sql_file).read_text(), conn)


kpis = q("01_overall_kpis.sql")
monthly = q("02_monthly_trend.sql")
by_state = q("03_by_state.sql")
stages = q("04_stage_breakdown.sql")
reviews = q("05_review_impact.sql")

# ---------- Export for Power BI ----------
exp = Path("powerbi_exports")
exp.mkdir(exist_ok=True)
kpis.to_csv(exp / "kpis.csv", index=False)
monthly.to_csv(exp / "monthly_trend.csv", index=False)
by_state.to_csv(exp / "by_state.csv", index=False)
stages.to_csv(exp / "stage_breakdown.csv", index=False)
reviews.to_csv(exp / "review_impact.csv", index=False)

# ---------- Charts ----------
charts = Path("charts")
charts.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED, GREY = "#2b6cb0", "#c53030", "#718096"

# 1. Monthly on-time trend
fig, ax = plt.subplots(figsize=(9, 4.5))
ax.plot(monthly["month"], monthly["on_time_pct"], color=BLUE, marker="o", linewidth=2)
ax.set_title("On-time delivery rate by month" + TAG, loc="left", fontweight="bold")
ax.set_ylabel("On-time delivery (%)")
ax.set_ylim(max(0, monthly["on_time_pct"].min() - 5), 100)
ax.tick_params(axis="x", rotation=60)
step = max(1, len(monthly) // 12)
ax.set_xticks(range(0, len(monthly), step))
ax.set_xticklabels(monthly["month"].iloc[::step])
fig.tight_layout()
fig.savefig(charts / "01_monthly_on_time_rate.png")
plt.close(fig)

# 2. Weakest states
worst = by_state.head(10).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.barh(worst["state"], worst["on_time_pct"], color=RED)
for i, v in enumerate(worst["on_time_pct"]):
    ax.text(v + 0.3, i, f"{v:.1f}%", va="center", fontsize=9)
ax.set_title("10 lowest on-time delivery rates by state" + TAG, loc="left", fontweight="bold")
ax.set_xlabel("On-time delivery (%)")
fig.tight_layout()
fig.savefig(charts / "02_worst_states_on_time.png")
plt.close(fig)

# 3. Stage breakdown
st = stages.set_index("delivery_status")[["days_to_approval", "days_to_carrier_handover", "days_in_transit"]]
fig, ax = plt.subplots(figsize=(8, 4.5))
st.plot(kind="bar", stacked=True, ax=ax, color=["#a0aec0", "#ed8936", BLUE], rot=0)
ax.set_title("Where the time goes: average days per stage" + TAG, loc="left", fontweight="bold")
ax.set_xlabel("")
ax.set_ylabel("Average days")
ax.legend(["Purchase to approval", "Approval to carrier", "In transit"], frameon=False)
fig.tight_layout()
fig.savefig(charts / "03_stage_breakdown.png")
plt.close(fig)

# 4. Review impact
fig, ax = plt.subplots(figsize=(6.5, 4.5))
colors = [BLUE if s == "On time" else RED for s in reviews["delivery_status"]]
ax.bar(reviews["delivery_status"], reviews["avg_review_score"], color=colors, width=0.5)
for i, v in enumerate(reviews["avg_review_score"]):
    ax.text(i, v + 0.05, f"{v:.2f}", ha="center", fontweight="bold")
ax.set_ylim(0, 5.5)
ax.set_title("Average review score: on-time vs late" + TAG, loc="left", fontweight="bold")
ax.set_ylabel("Average review score (1-5)")
fig.tight_layout()
fig.savefig(charts / "04_review_score_impact.png")
plt.close(fig)

# ---------- Auto-generated findings ----------
k = kpis.iloc[0]
late_row = stages.set_index("delivery_status").loc["Late"]
ontime_row = stages.set_index("delivery_status").loc["On time"]
rv = reviews.set_index("delivery_status")
best, worst1 = by_state.iloc[-1], by_state.iloc[0]
stage_cols = ["days_to_approval", "days_to_carrier_handover", "days_in_transit"]
gaps = (late_row[stage_cols] - ontime_row[stage_cols]).sort_values(ascending=False)
biggest_stage = gaps.index[0].replace("_", " ")

findings = f"""# Key findings{' (SIMULATED SAMPLE DATA - DO NOT PUBLISH)' if IS_SAMPLE else ''}

- Analysed **{int(k.delivered_orders):,}** delivered orders.
- Overall on-time delivery rate: **{k.on_time_pct:.1f}%**; average delivery time **{k.avg_delivery_days:.1f} days**.
- When orders were late, they arrived on average **{k.avg_days_late_when_late:.1f} days** after the estimated date.
- Lowest on-time rate: **{worst1.state} ({worst1.on_time_pct:.1f}%)**; highest: **{best.state} ({best.on_time_pct:.1f}%)**.
- The biggest difference between late and on-time orders is in the **{biggest_stage}** stage (+{gaps.iloc[0]:.1f} days on average).
- Average review score: **{rv.loc['On time','avg_review_score']:.2f}** for on-time orders vs **{rv.loc['Late','avg_review_score']:.2f}** for late orders;
  **{rv.loc['Late','pct_negative_reviews']:.1f}%** of late orders got a 1-2 star review vs **{rv.loc['On time','pct_negative_reviews']:.1f}%** of on-time orders.
"""
Path("findings.md").write_text(findings)
print(findings)
print("Charts saved to ./charts, Power BI CSVs saved to ./powerbi_exports")
