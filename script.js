//-------------------------------------------------------------
// CONFIG
//-------------------------------------------------------------
const DATA_URL = "data.json";

const ONE_DAY = 24 * 60 * 60 * 1000;

const COLOR = {
  DUE: "#fb6d5d",      // today / overdue
  TOMORROW: "#ffc857", // tomorrow
  AFTER: "#3ad17c",    // after tomorrow & healthy (green)
};

//-------------------------------------------------------------
// MAP
//-------------------------------------------------------------
const map = L.map("map", {
  maxBounds: [
    [16.0, 34.0],
    [33.5, 56.0],
  ],
  maxBoundsViscosity: 0.8,
  minZoom: 4,
}).setView([23.8859, 45.0792], 6);

L.tileLayer(
  "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
  {
    attribution: "Tiles © Esri | Maxar",
  }
).addTo(map);

const markerLayer = L.layerGroup().addTo(map);

//-------------------------------------------------------------
// DOM ELEMENTS
//-------------------------------------------------------------
const metricTotal = document.getElementById("metric-total");
const metricDue = document.getElementById("metric-due");
const metricTomorrow = document.getElementById("metric-tomorrow");
const metricAfter = document.getElementById("metric-after");

const dueList = document.getElementById("due-list");
const loader = document.getElementById("loader");
const errorBanner = document.getElementById("error");

function toggleLoading(state) {
  loader.classList.toggle("hidden", !state);
}

//-------------------------------------------------------------
// DATE HELPERS
//-------------------------------------------------------------
function parseDate(str) {
  if (!str) return null;

  // Expecting "YYYY-MM-DD" coming from data.json
  const dt = new Date(str);
  if (Number.isNaN(dt.getTime())) return null;

  dt.setHours(0, 0, 0, 0);
  return dt;
}

function dateDiff(dt) {
  if (!dt) return null;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.round((dt - today) / ONE_DAY);
}

function formatDate(dt) {
  if (!dt) return "-";
  return dt.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function getStatus(days) {
  // Classification exactly as requested
  if (days === null) return { label: "unknown", color: COLOR.AFTER };
  if (days <= 0) return { label: "due", color: COLOR.DUE };          // today or overdue
  if (days === 1) return { label: "tomorrow", color: COLOR.TOMORROW };
  // >= 2 days
  return { label: "after", color: COLOR.AFTER };
}

//-------------------------------------------------------------
// AUTO-FOCUS LOOP ON RED SITES
//-------------------------------------------------------------
let priorityLoopTimer = null;
let priorityLoopIndex = 0;

function startPriorityLoop(priorityMarkers) {
  if (priorityLoopTimer) {
    clearInterval(priorityLoopTimer);
    priorityLoopTimer = null;
  }

  if (!priorityMarkers || priorityMarkers.length === 0) return;

  priorityLoopIndex = 0;

  // Every 7 seconds fly to next "due" site
  priorityLoopTimer = setInterval(() => {
    const marker = priorityMarkers[priorityLoopIndex];
    if (!marker) return;

    const latlng = marker.getLatLng();
    map.flyTo(latlng, 9, { duration: 1.8 });

    priorityLoopIndex = (priorityLoopIndex + 1) % priorityMarkers.length;
  }, 7000);
}

//-------------------------------------------------------------
// RENDER
//-------------------------------------------------------------
function renderSites(sites) {
  markerLayer.clearLayers();

  let countDue = 0;
  let countTomorrow = 0;
  let countAfter = 0;

  const dueSites = [];
  const allMarkers = [];
  const priorityMarkers = [];

  sites.forEach((s) => {
    const days = dateDiff(s.fuelDate);
    const { label, color } = getStatus(days);

    if (days !== null) {
      if (days <= 0) countDue += 1;
      else if (days === 1) countTomorrow += 1;
      else if (days >= 2) countAfter += 1;
    }

    if (label === "due") {
      dueSites.push(s);
    }

    const marker = L.circleMarker([s.lat, s.lng], {
      radius: 9,
      color,
      fillColor: color,
      fillOpacity: 0.85,
      weight: 2,
    }).addTo(markerLayer);

    marker.bindPopup(
      `<strong>${s.siteName}</strong><br/>Fueling: ${formatDate(s.fuelDate)}`
    );

    allMarkers.push(marker);
    if (label === "due") priorityMarkers.push(marker);
  });

  // METRICS
  metricTotal.textContent = sites.length; // all Central + ON-AIR / In Progress from backend
  metricDue.textContent = countDue;
  metricTomorrow.textContent = countTomorrow;
  metricAfter.textContent = countAfter;

  // MAP BOUNDS
  if (priorityMarkers.length > 0) {
    const group = L.featureGroup(priorityMarkers);
    map.fitBounds(group.getBounds().pad(0.4));
  } else if (allMarkers.length > 0) {
    const group = L.featureGroup(allMarkers);
    map.fitBounds(group.getBounds().pad(0.3));
  }

  // DUE LIST
  dueList.innerHTML = "";
  if (dueSites.length === 0) {
    dueList.innerHTML = `<li class="empty-row">No sites due today.</li>`;
  } else {
    // sort by date ascending (oldest first)
    dueSites
      .sort((a, b) => a.fuelDate - b.fuelDate)
      .forEach((s) => {
        const li = document.createElement("li");
        li.className = "site-item";
        li.innerHTML = `
          <div class="site-name">${s.siteName}</div>
          <div class="site-date">${formatDate(s.fuelDate)}</div>
        `;
        dueList.appendChild(li);
      });
  }

  // start loop over red markers
  startPriorityLoop(priorityMarkers);
}

//-------------------------------------------------------------
// FETCH FROM data.json
//-------------------------------------------------------------
async function fetchAndRender() {
  try {
    toggleLoading(true);
    errorBanner.classList.add("hidden");

    const response = await fetch(DATA_URL, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const json = await response.json();

    // json comes from Python: already filtered to
    // Central + (ON-AIR / IN PROGRESS) + valid date + coords
    const sites = json
      .map((item) => ({
        siteName: item.SiteName,
        lat: parseFloat(item.lat),
        lng: parseFloat(item.lng),
        fuelDate: parseDate(item.NextFuelingPlan),
      }))
      .filter(
        (s) =>
          s.siteName &&
          !Number.isNaN(s.lat) &&
          !Number.isNaN(s.lng) &&
          s.fuelDate !== null
      );

    renderSites(sites);
  } catch (err) {
    console.error(err);
    errorBanner.textContent = "Failed to load data.";
    errorBanner.classList.remove("hidden");
  } finally {
    toggleLoading(false);
  }
}

fetchAndRender();
