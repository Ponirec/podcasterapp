// =========================
//  i18n simple ES/EN
// =========================

const I18N = {
  es: {
    // Header
    "hero.title": "Mejora tu audio",
    "hero.subtitle":
      "Sube tu grabación, elige cómo fue capturada y obtén un archivo listo para podcast.",

    // Section 1
    "section1.title": "1. Configura tu procesamiento",
    "section1.subtitle": "¿Cómo grabaste tu audio?",
    "field.recording.label": "¿Cómo grabaste tu audio?",
    "field.recording.option.laptop": "Laptop / Celular",
    "field.recording.option.externalMic": "Micrófono externo (USB / Interfaz)",
    "field.file.label": "Archivo de audio",
    "dropzone.placeholder": "Arrastra tu archivo aquí o haz clic para seleccionarlo",
    "dropzone.limit":
      "Máximo 20 MB (aprox. 10 minutos de audio). Si tu archivo es más grande, sube un extracto o una parte del episodio.",
    "formats.recommended": "Formatos recomendados: WAV, MP3, M4A.",
    "btn.process": "Procesar audio",

    // Status / errors
    "status.uploading": "Subiendo archivo...",
    "status.processing": "Procesando audio...",
    "status.done": "¡Listo!",
    "status.error.generic":
      "Ocurrió un error al procesar el audio. Intenta nuevamente más tarde.",
    "status.error.noFile": "Selecciona un archivo primero.",
    "status.error.fileTooBig":
      "El archivo supera el límite de 20 MB. Sube un extracto o una parte del episodio.",
    "status.error.noServer": "No se pudo conectar al servidor.",
    "status.selected": "Archivo seleccionado:",

    // Section 2 (result)
    "section2.title": "2. Revisa tu resultado",
    "player.original": "player.original",
    "player.processed": "player.processed",
    "btn.downloadAudio": "Descargar audio procesado",
    "btn.downloadReport": "Descargar informe detallado",

    // Filename helpers
    "filename.processedSuffix": "_processed.wav",
    "filename.reportSuffix": "_report.json",
    "filename.fallbackProcessed": "processed.wav",
    "filename.fallbackReport": "report.json",

    // Pricing
    "pricing.title": "Planes (próximamente)",
    "pricing.subtitle":
      "Hoy estás usando la versión beta gratuita (plan Free). Más adelante podrás elegir entre estos planes, según el nivel de tu podcast y el tipo de acompañamiento que necesites.",
    "pricing.free": "Gratis",
    "pricing.plus": "USD $9 / mes",
    "pricing.pro": "USD $55 / mes",

    "pricing.free.tagline": "Ideal para probar la app y mejorar tus primeras grabaciones.",
    "pricing.plus.tagline": "Para podcasters que suben episodios completos.",
    "pricing.pro.tagline": "Asesoría 1:1 + mastering profesional.",

    "pricing.btn.soon": "Disponible pronto",

    "pricing.note.free": "Esto es lo que estás usando ahora mismo.",
    "pricing.note.plus": "Se ajustará según el feedback de esta beta.",
    "pricing.note.pro": "Primero se abrirá para un grupo reducido de creadores.",

    "pricing.free.f1": "Procesamiento automático de audio",
    "pricing.free.f2": "Informe de calidad con recomendaciones básicas",

    "pricing.plus.f1": "Todo lo del plan Free",
    "pricing.plus.f2": "Archivos hasta ~60 minutos (o ~100 MB)",

    "pricing.pro.f1": "Todo lo del plan Plus",
    "pricing.pro.f2": "1 sesión mensual 1:1 para revisar tu sonido y setup",
    "pricing.pro.f3": "1 episodio al mes masterizado manualmente en estudio",
    "pricing.pro.f4": "Descuento en masters adicionales",
    "pricing.pro.f5": "Ideal para podcasters que quieren subir de nivel",

    "pricing.disclaimer":
      "Los precios y características son referenciales (valores aprox. en USD) y pueden ajustarse según uso real y feedback.",
  },

  en: {
    // Header
    "hero.title": "Improve your audio",
    "hero.subtitle":
      "Upload your recording, choose how it was captured, and get a podcast-ready file.",

    // Section 1
    "section1.title": "1. Configure your processing",
    "section1.subtitle": "How did you record your audio?",
    "field.recording.label": "How did you record your audio?",
    "field.recording.option.laptop": "Laptop / Phone",
    "field.recording.option.externalMic": "External microphone (USB / interface)",
    "field.file.label": "Audio file",
    "dropzone.placeholder": "Drag your file here or click to select it",
    "dropzone.limit":
      "Max 20 MB (about 10 minutes of audio). If your file is larger, upload an excerpt or a part of the episode.",
    "formats.recommended": "Recommended formats: WAV, MP3, M4A.",
    "btn.process": "Process audio",

    // Status / errors
    "status.uploading": "Uploading file...",
    "status.processing": "Processing audio...",
    "status.done": "Done!",
    "status.error.generic":
      "There was an error processing the audio. Please try again later.",
    "status.error.noFile": "Please select a file first.",
    "status.error.fileTooBig":
      "File exceeds the 20 MB limit. Upload an excerpt or a part of the episode.",
    "status.error.noServer": "Could not connect to the server.",
    "status.selected": "Selected file:",

    // Section 2 (result)
    "section2.title": "2. Review your result",
    "player.original": "player.original",
    "player.processed": "player.processed",
    "btn.downloadAudio": "Download processed audio",
    "btn.downloadReport": "Download detailed report",

    // Filename helpers
    "filename.processedSuffix": "_processed.wav",
    "filename.reportSuffix": "_report.json",
    "filename.fallbackProcessed": "processed.wav",
    "filename.fallbackReport": "report.json",

    // Pricing
    "pricing.title": "Plans (coming soon)",
    "pricing.subtitle":
      "You're currently using the free beta version (Free plan). Later you'll be able to choose between these plans depending on your podcast level and the kind of support you need.",
    "pricing.free": "Free",
    "pricing.plus": "USD $9 / month",
    "pricing.pro": "USD $55 / month",

    "pricing.free.tagline": "Great for testing the app and improving your first recordings.",
    "pricing.plus.tagline": "For podcasters uploading full episodes.",
    "pricing.pro.tagline": "1:1 support + professional mastering.",

    "pricing.btn.soon": "Available soon",

    "pricing.note.free": "This is what you're using right now.",
    "pricing.note.plus": "Will be adjusted based on beta feedback.",
    "pricing.note.pro": "Will open first to a small group of creators.",

    "pricing.free.f1": "Automatic audio processing",
    "pricing.free.f2": "Quality report with basic recommendations",

    "pricing.plus.f1": "Everything in Free",
    "pricing.plus.f2": "Files up to ~60 minutes (or ~100 MB)",

    "pricing.pro.f1": "Everything in Plus",
    "pricing.pro.f2": "1 monthly 1:1 session to review your sound and setup",
    "pricing.pro.f3": "1 episode/month manually mastered in studio",
    "pricing.pro.f4": "Discount on additional masters",
    "pricing.pro.f5": "Ideal if you want to level up",

    "pricing.disclaimer":
      "Prices and features are indicative (approx. USD values) and may change based on real usage and feedback.",
  },
};

