document.addEventListener("DOMContentLoaded", () => {
  // =========================
  //   i18n (ES/EN)
  // =========================
  const SUPPORTED_LANGS = ["es", "en"];
  const LANG_STORAGE_KEY = "podcasterapp_lang";
  let currentLang = "es";

  const I18N = {
    es: {
      "head.title": "Limpia tu audio",
      "lang.es": "ES",
      "lang.en": "EN",

      "header.title": "Mejora tu audio",
      "header.subtitle":
        "Sube tu grabación, elige cómo fue capturada y obtén un archivo listo para podcast.",

      "s1.title": "1. Configura tu procesamiento",
      "s1.capture.label": "¿Cómo grabaste tu audio?",
      "s1.capture.laptop": "Laptop / Celular",
      "s1.capture.external": "Micrófono externo (USB / interfaz)",
      "s1.file.label": "Archivo de audio",

      "dropzone.text": "Arrastra tu archivo aquí o haz clic para seleccionarlo",
      "dropzone.selected": "Archivo seleccionado: {name}",
      "dropzone.max":
        "Máximo 20 MB (aprox. 10 minutos de audio). Si tu archivo es más grande, sube un extracto o una parte del episodio.",
      "help.formats": "Formatos recomendados: WAV, MP3, M4A.",

      "actions.process": "Procesar audio",
      "note.beta":
        "Más adelante lanzaremos planes Plus y Pro con episodios completos y asesoría 1:1. Por ahora esta versión es gratuita para pruebas.",

      "s2.title": "2. Revisa tu resultado",
      "s2.original": "Original",
      "s2.processed": "Procesado",
      "actions.downloadAudio": "Descargar audio procesado",
      "actions.downloadReport": "Descargar informe detallado",

      "pricing.title": "Planes (próximamente)",
      "pricing.intro":
        "Hoy estás usando la versión beta gratuita (plan Free). Más adelante podrás elegir entre estos planes, según el nivel de tu podcast y el tipo de acompañamiento que necesites.",

      "pricing.free.name": "Free",
      "pricing.free.price": "Gratis",
      "pricing.free.tagline": "Ideal para probar la app y mejorar tus primeras grabaciones.",
      "pricing.free.li1": "Procesamiento automático de audio",
      "pricing.free.li2": "Informe de calidad con recomendaciones básicas",
      "pricing.free.li3": "Archivos hasta ~20 MB (≈10 minutos)",
      "pricing.free.li4": "Versión beta: sin soporte personalizado",
      "pricing.free.btn": "Plan actual",
      "pricing.free.note": "Esto es lo que estás usando ahora mismo.",

      "pricing.plus.name": "Plus",
      "pricing.plus.price": "USD $9 / mes",
      "pricing.plus.tagline": "Para podcasters que suben episodios completos.",
      "pricing.plus.li1": "Todo lo del plan Free",
      "pricing.plus.li2": "Archivos hasta ~60 minutos (o ~100 MB)",
      "pricing.plus.li3": "Hasta 20 procesamientos al mes (ajustable)",
      "pricing.plus.li4": "Informe más detallado por episodio",
      "pricing.plus.li5": "Prioridad suave en el procesamiento",
      "pricing.plus.btn": "Disponible pronto",
      "pricing.plus.note": "Se ajustará según el feedback de esta beta.",

      "pricing.pro.name": "Pro",
      "pricing.pro.price": "USD $55 / mes",
      "pricing.pro.tagline": "Asesoría 1:1 + mastering profesional.",
      "pricing.pro.li1": "Todo lo del plan Plus",
      "pricing.pro.li2": "1 sesión mensual 1:1 para revisar tu sonido y setup",
      "pricing.pro.li3": "1 episodio al mes masterizado manualmente en estudio",
      "pricing.pro.li4": "Descuento en masters adicionales",
      "pricing.pro.li5": "Ideal para podcasters que quieren subir de nivel",
      "pricing.pro.btn": "Disponible pronto",
      "pricing.pro.note": "Primero se abrirá para un grupo reducido de creadores.",

      "pricing.disclaimer.before": "Los precios y características son",
      "pricing.disclaimer.strong": "referenciales",
      "pricing.disclaimer.after":
        "(valores aprox. en USD) y pueden ajustarse según el uso real y el feedback que recibamos durante esta etapa beta.",

      // Estados / errores dinámicos
      "status.idle": "",
      "status.uploading": "Subiendo audio…",
      "status.processing": "Procesando audio…",
      "status.done": "Procesamiento completado.",
      "status.error.noServer":
        "No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.",
      "status.error.generic":
        "Ocurrió un error al procesar el audio. Intenta nuevamente más tarde.",
      "status.error.noFile": "Primero selecciona un archivo de audio.",
      "status.error.invalidFile": "Archivo no válido. Sube un audio (mp3, wav, m4a, etc).",
      "status.error.tooBig":
        "El archivo es demasiado pesado. Prueba con un audio más corto (máx. 20 MB).",
      "status.error.download": "No se pudo descargar el archivo.",

      // Nombres de descarga
      "filename.processedSuffix": "_PROCESADO.wav",
      "filename.reportSuffix": "_PROCESADO_report.txt",
      "filename.fallbackAudio": "audio_procesado.wav",
      "filename.fallbackReport": "informe_audio.txt",
    },

    en: {
      "head.title": "Clean your audio",
      "lang.es": "ES",
      "lang.en": "EN",

      "header.title": "Improve your audio",
      "header.subtitle":
        "Upload your recording, choose how it was captured, and get a podcast-ready file.",

      "s1.title": "1. Configure your processing",
      "s1.capture.label": "How did you record your audio?",
      "s1.capture.laptop": "Laptop / Phone",
      "s1.capture.external": "External microphone (USB / interface)",
      "s1.file.label": "Audio file",

      "dropzone.text": "Drag your file here or click to select it",
      "dropzone.selected": "Selected file: {name}",
      "dropzone.max":
        "Max 20 MB (about 10 minutes). If your file is larger, upload a short excerpt or part of the episode.",
      "help.formats": "Recommended formats: WAV, MP3, M4A.",

      "actions.process": "Process audio",
      "note.beta":
        "Later we’ll launch Plus and Pro plans with full episodes and 1:1 support. For now, this version is free for testing.",

      "s2.title": "2. Review your result",
      "s2.original": "Original",
      "s2.processed": "Processed",
      "actions.downloadAudio": "Download processed audio",
      "actions.downloadReport": "Download detailed report",

      "pricing.title": "Plans (coming soon)",
      "pricing.intro":
        "You’re currently using the free beta version (Free plan). Later you’ll be able to choose between these plans depending on your podcast level and the kind of support you need.",

      "pricing.free.name": "Free",
      "pricing.free.price": "Free",
      "pricing.free.tagline": "Great for testing the app and improving your first recordings.",
      "pricing.free.li1": "Automatic audio processing",
      "pricing.free.li2": "Quality report with basic recommendations",
      "pricing.free.li3": "Files up to ~20 MB (≈10 minutes)",
      "pricing.free.li4": "Beta: no personalized support",
      "pricing.free.btn": "Current plan",
      "pricing.free.note": "This is what you’re using right now.",

      "pricing.plus.name": "Plus",
      "pricing.plus.price": "USD $9 / month",
      "pricing.plus.tagline": "For podcasters uploading full episodes.",
      "pricing.plus.li1": "Everything in Free",
      "pricing.plus.li2": "Files up to ~60 minutes (or ~100 MB)",
      "pricing.plus.li3": "Up to 20 processes per month (adjustable)",
      "pricing.plus.li4": "More detailed report per episode",
      "pricing.plus.li5": "Soft priority in processing",
      "pricing.plus.btn": "Available soon",
      "pricing.plus.note": "Will be adjusted based on beta feedback.",

      "pricing.pro.name": "Pro",
      "pricing.pro.price": "USD $55 / month",
      "pricing.pro.tagline": "1:1 support + professional mastering.",
      "pricing.pro.li1": "Everything in Plus",
      "pricing.pro.li2": "1 monthly 1:1 session to review your sound and setup",
      "pricing.pro.li3": "1 episode/month manually mastered in studio",
      "pricing.pro.li4": "Discount on additional masters",
      "pricing.pro.li5": "Ideal if you want to level up",
      "pricing.pro.btn": "Available soon",
      "pricing.pro.note": "Will open first to a small group of creators.",

      "pricing.disclaimer.before": "Prices and features are",
      "pricing.disclaimer.strong": "indicative",
      "pricing.disclaimer.after":
        "(approx. USD values) and may change depending on real usage and the feedback we receive during this beta stage.",

      // Status / errors
      "status.idle": "",
      "status.uploading": "Uploading audio…",
      "status.processing": "Processing audio…",
      "status.done": "Processing complete.",
      "status.error.noServer":
        "Couldn't reach the server. Check your connection and try again.",
      "status.error.generic":
        "Something went wrong while processing the audio. Please try again later.",
      "status.error.noFile": "Please select an audio file first.",
      "status.error.invalidFile":
        "Invalid file. Please upload an audio file (mp3, wav, m4a, etc).",
      "status.error.tooBig":
        "File is too large. Try a shorter audio (max 20 MB).",
      "status.error.download": "Could not download the file.",

      // Download filenames
      "filename.processedSuffix": "_PROCESSED.wav",
      "filename.reportSuffix": "_PROCESSED_report.txt",
      "filename.fallbackAudio": "processed_audio.wav",
      "filename.fallbackReport": "audio_report.txt",
    },
  };

  function detectBrowserLang() {
    const nav = (navigator.language || "").toLowerCase();
    if (nav.startsWith("en")) return "en";
    return "es";
  }

  function getSavedLang() {
    try {
      const v = localStorage.getItem(LANG_STORAGE_KEY);
      if (v && SUPPORTED_LANGS.includes(v)) return v;
    } catch (_) {}
    return null;
  }

  function t(key, vars = null) {
    const dict = I18N[currentLang] || I18N.es;
    const fallback = I18N.es;
    let s = dict[key] ?? fallback[key] ?? key;

    if (vars && typeof vars === "object") {
      for (const [k, v] of Object.entries(vars)) {
        s = s.replaceAll(`{${k}}`, String(v));
      }
    }
    return s;
  }

  function applyTranslations() {
    document.documentElement.lang = currentLang;

    // textContent
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;
      el.textContent = t(key);
    });

    // placeholder
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!key) return;
      el.setAttribute("placeholder", t(key));
    });

    // attr mapping: data-i18n-attr="aria-label:key1;title:key2"
    document.querySelectorAll("[data-i18n-attr]").forEach((el) => {
      const spec = el.getAttribute("data-i18n-attr");
      if (!spec) return;
      const parts = spec.split(";").map((x) => x.trim()).filter(Boolean);
      for (const part of parts) {
        const [attr, key] = part.split(":").map((x) => x.trim());
        if (attr && key) el.setAttribute(attr, t(key));
      }
    });

    updateLangToggleUI();
    updateDropzoneText(); // refresca texto si ya había archivo seleccionado
  }

  function setLanguage(lang, { persist = true } = {}) {
    if (!SUPPORTED_LANGS.includes(lang)) lang = "es";
    currentLang = lang;

    if (persist) {
      try {
        localStorage.setItem(LANG_STORAGE_KEY, lang);
      } catch (_) {}
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
  //   APP
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

  const API_ENDPOINT = `/api/process_audio`;
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

  function clearMessages() {
    setError("");
    setStatus("");
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
    // lastOriginalFileName lo mantenemos si quieres, pero no afecta

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
    }

    clearMessages();
    updateDropzoneText();
  }

  function isValidAudioFile(file) {
    if (!file) return false;
    const typeOk = (file.type || "").startsWith("audio/");
    const name = (file.name || "").toLowerCase();
    const extOk = [
      ".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".opus", ".webm", ".aiff", ".aif",
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

  function getSelectedMode() {
    const el = document.querySelector('input[name="modo"]:checked');
    return el ? el.value : null;
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
    } catch (_) {
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
    } catch (_) {
      setError(t("status.error.download"));
    }
  }

  // =========================
  //   Eventos UI
  // =========================
  if (fileInput) {
    fileInput.addEventListener("change", (e) => {
      const file = e.target.files && e.target.files[0];
      if (file) handleSelectedFile(file);
    });
  }

  if (dropzone) {
    dropzone.addEventListener("click", (e) => {
      if (!fileInput) return;
      if (e.target === fileInput || e.target.tagName === "LABEL") return;
      fileInput.value = "";
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

      const mode = getSelectedMode();

      try {
        const formData = new FormData();
        formData.append("file", selectedFile);
        if (mode) formData.append("mode", mode);

        setStatus(t("status.processing"));

        const resp = await fetch(API_ENDPOINT, {
          method: "POST",
          body: formData,
        });

        if (!resp.ok) {
          if (resp.status === 413) {
            setError(t("status.error.tooBig"));
          } else {
            setError(t("status.error.generic"));
          }
          setStatus("");
          processBtn.disabled = false;
          return;
        }

        const data = await resp.json();

        // Asumido por tu backend típico:
        // { original_url, processed_url, report_url, analysis, original_filename }
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
        if (processBtn) processBtn.disabled = false;
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
  //   INIT
  // =========================
  initLangToggle(); // localStorage > navegador
  resetEstado();
  applyTranslations();
});
