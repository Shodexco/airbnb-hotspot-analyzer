document.addEventListener("DOMContentLoaded", () => {
  const citySelect = document.getElementById("city-select");
  const thresholdInput = document.getElementById("threshold-input");
  const form = document.getElementById("analyzer-form");
  const runBtn = document.getElementById("run-btn");

  const summarySection = document.getElementById("summary-section");
  const summaryCityLabel = document.getElementById("summary-city-label");

  const statListings = document.querySelector('[data-stat="listings"]');
  const statMedian = document.querySelector('[data-stat="median"]');
  const statThreshold = document.querySelector('[data-stat="threshold"]');
  const statClusters = document.querySelector('[data-stat="clusters"]');

  const logOutput = document.getElementById("log-output");

  const mapFrame = document.getElementById("map-frame");
  const mapHint = document.getElementById("map-hint");
  const mapLink = document.getElementById("map-link");

  // Export buttons
  const exportData = document.getElementById("export-data");
  const exportPremium = document.getElementById("export-premium");
  const exportLuxury = document.getElementById("export-luxury");
  const exportUltra = document.getElementById("export-ultra");
  const exportNeighborhoods = document.getElementById("export-neighborhoods");
  const exportLog = document.getElementById("export-log");

  let selectedCity = null;

  // ----------------------------
  // Load cities
  // ----------------------------
  fetch("/api/cities")
    .then((res) => res.json())
    .then((data) => {
      const cities = data.cities || [];
      citySelect.innerHTML = "";

      if (!cities.length) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No cities available";
        citySelect.appendChild(opt);
        return;
      }

      cities.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.code;
        opt.textContent = `${c.name} (${c.code})`;
        citySelect.appendChild(opt);
      });
    })
    .catch(() => {
      citySelect.innerHTML = "<option value=''>Error loading cities</option>";
    });

  // ----------------------------
  // Run analysis
  // ----------------------------
  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const city = citySelect.value;
    const threshold = parseFloat(thresholdInput.value || "200");

    if (!city) {
      alert("Please select a city.");
      return;
    }

    selectedCity = city;

    runBtn.disabled = true;
    runBtn.textContent = "Analyzing...";
    logOutput.textContent = "Running analysis...";

    fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        city,
        premium_threshold: threshold,
      }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (!data.success) throw new Error(data.error || "Unknown error.");

        const s = data.summary;

        summarySection.classList.remove("hidden");
        summaryCityLabel.textContent = `${s.city_name} (${s.city_code}) — snapshot ${s.data_date}`;

        statListings.textContent = (s.total_listings || 0).toLocaleString();
        statMedian.textContent = `$${Math.round(s.median_price || 0)}`;
        statThreshold.textContent = `$${Math.round(s.premium_threshold || threshold)}`;
        statClusters.textContent = s.premium_cluster_count || 0;

        logOutput.textContent = s.log || "No log output.";

        if (s.map_url) {
          mapHint.classList.add("hidden");
          mapFrame.classList.remove("hidden");
          mapFrame.src = s.map_url;
          mapLink.href = s.map_url;
          mapLink.classList.remove("hidden");
        } else {
          mapHint.classList.remove("hidden");
          mapFrame.classList.add("hidden");
          mapLink.classList.add("hidden");
        }

        updateExportLinks(selectedCity);
      })
      .catch((err) => {
        logOutput.textContent = `Error: ${err.message}`;
      })
      .finally(() => {
        runBtn.disabled = false;
        runBtn.textContent = "Run Analysis";
      });
  });

  // ----------------------------
  // Update export links
  // ----------------------------
  function updateExportLinks(city) {
    exportData.href = `/api/export/latest/${city}/data`;
    exportPremium.href = `/api/export/latest/${city}/clusters`;
    exportLuxury.href = `/api/export/latest/${city}/luxury`;
    exportUltra.href = `/api/export/latest/${city}/ultra`;
    exportNeighborhoods.href = `/api/export/latest/${city}/neighborhoods`;
    exportLog.href = `/api/export/latest/${city}/log`;
  }
});
