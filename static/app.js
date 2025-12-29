document.addEventListener("DOMContentLoaded", () => {
  // =========================
  //   i18n (ES/EN)
  // =========================
  const SUPPORTED_LANGS = ["es", "en"];
  const LANG_STORAGE_KEY = "podcasterapp_lang";
  let currentLang = "es";

  // 🔁 Aliases: tu HTML usa keys tipo "section1.title" pero tu diccionario usa "s1.title".
  // Esto evita que se impriman las keys en pantalla.
  const KEY_ALIAS = {
    // Sección 1
    "section1.title": "s1.title",
    "field.recording.label": "s1.capture.label",
    "field.recording.option.laptop": "s1.capture.laptop",
    "field.recording.option.externalMic": "s1.capture.external",
    "field.file.label": "s1.file.label",

    // Dropzone
    "dropzone.limit": "dropzone.max",

    // Sección 2
    "section2.title": "s2.title",
    "player.original": "s2.original",
    "player.processed": "s2.processed",

    // Pricing (tu HTML usa pricing.btn.soon y pricing.note.*)
    "pricing.btn.soon": "pricing.plus.btn",
    "pricing.note.free": "pricing.free.note",
    "pricing.note.plus": "pricing.plus.note",
    "pricing.note.pro": "pricing.pro.note",
  };

  const I18N = {
    es: {
      "head.title": "Limpia tu audio",
      "lang.es": "ES",
      "lang.en": "EN",

      "header.title": "Mejora tu audio",
      "header.subtitle":
        "Sube tu grabación, elige cómo fue capturada y obtén un archivo listo para podcast.",

      // (Tus keys internas)
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
        "Max 20 MB (about 10 minutes of audio). If your file is larger, upload an excerpt or a part of the episode.",
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

    const alias = KEY_ALIAS[key];

    let s =
      dict[key] ??
      (alias ? dict[alias] : undefined) ??
      fallback[key] ??
      (alias ? fallback[alias] : undefined) ??
      key;

    if (vars && typeof vars === "object") {
      for (const [k, v] of Object.entries(vars)) {
        s = s.replaceAll(`{${k}}`, String(v));
      }
    }
    return s;
  }

  function applyTranslations() {
    document.documentElement.lang = currentLang;
    document.title = t("head.title");

    // textContent / innerHTML (para mantener <strong> del disclaimer)
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (!key) return;

      if (key === "pricing.disclaimer") {
        el.innerHTML = `${t("pricing.disclaimer.before")} <strong>${t(
          "pricing.disclaimer.strong"
        )}</strong> ${t("pricing.disclaimer.after")}`;
        return;
      }

      el.textContent = t(key);
    });

    // placeholder
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (!key) return;
      el.setAttribute("placeholder", t(key));
    });

    // (Opcional) aria-label en botones de idioma
    const btnEs = document.getElementById("lang-es");
    const btnEn = document.getElementById("lang-en");
    if (btnEs) btnEs.setAttribute("aria-label", currentLang === "en" ? "Spanish" : "Español");
    if (btnEn) btnEn.setAttribute("aria-label", currentLang === "en" ? "English" : "Inglés");
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

    // Estado activo de los botones
    const btnEs = document.getElementById("lang-es");
    const btnEn = document.getElementById("lang-en");
    if (btnEs) btnEs.classList.toggle("btn--active", currentLang === "es");
    if (btnEn) btnEn.classList.toggle("btn--active", currentLang === "en");
  }

  function initLangToggle() {
    const btnEs = document.getElementById("lang-es");
    const btnEn = document.getElementById("lang-en");
    if (!btnEs || !btnEn) return;

    btnEs.addEventListener("click", () => setLanguage("es"));
    btnEn.addEventListener("click", () => setLanguage("en"));

    const initial = getSavedLang() || detectBrowserLang() || "es";
    setLanguage(initial, { persist: false });
  }

  initLangToggle();

  // =========================
  //   App logic (upload/process)
  // =========================
  const processBtn = document.getElementById("process-btn");
  const fileInput = document.getElementById("file-input");
  const dropzone = document.getElementById("dropzone");
  const dropzoneText = document.getElementById("dropzone-text");
  const statusEl = document.getElementById("status");
  const errorEl = document.getElementById("error-message");

  const resultSection = document.getElementById("result-section");
  const playerOriginal = document.getElementById("player-original");
  const playerProcessed = document.getElementById("player-processed");
  const downloadBtn = document.getElementById("download-btn");
  const downloadReportBtn = document.getElementById("download-report-btn");
  const analysisEl = document.getElementById("analysis");

  let lastProcessedAudioUrl = null;
  let lastReportUrl = null;

  // ✅ FIX: archivo seleccionado “real”, independiente de fileInput.files
  let selectedFile = null;

  function setStatus(key) {
    if (!statusEl) return;
    statusEl.textContent = t(key);
  }

  function showError(key) {
    if (!errorEl) return;
    errorEl.style.display = "block";
    errorEl.textContent = t(key);
  }

  function clearError() {
    if (!errorEl) return;
    errorEl.style.display = "none";
    errorEl.textContent = "";
  }

  function getSelectedMode() {
    const checked = document.querySelector("input[name='modo']:checked");
    return checked ? checked.value : "LAPTOP_CELULAR";
  }

  function isAudioFile(file) {
    if (!file) return false;
    return (file.type || "").startsWith("audio/") || /\.(mp3|wav|m4a|aac|flac|ogg)$/i.test(file.name);
  }

  function updateDropzoneText(file) {
    if (!dropzoneText) return;
    if (file) {
      dropzoneText.textContent = t("dropzone.selected", { name: file.name });
    } else {
      dropzoneText.textContent = t("dropzone.text");
    }
  }

  // Click en dropzone abre file picker
  if (dropzone && fileInput) {
    dropzone.addEventListener("click", (e) => {
      // si el click fue directamente sobre el input, no duplicar el click
      if (e.target === fileInput) return;

      // ✅ fuerza a que "change" dispare incluso si eliges el mismo archivo
      fileInput.value = "";
      fileInput.click();
    });

    dropzone.addEventListener("dragover", (e) => {
      e.preventDefault();
      dropzone.classList.add("dropzone--hover");
    });

    dropzone.addEventListener("dragleave", () => {
      dropzone.classList.remove("dropzone--hover");
    });

    dropzone.addEventListener("drop", (e) => {
      e.preventDefault();
      dropzone.classList.remove("dropzone--hover");

      const file = e.dataTransfer.files && e.dataTransfer.files[0];
      if (file) {
        // ✅ NO tocar fileInput.files (en muchos browsers es read-only/inconsistente)
        selectedFile = file;
        updateDropzoneText(file);
        clearError();
      }
    });
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => {
      const file = fileInput.files && fileInput.files[0];
      selectedFile = file || null;
      updateDropzoneText(selectedFile);
      clearError();
    });
  }

  async function downloadFile(url, filenameFallback) {
    try {
      const res = await fetch(url);
      if (!res.ok) throw new Error("download failed");
      const blob = await res.blob();
      const a = document.createElement("a");
      const objectUrl = URL.createObjectURL(blob);
      a.href = objectUrl;
      a.download = filenameFallback;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (e) {
      showError("status.error.download");
    }
  }

  if (downloadBtn) {
    downloadBtn.addEventListener("click", () => {
      if (!lastProcessedAudioUrl) return;
      downloadFile(lastProcessedAudioUrl, t("filename.fallbackAudio"));
    });
  }

  if (downloadReportBtn) {
    downloadReportBtn.addEventListener("click", () => {
      if (!lastReportUrl) return;
      downloadFile(lastReportUrl, t("filename.fallbackReport"));
    });
  }

  async function processAudio() {
    clearError();

    // ✅ toma primero el archivo guardado por drop/picker
    const file =
      selectedFile || (fileInput && fileInput.files ? fileInput.files[0] : null);

    if (!file) return showError("status.error.noFile");
    if (!isAudioFile(file)) return showError("status.error.invalidFile");

    // 20 MB
    const MAX_BYTES = 20 * 1024 * 1024;
    if (file.size > MAX_BYTES) return showError("status.error.tooBig");

    setStatus("status.uploading");

    const form = new FormData();
    form.append("file", file);
    form.append("modo", getSelectedMode());
    form.append("lang", currentLang);


    try {
      setStatus("status.processing");

      const resp = await fetch("/process", { method: "POST", body: form });
      if (!resp.ok) {
        if (resp.status >= 500) throw new Error("server");
        throw new Error("bad request");
      }

      const data = await resp.json();

      // Backend expected keys: processed_audio_url, original_audio_url, report_url, analysis_html
      if (playerOriginal && data.original_audio_url) playerOriginal.src = data.original_audio_url;
      if (playerProcessed && data.processed_audio_url) playerProcessed.src = data.processed_audio_url;

      lastProcessedAudioUrl = data.processed_audio_url || null;
      lastReportUrl = data.report_url || null;

      if (analysisEl) {
        analysisEl.innerHTML = data.analysis_html || "";
      }

      if (resultSection) {
        resultSection.classList.remove("hidden");
        resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
      }

      setStatus("status.done");
    } catch (err) {
      if (String(err).includes("server")) showError("status.error.noServer");
      else showError("status.error.generic");
      setStatus("status.idle");
    }
  }

  if (processBtn) {
    processBtn.addEventListener("click", processAudio);
  }

  // Estado inicial
  selectedFile = fileInput && fileInput.files ? fileInput.files[0] : null;
  setStatus("status.idle");
  updateDropzoneText(selectedFile);
});
