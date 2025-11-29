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
  // Security: Escape HTML to prevent XSS
  // ------------------------------------
  function escapeHTML(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // ------------------------------------
  // Parse CSV properly (handles quoted fields with commas)
  // ------------------------------------
  function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;

    for (let i = 0; i < line.length; i++) {
      const char = line[i];
      const nextChar = line[i + 1];

      if (char === '"') {
        if (inQuotes && nextChar === '"') {
          // Escaped quote
          current += '"';
          i++; // Skip next quote
        } else {
          // Toggle quote state
          inQuotes = !inQuotes;
        }
      } else if (char === ',' && !inQuotes) {
        // Field separator
        result.push(current.trim());
        current = '';
      } else {
        current += char;
      }
    }

    // Add the last field
    result.push(current.trim());
    return result;
  }

  // ------------------------------------
  // Convert CSV -> table (with pagination and security)
  // ------------------------------------
  function csvToTable(csv, maxRows = 1000) {
    // Normalize line endings (handles Windows \r\n and Mac \r)
    const normalized = csv.replace(/\r\n/g, '\n').replace(/\r/g, '\n');
    const lines = normalized.trim().split("\n");

    if (!lines.length) return "<p>No data.</p>";

    const rows = lines.map(line => parseCSVLine(line));
    const totalRows = rows.length - 1; // Exclude header
    const hasMore = totalRows > maxRows;
    const displayRows = hasMore ? rows.slice(0, maxRows + 1) : rows;

    let html = '';

    // Show warning if data is truncated
    if (hasMore) {
      html += `<div style="padding: 12px; margin-bottom: 16px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; color: #856404;">
        <strong>⚠️ Large Dataset:</strong> Showing first ${maxRows.toLocaleString()} of ${totalRows.toLocaleString()} rows for performance.
      </div>`;
    }

    html += `<div class="table-wrapper"><table class="data-table">`;

    displayRows.forEach((row, i) => {
      if (i === 0) {
        html += "<thead><tr>";
        row.forEach((col) => (html += `<th>${escapeHTML(col)}</th>`));
        html += "</tr></thead><tbody>";
      } else {
        html += "<tr>";
        row.forEach((col) => (html += `<td>${escapeHTML(col)}</td>`));
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
