async function fetchAndRender() {
  try {
    toggleLoading(true);

    const response = await fetch(DATA_URL);
    const json = await response.json();

    console.log("RAW API RESPONSE:", json);  // <-- Debug

    // FIXED FIELD NAMES MATCHING YOUR GOOGLE SCRIPT OUTPUT
    const sites = json
      .filter((s) =>
        (s.RegionName || s.regionName || "").toLowerCase() === "central"
      )
      .map((s) => ({
        siteName: s.siteName || s.SiteName,
        lat: parseFloat(s.lat),
        lng: parseFloat(s.lng),
        fuelDate: parseDate(s.NextFuelingPlan),
      }))
      .filter((s) => !isNaN(s.lat) && !isNaN(s.lng));

    console.log("FILTERED SITES:", sites); // <-- Debug

    renderSites(sites);
  } catch (err) {
    console.error("ERROR LOADING DATA:", err);
    errorBanner.classList.remove("hidden");
    errorBanner.textContent = "Failed to load data.";
  } finally {
    toggleLoading(false);
  }
}
