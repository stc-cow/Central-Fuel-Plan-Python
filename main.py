import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence, Tuple
import pandas as pd

SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/e/"
    "2PACX-1vS0GkXnQMdKYZITuuMsAzeWDtGUqEJ3lWwqNdA67NewOsDOgqsZHKHECEEkea4nrukx4-DqxKmf62nC"
    "/pub?gid=1149576218&single=true&output=csv"
)

# -------------------------------------------------------
# SAFE DATE PARSER (fix errors in AJ)
# -------------------------------------------------------
def safe_parse_date(value):
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value in ("", "#N/A", "#DIV/0!", "#VALUE!"):
        return None

    formats = [
        "%d-%m-%Y", "%m-%d-%Y", "%Y-%m-%d",
        "%d/%m/%Y", "%m/%d/%Y",
        "%d-%b-%Y", "%d %b %Y"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except:
            pass
    return None


# -------------------------------------------------------
# LOAD SHEET
# -------------------------------------------------------
def load_data() -> pd.DataFrame:
    print(f"[INFO] Loading sheet: {SHEET_URL}")
    cache = Path("sheet_cache.csv")

    try:
        return pd.read_csv(SHEET_URL)
    except Exception:
        print("[WARN] Live sheet failed, using cache")
        if not cache.exists():
            raise
        return pd.read_csv(cache)


# -------------------------------------------------------
# CLEAN & FILTER ACCORDING TO PROJECT RULES
# -------------------------------------------------------
def clean_and_filter(df):

    # NORMALIZE COLUMNS
    df.columns = (
        pd.Index(df.columns)
        .astype(str).str.strip().str.lower().str.replace(" ", "")
    )

    site_col = "sitename"      # Column B
    region_col = "regionnam"   # Column D
    status_col = "cowstatus"   # Column J
    date_col = "nextfuelingplan" # Column AJ
    lat_col = "lat"            # Column L
    lng_col = "lng"            # Column M

    # 1️⃣ Region filter → Central only
    df = df[df[region_col].str.strip().str.lower() == "central"]

    # 2️⃣ Status filter → ON-AIR or IN PROGRESS
    df[status_col] = df[status_col].str.upper().str.strip()
    df = df[df[status_col].isin(["ON-AIR", "IN PROGRESS"])]

    # 3️⃣ Clean AJ → remove all invalid entries
    print("[INFO] Cleaning AJ (NextFuelingPlan)...")
    df["parsed_date"] = df[date_col].apply(safe_parse_date)
    df = df.dropna(subset=["parsed_date"])
    df["parsed_date"] = pd.to_datetime(df["parsed_date"])

    # Extract cleaned DF
    clean = pd.DataFrame({
        "SiteName": df[site_col],
        "Region": df[region_col],
        "COWStatus": df[status_col],
        "NextFuelingPlan": df["parsed_date"],
        "lat": df[lat_col],
        "lng": df[lng_col]
    })

    return clean


# -------------------------------------------------------
# EXPORT JSON FOR DASHBOARD
# -------------------------------------------------------
def generate_dashboard(df):
    df = df.dropna(subset=["lat", "lng"])
    df = df.copy()
    df["NextFuelingPlan"] = df["NextFuelingPlan"].dt.strftime("%Y-%m-%d")

    records = df.to_dict(orient="records")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2)

    print(f"[OK] data.json exported → {len(records)} sites")


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():
    df = load_data()
    clean = clean_and_filter(df)
    generate_dashboard(clean)
    print("[OK] Completed successfully")


if __name__ == "__main__":
    main()
