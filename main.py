import json
import os
from datetime import datetime
from typing import List

import pandas as pd

# Remote CSV export URL (live Google Sheet)
CSV_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vS0GkXnQMdKYZITuuMsAzeWDtGUqEJ3lWwqNdA67NewOsDOgqsZHKHECEEkea4nrukx4-DqxKmf62nC"
    "/pub?gid=1149576218&output=csv"
)

# Optional local fallback
LOCAL_FALLBACK = "sheet_cache.csv"


# -------------------------------------------------------
# LOAD DATA (Remote Google Sheet with graceful fallback)
# -------------------------------------------------------
def load_data() -> pd.DataFrame:
    print(f"Loading data from Google Sheet…")
    try:
        df = pd.read_csv(CSV_URL)
        df.to_csv(LOCAL_FALLBACK, index=False)  # Keep local backup
        print("✔ Remote sheet loaded.")
        return df
    except Exception as exc:
        if os.path.exists(LOCAL_FALLBACK):
            print(f"⚠ Remote load failed: {exc}")
            print(f"→ Loading local cached file: {LOCAL_FALLBACK}")
            return pd.read_csv(LOCAL_FALLBACK)

        raise RuntimeError("Google Sheet unreachable AND no local backup found.") from exc


# -------------------------------------------------------
# CLEAN + AUTO-DETECT COLUMN NAMES
# -------------------------------------------------------
def clean_and_filter(df: pd.DataFrame) -> pd.DataFrame:
    # Normalize all column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.replace("_", "", regex=False)
        .str.lower()
    )

    # Auto-detect possible column names
    site_candidates = ["sitename", "site", "name", "cowid", "siteno", "sitenumber"]
    city_candidates = ["cityname", "city", "area", "location", "region"]
    fuel_candidates = ["nextfuelingplan", "nextfueldate", "nextfuel", "fueldate", "fuelplan"]
    lat_candidates = ["lat", "latitude", "x", "gpslat", "site_lat"]
    lng_candidates = ["lng", "lon", "long", "longitude", "gpslng", "site_lng"]

    # Helper to find first matching column
    def pick(col_list):
        return next((c for c in df.columns if c in col_list), None)

    site_col = pick(site_candidates)
    city_col = pick(city_candidates)
    fuel_col = pick(fuel_candidates)
    lat_col = pick(lat_candidates)
    lng_col = pick(lng_candidates)

    # Ensure fuel column always exists
    if fuel_col is None:
        df["nextfuelingplan"] = pd.NaT
        fuel_col = "nextfuelingplan"

    # Convert date column
    df[fuel_col] = pd.to_datetime(df[fuel_col], errors="coerce")
    df = df.dropna(subset=[fuel_col])

    # Ensure site & city exist
    if site_col is None:
        df["sitename"] = "Unknown"
        site_col = "sitename"

    if city_col is None:
        df["cityname"] = "Unknown"
        city_col = "cityname"

    # Convert latitude & longitude if present
    df["lat"] = pd.to_numeric(df.get(lat_col), errors="coerce") if lat_col else None
    df["lng"] = pd.to_numeric(df.get(lng_col), errors="coerce") if lng_col else None

    print(f"""
[INFO] Auto-detected columns:
   Site       → {site_col}
   City       → {city_col}
   Fuel Date  → {fuel_col}
   Latitude   → {lat_col}
   Longitude  → {lng_col}
""")

    return df[[site_col, city_col, fuel_col, "lat", "lng"]]


# -------------------------------------------------------
# REPORT GENERATION
# -------------------------------------------------------
def generate_reports(df: pd.DataFrame) -> None:
    today = pd.to_datetime(datetime.today().date())

    df_today = df[df[df.columns[2]] == today]
    df_pending = df[df[df.columns[2]] < today]

    df_today.to_csv("fuel_today.csv", index=False)
    df_pending.to_csv("fuel_pending.csv", index=False)

    print("✔ fuel_today.csv generated.")
    print("✔ fuel_pending.csv generated.")
    print(f"   → Due today: {len(df_today)}")
    print(f"   → Pending/overdue: {len(df_pending)}")


# -------------------------------------------------------
# DASHBOARD JSON EXPORT
# -------------------------------------------------------
def generate_dashboard_data(df: pd.DataFrame, output_path: str = "data.json") -> None:
    records: List[dict] = []

    for r in df.to_dict(orient="records"):
        date_value = r[df.columns[2]]  # 3rd column = fuel date

        records.append(
            {
                "SiteName": r[df.columns[0]],
                "CityName": r[df.columns[1]],
                "NextFuelingPlan": date_value.date().isoformat(),
                "lat": float(r["lat"]) if r["lat"] else None,
                "lng": float(r["lng"]) if r["lng"] else None,
            }
        )

    with open(output_path, "w", encoding="utf-8") as fp:
        json.dump(records, fp, indent=2, ensure_ascii=False)

    print(f"✔ {output_path} generated for the dashboard.")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main() -> None:
    print("\nLoading Central Fuel Plan database…")
    df = load_data()

    print("Cleaning & filtering data…")
    df = clean_and_filter(df)

    print("Generating reports…")
    generate_reports(df)

    print("Exporting dashboard data…")
    generate_dashboard_data(df)

    print("\n✔ All tasks completed successfully.\n")


if __name__ == "__main__":
    main()
