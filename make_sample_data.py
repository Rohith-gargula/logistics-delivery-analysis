"""
Generates SIMULATED data in the same format as the Olist Brazilian
E-Commerce dataset, so the pipeline can be tested without downloading
anything. These numbers are NOT real. Never present sample-data results
as real findings.
"""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
out = Path("sample_data")
out.mkdir(exist_ok=True)

N = 20000
states = ["SP", "RJ", "MG", "RS", "PR", "SC", "BA", "DF", "GO", "ES", "PE", "CE", "PA", "MA"]
# Higher value = more delay-prone
state_risk = dict(zip(states, [0.04, 0.10, 0.07, 0.06, 0.06, 0.07, 0.14, 0.08, 0.09, 0.09, 0.15, 0.14, 0.20, 0.22]))
state_w = np.array([0.35, 0.13, 0.12, 0.06, 0.06, 0.05, 0.05, 0.04, 0.03, 0.03, 0.03, 0.02, 0.02, 0.01])
state_w = state_w / state_w.sum()

customers = pd.DataFrame({
    "customer_id": [f"c{i:06d}" for i in range(N)],
    "customer_unique_id": [f"u{i:06d}" for i in range(N)],
    "customer_zip_code_prefix": rng.integers(1000, 99999, N),
    "customer_city": "sample_city",
    "customer_state": rng.choice(states, N, p=state_w),
})

start = pd.Timestamp("2017-01-01")
purchase = start + pd.to_timedelta(rng.integers(0, 600 * 24 * 60, N), unit="m")
approval = purchase + pd.to_timedelta(rng.gamma(2, 0.3, N), unit="D")
handover_days = rng.gamma(2.2, 1.0, N)
risk = customers["customer_state"].map(state_risk).to_numpy()
transit_days = rng.gamma(3.0, 2.2, N) * (1 + 3 * risk)
carrier = approval + pd.to_timedelta(handover_days, unit="D")
delivered = carrier + pd.to_timedelta(transit_days, unit="D")
estimated = purchase + pd.to_timedelta(rng.normal(22, 3, N).clip(10, None), unit="D")

status = np.where(rng.random(N) < 0.03, "canceled", "delivered")
orders = pd.DataFrame({
    "order_id": [f"o{i:06d}" for i in range(N)],
    "customer_id": customers["customer_id"],
    "order_status": status,
    "order_purchase_timestamp": purchase,
    "order_approved_at": approval,
    "order_delivered_carrier_date": carrier,
    "order_delivered_customer_date": delivered,
    "order_estimated_delivery_date": estimated,
})
canceled = orders["order_status"] == "canceled"
orders.loc[canceled, ["order_delivered_carrier_date", "order_delivered_customer_date"]] = pd.NaT

late = np.asarray(delivered > estimated)
base = rng.choice([1, 2, 3, 4, 5], N, p=[0.04, 0.04, 0.10, 0.22, 0.60])
late_score = rng.choice([1, 2, 3, 4, 5], N, p=[0.35, 0.18, 0.17, 0.15, 0.15])
reviews = pd.DataFrame({
    "review_id": [f"r{i:06d}" for i in range(N)],
    "order_id": orders["order_id"],
    "review_score": np.where(late, late_score, base),
})

fmt = "%Y-%m-%d %H:%M:%S"
for col in orders.columns:
    if "date" in col or "timestamp" in col or col == "order_approved_at":
        orders[col] = pd.to_datetime(orders[col]).dt.strftime(fmt)

orders.to_csv(out / "olist_orders_dataset.csv", index=False)
customers.to_csv(out / "olist_customers_dataset.csv", index=False)
reviews.to_csv(out / "olist_order_reviews_dataset.csv", index=False)
print(f"Wrote {N} simulated orders to {out}/")
