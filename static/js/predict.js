// predict.js — handles the prediction form: validation, submission, result rendering

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("predictForm");
  const predictBtn = document.getElementById("predictBtn");
  const resetBtn = document.getElementById("resetBtn");
  const resultPlaceholder = document.getElementById("resultPlaceholder");
  const resultCard = document.getElementById("resultCard");
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toastMsg");

  // Validation ranges must mirror the server-side ranges in app.py
  const RANGES = {
    Age:        { min: 0,   max: 120 },
    Gender:     { min: 0,   max: 1 },
    Hemoglobin: { min: 3,   max: 20 },
    RBC:        { min: 1,   max: 8 },
    WBC:        { min: 1,   max: 30 },
    HCT:        { min: 10,  max: 65 },
    MCV:        { min: 50,  max: 130 },
    MCH:        { min: 10,  max: 45 },
    MCHC:       { min: 20,  max: 40 },
    Platelets:  { min: 10,  max: 800 },
  };

  function getFieldWrapper(input) {
    return input.closest(".field");
  }

  function validateField(input) {
    const wrapper = getFieldWrapper(input);
    const name = input.name;
    const range = RANGES[name];
    const rawValue = input.value.trim();

    let isValid = rawValue !== "";
    if (isValid && range) {
      const num = parseFloat(rawValue);
      isValid = !isNaN(num) && num >= range.min && num <= range.max;
    }

    wrapper.classList.remove("valid", "invalid");
    wrapper.classList.add(isValid ? "valid" : "invalid");
    return isValid;
  }

  // Live validation as the user types / selects
  form.querySelectorAll("input, select").forEach((input) => {
    input.addEventListener("input", () => {
      if (getFieldWrapper(input).classList.contains("invalid")) {
        validateField(input);
      }
    });
    input.addEventListener("blur", () => validateField(input));
  });

  function validateAll() {
    let allValid = true;
    form.querySelectorAll("input, select").forEach((input) => {
      if (!validateField(input)) allValid = false;
    });
    return allValid;
  }

  function showToast(message) {
    toastMsg.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), 3200);
  }

  function setLoading(isLoading) {
    predictBtn.classList.toggle("loading", isLoading);
    predictBtn.disabled = isLoading;
    resetBtn.disabled = isLoading;
  }

  function collectFormData() {
    const data = {};
    form.querySelectorAll("input, select").forEach((input) => {
      data[input.name] = input.value;
    });
    return data;
  }

  const ICONS = {
    positive: `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L14.7 3.86a2 2 0 00-3.4 0z"/></svg>`,
    negative: `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2"><path d="M20 6L9 17l-5-5"/></svg>`,
  };

  function renderList(ulEl, items) {
    ulEl.innerHTML = "";
    items.forEach((text) => {
      const li = document.createElement("li");
      li.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" style="margin-top:3px;"><path d="M20 6L9 17l-5-5"/></svg><span>${text}</span>`;
      ulEl.appendChild(li);
    });
  }

  function renderResult(result) {
    const isPositive = result.anemia_detected;

    resultCard.classList.remove("positive", "negative");
    resultCard.classList.add(isPositive ? "positive" : "negative");

    document.getElementById("resultIcon").innerHTML = isPositive ? ICONS.positive : ICONS.negative;
    document.getElementById("resultTitle").textContent = result.prediction;
    document.getElementById("resultHealthStatus").textContent = "Health Status: " + result.health_status;
    document.getElementById("confidenceValue").textContent = result.confidence + "%";

    renderList(document.getElementById("precautionsList"), result.recommendations.precautions);
    renderList(document.getElementById("dietList"), result.recommendations.diet);
    document.getElementById("doctorAdvice").textContent = result.recommendations.doctor_advice;

    resultPlaceholder.style.display = "none";
    resultCard.classList.add("show");

    // Animate confidence bar after paint
    const bar = document.getElementById("confidenceBar");
    bar.style.width = "0%";
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        bar.style.width = result.confidence + "%";
      });
    });

    resultCard.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    if (!validateAll()) {
      showToast("Please correct the highlighted fields before submitting.");
      const firstInvalid = form.querySelector(".field.invalid input, .field.invalid select");
      if (firstInvalid) firstInvalid.focus();
      return;
    }

    setLoading(true);

    try {
      const response = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collectFormData()),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        throw new Error(data.error || "Prediction failed. Please check your inputs.");
      }

      renderResult(data);
    } catch (err) {
      showToast(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  });

  resetBtn.addEventListener("click", () => {
    form.reset();
    form.querySelectorAll(".field").forEach((wrapper) => {
      wrapper.classList.remove("valid", "invalid");
    });
    resultCard.classList.remove("show", "positive", "negative");
    resultPlaceholder.style.display = "block";
  });
});