let currentLang = "en";

function t(key) {
  const langDict = I18N[currentLang] || I18N.en;
  return langDict[key] ?? key;
}

function setLang(lang) {
  currentLang = lang === "es" ? "es" : "en";
  localStorage.setItem("lang", currentLang);
  applyTranslations();
}

function applyTranslations(root = document) {
  // 1) Translate explicit markers: data-i18n / data-i18n-* attributes
  root.querySelectorAll("[data-i18n]").forEach((el) => {
    const key = (el.getAttribute("data-i18n") || "").trim();
    if (!key) return;
    const value = t(key);
    if (value !== key) el.textContent = value;
  });

  root.querySelectorAll("[data-i18n-html]").forEach((el) => {
    const key = (el.getAttribute("data-i18n-html") || "").trim();
    if (!key) return;
    const value = t(key);
    if (value !== key) el.innerHTML = value;
  });

  root.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
    const key = (el.getAttribute("data-i18n-placeholder") || "").trim();
    if (!key) return;
    const value = t(key);
    if (value !== key) el.setAttribute("placeholder", value);
  });

  // 2) Safety net: if some elements were left with raw i18n keys as text
  // (e.g., "pricing.free.tagline"), translate them too.
  // This prevents "pricing.*" strings from leaking to the UI even if
  // an element is missing data-i18n attributes.
  const keyLike = /^[a-z0-9]+(\.[a-z0-9_-]+)+$/i;
  root.querySelectorAll("body *:not(script):not(style)").forEach((el) => {
    if (
      el.hasAttribute("data-i18n") ||
      el.hasAttribute("data-i18n-html") ||
      el.hasAttribute("data-i18n-placeholder")
    )
      return;
    if (el.children && el.children.length > 0) return; // avoid clobbering complex nodes
    const raw = (el.textContent || "").trim();
    if (!raw || !keyLike.test(raw)) return;
    const value = t(raw);
    if (value !== raw) el.textContent = value;
  });

  updateLangToggleUI();
}

function updateLangToggleUI() {
  const btnES = document.getElementById("btnLangES");
  const btnEN = document.getElementById("btnLangEN");
  if (!btnES || !btnEN) return;
  if (currentLang === "es") {
    btnES.classList.add("active");
    btnEN.classList.remove("active");
  } else {
    btnEN.classList.add("active");
    btnES.classList.remove("active");
  }
}

function initLangToggle() {
  const saved = localStorage.getItem("lang");
  if (saved === "es" || saved === "en") currentLang = saved;
  else currentLang = (navigator.language || "").toLowerCase().startsWith("es")
    ? "es"
    : "en";

  const btnES = document.getElementById("btnLangES");
  const btnEN = document.getElementById("btnLangEN");

  if (btnES) btnES.addEventListener("click", () => setLang("es"));
  if (btnEN) btnEN.addEventListener("click", () => setLang("en"));
}

// =========================
//   APP LOGIC
// =========================

