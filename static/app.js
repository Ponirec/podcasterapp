/* static/app.js */

(() => {
  "use strict";

  // ---------------------------
  // i18n
  // ---------------------------
  const I18N = {
    es: {
      "hero.title": "Mejora tu audio",
      "hero.subtitle": "Sube tu grabación, elige cómo fue capturada y obtén un archivo listo para podcast.",

      "section1.title": "1. Configura tu procesamiento",
      "field.recording.label": "¿Cómo grabaste tu audio?",
      "field.recording.option.laptop": "Laptop / Celular",
      "field.recording.option.external": "Micrófono externo (USB / Interfaz)",
      "field.file.label": "Archivo de audio",
      "dropzone.label": "Arrastra tu archivo aquí o haz clic para seleccionarlo",
      "dropzone.limit": "Máximo 20 MB (aprox. 10 minutos). Si tu archivo es más grande, sube un extracto o una parte del episodio.",
      "formats.recommended": "Formatos recomendados: WAV, MP3, M4A.",
      "button.process": "Procesar audio",
      "status.processing": "Procesando…",
      "status.ready": "Listo.",
      "error.generic": "Ocurrió un error al procesar el audio. Intenta nuevamente más tarde.",

      "section2.title": "2. Revisa tu resultado",
      "player.original": "player.original",
      "player.processed": "player.processed",
      "button.download.processed": "Descargar audio procesado",
      "button.download.report": "Descargar informe detallado",

      "pricing.title": "Planes (próximamente)",
      "pricing.intro": "Hoy estás usando la versión beta gratuita (plan Free). Más adelante podrás elegir entre estos planes, según el nivel de tu podcast y el tipo de acompañamiento que necesites.",
      "pricing.free.title": "Free",
      "pricing.free.price": "Gratis",
      "pricing.free.tagline": "Ideal para probar la app y mejorar tus primeras grabaciones.",
      "pricing.free.b1": "Procesamiento automático de audio",
      "pricing.free.b2": "Informe de calidad con recomendaciones básicas",
      "pricing.plus.title": "Plus",
      "pricing.plus.price": "USD $9 / mes",
      "pricing.plus.tagline": "Para podcasters que suben episodios completos.",
      "pricing.plus.b1": "Todo lo del plan Free",
      "pricing.plus.b2": "Archivos hasta ~60 minutos (o ~100 MB)",
      "pricing.pro.title": "Pro",
      "pricing.pro.price": "USD $55 / mes",
      "pricing.pro.tagline": "Asesoría 1:1 + mastering profesional.",
      "pricing.pro.b1": "Todo lo del plan Plus",
      "pricing.pro.b2": "1 sesión mensual 1:1 para revisar tu sonido y setup",
      "pricing.pro.b3": "1 episodio al mes masterizado manualmente en estudio",
      "pricing.pro.b4": "Descuento en masters adicionales",
      "pricing.btn.soon": "Disponible pronto",
      "pricing.note.free": "Esto es lo que estás usando ahora mismo.",
      "pricing.note.plus": "Se ajustará según feedback de esta beta.",
      "pricing.note.pro": "Primero se abrirá para un grupo reducido de creadores.",
      "pricing.disclaimer": "Los precios y características son referenciales (valores aprox. en USD) y pueden ajustarse según uso real y feedback.",
    },

    en: {
      "hero.title": "Improve your audio",
      "hero.subtitle": "Upload your recording, choose how it was captured, and get a podcast-ready file.",

      "section1.title": "1. Configure your processing",
      "field.recording.label": "How did you record your audio?",
      "field.recording.option.laptop": "Laptop / Phone",
      "field.recording.option.external": "External microphone (USB / Interface)",
      "field.file.label": "Audio file",
      "dropzone.label": "Drag your file here or click to select it",
      "dropzone.limit": "Max 20 MB (about 10 minutes). If your file is larger, upload a shorter excerpt.",
      "formats.recommended": "Recommended formats: WAV, MP3, M4A.",
      "button.process": "Process audio",
      "status.processing": "Processing…",
      "status.ready": "Done.",
      "error.generic": "An error occurred while processing the audio. Please try again later.",

      "section2.title": "2. Review your result",
      "player.original": "player.original",
      "player.processed": "player.processed",
      "button.download.processed": "Download processed audio",
      "button.download.report": "Download detailed report",

      "pricing.title": "Plans (coming soon)",
      "pricing.intro": "You're currently using the free beta version (Free plan). Later you'll be able to choose between these plans depending on your podcast level and the kind of support you need.",
      "pricing.free.title": "Free",
      "pricing.free.price": "Free",
      "pricing.free.tagline": "Great for testing the app and improving your first recordings.",
      "pricing.free.b1": "Automatic audio processing",
      "pricing.free.b2": "Quality report with basic recommendations",
      "pricing.plus.title": "Plus",
      "pricing.plus.price": "USD $9 / month",
      "pricing.plus.tagline": "For podcasters uploading full episodes.",
      "pricing.plus.b1": "Everything in Free",
      "pricing.plus.b2": "Files up to ~60 minutes (or ~100 MB)",
      "pricing.pro.title": "Pro",
      "pricing.pro.price": "USD $55 / month",
      "pricing.pro.tagline": "1:1 support + professional mastering.",
      "pricing.pro.b1": "Everything in Plus",
      "pricing.pro.b2": "1 monthly 1:1 session to review your sound and setup",
      "pricing.pro.b3": "1 episode/month manually mastered in studio",
      "pricing.pro.b4": "Discount on additional masters",
      "pricing.btn.soon": "Available soon",
      "pricing.note.free": "This is what you're using right now.",
      "pricing.note.plus": "Will be adjusted based on beta feedback.",
      "pricing.note.pro": "Will first open to a small group of creators.",
      "pricing.disclaimer": "Prices and features are indicative (approx. USD values) and may change depending on usage and feedback.",
    },
  };

  const LANG_KEY = "podcaster_lang";

  function getLang() {
    const saved = localStorage.getItem(LANG_KEY);
    return saved === "en" ? "en" : "es";
  }

  function setLang(lang) {
    const next = lang === "en" ? "en" : "es";
    localStorage.setItem(LANG_KEY, next);
    applyI18n(next);
    updateLangButtons(next);
  }

  function t(key, lang) {
    const L = I18N[lang] || I18N.es;
    return L[key] ?? I18N.es[key] ?? I18N.en[key] ?? key;
  }

  function applyI18n(lang) {
    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      el.textContent = t(key, lang);
    });

    document.querySelectorAll("[data-i18n-html]").forEach((el) => {
      const key = el.getAttribute("data-i18n-html");
      el.innerHTML = t(key, lang);
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      el.setAttribute("placeholder", t(key, lang));
    });
  }

  function updateLangButtons(lang) {
    const esBtn = document.querySelector("[data-lang='es']");
    const enBtn = document.querySelector("[data-lang='en']");
    if (esBtn) esBtn.classList.toggle("active", lang === "es");
    if (enBtn) enBtn.classList.toggle("active", lang === "en");
  }

  // ---------------------------
  // UI helpers
  // ---------------------------
  function $(sel) {
    return document.querySelector(sel);
  }

  function setText(el, txt) {
    if (el) el.textContent = txt;
  }

  function show(el) {
    if (el) el.style.display = "";
  }

  function hide(el) {
    if (el) el.style.display = "none";
  }

  // ---------------------------
  // Processing
  // ---------------------------
  const API_URL = "/api/process_audio";

  function getSelectedMode() {
    // intenta varios nombres típicos
    const radio =
      document.querySelector("input[name='mode']:checked") ||
      document.querySelector("input[name='recording_mode']:checked") ||
      document.querySelector("input[name='recording']:checked") ||
      document.querySelector("input[name='recording_type']:checked");
    if (!radio) return "Laptop";

    // Alineado con tu backend: si contiene "Laptop" -> laptop; si no -> externo
    const v = (radio.value || "").trim();
    if (!v) return "Laptop";
    return v; // puede ser "Laptop" u otra cosa (cae a externo en backend)
  }

  function getFileInput() {
    return (
      $("#audio_file") ||
      $("#audioFile") ||
      document.querySelector("input[type='file']")
    );
  }

  function getForm() {
    return $("#processForm") || document.querySelector("form");
  }

  function setAudioPlayer(selector, src) {
    const el = $(selector);
    if (!el) return;
    el.src = src;
    el.load?.();
  }

  function setDownloadLink(selector, href, filename) {
    const a = $(selector);
    if (!a) return;
    a.href = href;
    if (filename) a.setAttribute("download", filename);
    a.classList.remove("disabled");
  }

  async function processAudio(file, mode, lang) {
    const fd = new FormData();
    fd.append("audio_file", file);
    fd.append("mode", mode);

    const res = await fetch(API_URL, { method: "POST", body: fd });

    let payload = null;
    try {
      payload = await res.json();
    } catch (_) {}

    if (!res.ok) {
      // intenta mostrar detalle si viene
      const detail =
        payload?.detail ||
        payload?.error ||
        payload?.message ||
        t("error.generic", lang);
      throw new Error(detail);
    }

    return payload;
  }

  function renderReport(analysis, lang) {
    const box = $("#reportBox") || $("#reportContainer") || $("#report");
    if (!box) return;

    // Si tu HTML ya tiene un diseño para esto, aquí solo rellenamos texto.
    // Mostramos recomendaciones si vienen.
    const recs = Array.isArray(analysis?.recomendaciones)
      ? analysis.recomendaciones
      : [];

    if (recs.length === 0) return;

    const ul = document.createElement("ul");
    ul.className = "report-list";
    recs.forEach((r) => {
      const li = document.createElement("li");
      li.textContent = r;
      ul.appendChild(li);
    });

    box.innerHTML = "";
    box.appendChild(ul);
  }

  // ---------------------------
  // Init
  // ---------------------------
  window.addEventListener("DOMContentLoaded", () => {
    const lang = getLang();
    applyI18n(lang);
    updateLangButtons(lang);

    // botones idioma (ES/EN)
    document.querySelectorAll("[data-lang]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const l = btn.getAttribute("data-lang");
        setLang(l);
      });
    });

    const form = getForm();
    const fileInput = getFileInput();

    const statusEl = $("#statusMsg") || $("#status");
    const errorEl = $("#errorMsg") || $("#error");

    const processBtn = $("#processBtn") || $("#btnProcess") || $("button[type='submit']");

    // Si hay un label de archivo seleccionado
    const fileNameEl = $("#fileName") || $("#selectedFileName");

    if (fileInput && fileNameEl) {
      fileInput.addEventListener("change", () => {
        const f = fileInput.files?.[0];
        setText(fileNameEl, f ? f.name : "");
      });
    }

    if (!form || !fileInput) {
      // No rompemos la app si el DOM cambió
      return;
    }

    form.addEventListener("submit", async (e) => {
      e.preventDefault();

      hide(errorEl);
      setText(errorEl, "");

      const currentLang = getLang();

      const file = fileInput.files?.[0];
      if (!file) {
        show(errorEl);
        setText(errorEl, currentLang === "en" ? "Please select an audio file." : "Selecciona un archivo de audio.");
        return;
      }

      const mode = getSelectedMode();

      // UI
      if (processBtn) processBtn.disabled = true;
      show(statusEl);
      setText(statusEl, t("status.processing", currentLang));

      try {
        // players: original desde archivo local
        const originalUrl = URL.createObjectURL(file);
        setAudioPlayer("#playerOriginal", originalUrl);
        setAudioPlayer("#player_original", originalUrl);

        const data = await processAudio(file, mode, currentLang);

        // processed
        if (data?.processed_audio_url) {
          setAudioPlayer("#playerProcessed", data.processed_audio_url);
          setAudioPlayer("#player_processed", data.processed_audio_url);

          setDownloadLink(
            "#downloadProcessed",
            data.processed_audio_url,
            data.processed_audio_filename || "processed_audio.wav"
          );
          setDownloadLink(
            "#download_processed",
            data.processed_audio_url,
            data.processed_audio_filename || "processed_audio.wav"
          );
        }

        // report
        if (data?.report_url) {
          setDownloadLink(
            "#downloadReport",
            data.report_url,
            data.report_filename || "report.txt"
          );
          setDownloadLink(
            "#download_report",
            data.report_url,
            data.report_filename || "report.txt"
          );
        }

        if (data?.analysis) renderReport(data.analysis, currentLang);

        setText(statusEl, t("status.ready", currentLang));
      } catch (err) {
        show(errorEl);
        setText(errorEl, err?.message || t("error.generic", getLang()));
        setText(statusEl, "");
        hide(statusEl);
      } finally {
        if (processBtn) processBtn.disabled = false;
      }
    });
  });
})();
