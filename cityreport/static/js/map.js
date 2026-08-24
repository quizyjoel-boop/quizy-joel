const CFG = window.CITYREPORT_CONFIG;

const CATEGORY_COLORS = {
  pothole: "#C0392B",
  streetlight: "#E8A33D",
  waste: "#6B4226",
  other: "#6B7178",
};

let map, pickMap, pickMarker, markersLayer;
let allReports = [];
let activeCategory = "";

function colorFor(cat) { return CATEGORY_COLORS[cat] || CATEGORY_COLORS.other; }

function makeIcon(cat) {
  return L.divIcon({
    className: "",
    html: `<div style="width:16px;height:16px;border-radius:50%;background:${colorFor(cat)};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,0.4)"></div>`,
    iconSize: [16, 16],
  });
}

function initMap() {
  map = L.map("map").setView([CFG.defaultLat, CFG.defaultLng], 13);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(map);
  markersLayer = L.layerGroup().addTo(map);
  loadReports();
}

async function loadReports() {
  const res = await fetch("/api/reports");
  allReports = await res.json();
  renderMarkers();
  renderStats();
}

function renderMarkers() {
  markersLayer.clearLayers();
  const filtered = activeCategory
    ? allReports.filter(r => r.category === activeCategory)
    : allReports;

  filtered.forEach(r => {
    const marker = L.marker([r.lat, r.lng], { icon: makeIcon(r.category) });
    marker.bindPopup(`
      <div class="popup-cat">${r.category_label}</div>
      <div>${escapeHtml(r.ai_summary || r.description).slice(0, 140)}</div>
      <div class="popup-status">${r.status_label} &middot; ${r.reference}</div>
      <a href="/track/${r.reference}" target="_blank">Track this report &rarr;</a>
    `);
    markersLayer.addLayer(marker);
  });
}

function renderStats() {
  const total = allReports.length;
  const resolved = allReports.filter(r => r.status === "resolved").length;
  const progress = allReports.filter(r => r.status === "in_progress").length;
  const statTotal = document.getElementById("statTotal");
  const statResolved = document.getElementById("statResolved");
  const statProgress = document.getElementById("statProgress");
  if (statTotal) statTotal.textContent = total;
  if (statResolved) statResolved.textContent = resolved;
  if (statProgress) statProgress.textContent = progress;
  const bannerTotal = document.getElementById("bannerTotal");
  const bannerProgress = document.getElementById("bannerProgress");
  if (bannerTotal) bannerTotal.textContent = total;
  if (bannerProgress) bannerProgress.textContent = progress;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str || "";
  return div.innerHTML;
}

// ---------- Filter chips ----------
document.querySelectorAll(".chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(c => c.classList.remove("active"));
    chip.classList.add("active");
    activeCategory = chip.dataset.filterCat || "";
    renderMarkers();
  });
});

// ---------- Report modal ----------
const modal = document.getElementById("reportModal");
const form = document.getElementById("reportForm");
const successPanel = document.getElementById("successPanel");

function openModal() {
  modal.hidden = false;
  form.hidden = false;
  successPanel.hidden = true;
  setTimeout(initPickMap, 50);
}
function closeModal() { modal.hidden = true; }

document.getElementById("openReportBtn").addEventListener("click", openModal);
document.getElementById("closeReportBtn").addEventListener("click", closeModal);
modal.addEventListener("click", e => { if (e.target === modal) closeModal(); });

function initPickMap() {
  if (pickMap) { pickMap.invalidateSize(); return; }
  pickMap = L.map("pickMap").setView([CFG.defaultLat, CFG.defaultLng], 14);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(pickMap);

  pickMap.on("click", e => setPickLocation(e.latlng.lat, e.latlng.lng));

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      pos => {
        pickMap.setView([pos.coords.latitude, pos.coords.longitude], 16);
        setPickLocation(pos.coords.latitude, pos.coords.longitude);
      },
      () => setPickLocation(CFG.defaultLat, CFG.defaultLng),
      { timeout: 4000 }
    );
  } else {
    setPickLocation(CFG.defaultLat, CFG.defaultLng);
  }
}

function setPickLocation(lat, lng) {
  document.getElementById("latInput").value = lat;
  document.getElementById("lngInput").value = lng;
  if (pickMarker) {
    pickMarker.setLatLng([lat, lng]);
  } else {
    pickMarker = L.marker([lat, lng], { draggable: true }).addTo(pickMap);
    pickMarker.on("dragend", () => {
      const p = pickMarker.getLatLng();
      document.getElementById("latInput").value = p.lat;
      document.getElementById("lngInput").value = p.lng;
    });
  }
}

// ---------- Live AI preview ----------
const descInput = document.getElementById("descriptionInput");
const photoInput = document.getElementById("photoInput");
const aiPreview = document.getElementById("aiPreview");
let previewTimer;

function triggerPreview() {
  clearTimeout(previewTimer);
  const text = descInput.value.trim();
  if (text.length < 12) { aiPreview.hidden = true; return; }
  previewTimer = setTimeout(runPreview, 700);
}

async function runPreview() {
  const fd = new FormData();
  fd.append("description", descInput.value.trim());
  if (photoInput.files[0]) fd.append("photo", photoInput.files[0]);

  try {
    const res = await fetch("/api/classify-preview", { method: "POST", body: fd });
    if (!res.ok) return;
    const data = await res.json();
    document.getElementById("aiCategoryPill").textContent = CFG.categories[data.category] || data.category;
    const hazardPill = document.getElementById("aiHazardPill");
    hazardPill.textContent = data.hazard_level + " hazard";
    hazardPill.className = "pill hazard hazard-" + data.hazard_level;
    document.getElementById("aiSummaryText").textContent = data.summary;
    aiPreview.hidden = false;
  } catch (e) { /* silent fail — AI preview is a nice-to-have */ }
}

descInput.addEventListener("input", triggerPreview);
photoInput.addEventListener("change", triggerPreview);

// ---------- Submit ----------
form.addEventListener("submit", async e => {
  e.preventDefault();
  const btn = document.getElementById("submitReportBtn");
  btn.disabled = true;
  btn.textContent = "Submitting...";

  const fd = new FormData(form);
  try {
    const res = await fetch("/api/reports", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || "Submission failed");

    form.hidden = true;
    successPanel.hidden = false;
    document.getElementById("successRef").textContent = data.reference;
    document.getElementById("trackLink").href = "/track/" + data.reference;

    loadReports();
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Submit report";
  }
});

initMap();
