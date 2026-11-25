const fmt = (n) => Number(n).toLocaleString("en-IN");
const $ = (id) => document.getElementById(id);

async function loadSummary() {
  const s = await (await fetch("/api/summary")).json();
  $("coverage").textContent =
    `${s.rows.toLocaleString("en-IN")} daily records · ${s.countries.join(", ")} · ${s.date_min} to ${s.date_max}`;
  const india = s.latest_totals["India"] || {};
  const top = Object.entries(s.latest_totals).sort((a, b) => b[1].confirmed - a[1].confirmed)[0];
  $("kpis").innerHTML = [
    ["India confirmed", fmt(india.confirmed || 0)],
    ["India deaths", fmt(india.deaths || 0)],
    ["Highest: " + (top ? top[0] : "—"), fmt(top ? top[1].confirmed : 0)],
    ["Countries", s.countries.length],
    ["Records", fmt(s.rows)],
  ].map(([k, v]) => `<div class="kpi"><span>${k}</span><b>${v}</b></div>`).join("");
  const sel = $("country");
  sel.innerHTML = s.countries.map((c) => `<option ${c === "India" ? "selected" : ""}>${c}</option>`).join("");
  sel.onchange = () => loadTrend(sel.value);
  const topRows = Object.entries(s.latest_totals)
    .sort((a, b) => b[1].confirmed - a[1].confirmed)
    .map(([c, t]) => `<tr><td>${c}</td><td>${fmt(t.confirmed)}</td><td>${fmt(t.deaths)}</td><td>${t.date}</td></tr>`).join("");
  document.querySelector("#top tbody").innerHTML = topRows;
}

function drawChart(points) {
  const svg = $("chart");
  const data = points.slice(-180);
  const max = Math.max(...data.map((p) => p.new_confirmed), 1);
  const W = 800, H = 260, P = 24;
  const x = (i) => P + (i / Math.max(data.length - 1, 1)) * (W - 2 * P);
  const y = (v) => H - P - (v / max) * (H - 2 * P);
  const line = (key) => data.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[key]).toFixed(1)}`).join(" ");
  svg.innerHTML =
    `<line x1="${P}" y1="${H - P}" x2="${W - P}" y2="${H - P}" stroke="#ccc"/>` +
    `<path d="${line("new_confirmed")}" fill="none" stroke="#2563eb" stroke-width="1.5"/>` +
    `<path d="${line("rolling_avg_7d")}" fill="none" stroke="#dc2626" stroke-width="2" stroke-dasharray="5 4"/>` +
    `<text x="${P}" y="14" font-size="12">Peak in window: ${fmt(max)} new cases</text>`;
}

async function loadTrend(country) {
  const res = await fetch(`/api/trends?country=${encodeURIComponent(country)}`);
  if (!res.ok) { $("chart").innerHTML = ""; return; }
  const data = await res.json();
  drawChart(data.points);
}

async function loadAnomalies() {
  const data = await (await fetch("/api/anomalies")).json();
  const rows = data.anomalies.slice(-15).reverse().map((a) =>
    `<tr><td>${a.date}</td><td>${a.country}</td><td>${fmt(a.new_confirmed)}</td><td>${fmt(a.median_14d)}</td><td>${a.ratio}×</td></tr>`).join("");
  document.querySelector("#anomalies tbody").innerHTML = rows || `<tr><td colspan="5">No spike days found.</td></tr>`;
}

async function loadReport() {
  const data = await (await fetch("/api/report?country=India")).json();
  $("report").textContent = data.report;
}

$("upload").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const res = await fetch("/api/upload", { method: "POST", body: fd });
  const data = await res.json();
  $("upload-result").textContent = res.ok
    ? `Loaded ${data.rows_loaded} rows (${data.rows_dropped} dropped, ${data.values_cleaned} values cleaned) from ${data.filename}.`
    : `Upload failed: ${data.detail || res.statusText}`;
  if (res.ok) { loadSummary(); loadTrend($("country").value); loadAnomalies(); loadReport(); }
});

loadSummary().then(() => loadTrend("India"));
loadAnomalies();
loadReport();
