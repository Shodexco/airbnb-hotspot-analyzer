document.addEventListener("DOMContentLoaded", async () => {
  const citySelect = document.getElementById("city-select");
  const gallery = document.getElementById("gallery");

  async function loadMapList() {
    const res = await fetch("/api/maps/list");
    const data = await res.json();
    return data.maps || {};
  }

  function renderCities(mapDict) {
    citySelect.innerHTML = `<option value="">Select a city</option>`;
    Object.keys(mapDict).forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c.toUpperCase();
      citySelect.appendChild(opt);
    });
  }

  function renderGallery(city, maps) {
    gallery.innerHTML = "";

    if (!city) {
      gallery.innerHTML = `<p class="section-hint">Select a city to view generated maps.</p>`;
      return;
    }

    if (!maps || maps.length === 0) {
      gallery.innerHTML = `<p class="section-hint">No maps found for ${city.toUpperCase()} yet. Run an analysis on the Dashboard first.</p>`;
      return;
    }

    maps.forEach((file) => {
      const card = document.createElement("div");
      card.className = "map-card glass-panel";

      card.innerHTML = `
        <iframe class="map-thumb" src="/maps/${file}"></iframe>

        <div class="map-card-info">
          <div class="map-name">${file}</div>

          <div class="map-actions">
            <a href="/maps/${file}" target="_blank" class="btn btn-primary">Open Full Screen</a>
            <a href="/maps/${file}" download class="btn btn-secondary">Download</a>
          </div>
        </div>
      `;

      gallery.appendChild(card);
    });
  }

  // Load all map metadata
  const mapDict = await loadMapList();
  renderCities(mapDict);

  citySelect.addEventListener("change", () => {
    const city = citySelect.value;
    renderGallery(city, mapDict[city]);
  });

  // Initial state
  renderGallery(null, null);
});
