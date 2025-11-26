document.addEventListener("DOMContentLoaded", () => {
  const citySelect = document.getElementById("city-select-hotspot");
  const tabs = document.querySelectorAll(".tab");
  const tabContent = document.getElementById("tab-content");

  let activeTab = "premium";

  // ------------------------------------
  // Helper: Get Active City
  // ------------------------------------
  function getActiveCity() {
    const v = citySelect.value;
    return v && v.trim() !== "" ? v.trim() : null;
  }

  // ------------------------------------
  // Load Cities
  // ------------------------------------
  fetch("/api/cities")
    .then((res) => res.json())
    .then((data) => {
      citySelect.innerHTML = "";

      if (!data.cities || data.cities.length === 0) {
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "No cities available";
        citySelect.appendChild(opt);
        tabContent.textContent = "No cities configured.";
        return;
      }

      data.cities.forEach((city) => {
        const opt = document.createElement("option");
        opt.value = city.code;
        opt.textContent = city.name;
        citySelect.appendChild(opt);
      });

      citySelect.value = data.cities[0].code;
      loadCurrentTab();
    })
    .catch((err) => {
      console.error("Error loading cities:", err);
      tabContent.textContent = "Could not load cities.";
    });

  // ------------------------------------
  // Handle tab switches
  // ------------------------------------
  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      tabs.forEach((t) => t.classList.remove("active"));
      tab.classList.add("active");

      activeTab = tab.getAttribute("data-tab");
      loadCurrentTab();
    });
  });

  citySelect.addEventListener("change", () => {
    loadCurrentTab();
  });

  // ------------------------------------
  // Fetch CSV via /api/export/latest/<city>/<dtype>
  // ------------------------------------
  function fetchCSV(dtype) {
    const city = getActiveCity();
    if (!city) return Promise.reject("No city selected");

    return fetch(`/api/export/latest/${city}/${dtype}`).then((res) => {
      if (!res.ok) throw new Error("File not found");
      return res.text();
    });
  }

  // ------------------------------------
  // Convert CSV -> table
  // ------------------------------------
  function csvToTable(csv) {
    const rows = csv.trim().split("\n").map((r) => r.split(","));
    if (!rows.length) return "<p>No data.</p>";

    let html = `<div class="table-wrapper"><table class="data-table">`;

    rows.forEach((row, i) => {
      if (i === 0) {
        html += "<thead><tr>";
        row.forEach((col) => (html += `<th>${col}</th>`));
        html += "</tr></thead><tbody>";
      } else {
        html += "<tr>";
        row.forEach((col) => (html += `<td>${col}</td>`));
        html += "</tr>";
      }
    });

    html += "</tbody></table></div>";
    return html;
  }

  // ------------------------------------
  // Load tab content
  // ------------------------------------
  function loadCurrentTab() {
    const city = getActiveCity();

    if (!city) {
      tabContent.textContent = "Select a city first.";
      return;
    }

    if (activeTab === "premium") loadPremium();
    else if (activeTab === "luxury") loadLuxury();
    else if (activeTab === "ultra") loadUltra();
    else if (activeTab === "neighborhoods") loadNeighborhoods();
    else if (activeTab === "listings") loadListings();
  }

  // --------------- Tabs ------------------

  function loadPremium() {
    tabContent.textContent = "Loading premium clusters...";
    fetchCSV("clusters")
      .then((csv) => (tabContent.innerHTML = csvToTable(csv)))
      .catch(() => {
        tabContent.textContent =
          "No premium clusters found. Run an analysis first.";
      });
  }

  function loadLuxury() {
    tabContent.textContent = "Loading luxury clusters...";
    fetchCSV("luxury")
      .then((csv) => (tabContent.innerHTML = csvToTable(csv)))
      .catch(() => {
        tabContent.textContent =
          "No luxury clusters found. Run an analysis first.";
      });
  }

  function loadUltra() {
    tabContent.textContent = "Loading ultra luxury clusters...";
    fetchCSV("ultra")
      .then((csv) => (tabContent.innerHTML = csvToTable(csv)))
      .catch(() => {
        tabContent.textContent =
          "No ultra luxury clusters found. Run an analysis first.";
      });
  }

  function loadNeighborhoods() {
    tabContent.textContent = "Loading neighborhood scores...";
    fetchCSV("neighborhoods")
      .then((csv) => (tabContent.innerHTML = csvToTable(csv)))
      .catch(() => {
        tabContent.textContent =
          "No neighborhood scores found. Run an analysis first.";
      });
  }

  function loadListings() {
    tabContent.textContent = "Loading listings...";
    fetchCSV("data")
      .then((csv) => (tabContent.innerHTML = csvToTable(csv)))
      .catch(() => {
        tabContent.textContent =
          "No listing data found. Run an analysis first.";
      });
  }
});
