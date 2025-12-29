from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi import Response

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import time

import sys
import types
import os
import logging
import hashlib
import uuid
from html import escape as html_escape

# --------------------------------------
# Compatibilidad pydub / audioop / pyaudioop
# --------------------------------------
try:
    import pyaudioop as audioop  # type: ignore
except ImportError:
    try:
        import audioop  # type: ignore
        fake = types.ModuleType("pyaudioop")
        for name in dir(audioop):
            setattr(fake, name, getattr(audioop, name))
        sys.modules["pyaudioop"] = fake
    except ImportError:
        audioop = None  # type: ignore

from pydub import AudioSegment, effects

# =========================
#   LOGGING
# =========================
logger = logging.getLogger("podcasterapp")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

# =========================
#   POSTGRES (MÉTRICAS)
# =========================
def _truthy(v: Optional[str]) -> bool:
    return str(v or "").strip().lower() in {"1", "true", "yes", "y", "on"}

ENABLE_DB_METRICS = _truthy(os.getenv("ENABLE_DB_METRICS", "0"))
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
METRICS_SALT = os.getenv("METRICS_SALT", "").strip() or "change-me"

db_driver = None
try:
    import psycopg  # type: ignore
    db_driver = "psycopg"
except ImportError:
    psycopg = None  # type: ignore
    db_driver = None

try:
    import psycopg2  # type: ignore
    if db_driver is None:
        db_driver = "psycopg2"
except ImportError:
    psycopg2 = None  # type: ignore


