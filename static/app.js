document.addEventListener("DOMContentLoaded", () => {
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const processBtn = document.getElementById("process-btn");
  const downloadAudioBtn = document.getElementById("download-btn");
  const downloadReportBtn = document.getElementById("download-report-btn");

  const playerOriginal = document.getElementById("player-original");
  const playerProcessed = document.getElementById("player-processed");

  const resultSection = document.getElementById("result-section");
  const statusEl = document.getElementById("status");
  const analysisEl = document.getElementById("analysis");

const BASE_API_URL = ""; 
const API_ENDPOINT = `/api/process_audio`;


  let selectedFile = null;
  let processedFileUrl = "";
  let reportFileUrl = "";
  let lastOriginalFileName = "";

  // =========================
  //   ESTADO / UI
  // =========================

  function resetEstado() {
    if (statusEl) {
      statusEl.textContent = "";
      statusEl.classList.remove("status--error");
    }

    if (resultSection) {
      resultSection.classList.add("hidden");
    }

    if (playerOriginal) {
      playerOriginal.removeAttribute("src");
      playerOriginal.load();
    }

    if (playerProcessed) {
      playerProcessed.removeAttribute("src");
      playerProcessed.load();
    }

    if (analysisEl) {
      analysisEl.innerHTML = "";
    }

    processedFileUrl = "";
    reportFileUrl = "";
  }

  function renderAnalysis(a) {
    if (!analysisEl) return;
    if (!a) {
      analysisEl.innerHTML = "";
      return;
    }

    const html = `
      <p><strong>Modo:</strong> ${a.modo}</p>
      <p><strong>Sala:</strong> ${a.sala_descripcion} (índice ${a.sala_indice})</p>
      <p><strong>Ruido estimado:</strong> ${a.ruido_estimado_dbfs} dBFS</p>
      <p><strong>Nivel de voz original:</strong> ${a.nivel_original_dbfs} dBFS</p>
      <p><strong>Nivel de voz final:</strong> ${a.nivel_final_dbfs} dBFS</p>
      <p><strong>Relación señal/ruido:</strong> ${a.snr_db} dB</p>
      <p><strong>Puntaje de calidad:</strong> ${a.quality_score} / 100 (${a.quality_label})</p>
      <p><strong>Clips / distorsión digital:</strong> ${
        a.clip_detectado ? "Probables" : "No se detectan claros indicios"
      }</p>
    `;
    analysisEl.innerHTML = html;
  }

  // =========================
 //   DESCARGA SIN NAVEGAR
 // =========================
async function triggerDownload(resourceUrl, suggestedName) {
  try {
    // En tu código, processedFileUrl y reportFileUrl YA vienen con BASE_API_URL
    const fullUrl = resourceUrl;

    const resp = await fetch(fullUrl);
    if (!resp.ok) {
      throw new Error(`HTTP ${resp.status}`);
    }

    const blob = await resp.blob();
    const blobUrl = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = suggestedName || "";
    a.style.display = "none";

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);

    URL.revokeObjectURL(blobUrl);
  } catch (err) {
    console.error("Error descargando archivo:", err);
    alert("No se pudo descargar el archivo.");
  }
}


  // =========================
  //   SELECCIÓN DE ARCHIVO
  // =========================

  if (fileInput) {
  // Vaciar el valor ANTES de abrir el selector, para que
  // elegir el mismo archivo vuelva a disparar "change"
  fileInput.addEventListener("click", () => {
    fileInput.value = "";
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files && e.target.files[0];
    if (!file) return;

    selectedFile = file;
    lastOriginalFileName = file.name;
    if (processBtn) processBtn.disabled = false;

    if (dropzone) {
      dropzone.dataset.filename = file.name;
      dropzone.classList.add("has-file");
    }

    console.log("Archivo seleccionado:", file.name);
  });
}


  if (dropzone) {
  // IMPORTANTE: NO volver a llamar al fileInput si el clic fue en el botón
  // "Seleccionar archivo" (label) o en el propio input, para evitar doble diálogo.
  dropzone.addEventListener("click", (e) => {
    // Si el clic viene directamente del input o de un <label>, no hacemos nada extra
    if (e.target === fileInput || e.target.tagName === "LABEL") {
      return;
    }

    if (fileInput) {
      fileInput.value = ""; // opcional, por si quieres permitir mismo archivo
      fileInput.click();
    }
  });

  // drag & drop básico
  ["dragenter", "dragover"].forEach((ev) => {
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.add("dropzone--hover");
    });
  });
  ["dragleave", "drop"].forEach((ev) => {
    dropzone.addEventListener(ev, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove("dropzone--hover");
    });
  });

  dropzone.addEventListener("drop", (e) => {
    const dt = e.dataTransfer;
    if (!dt || !dt.files || dt.files.length === 0) return;

    const file = dt.files[0];
    if (fileInput) {
      fileInput.files = dt.files;
    }

    selectedFile = file;
    lastOriginalFileName = file.name;
    if (processBtn) processBtn.disabled = false;

    if (dropzone) {
      dropzone.dataset.filename = file.name;
      dropzone.classList.add("has-file");
    }

    console.log("Archivo seleccionado (drop):", file.name);
  });
}



  // =========================
  //   PROCESAR AUDIO
  // =========================

  if (processBtn) {
  processBtn.addEventListener("click", async () => {
    if (!selectedFile) {
      statusEl.textContent = "Primero selecciona un archivo de audio.";
      statusEl.classList.add("status--error");
      return;
    }

    resetEstado();
    processBtn.disabled = true;
    statusEl.textContent = "Procesando audio...";

    const modeRadio = document.querySelector('input[name="modo"]:checked');
    const modeValue = modeRadio ? modeRadio.value : "LAPTOP_CELULAR";

    console.log("CLICK en Procesar audio");
    console.log("Modo seleccionado:", modeValue);

    const formData = new FormData();
    formData.append("audio_file", selectedFile);
    formData.append("mode", modeValue);

    try {
  const resp = await fetch(API_ENDPOINT, {
    method: "POST",
    body: formData,
  });

  console.log("Status respuesta backend:", resp.status);

  // 👉 Manejo especial del 413 (archivo demasiado grande)
  if (resp.status === 413) {
    let msg =
      "El archivo es demasiado pesado. Prueba con un audio más corto (máx. 20 MB).";

    try {
      const errData = await resp.json();
      if (errData && errData.detail) {
        msg = errData.detail;
      }
    } catch (e) {
      // si no viene JSON, usamos el mensaje por defecto
    }

    statusEl.textContent = msg;
    statusEl.classList.add("status--error");
    return; // no seguimos con el flujo normal
  }

  // 👉 Otros errores HTTP genéricos
  if (!resp.ok) {
    statusEl.textContent =
      "Ocurrió un error al procesar el audio. Intenta nuevamente más tarde.";
    statusEl.classList.add("status--error");
    return;
  }

  const data = await resp.json();
  console.log("JSON recibido:", data);

  const originalUrl = `${BASE_API_URL}${data.original_url}`;
  const processedUrl = `${BASE_API_URL}${data.processed_url}`;
  const reportUrl = `${BASE_API_URL}${data.report_url}`;

  processedFileUrl = processedUrl;
  reportFileUrl = reportUrl;
  lastOriginalFileName = data.original_filename || lastOriginalFileName;

  if (playerOriginal) {
    playerOriginal.src = originalUrl;
    playerOriginal.load();
  }
  if (playerProcessed) {
    playerProcessed.src = processedUrl;
    playerProcessed.load();
  }

  renderAnalysis(data.analysis);
  resultSection.classList.remove("hidden");

  statusEl.textContent = "Procesamiento completado.";
  statusEl.classList.remove("status--error");
} catch (err) {
  console.error("Error en procesamiento:", err);
  statusEl.textContent =
    "No se pudo conectar con el servidor. Revisa tu conexión e intenta de nuevo.";
  statusEl.classList.add("status--error");
} finally {
  processBtn.disabled = false;
}

  });
}


  // =========================
  //   DESCARGAS
  // =========================

  if (downloadAudioBtn) {
    downloadAudioBtn.addEventListener("click", () => {
      if (!processedFileUrl) return;
      const suggested = lastOriginalFileName
        ? lastOriginalFileName.replace(/\.[^.]+$/, "_PROCESADO.wav")
        : "audio_procesado.wav";
      triggerDownload(processedFileUrl, suggested);
    });
  }

  if (downloadReportBtn) {
    downloadReportBtn.addEventListener("click", () => {
      if (!reportFileUrl) return;
      const suggested = lastOriginalFileName
        ? lastOriginalFileName.replace(/\.[^.]+$/, "_PROCESADO_report.txt")
        : "informe_audio.txt";
      triggerDownload(reportFileUrl, suggested);
    });
  }

  // =========================
  //   ESTADO INICIAL
  // =========================

  resetEstado();
  if (processBtn) processBtn.disabled = true;

  console.log("app.js cargado");
});
