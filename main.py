def clean_and_filter(df):
    # Normalize all column names
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.replace(" ", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.replace("_", "", regex=False)
        .str.lower()
    )

    # Candidates for site name
    site_candidates = ["sitename", "site", "name", "siteno", "sitenumber", "siteid", "cowid"]
    site_col = next((c for c in df.columns if c in site_candidates), None)

    # Candidates for city
    city_candidates = ["cityname", "city", "location", "area", "region", "municipality"]
    city_col = next((c for c in df.columns if c in city_candidates), None)

    # Candidates for next fueling date
    fuel_candidates = ["nextfuelingplan", "nextfueldate", "nextfuel", "fueldate", "nextfueling"]
    fuel_col = next((c for c in df.columns if c in fuel_candidates), None)

    # Parse date column
    if fuel_col:
        df[fuel_col] = pd.to_datetime(df[fuel_col], errors="coerce")
    else:
        df["nextfuelingplan"] = pd.NaT
        fuel_col = "nextfuelingplan"

    # Fallbacks
    if site_col is None:
        df["sitename"] = "Unknown"
        site_col = "sitename"

    if city_col is None:
        df["cityname"] = "Unknown"
        city_col = "cityname"

    print(f"[INFO] Using columns: Site={site_col} | City={city_col} | NextFuel={fuel_col}")

    return df[[site_col, city_col, fuel_col]]