def db_metrics_ready() -> bool:
    if not ENABLE_DB_METRICS:
        return False
    if not DATABASE_URL:
        return False
    if db_driver is None:
        return False
    return True


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS request_metrics (
  id UUID PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  mode TEXT,
  client_ip_hash TEXT,
  user_agent TEXT,

  input_filename TEXT,
  input_bytes BIGINT,
  output_bytes BIGINT,
  report_bytes BIGINT,

  duration_original_s DOUBLE PRECISION,
  duration_processed_s DOUBLE PRECISION,

  processing_ms INTEGER,

  quality_score INTEGER,
  snr_db DOUBLE PRECISION,
  sala_indice DOUBLE PRECISION,
  clip_detectado BOOLEAN
);
"""

INSERT_SQL = """
INSERT INTO request_metrics (
  id, mode, client_ip_hash, user_agent,
  input_filename, input_bytes, output_bytes, report_bytes,
  duration_original_s, duration_processed_s,
  processing_ms,
  quality_score, snr_db, sala_indice, clip_detectado
) VALUES (
  %(id)s, %(mode)s, %(client_ip_hash)s, %(user_agent)s,
  %(input_filename)s, %(input_bytes)s, %(output_bytes)s, %(report_bytes)s,
  %(duration_original_s)s, %(duration_processed_s)s,
  %(processing_ms)s,
  %(quality_score)s, %(snr_db)s, %(sala_indice)s, %(clip_detectado)s
);
"""

def _anonymize_ip(ip: Optional[str]) -> Optional[str]:
    if not ip:
        return None
    h = hashlib.sha256((METRICS_SALT + "|" + ip).encode("utf-8")).hexdigest()
    return h[:16]


def _exec_sql(sql: str, params: Optional[dict] = None) -> None:
    if not db_metrics_ready():
        return
    try:
        if db_driver == "psycopg2":
            if psycopg2 is None:
                return
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
            finally:
                conn.close()

        elif db_driver == "psycopg":
            if psycopg is None:
                return
            with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)

    except Exception as e:
        logger.warning(f"[DB_METRICS] Error ejecutando SQL: {e}")


def init_db() -> None:
    if not db_metrics_ready():
        if ENABLE_DB_METRICS and db_driver is None:
            logger.warning("[DB_METRICS] ENABLE_DB_METRICS=1 pero no hay driver instalado (psycopg2/psycopg).")
        return
    _exec_sql(CREATE_TABLE_SQL)
    logger.info("[DB_METRICS] Tabla request_metrics lista.")


def record_metrics(payload: dict) -> None:
    _exec_sql(INSERT_SQL, payload)


# =========================
#   RUTAS DE ARCHIVOS
# =========================
BASE_DIR = Path(__file__).resolve().parent
MEDIA_DIR = BASE_DIR / "media"
ORIGINAL_DIR = MEDIA_DIR / "original"
PROCESSED_DIR = MEDIA_DIR / "processed"
REPORT_DIR = MEDIA_DIR / "reports"
STATIC_DIR = BASE_DIR / "static"

for d in (ORIGINAL_DIR, PROCESSED_DIR, REPORT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# =========================
#   LÍMITE DE TAMAÑO DE ARCHIVO
# =========================
MAX_FILE_SIZE_MB = 20
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# =========================
#   i18n backend (report + resumen)
# =========================
SUPPORTED_LANGS = {"es", "en"}

def norm_lang(lang: Optional[str]) -> str:
    l = (lang or "").strip().lower()
    return l if l in SUPPORTED_LANGS else "es"

def mode_labels(mode_code: str) -> Dict[str, str]:
    if mode_code == "MICROFONO_EXTERNO":
        return {
            "es": "Micrófono externo (USB / interfaz)",
            "en": "External microphone (USB / interface)",
        }
    return {
        "es": "Laptop / Celular",
        "en": "Laptop / Phone",
    }

def sala_labels(sala_code: str) -> Dict[str, str]:
    m = {
        "very_controlled": {
            "es": "muy controlada (poca sala perceptible: micrófono muy cerca o espacio con buena absorción)",
            "en": "very controlled (little room sound: close mic or well-treated space)",
        },
        "controlled": {
            "es": "bastante controlada (pieza amoblada con varias cosas blandas)",
            "en": "quite controlled (furnished room with soft items)",
        },
        "reflective": {
            "es": "con bastante reflexión (típico living o pieza con poco tratamiento)",
            "en": "fairly reflective (typical room with little treatment)",
        },
        "very_live": {
            "es": "muy viva / con mucha reflexión (espacio duro o casi vacío, eco marcado)",
            "en": "very live / reflective (hard or mostly empty space, noticeable echo)",
        },
    }
    return m.get(sala_code, m["controlled"])

def clip_labels(clip_code: str) -> Dict[str, str]:
    m = {
        "clipping_detected": {
            "es": "Se detectan picos muy cercanos al máximo digital de forma repetida. Es probable que haya distorsión/clip en la grabación original.",
            "en": "Repeated peaks very close to 0 dBFS were detected. It's likely there is digital distortion/clipping in the original recording.",
        },
        "near_clipping": {
            "es": "Tu señal llega muy cerca del máximo digital. No se ve clip claro, pero estás al límite: conviene bajar un poco la ganancia.",
            "en": "Your signal gets very close to the digital ceiling. No clear clipping, but you're on the edge: lower the gain a bit.",
        },
        "no_clipping": {
            "es": "No se detectan señales claras de clip digital en la grabación.",
            "en": "No clear signs of digital clipping were detected.",
        },
    }
    return m.get(clip_code, m["no_clipping"])

def tr(lang: str, key: str) -> str:
    lang = norm_lang(lang)
    D = {
        "es": {
            "report.title": "=== Informe de procesamiento de audio ===",
            "report.file": "Archivo",
            "report.summary": "== Resumen general ==",
            "report.keydata": "== Datos clave ==",
            "report.clip_comment": "== Comentario sobre clipping ==",
            "report.trim_note": "Como parte del proceso, recortamos automáticamente un pequeño tramo al inicio y, cuando el audio es lo suficientemente largo, otro pequeño tramo al final para limpiar clics, ruidos de inicio/stop y silencios innecesarios.",
            "k.mode": "Modo",
            "k.room": "Sala",
            "k.noise": "Ruido estimado",
            "k.orig": "Nivel de voz original",
            "k.final": "Nivel de voz final",
            "k.snr": "Relación señal/ruido aproximada",
            "k.peak": "Pico máximo aproximado",
            "k.crest": "Crest factor aproximado",
            "k.clip": "Clips / distorsión digital",
            "k.score": "Puntaje de calidad",
            "clip.prob": "Probables",
            "clip.none": "No se detectan claros indicios",
            "html.title": "Resumen",
            "html.clip_yes": "Probable",
            "html.clip_no": "No se detecta claro",
        },
        "en": {
            "report.title": "=== Audio processing report ===",
            "report.file": "File",
            "report.summary": "== General summary ==",
            "report.keydata": "== Key data ==",
            "report.clip_comment": "== Clipping comment ==",
            "report.trim_note": "As part of the process, we automatically trim a short segment at the beginning and, when the audio is long enough, another short segment at the end to clean clicks, start/stop noises, and unnecessary silences.",
            "k.mode": "Mode",
            "k.room": "Room",
            "k.noise": "Estimated noise floor",
            "k.orig": "Original voice level",
            "k.final": "Final voice level",
            "k.snr": "Approx. signal-to-noise ratio",
            "k.peak": "Approx. peak level",
            "k.crest": "Approx. crest factor",
            "k.clip": "Clips / digital distortion",
            "k.score": "Quality score",
            "clip.prob": "Likely",
            "clip.none": "No clear signs detected",
            "html.title": "Summary",
            "html.clip_yes": "Likely",
            "html.clip_no": "No clear signs",
        },
    }
    return D.get(lang, D["es"]).get(key, key)

# =========================
#   APP FASTAPI + CORS
# =========================
app = FastAPI()

origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.on_event("startup")
def _startup():
    init_db()

@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")

@app.head("/health")
def health_head():
    return Response(status_code=200)

@app.get("/health")
async def health():
    return {
        "ok": True,
        "db_metrics_enabled": ENABLE_DB_METRICS,
        "db_driver": db_driver,
        "db_url_present": bool(DATABASE_URL),
    }

# =========================
#   LÓGICA DE AUDIO
# =========================
def analizar_audio(audio: AudioSegment) -> Dict[str, Any]:
    dur_ms = len(audio)
    nivel_dbfs = float(audio.dBFS) if audio.dBFS != float("-inf") else -90.0

    chunk_ms = 200
    niveles = []
    for i in range(0, dur_ms, chunk_ms):
        c = audio[i: i + chunk_ms]
        v = float(c.dBFS) if c.dBFS != float("-inf") else -90.0
        niveles.append(v)

    niveles.sort()
    if niveles:
        n_sub = max(1, len(niveles) // 4)
        ruido_estimado = sum(niveles[:n_sub]) / n_sub
    else:
        ruido_estimado = -90.0

    ruido_estimado = max(ruido_estimado, -80.0)
    snr = nivel_dbfs - ruido_estimado

    # Sala -> code + textos por idioma
    if snr >= 55 and ruido_estimado <= -75:
        sala_code = "very_controlled"
        sala_indice = 0.1
    elif snr >= 35 and ruido_estimado <= -60:
        sala_code = "controlled"
        sala_indice = 0.4
    elif snr >= 20:
        sala_code = "reflective"
        sala_indice = 0.7
    else:
        sala_code = "very_live"
        sala_indice = 1.0

    sala_txt = sala_labels(sala_code)

    sample_width = audio.sample_width
    max_possible = float((1 << (8 * sample_width - 1)) - 1)

    samples = audio.get_array_of_samples()
    if samples:
        max_abs = max(abs(s) for s in samples)
        peak_ratio = max_abs / max_possible
        clip_samples = sum(1 for s in samples if abs(s) >= 0.98 * max_possible)
        clip_ratio = clip_samples / len(samples)
    else:
        peak_ratio = 0.0
        clip_ratio = 0.0

    peak_db = audio.max_dBFS if audio.max_dBFS != float("-inf") else -90.0
    crest_factor = peak_db - nivel_dbfs

    clip_detectado = (peak_ratio > 0.985) and (clip_ratio > 0.0005)

    if clip_detectado:
        clip_code = "clipping_detected"
    elif peak_ratio > 0.96:
        clip_code = "near_clipping"
    else:
        clip_code = "no_clipping"

    clip_txt = clip_labels(clip_code)

    return {
        "sala_code": sala_code,
        "sala_indice": round(float(sala_indice), 2),
        "sala_descripcion_es": sala_txt["es"],
        "sala_descripcion_en": sala_txt["en"],
        "ruido_estimado_dbfs": round(float(ruido_estimado), 1),
        "nivel_original_dbfs": round(float(nivel_dbfs), 1),
        "snr_db": round(float(snr), 1),

        "peak_dbfs": round(float(peak_db), 1),
        "crest_factor_db": round(float(crest_factor), 1),

        "clip_detectado": bool(clip_detectado),
        "clip_ratio": round(float(clip_ratio), 5),
        "clip_code": clip_code,
        "clip_descripcion_es": clip_txt["es"],
        "clip_descripcion_en": clip_txt["en"],
    }

def calcular_quality(a: Dict[str, Any], mode_code: str) -> Tuple[int, str, str]:
    score = 45

    snr = float(a.get("snr_db", 0.0))
    sala = float(a.get("sala_indice", 0.5))
    nivel_orig = float(a.get("nivel_original_dbfs", -24.0))
    clip = bool(a.get("clip_detectado", False))

    snr_clamped = max(10.0, min(40.0, snr))
    snr_contrib = (snr_clamped - 10.0) * (20.0 / 30.0)
    score += snr_contrib

    score += (1.0 - min(max(sala, 0.0), 1.0)) * 15.0

    if -26 <= nivel_orig <= -16:
        score += 10
    elif -32 <= nivel_orig < -26 or -16 < nivel_orig <= -10:
        score += 5
    else:
        score -= 5

    if clip:
        score -= 30
        score -= snr_contrib * 0.3

    if mode_code == "LAPTOP_CELULAR":
        score -= 5
    else:
        score += 5

    score = int(max(0, min(100, round(score))))

    # label por idioma
    if score < 40:
        label_es = "Necesita bastante trabajo antes de publicar"
        label_en = "Needs significant work before publishing"
    elif score < 70:
        label_es = "Aceptable, pero con margen de mejora"
        label_en = "Acceptable, but with room to improve"
    elif score < 85:
        label_es = "Listo para podcast con pequeños ajustes"
        label_en = "Podcast-ready with small tweaks"
    else:
        label_es = "Nivel muy sólido / casi profesional"
        label_en = "Very solid / near professional"

    return score, label_es, label_en

def procesar_audio_core(original_path: Path, mode_code: str) -> Tuple[Path, Dict[str, Any]]:
    audio = AudioSegment.from_file(original_path)
    analisis = analizar_audio(audio)

    TRIM_INICIO_MS = 300
    TRIM_FINAL_MS = 700

    dur_ms = len(audio)

    if dur_ms > (TRIM_INICIO_MS + TRIM_FINAL_MS):
        audio_proc_base = audio[TRIM_INICIO_MS : dur_ms - TRIM_FINAL_MS]
    elif dur_ms > TRIM_INICIO_MS:
        audio_proc_base = audio[TRIM_INICIO_MS:]
    else:
        audio_proc_base = audio

    audio_proc_base = audio_proc_base.high_pass_filter(80)
    audio_proc = effects.normalize(audio_proc_base)
    audio_proc = audio_proc.fade_out(120)

    analisis["nivel_final_dbfs"] = round(
        float(audio_proc.dBFS) if audio_proc.dBFS != float("-inf") else -90.0, 1
    )

    # Mantener code + labels
    mode_code = "MICROFONO_EXTERNO" if mode_code == "MICROFONO_EXTERNO" else "LAPTOP_CELULAR"
    analisis["mode_code"] = mode_code
    mlabels = mode_labels(mode_code)
    analisis["modo_es"] = mlabels["es"]
    analisis["modo_en"] = mlabels["en"]

    # compat: "modo" (lo usamos en métricas/legacy) lo dejamos en ES
    analisis["modo"] = analisis["modo_es"]

    analisis["duracion_original_s"] = round(dur_ms / 1000.0, 2)
    analisis["duracion_procesada_s"] = round(len(audio_proc) / 1000.0, 2)

    quality_score, q_es, q_en = calcular_quality(analisis, mode_code)
    analisis["quality_score"] = int(quality_score)
    analisis["quality_label_es"] = q_es
    analisis["quality_label_en"] = q_en
    analisis["quality_label"] = q_es  # compat

    processed_name = f"{original_path.stem}_PROCESADO.wav"
    processed_path = PROCESSED_DIR / processed_name
    audio_proc.export(processed_path, format="wav")

    return processed_path, analisis

def construir_informe_texto(nombre_original: str, a: Dict[str, Any], lang: str) -> str:
    lang = norm_lang(lang)

    modo = a["modo_en"] if lang == "en" else a["modo_es"]
    sala_desc = a["sala_descripcion_en"] if lang == "en" else a["sala_descripcion_es"]
    clip_desc = a["clip_descripcion_en"] if lang == "en" else a["clip_descripcion_es"]
    quality_label = a["quality_label_en"] if lang == "en" else a["quality_label_es"]

    delta_nivel = float(a["nivel_final_dbfs"]) - float(a["nivel_original_dbfs"])

    lines = []
    lines.append(tr(lang, "report.title"))
    lines.append("")
    lines.append(f"{tr(lang,'report.file')}: {nombre_original}")
    lines.append("")
    lines.append(tr(lang, "report.summary"))

    if lang == "en":
        lines.append(
            f"We processed your audio in {modo} mode. "
            f"Your room is estimated as {sala_desc} (index {a['sala_indice']}). "
            f"Estimated noise floor is around {a['ruido_estimado_dbfs']} dBFS. "
            f"After processing, the voice level changed by about {delta_nivel:+.1f} dB compared to the original."
        )
    else:
        lines.append(
            f"Procesamos tu audio en modo {modo}. "
            f"Tu sala se evalúa como {sala_desc} (índice {a['sala_indice']}). "
            f"El ruido de fondo estimado está en torno a {a['ruido_estimado_dbfs']} dBFS. "
            f"La voz quedó aproximadamente {delta_nivel:+.1f} dB respecto de la grabación original después del procesamiento."
        )

    lines.append("")
    lines.append(tr(lang, "report.trim_note"))
    lines.append("")
    lines.append(tr(lang, "report.keydata"))
    lines.append(f"- {tr(lang,'k.mode')}: {modo}")
    lines.append(f"- {tr(lang,'k.room')}: {sala_desc} (index {a['sala_indice']})" if lang=="en" else f"- {tr(lang,'k.room')}: {sala_desc} (índice {a['sala_indice']})")
    lines.append(f"- {tr(lang,'k.noise')}: {a['ruido_estimado_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.orig')}: {a['nivel_original_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.final')}: {a['nivel_final_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.snr')}: {a.get('snr_db', 0.0)} dB")
    lines.append(f"- {tr(lang,'k.peak')}: {a.get('peak_dbfs', 0.0)} dBFS")
    lines.append(f"- {tr(lang,'k.crest')}: {a.get('crest_factor_db', 0.0)} dB")
    lines.append(
        f"- {tr(lang,'k.clip')}: {tr(lang,'clip.prob') if a.get('clip_detectado') else tr(lang,'clip.none')}"
    )
    lines.append(
        f"- {tr(lang,'k.score')}: {a.get('quality_score','-')} / 100 ({quality_label})"
    )
    lines.append("")
    lines.append(tr(lang, "report.clip_comment"))
    lines.append(clip_desc)
    lines.append("")
    return "\n".join(lines)

def analysis_to_html(a: Dict[str, Any], lang: str) -> str:
    lang = norm_lang(lang)

    modo = a["modo_en"] if lang == "en" else a["modo_es"]
    sala_desc = a["sala_descripcion_en"] if lang == "en" else a["sala_descripcion_es"]
    clip_desc = a["clip_descripcion_en"] if lang == "en" else a["clip_descripcion_es"]
    quality_label = a["quality_label_en"] if lang == "en" else a["quality_label_es"]

    def li(label: str, value: Any) -> str:
        return f"<li><strong>{html_escape(label)}:</strong> {html_escape(str(value))}</li>"

    items = []
    items.append(li(tr(lang, "k.mode"), modo))
    items.append(li(tr(lang, "k.score"), f"{a.get('quality_score','-')} / 100 ({quality_label})"))
    items.append(li(tr(lang, "k.room"), f"{sala_desc} (index {a.get('sala_indice','-')})" if lang=="en" else f"{sala_desc} (índice {a.get('sala_indice','-')})"))
    items.append(li(tr(lang, "k.noise"), f"{a.get('ruido_estimado_dbfs','-')} dBFS"))
    items.append(li(tr(lang, "k.orig"), f"{a.get('nivel_original_dbfs','-')} dBFS"))
    items.append(li(tr(lang, "k.final"), f"{a.get('nivel_final_dbfs','-')} dBFS"))
    items.append(li(tr(lang, "k.snr"), f"{a.get('snr_db','-')} dB"))
    items.append(li("Clipping", tr(lang, "html.clip_yes") if a.get("clip_detectado") else tr(lang, "html.clip_no")))

    clip_html = f"<p style='margin-top:10px; opacity:.9'>{html_escape(str(clip_desc))}</p>" if clip_desc else ""

    return (
        "<div class='report-box'>"
        f"<h3 style='margin:0 0 6px 0;'>{html_escape(tr(lang,'html.title'))}</h3>"
        "<ul class='report-list'>"
        + "".join(items)
        + "</ul>"
        + clip_html
        + "</div>"
    )

async def _process_impl(
    request: Request,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile,
    mode_raw: str,
    lang_raw: Optional[str],
) -> JSONResponse:
    t0 = time.perf_counter()
    lang = norm_lang(lang_raw)

    raw_bytes = await audio_file.read(MAX_FILE_SIZE_BYTES + 1)
    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail=f"Max {MAX_FILE_SIZE_MB} MB")

    original_filename = audio_file.filename or "audio"
    original_filename = os.path.basename(original_filename).replace(" ", "_")
    if not original_filename:
        original_filename = "audio"

    safe_name = f"{int(time.time())}_{original_filename}"
    original_path = ORIGINAL_DIR / safe_name
    with original_path.open("wb") as f:
        f.write(raw_bytes)

    # Normaliza modo
    mode_code = "MICROFONO_EXTERNO" if str(mode_raw).strip() == "MICROFONO_EXTERNO" else "LAPTOP_CELULAR"

    try:
        processed_path, analysis = procesar_audio_core(original_path, mode_code)
    except Exception as e:
        logger.exception(f"Error procesando audio: {e}")
        raise HTTPException(status_code=400, detail="No se pudo procesar el audio (formato no soportado o falta ffmpeg).")

    report_name = f"{processed_path.stem}_report.txt"
    report_path = REPORT_DIR / report_name

    report_text = construir_informe_texto(safe_name, analysis, lang)
    report_path.write_text(report_text, encoding="utf-8")

    processing_ms = int(round((time.perf_counter() - t0) * 1000.0))

    if db_metrics_ready():
        try:
            ip = request.client.host if request.client else None
            ua = request.headers.get("user-agent")
            payload = {
                "id": str(uuid.uuid4()),
                "mode": analysis.get("modo"),
                "client_ip_hash": _anonymize_ip(ip),
                "user_agent": ua,

                "input_filename": safe_name,
                "input_bytes": int(len(raw_bytes)),
                "output_bytes": int(processed_path.stat().st_size) if processed_path.exists() else None,
                "report_bytes": int(report_path.stat().st_size) if report_path.exists() else None,

                "duration_original_s": float(analysis.get("duracion_original_s")) if analysis.get("duracion_original_s") is not None else None,
                "duration_processed_s": float(analysis.get("duracion_procesada_s")) if analysis.get("duracion_procesada_s") is not None else None,

                "processing_ms": processing_ms,

                "quality_score": int(analysis.get("quality_score")) if analysis.get("quality_score") is not None else None,
                "snr_db": float(analysis.get("snr_db")) if analysis.get("snr_db") is not None else None,
                "sala_indice": float(analysis.get("sala_indice")) if analysis.get("sala_indice") is not None else None,
                "clip_detectado": bool(analysis.get("clip_detectado")) if analysis.get("clip_detectado") is not None else None,
            }
            background_tasks.add_task(record_metrics, payload)
        except Exception as e:
            logger.warning(f"[DB_METRICS] No se pudieron preparar métricas: {e}")

    original_url = f"/media/original/{safe_name}"
    processed_url = f"/media/processed/{processed_path.name}"
    report_url = f"/media/reports/{report_name}"

    analysis_html = analysis_to_html(analysis, lang)

    return JSONResponse(
        {
            # Legacy (tu app.js actual)
            "original_audio_url": original_url,
            "processed_audio_url": processed_url,
            "report_url": report_url,
            "analysis_html": analysis_html,

            # Nuevas (por si después migras)
            "original_url": original_url,
            "processed_url": processed_url,
            "original_filename": original_filename,
            "analysis": analysis,
            "lang": lang,
        }
    )

# =========================
#   ENDPOINTS
# =========================

@app.post("/process")
async def process_legacy(request: Request, background_tasks: BackgroundTasks):
    form = await request.form()

    audio_file = form.get("file") or form.get("audio_file")
    mode = form.get("modo") or form.get("mode") or "LAPTOP_CELULAR"
    lang = form.get("lang") or form.get("language") or "es"

    if audio_file is None or not hasattr(audio_file, "read"):
        raise HTTPException(status_code=422, detail="Falta archivo (file).")

    return await _process_impl(request, background_tasks, audio_file, str(mode), str(lang))


@app.post("/api/process_audio")
async def process_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    mode: str = Form(...),
    lang: str = Form("es"),
):
    return await _process_impl(request, background_tasks, audio_file, mode, lang)
