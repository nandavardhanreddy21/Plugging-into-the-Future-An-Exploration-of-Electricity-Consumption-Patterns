"""
Step 1 of the pipeline: cleans the raw CSV, adds calculated fields,
and rebuilds the dashboard's embedded data.

HOW TO RUN (in VS Code terminal, from the project folder):
    python scripts/prepare_data.py

Needs pandas. If you get "No module named pandas", install it first:
    pip install pandas
"""

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent
RAW_CSV = ROOT / "data" / "Consumption.csv"
CLEANED_CSV = ROOT / "data" / "consumption_cleaned.csv"
DASHBOARD_TEMPLATE = ROOT / "dashboard" / "index_template.html"
DASHBOARD_OUT = ROOT / "dashboard" / "index.html"

METRO_STATES = ["Delhi", "Maharashtra", "Tamil Nadu", "West Bengal", "Karnataka", "Telangana"]
LOCKDOWN_START = pd.Timestamp("2020-03-25")


def clean_and_enrich():
    df = pd.read_csv(RAW_CSV)
    df["Dates"] = pd.to_datetime(df["Dates"], format="%d/%m/%Y")

    df["Year"] = df["Dates"].dt.year
    df["Month"] = df["Dates"].dt.month
    df["MonthName"] = df["Dates"].dt.strftime("%b")
    df["Quarter"] = "Q" + df["Dates"].dt.quarter.astype(str)
    df["LockdownPeriod"] = df["Dates"].apply(
        lambda d: "After Lockdown" if d >= LOCKDOWN_START else "Before Lockdown"
    )
    df["CityType"] = df["States"].apply(lambda s: "Metro" if s in METRO_STATES else "Non-Metro")

    df = df.rename(columns={"States": "State", "Regions": "Region", "Dates": "Date", "Usage": "Usage_MU"})
    df.to_csv(CLEANED_CSV, index=False)
    print(f"Wrote {CLEANED_CSV.relative_to(ROOT)}  ({len(df)} rows)")
    return df


def build_dashboard_data(df):
    out = {}

    for yr in [2019, 2020]:
        s = df[df.Year == yr].groupby("State")["Usage_MU"].sum().sort_values(ascending=False)
        out[f"state_{yr}"] = [{"state": k, "usage": round(v, 1)} for k, v in s.items()]

    s = df.groupby("State")["Usage_MU"].sum().sort_values(ascending=False)
    out["state_total"] = [{"state": k, "usage": round(v, 1)} for k, v in s.items()]

    s = df.groupby("Region")["Usage_MU"].sum().sort_values(ascending=False)
    out["region_total"] = [{"region": k, "usage": round(v, 1)} for k, v in s.items()]

    out["region_by_year"] = df.groupby(["Region", "Year"])["Usage_MU"].sum().reset_index().to_dict("records")

    out["month_wise"] = (
        df.groupby(["Month", "MonthName", "Year"])["Usage_MU"]
        .sum().reset_index().sort_values(["Month", "Year"]).to_dict("records")
    )

    s = df.groupby("LockdownPeriod")["Usage_MU"].agg(["sum", "mean"]).reset_index()
    s.columns = ["period", "total", "avg"]
    out["lockdown"] = s.round(2).to_dict("records")

    out["quarter"] = (
        df.groupby(["Quarter", "Year"])["Usage_MU"].sum().reset_index()
        .sort_values(["Year", "Quarter"]).to_dict("records")
    )

    out["citytype"] = (
        df.groupby(["CityType", "State"])["Usage_MU"].sum().reset_index()
        .sort_values("Usage_MU", ascending=False).round(1).to_dict("records")
    )

    out["year_total"] = df.groupby("Year")["Usage_MU"].sum().reset_index().round(1).to_dict("records")

    geo = df.groupby(["State", "Region"])[["latitude", "longitude"]].mean().reset_index()
    totals = df.groupby("State")["Usage_MU"].sum()
    geo["usage"] = geo["State"].map(totals).round(1)
    out["state_geo"] = geo.round(4).to_dict("records")

    out["states"] = sorted(df["State"].unique().tolist())
    out["regions"] = sorted(df["Region"].unique().tolist())
    return out


def inject_into_dashboard(data):
    html = DASHBOARD_TEMPLATE.read_text(encoding="utf-8")
    html = html.replace("__DATA_JSON__", json.dumps(data))
    DASHBOARD_OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {DASHBOARD_OUT.relative_to(ROOT)}")


def main():
    if not RAW_CSV.exists():
        print(f"ERROR: expected the raw dataset at {RAW_CSV}")
        return
    df = clean_and_enrich()
    data = build_dashboard_data(df)
    inject_into_dashboard(data)
    print("\nDone. Open dashboard/index.html in your browser to view the result.")


if __name__ == "__main__":
    main()
