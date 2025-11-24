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

    # Auto-detect columns
    def pick(options):
        return next((c for c in df.columns if c in options), None)

    site_col = pick(["sitename", "site", "cowid", "siteno", "sitenumber", "name"])
    city_col = pick(["cityname", "city", "location", "area", "region"])
    fuel_col = pick(["nextfuelingplan", "nextfueldate", "nextfuel", "fueldate", "fuelplan"])
    lat_col = pick(["lat", "latitude", "gpslat"])
    lng_col = pick(["lng", "lon", "long", "longitude", "gpslng"])

    # Ensure fuel column exists
    if fuel_col is None:
        df["nextfuelingplan"] = pd.NaT
        fuel_col = "nextfuelingplan"

    # Convert date
    df[fuel_col] = pd.to_datetime(df[fuel_col], errors="coerce")
    df = df.dropna(subset=[fuel_col])

    # Fallbacks
    if site_col is None:
        df["sitename"] = "Unknown"
        site_col = "sitename"

    if city_col is None:
        df["cityname"] = "Unknown"
        city_col = "cityname"

    # Convert coordinates
    df["lat"] = pd.to_numeric(df.get(lat_col), errors="coerce") if lat_col else None
    df["lng"] = pd.to_numeric(df.get(lng_col), errors="coerce") if lng_col else None

    print(f"[INFO] using: site={site_col}, city={city_col}, fuel={fuel_col}, lat={lat_col}, lng={lng_col}")

    return df[[site_col, city_col, fuel_col, "lat", "lng"]]