let lastOriginalFileName = "";
let processedFileUrl = "";
let reportFileUrl = "";

function setStatus(msg) {
  const el = document.getElementById("statusText");
  if (el) el.textContent = msg;
}

function setError(msg) {
  const el = document.getElementById("errorText");
  if (el) el.textContent = msg;
}

function resetEstado() {
  processedFileUrl = "";
  reportFileUrl = "";
  lastOriginalFileName = "";
  setStatus("");
  setError("");
}

function triggerDownload(url, filename) {
  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "";
  document.body.appendChild(a);
  a.click();
  a.remove();
}

// =========================
//   DOM READY
// =========================

document.addEventListener("DOMContentLoaded", () => {
  const fileInput = document.getElementById("audioFile");
  const dropzone = document.getElementById("dropzone");
  const dropzoneText = document.getElementById("dropzoneText");
  const processBtn = document.getElementById("processBtn");

  const playerOriginal = document.getElementById("playerOriginal");
  const playerProcessed = document.getElementById("playerProcessed");

  const downloadAudioBtn = document.getElementById("downloadAudioBtn");
  const downloadReportBtn = document.getElementById("downloadReportBtn");

  // Init language
  initLangToggle();
  applyTranslations();

  // Dropzone UI helpers
  function setDropzoneTextSelected(name) {
    if (!dropzoneText) return;
    dropzoneText.textContent = `${t("status.selected")} ${name}`;
  }

  function setDropzoneTextDefault() {
    if (!dropzoneText) return;
    dropzoneText.textContent = t("dropzone.placeholder");
  }

  // Initial dropzone text
  setDropzoneTextDefault();

  // File selection
  function handleFile(file) {
    if (!file) return;

    resetEstado();
    lastOriginalFileName = file.name || "";

    // 20 MB limit
    const maxBytes = 20 * 1024 * 1024;
    if (file.size > maxBytes) {
      setError(t("status.error.fileTooBig"));
      if (fileInput) fileInput.value = "";
      setDropzoneTextDefault();
      return;
    }

    setDropzoneTextSelected(file.name);

    // Show original player
    if (playerOriginal) {
      const url = URL.createObjectURL(file);
      playerOriginal.src = url;
    }
  }

  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      handleFile(file);
    });
  }

  // Drag & drop
  if (dropzone) {
    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dragover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      if (fileInput && file) fileInput.files = e.dataTransfer.files;
      handleFile(file);
    });

    dropzone.addEventListener("click", () => {
      if (fileInput) fileInput.click();
    });
  }

  // Processing
  async function processAudio(file, recordingType) {
    setError("");
    setStatus(t("status.uploading"));

    const formData = new FormData();
    formData.append("file", file);
    formData.append("recording_type", recordingType);

    const resp = await fetch("/process", {
      method: "POST",
      body: formData,
    });

    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const data = await resp.json();

    // expected: { processed_url, report_url }
    processedFileUrl = data.processed_url || "";
    reportFileUrl = data.report_url || "";

    return data;
  }

  function getRecordingType() {
    const rbLaptop = document.getElementById("recLaptop");
    const rbExternal = document.getElementById("recExternal");
    if (rbExternal && rbExternal.checked) return "external_mic";
    if (rbLaptop && rbLaptop.checked) return "laptop_phone";
    return "laptop_phone";
  }

  if (processBtn) {
    processBtn.addEventListener("click", async () => {
      try {
        setError("");
        if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
          setError(t("status.error.noFile"));
          return;
        }

        const file = fileInput.files[0];
        const recordingType = getRecordingType();

        processBtn.disabled = true;
        setStatus(t("status.processing"));

        await processAudio(file, recordingType);

        setStatus(t("status.done"));

        // Update processed player
        if (playerProcessed && processedFileUrl) {
          playerProcessed.src = processedFileUrl;
        }

        // Enable download buttons
        if (downloadAudioBtn) downloadAudioBtn.disabled = !processedFileUrl;
        if (downloadReportBtn) downloadReportBtn.disabled = !reportFileUrl;
      } catch (err) {
        console.error(err);
        setError(t("status.error.generic"));
        setStatus("");
      } finally {
        if (processBtn) processBtn.disabled = false;
      }
    });
  }

  // Downloads
  if (downloadAudioBtn) {
    downloadAudioBtn.addEventListener("click", () => {
      if (!processedFileUrl) {
        setError(t("status.error.generic"));
        return;
      }
      const base = (lastOriginalFileName || "").replace(/\.[^/.]+$/, "");
      const suggested = base
        ? `${base}${t("filename.processedSuffix")}`
        : t("filename.fallbackProcessed");
      triggerDownload(processedFileUrl, suggested);
    });
  }

  if (downloadReportBtn) {
    downloadReportBtn.addEventListener("click", () => {
      if (!reportFileUrl) {
        setError(t("status.error.generic"));
        return;
      }
      const base = (lastOriginalFileName || "").replace(/\.[^/.]+$/, "");
      const suggested = base
        ? `${base}${t("filename.reportSuffix")}`
        : t("filename.fallbackReport");
      triggerDownload(reportFileUrl, suggested);
    });
  }
});
