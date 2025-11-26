document.addEventListener("DOMContentLoaded", () => {
  const citiesBtn = document.getElementById("test-cities-btn");
  const analyzeForm = document.getElementById("api-analyze-form");
  const cityInput = document.getElementById("api-city-input");
  const thresholdInput = document.getElementById("api-threshold-input");
  const responseBox = document.getElementById("api-response");

  citiesBtn?.addEventListener("click", () => {
    responseBox.textContent = "Loading /api/cities...";
    fetch("/api/cities")
      .then((res) => res.json())
      .then((data) => {
        responseBox.textContent = JSON.stringify(data, null, 2);
      })
      .catch((err) => {
        responseBox.textContent = `Error: ${err.message}`;
      });
  });

  analyzeForm?.addEventListener("submit", (e) => {
    e.preventDefault();
    const city = cityInput.value.trim();
    const threshold = parseFloat(thresholdInput.value || "200");

    if (!city) {
      alert("City code is required (e.g. nyc).");
      return;
    }

    responseBox.textContent = "Posting to /api/analyze...";

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
        responseBox.textContent = JSON.stringify(data, null, 2);
      })
      .catch((err) => {
        responseBox.textContent = `Error: ${err.message}`;
      });
  });
});
