document.addEventListener("DOMContentLoaded", () => {
  // =========================
  //   i18n
  // =========================
  const LANG_STORAGE_KEY = "podcasterapp_lang";
  const SUPPORTED_LANGS = ["es", "en"];
  let currentLang = "es";

  const translations = {
    es: {
      "header.title": "Mejora tu audio",
      "header.subtitle":
        "Sube tu grabación, elige cómo fue capturada y obtén un archivo listo para podcast.",

      "section1.title": "1. Configura tu procesamiento",
      "field.recording.label": "¿Cómo grabaste tu audio?",
      "field.recording.option.laptop": "Laptop / Celular",
      "field.recording.option.externalMic": "Micrófono externo (USB / interfaz)",
      "field.file.label": "Archivo de audio",

      "dropzone.text": "Arrastra tu archivo aquí o haz clic para seleccionarlo",
      "dropzone.selected": "Archivo seleccionado: {name}",
      "dropzone.limit":
        "Máximo 20 MB (aprox. 10 minutos de audio). Si tu archivo es más grande, sube un extracto o una parte del episodio.",
      "help.formats": "Formatos recomendados: WAV, MP3, M4A.",

      "actions.process": "Procesar audio",

      "status.uploading": "Subiendo archivo…",
      "status.processing": "Procesando audio…",
      "status.done": "Listo ✅",

      "status.error.noFile": "Primero selecciona un archivo de audio.",
      "status.error.invalidFile": "Ese archivo no parece ser audio válido.",
      "status.error.tooBig": "El archivo es demasiado pesado (máx. 20 MB).",
      "status.error.noServer":
        "No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.",
      "status.error.badRequest":
        "Faltan datos (archivo o modo). Reintenta seleccionando el archivo.",
      "status.error.generic":
        "Ocurrió un error al procesar el audio. Intenta nuevamente más tarde.",
      "status.error.download": "No se pudo descargar el archivo.",

      "section2.title": "2. Revisa tu resultado",
      "section2.original": "Original",
      "section2.processed": "Procesado",
      "actions.downloadAudio": "Descargar audio procesado",
      "actions.downloadReport": "Descargar informe detallado",

      "section3.title": "Planes (próximamente)",
      "pricing.subtitle":
        "Hoy estás usando la versión beta gratuita (plan Free). Más adelante podrás elegir entre estos planes, según el nivel de tu podcast y el tipo de acompañamiento que necesites.",
      "pricing.free.title": "Free",
      "pricing.free.price": "Gratis",
      "pricing.plus.title": "Plus",
      "pricing.plus.price": "USD $9 / mes",
      "pricing.pro.title": "Pro",
      "pricing.pro.price": "USD $55 / mes",
      "pricing.disclaimer":
        "Los precios y características son referenciales (valores aprox. en USD) y pueden ajustarse según uso real y feedback.",
      "filename.processedSuffix": "_PROCESADO.wav",
      "filename.reportSuffix": "_PROCESADO_report.txt",
      "filename.fallbackAudio": "audio_procesado.wav",
      "filename.fallbackReport": "informe_audio.txt",
    },
    en: {
      "header.title": "Improve your audio",
      "header.subtitle":
        "Upload your recording, choose how it was captured, and get a podcast-ready file.",

      "section1.title": "1. Configure your processing",
      "field.recording.label": "How did you record your audio?",
      "field.recording.option.laptop": "Laptop / Phone",
      "field.recording.option.externalMic": "External microphone (USB / interface)",
      "field.file.label": "Audio file",

      "dropzone.text": "Drag your file here or click to select it",
      "dropzone.selected": "Selected file: {name}",
      "dropzone.limit":
        "Max 20 MB (about 10 minutes of audio). If your file is bigger, upload a shorter excerpt.",
      "help.formats": "Recommended formats: WAV, MP3, M4A.",

      "actions.process": "Process audio",

      "status.uploading": "Uploading…",
      "status.processing": "Processing…",
      "status.done": "Done ✅",

      "status.error.noFile": "Please select an audio file first.",
      "status.error.invalidFile": "That file doesn't look like valid audio.",
      "status.error.tooBig": "File is too large (max 20 MB).",
      "status.error.noServer":
        "Could not reach the server. Check your connection and try again.",
      "status.error.badRequest":
        "Missing data (file or mode). Please re-select the file.",
      "status.error.generic":
        "Something went wrong while processing the audio. Please try again later.",
      "status.error.download": "Could not download the file.",

      "section2.title": "2. Review your result",
      "section2.original": "Original",
      "section2.processed": "Processed",
      "actions.downloadAudio": "Download processed audio",
      "actions.downloadReport": "Download detailed report",

      "section3.title": "Plans (coming soon)",
      "pricing.subtitle":
        "You're currently using the free beta version (Free plan). Later you'll be able to choose between these plans depending on your podcast level and the kind of support you need.",
      "pricing.free.title": "Free",
      "pricing.free.price": "Free",
      "pricing.plus.title": "Plus",
      "pricing.plus.price": "USD $9 / month",
      "pricing.pro.title": "Pro",
      "pricing.pro.price": "USD $55 / month",
      "pricing.disclaimer":
        "Prices and features are indicative (approx. USD) and may change based on real usage and feedback.",
      "filename.processedSuffix": "_PROCESSED.wav",
      "filename.reportSuffix": "_PROCESSED_report.txt",
      "filename.fallbackAudio": "processed_audio.wav",
      "filename.fallbackReport": "audio_report.txt",
    },
  };

  function t(key, vars = {}) {
    const table = translations[currentLang] || translations.es;
    let s = table[key] ?? key;
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, String(v));
    }
    return s;
  }

  function applyTranslations() {
    document.documentElement.lang = currentLang;
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      el.textContent = t(key);
    });
    updateLangToggleUI();
    updateDropzoneText(); // no pisar el nombre del archivo seleccionado
  }

  function getSavedLang() {
    try {
      const v = localStorage.getItem(LANG_STORAGE_KEY);
      return SUPPORTED_LANGS.includes(v) ? v : null;
    } catch {
      return null;
    }
  }

  function detectBrowserLang() {
    const nav = (navigator.language || "es").toLowerCase();
    return nav.startsWith("en") ? "en" : "es";
  }

  function setLanguage(lang, { persist = true } = {}) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = "es";
    currentLang = lang;
    if (persist) {
      try {
        localStorage.setItem(LANG_STORAGE_KEY, lang);
      } catch {}
    }
    applyTranslations();
  }

  function updateLangToggleUI() {
    const esBtn = document.getElementById("lang-es");
    const enBtn = document.getElementById("lang-en");
    if (!esBtn || !enBtn) return;
    const isEs = currentLang === "es";
    esBtn.classList.toggle("is-active", isEs);
    enBtn.classList.toggle("is-active", !isEs);
    esBtn.setAttribute("aria-pressed", String(isEs));
    enBtn.setAttribute("aria-pressed", String(!isEs));
  }

  function initLangToggle() {
    const esBtn = document.getElementById("lang-es");
    const enBtn = document.getElementById("lang-en");

    const initial = getSavedLang() || detectBrowserLang();
    setLanguage(initial, { persist: false });

    if (esBtn) esBtn.addEventListener("click", () => setLanguage("es"));
    if (enBtn) enBtn.addEventListener("click", () => setLanguage("en"));
  }

  // =========================
  //   App refs
  // =========================
  const dropzone = document.getElementById("dropzone");
  const dropzoneText = document.getElementById("dropzone-text");
  const fileInput = document.getElementById("file-input");
  const processBtn = document.getElementById("process-btn");
  const downloadAudioBtn = document.getElementById("download-btn");
  const downloadReportBtn = document.getElementById("download-report-btn");

  const playerOriginal = document.getElementById("player-original");
  const playerProcessed = document.getElementById("player-processed");

  const resultSection = document.getElementById("result-section");
  const statusEl = document.getElementById("status");
  const errorEl = document.getElementById("error-message");
  const analysisEl = document.getElementById("analysis");

  const API_ENDPOINT = "/api/process_audio";
  const MAX_MB = 20;

  let selectedFile = null;
  let processedFileUrl = "";
  let reportFileUrl = "";
  let lastOriginalFileName = "";

  function setStatus(text) {
    if (!statusEl) return;
    statusEl.textContent = text || "";
  }

  function setError(text) {
    if (!errorEl) return;
    errorEl.textContent = text || "";
    errorEl.style.display = text ? "block" : "none";
  }

  function updateDropzoneText() {
    if (!dropzoneText) return;
    if (selectedFile?.name) {
      dropzoneText.textContent = t("dropzone.selected", { name: selectedFile.name });
    } else {
      dropzoneText.textContent = t("dropzone.text");
    }
  }

  function resetEstado() {
    selectedFile = null;
    processedFileUrl = "";
    reportFileUrl = "";

    if (processBtn) processBtn.disabled = true;

    if (playerOriginal) {
      playerOriginal.removeAttribute("src");
      playerOriginal.load();
    }
    if (playerProcessed) {
      playerProcessed.removeAttribute("src");
      playerProcessed.load();
    }

    if (analysisEl) analysisEl.textContent = "";
    if (resultSection) resultSection.classList.add("hidden");

    if (dropzone) {
      dropzone.dataset.filename = "";
      dropzone.classList.remove("has-file");
      dropzone.classList.remove("is-dragover");
    }

    setError("");
    setStatus("");
    updateDropzoneText();
  }

  function isValidAudioFile(file) {
    if (!file) return false;
    const typeOk = (file.type || "").startsWith("audio/");
    const name = (file.name || "").toLowerCase();
    const extOk = [
      ".wav",
      ".mp3",
      ".m4a",
      ".aac",
      ".flac",
      ".ogg",
      ".opus",
      ".webm",
      ".aiff",
      ".aif",
    ].some((ext) => name.endsWith(ext));
    return typeOk || extOk;
  }

  function validateFile(file) {
    if (!file) return { ok: false, key: "status.error.noFile" };
    if (!isValidAudioFile(file)) return { ok: false, key: "status.error.invalidFile" };
    const mb = file.size / (1024 * 1024);
    if (mb > MAX_MB) return { ok: false, key: "status.error.tooBig" };
    return { ok: true };
  }

  function handleSelectedFile(file) {
    const v = validateFile(file);
    if (!v.ok) {
      setError(t(v.key));
      return;
    }

    selectedFile = file;
    lastOriginalFileName = file.name;

    if (processBtn) processBtn.disabled = false;

    if (dropzone) {
      dropzone.dataset.filename = file.name;
      dropzone.classList.add("has-file");
    }

    setError("");
    updateDropzoneText();
  }

  function getSelectedModeOrDefault() {
    const el = document.querySelector('input[name="modo"]:checked');
    return el ? el.value : "LAPTOP_CELULAR";
  }

  function renderAnalysis(analysis) {
    if (!analysisEl) return;
    if (!analysis) {
      analysisEl.textContent = "";
      return;
    }
    if (typeof analysis === "string") {
      analysisEl.textContent = analysis;
      return;
    }
    try {
      analysisEl.textContent = JSON.stringify(analysis, null, 2);
    } catch {
      analysisEl.textContent = String(analysis);
    }
  }

  function triggerDownload(url, filename) {
    try {
      const a = document.createElement("a");
      a.href = url;
      a.download = filename || "";
      document.body.appendChild(a);
      a.click();
      a.remove();
    } catch {
      setError(t("status.error.download"));
    }
  }

  // =========================
  //   UI events
  // =========================
  if (fileInput) {
    // clave: permitir re-seleccionar el mismo archivo
    fileInput.addEventListener("click", () => {
      fileInput.value = "";
    });

    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleSelectedFile(file);
    });
  }

  if (dropzone) {
    dropzone.addEventListener("click", (e) => {
      if (!fileInput) return;
      if (e.target === fileInput) return;
      fileInput.click();
    });

    ["dragenter", "dragover"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.add("is-dragover");
      });
    });

    ["dragleave", "drop"].forEach((ev) => {
      dropzone.addEventListener(ev, (e) => {
        e.preventDefault();
        e.stopPropagation();
        dropzone.classList.remove("is-dragover");
      });
    });

    dropzone.addEventListener("drop", (e) => {
      const file = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) handleSelectedFile(file);
    });
  }

  if (processBtn) {
    processBtn.addEventListener("click", async () => {
      const v = validateFile(selectedFile);
      if (!v.ok) {
        setError(t(v.key));
        return;
      }

      setError("");
      setStatus(t("status.uploading"));
      processBtn.disabled = true;

      const modeValue = getSelectedModeOrDefault();

      try {
        const formData = new FormData();

        // ✅ backend espera audio_file + mode (obligatorios)
        formData.append("audio_file", selectedFile);
        formData.append("mode", modeValue);

        setStatus(t("status.processing"));

        const resp = await fetch(API_ENDPOINT, {
          method: "POST",
          body: formData,
        });

        if (!resp.ok) {
          let detail = "";
          try {
            const errData = await resp.json();
            detail = errData?.detail || "";
          } catch {}

          if (resp.status === 413) {
            setError(detail || t("status.error.tooBig"));
          } else if (resp.status === 422) {
            setError(detail || t("status.error.badRequest"));
          } else {
            setError(detail || t("status.error.generic"));
          }
          setStatus("");
          return;
        }

        const data = await resp.json();

        const originalUrl = data.original_url;
        const processedUrl = data.processed_url;
        const reportUrl = data.report_url;

        processedFileUrl = processedUrl || "";
        reportFileUrl = reportUrl || "";
        lastOriginalFileName = data.original_filename || lastOriginalFileName;

        if (playerOriginal && originalUrl) {
          playerOriginal.src = originalUrl;
          playerOriginal.load();
        }
        if (playerProcessed && processedUrl) {
          playerProcessed.src = processedUrl;
          playerProcessed.load();
        }

        renderAnalysis(data.analysis);

        if (resultSection) resultSection.classList.remove("hidden");
        setStatus(t("status.done"));
      } catch (err) {
        console.error(err);
        setError(t("status.error.noServer"));
        setStatus("");
      } finally {
        processBtn.disabled = false;
      }
    });
  }

  if (downloadAudioBtn) {
    downloadAudioBtn.addEventListener("click", () => {
      if (!processedFileUrl) {
        setError(t("status.error.generic"));
        return;
      }
      const base = (lastOriginalFileName || "").replace(/\.[^/.]+$/, "");
      const suggested = base
        ? `${base}${t("filename.processedSuffix")}`
        : t("filename.fallbackAudio");
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

  // =========================
  //   Init
  // =========================
  initLangToggle();
  resetEstado();
  applyTranslations();
});
