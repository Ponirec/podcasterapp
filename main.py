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
import subprocess
import tempfile
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
#   LÍMITE DE TAMAÑO
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
        return {"es": "Micrófono externo (USB / interfaz)", "en": "External microphone (USB / interface)"}
    return {"es": "Laptop / Celular", "en": "Laptop / Phone"}

def sala_labels(sala_code: str) -> Dict[str, str]:
    # Copy más prudente (no afirma “eco marcado” si no lo medimos de verdad)
    m = {
        "very_controlled": {
            "es": "muy controlada (fondo bien bajo y voz clara)",
            "en": "very controlled (low background and clear voice)",
        },
        "controlled": {
            "es": "bastante controlada (fondo moderado, voz entendible)",
            "en": "quite controlled (moderate background, intelligible voice)",
        },
        "reflective_or_busy": {
            "es": "con poca separación voz/fondo (puede haber reflexión o ambiente activo)",
            "en": "low voice/background separation (could be reflections or a busy environment)",
        },
        "very_busy": {
            "es": "ambiente difícil (fondo alto o poca separación voz/fondo)",
            "en": "challenging environment (high background or low separation)",
        },
        "unknown": {
            "es": "no concluyente (no detectamos pausas claras para estimar el fondo)",
            "en": "inconclusive (no clear pauses to estimate background)",
        },
    }
    return m.get(sala_code, m["controlled"])

def clip_labels(clip_code: str) -> Dict[str, str]:
    # “clipping” solo si es realmente probable; si no, “señal al límite”
    m = {
        "clipping_detected": {
            "es": "Probable distorsión/clipping. Si puedes, regraba con menos ganancia (baja el input). Esto no siempre se puede reparar.",
            "en": "Likely clipping/distortion. If you can, re-record with lower input gain. This can't always be fixed.",
        },
        "hot_signal": {
            "es": "Señal al límite (picos muy altos). Recomendado bajar un poco la ganancia para evitar problemas al exportar/convertir.",
            "en": "Hot signal (very high peaks). Consider lowering gain a bit to avoid issues when exporting/encoding.",
        },
        "no_clipping": {
            "es": "No se detectan señales claras de clip digital.",
            "en": "No clear signs of digital clipping detected.",
        },
    }
    return m.get(clip_code, m["no_clipping"])

def tr(lang: str, key: str) -> str:
    lang = norm_lang(lang)
    D = {
        "es": {
            "report.title": "=== Informe de procesamiento de audio ===",
            "report.file": "Archivo",
            "report.quick": "== Resumen rápido ==",
            "report.summary": "== Resumen general ==",
            "report.keydata": "== Datos clave (opcional) ==",
            "report.clip_comment": "== Comentario sobre picos/clipping ==",
            "report.trim_note": "Aplicamos un recorte muy breve al inicio y al final para limpiar clics/ruidos y silencios innecesarios.",
            "k.mode": "Modo",
            "k.room": "Ambiente",
            "k.noise": "Fondo estimado",
            "k.noise_conf": "Confiabilidad fondo",
            "k.orig": "Nivel de voz original",
            "k.final": "Nivel de voz final",
            "k.snr": "Separación voz/fondo (aprox.)",
            "k.peak": "Pico máximo aproximado",
            "k.crest": "Crest factor aproximado",
            "k.clip": "Picos / clipping",
            "k.score": "Puntaje",
            "conf.low": "baja (pocas pausas detectadas)",
            "conf.ok": "ok",
            "html.title": "Resumen",
        },
        "en": {
            "report.title": "=== Audio processing report ===",
            "report.file": "File",
            "report.quick": "== Quick summary ==",
            "report.summary": "== General summary ==",
            "report.keydata": "== Key data (optional) ==",
            "report.clip_comment": "== Peak/clipping comment ==",
            "report.trim_note": "We apply a very short trim at the start and end to remove clicks/noises and unnecessary silence.",
            "k.mode": "Mode",
            "k.room": "Environment",
            "k.noise": "Estimated background",
            "k.noise_conf": "Background confidence",
            "k.orig": "Original voice level",
            "k.final": "Final voice level",
            "k.snr": "Voice/background separation (approx.)",
            "k.peak": "Approx. max peak",
            "k.crest": "Approx. crest factor",
            "k.clip": "Peaks / clipping",
            "k.score": "Score",
            "conf.low": "low (few pauses detected)",
            "conf.ok": "ok",
            "html.title": "Summary",
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
#   Audio utils
# =========================
LOSSY_EXTS = {"mp3", "m4a", "aac", "ogg", "opus", "wma"}

def file_ext_lower(path: Path) -> str:
    return (path.suffix or "").lower().lstrip(".")

def apply_ceiling_dbfs(audio: AudioSegment, ceiling_dbfs: float = -1.0) -> AudioSegment:
    if audio.max_dBFS == float("-inf"):
        return audio
    if audio.max_dBFS > ceiling_dbfs:
        return audio.apply_gain(ceiling_dbfs - audio.max_dBFS)
    return audio

def ffmpeg_compresor_la76_sutil(input_wav: Path, output_wav: Path) -> None:
    """
    Compresión sutil tipo 1176 (rápida) + limitador.
    Si ffmpeg no está disponible, se manejará excepción y se hará fallback.
    """
    limit_amp = 10 ** (-1 / 20)  # -1 dBFS ~ 0.8913
    filtergraph = (
        "acompressor=threshold=0.16:ratio=4:attack=5:release=80:knee=2.5:makeup=1.5:mix=1,"
        f"alimiter=limit={limit_amp}:attack=5:release=60:level=false"
    )
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(input_wav),
        "-af", filtergraph,
        "-c:a", "pcm_s16le",
        str(output_wav),
    ]
    subprocess.run(cmd, check=True)

# =========================
#   ANALISIS
# =========================
def analizar_audio(audio: AudioSegment, original_path: Optional[Path] = None) -> Dict[str, Any]:
    dur_ms = len(audio)
    nivel_dbfs = float(audio.dBFS) if audio.dBFS != float("-inf") else -90.0

    # Estimar “fondo” usando ventanas; percentil 10% (no 25%) para reducir sesgo si casi no hay pausas.
    chunk_ms = 200
    niveles: list[float] = []
    for i in range(0, dur_ms, chunk_ms):
        c = audio[i: i + chunk_ms]
        v = float(c.dBFS) if c.dBFS != float("-inf") else -90.0
        niveles.append(v)

    niveles.sort()
    ruido_estimado = -80.0
    ruido_confiable = True

    if niveles:
        n_sub = max(1, len(niveles) // 10)  # ✅ 10% más bajo
        ruido_estimado = sum(niveles[:n_sub]) / n_sub
        # Si ni siquiera el “10% más bajo” baja de cierto umbral, probablemente no hubo pausas limpias.
        if ruido_estimado > -45.0:
            ruido_confiable = False

    # Limitar para no inventar fondos absurdos
    ruido_estimado = max(ruido_estimado, -80.0)

    snr = nivel_dbfs - ruido_estimado

    # Ambiente (copy prudente)
    if not ruido_confiable:
        sala_code = "unknown"
        sala_indice = 0.7
    else:
        if snr >= 40 and ruido_estimado <= -70:
            sala_code = "very_controlled"
            sala_indice = 0.15
        elif snr >= 28 and ruido_estimado <= -58:
            sala_code = "controlled"
            sala_indice = 0.45
        elif snr >= 18:
            sala_code = "reflective_or_busy"
            sala_indice = 0.75
        else:
            sala_code = "very_busy"
            sala_indice = 1.0

    sala_txt = sala_labels(sala_code)

    # Peak/clipping heurística
    sample_width = audio.sample_width
    max_possible = float((1 << (8 * sample_width - 1)) - 1)

    samples = audio.get_array_of_samples()
    if samples:
        max_abs = max(abs(s) for s in samples)
        peak_ratio = max_abs / max_possible
        clip_samples = sum(1 for s in samples if abs(s) >= 0.985 * max_possible)
        clip_ratio = clip_samples / len(samples)
    else:
        peak_ratio = 0.0
        clip_ratio = 0.0

    peak_db = audio.max_dBFS if audio.max_dBFS != float("-inf") else -90.0
    crest_factor = peak_db - nivel_dbfs

    ext = file_ext_lower(original_path) if original_path else ""
    is_lossy = ext in LOSSY_EXTS

    # Para archivos lossy, ser más conservador (menos falsos positivos)
    if is_lossy:
        clip_detectado = (peak_ratio > 0.995) and (clip_ratio > 0.0020)
        hot_signal = (peak_ratio > 0.985)
    else:
        clip_detectado = (peak_ratio > 0.992) and (clip_ratio > 0.0010)
        hot_signal = (peak_ratio > 0.98)

    if clip_detectado:
        clip_code = "clipping_detected"
    elif hot_signal:
        clip_code = "hot_signal"
    else:
        clip_code = "no_clipping"

    clip_txt = clip_labels(clip_code)

    return {
        "file_ext": ext,
        "is_lossy": bool(is_lossy),

        "sala_code": sala_code,
        "sala_indice": round(float(sala_indice), 2),
        "sala_descripcion_es": sala_txt["es"],
        "sala_descripcion_en": sala_txt["en"],

        "ruido_estimado_dbfs": round(float(ruido_estimado), 1),
        "ruido_confiable": bool(ruido_confiable),
        "nivel_original_dbfs": round(float(nivel_dbfs), 1),
        "snr_db": round(float(snr), 1),

        "peak_dbfs": round(float(peak_db), 1),
        "crest_factor_db": round(float(crest_factor), 1),

        "clip_detectado": bool(clip_detectado),
        "hot_signal": bool(hot_signal),
        "clip_ratio": round(float(clip_ratio), 5),
        "clip_code": clip_code,
        "clip_descripcion_es": clip_txt["es"],
        "clip_descripcion_en": clip_txt["en"],
    }

def calcular_quality(a: Dict[str, Any], mode_code: str) -> Tuple[int, str, str]:
    score = 55

    snr = float(a.get("snr_db", 0.0))
    sala = float(a.get("sala_indice", 0.5))
    nivel_orig = float(a.get("nivel_original_dbfs", -24.0))
    clip_code = str(a.get("clip_code", "no_clipping"))
    ruido_confiable = bool(a.get("ruido_confiable", True))
    is_lossy = bool(a.get("is_lossy", False))

    # SNR contribución (si no es confiable, pesa menos)
    snr_clamped = max(10.0, min(40.0, snr))
    snr_contrib = (snr_clamped - 10.0) * (18.0 / 30.0)  # hasta +18
    if not ruido_confiable:
        snr_contrib *= 0.45
    score += snr_contrib

    # Sala/ambiente (ligero)
    score += (1.0 - min(max(sala, 0.0), 1.0)) * 12.0

    # Nivel original (solo para orientar)
    if -26 <= nivel_orig <= -16:
        score += 8
    elif -32 <= nivel_orig < -26 or -16 < nivel_orig <= -10:
        score += 4
    else:
        score -= 4

    # Penalizaciones por picos/clipping (más suaves, especialmente en lossy)
    if clip_code == "clipping_detected":
        score -= 22 if not is_lossy else 16
    elif clip_code == "hot_signal":
        score -= 8 if not is_lossy else 6

    # Modo (micro externo bonus leve)
    if mode_code == "LAPTOP_CELULAR":
        score -= 3
    else:
        score += 3

    score = int(max(0, min(100, round(score))))

    # Labels más justos (especialmente si clipping)
    if clip_code == "clipping_detected":
        label_es = "Picos/clipping probable: conviene regrabar con menos ganancia"
        label_en = "Likely clipping/overload: consider re-recording with lower input gain"
    elif clip_code == "hot_signal":
        label_es = "Señal al límite: baja un poco la ganancia para ir seguro"
        label_en = "Hot signal: lower gain slightly to stay safe"
    elif score < 40:
        label_es = "Necesita ajustes antes de publicar"
        label_en = "Needs adjustments before publishing"
    elif score < 70:
        label_es = "Aceptable, pero con margen de mejora"
        label_en = "Acceptable, with room to improve"
    elif score < 85:
        label_es = "Listo para podcast con pequeños ajustes"
        label_en = "Podcast-ready with small tweaks"
    else:
        label_es = "Nivel muy sólido / casi profesional"
        label_en = "Very solid / near professional"

    return score, label_es, label_en

# =========================
#   PROCESAMIENTO
# =========================
def procesar_audio_core(original_path: Path, mode_code: str) -> Tuple[Path, Dict[str, Any]]:
    audio = AudioSegment.from_file(original_path)
    analisis = analizar_audio(audio, original_path=original_path)

    # Recortes más conservadores (evita “comerse” palabra)
    TRIM_INICIO_MS = 120
    TRIM_FINAL_MS = 200

    dur_ms = len(audio)
    if dur_ms > (TRIM_INICIO_MS + TRIM_FINAL_MS):
        audio_proc_base = audio[TRIM_INICIO_MS : dur_ms - TRIM_FINAL_MS]
    elif dur_ms > TRIM_INICIO_MS:
        audio_proc_base = audio[TRIM_INICIO_MS:]
    else:
        audio_proc_base = audio

    # Limpieza básica
    audio_proc_base = audio_proc_base.high_pass_filter(80)

    # Compresión + limitador (sutil), con fallback si no hay ffmpeg
    audio_proc: AudioSegment
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            pre = tmpdir / "pre.wav"
            post = tmpdir / "post.wav"
            audio_proc_base.export(pre, format="wav")
            ffmpeg_compresor_la76_sutil(pre, post)
            audio_proc = AudioSegment.from_file(post)
    except Exception as e:
        logger.warning(f"[AUDIO] Fallback sin ffmpeg/filters: {e}")
        # Fallback suave: normalizar pero dejando techo seguro -1 dBFS
        audio_proc = effects.normalize(audio_proc_base)
        audio_proc = apply_ceiling_dbfs(audio_proc, -1.0)

    # Fade out leve para evitar clicks al final
    audio_proc = audio_proc.fade_out(120)

    # Techo final (seguro)
    audio_proc = apply_ceiling_dbfs(audio_proc, -1.0)



    analisis["nivel_final_dbfs"] = round(
        float(audio_proc.dBFS) if audio_proc.dBFS != float("-inf") else -90.0, 1
    )

    # Peak real del PROCESADO (post techo)
    analisis["peak_dbfs"] = round(
        float(audio_proc.max_dBFS) if audio_proc.max_dBFS != float("-inf") else -90.0, 1
    )

    # Crest factor del PROCESADO (pico - nivel promedio)
    analisis["crest_factor_db"] = round(
        float(analisis["peak_dbfs"] - analisis["nivel_final_dbfs"]), 1
    )

    # Recalcular SOLO el bloque de picos/clipping para que el reporte sea coherente con el procesado
    a_proc = analizar_audio(audio_proc, original_path=original_path)
    for k in ("clip_detectado", "hot_signal", "clip_ratio", "clip_code", "clip_descripcion_es", "clip_descripcion_en"):
        analisis[k] = a_proc[k]


    # Normaliza modo
    mode_code = "MICROFONO_EXTERNO" if mode_code == "MICROFONO_EXTERNO" else "LAPTOP_CELULAR"
    analisis["mode_code"] = mode_code
    mlabels = mode_labels(mode_code)
    analisis["modo_es"] = mlabels["es"]
    analisis["modo_en"] = mlabels["en"]
    analisis["modo"] = analisis["modo_es"]  # compat

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

# =========================
#   REPORT (TXT + HTML)
# =========================
def construir_informe_texto(nombre_original: str, a: Dict[str, Any], lang: str) -> str:
    lang = norm_lang(lang)

    modo = a["modo_en"] if lang == "en" else a["modo_es"]
    ambiente = a["sala_descripcion_en"] if lang == "en" else a["sala_descripcion_es"]
    clip_desc = a["clip_descripcion_en"] if lang == "en" else a["clip_descripcion_es"]
    quality_label = a["quality_label_en"] if lang == "en" else a["quality_label_es"]

    delta_nivel = float(a["nivel_final_dbfs"]) - float(a["nivel_original_dbfs"])
    ruido_conf = tr(lang, "conf.ok") if a.get("ruido_confiable", True) else tr(lang, "conf.low")

    # Resumen “humano” (pero NO lo usaremos en el resumen rápido para no saturar)
    cambio_txt_es = "cambio sutil" if abs(delta_nivel) < 1.5 else ("cambio moderado" if abs(delta_nivel) < 5 else "cambio fuerte")
    cambio_txt_en = "subtle change" if abs(delta_nivel) < 1.5 else ("moderate change" if abs(delta_nivel) < 5 else "strong change")

    # Tips principales (cortos)
    if lang == "en":
        score_line = f"Score: {a.get('quality_score','-')} / 100 — {quality_label}"
        peak_line = f"Safety: max peak ~ {a.get('peak_dbfs', '-')} dBFS"
        main_hint_1 = "Lower input gain a bit (avoid very hot peaks)."
        main_hint_2 = "Add 1 second of silence at the start/end for better background estimation."
    else:
        score_line = f"Puntaje: {a.get('quality_score','-')} / 100 — {quality_label}"
        peak_line = f"Seguridad: pico máx. ~ {a.get('peak_dbfs', '-')} dBFS"
        main_hint_1 = "Baja un poco la ganancia al grabar (evita picos al límite)."
        main_hint_2 = "Deja 1 segundo de silencio al inicio/fin para estimar mejor el fondo."

    # Tips educativos para grabación casera
    if lang == "en":
        edu_title = "== Tips to record better at home =="
        edu = [
            "Choose a room with soft stuff (curtains, carpet, sofa). Avoid empty rooms.",
            "Don't face a hard wall. Aim the mic toward a blanket/curtain 30–60 cm away.",
            "DIY booth: record near a closet full of clothes or hang a blanket behind you.",
            "Mic distance: 10–15 cm with a pop filter (or 15–20 cm slightly off-axis).",
            "Reduce noise: turn off fan/AC, close windows, keep the mic away from the laptop.",
            "Record 5–10 seconds of silence at the start to help noise estimation/cleanup.",
        ]
    else:
        edu_title = "== Tips para grabar mejor en casa =="
        edu = [
            "Elige una pieza con cosas blandas (cortinas, alfombra, sofá). Evita piezas vacías.",
            "No grabes mirando una pared dura. Mejor apunta el mic hacia una manta/cortina a 30–60 cm.",
            "Cabina casera: graba cerca de un closet con ropa o cuelga una manta detrás tuyo.",
            "Distancia al mic: 10–15 cm con pop filter (o 15–20 cm y un poco de lado).",
            "Reduce ruido: apaga ventilador/AC, cierra ventanas, aleja el mic del notebook.",
            "Graba 5–10 s de “silencio” al inicio para ayudar a estimar el fondo/limpieza.",
        ]

    lines = []
    lines.append(tr(lang, "report.title"))
    lines.append("")
    lines.append(f"{tr(lang,'report.file')}: {nombre_original}")
    lines.append("")

    # ✅ Resumen rápido: 4 líneas máximo
    lines.append(tr(lang, "report.quick"))
    lines.append(f"- {score_line}")
    lines.append(f"- {peak_line}")
    lines.append(f"- Tip #1: {main_hint_1}")
    lines.append(f"- Tip #2: {main_hint_2}")
    lines.append("")

    # ✅ Sección educativa (valor real sin llenar el resumen)
    lines.append(edu_title)
    for tip in edu:
        lines.append(f"- {tip}")
    lines.append("")

    # Resumen general (puede quedar, pero sin sobrecargar arriba)
    lines.append(tr(lang, "report.summary"))
    if lang == "en":
        lines.append(
            f"We processed your audio in {modo} mode. "
            f"Environment estimate: {ambiente}. "
            f"Estimated background: {a['ruido_estimado_dbfs']} dBFS (confidence: {ruido_conf})."
        )
    else:
        lines.append(
            f"Procesamos tu audio en modo {modo}. "
            f"Estimación de ambiente: {ambiente}. "
            f"Fondo estimado: {a['ruido_estimado_dbfs']} dBFS (confiabilidad: {ruido_conf})."
        )
    lines.append("")

    lines.append(tr(lang, "report.trim_note"))
    lines.append("")

    # Datos técnicos (opcional)
    lines.append(tr(lang, "report.keydata"))
    lines.append(f"- {tr(lang,'k.mode')}: {modo}")
    lines.append(f"- {tr(lang,'k.room')}: {ambiente} (índice {a['sala_indice']})" if lang=="es" else f"- {tr(lang,'k.room')}: {ambiente} (index {a['sala_indice']})")
    lines.append(f"- {tr(lang,'k.noise')}: {a['ruido_estimado_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.noise_conf')}: {ruido_conf}")
    lines.append(f"- {tr(lang,'k.orig')}: {a['nivel_original_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.final')}: {a['nivel_final_dbfs']} dBFS")
    lines.append(f"- {tr(lang,'k.snr')}: {a.get('snr_db', 0.0)} dB")
    lines.append(f"- {tr(lang,'k.peak')}: {a.get('peak_dbfs', 0.0)} dBFS")
    lines.append(f"- {tr(lang,'k.crest')}: {a.get('crest_factor_db', 0.0)} dB")
    lines.append(f"- {tr(lang,'k.score')}: {a.get('quality_score','-')} / 100 ({quality_label})")
    lines.append("")
    lines.append(tr(lang, "report.clip_comment"))
    lines.append(clip_desc)
    lines.append("")
    return "\n".join(lines)


def analysis_to_html(a: Dict[str, Any], lang: str) -> str:
    lang = norm_lang(lang)

    modo = a["modo_en"] if lang == "en" else a["modo_es"]
    ambiente = a["sala_descripcion_en"] if lang == "en" else a["sala_descripcion_es"]
    clip_desc = a["clip_descripcion_en"] if lang == "en" else a["clip_descripcion_es"]
    quality_label = a["quality_label_en"] if lang == "en" else a["quality_label_es"]
    ruido_conf = tr(lang, "conf.ok") if a.get("ruido_confiable", True) else tr(lang, "conf.low")

    delta_nivel = float(a["nivel_final_dbfs"]) - float(a["nivel_original_dbfs"])
    cambio_txt = ("sutil" if abs(delta_nivel) < 1.5 else ("moderado" if abs(delta_nivel) < 5 else "fuerte")) if lang=="es" else (
        "subtle" if abs(delta_nivel) < 1.5 else ("moderate" if abs(delta_nivel) < 5 else "strong")
    )

    def li(label: str, value: Any) -> str:
        return f"<li><strong>{html_escape(label)}:</strong> {html_escape(str(value))}</li>"

    items = []
    items.append(li(tr(lang, "k.score"), f"{a.get('quality_score','-')} / 100 — {quality_label}"))
    items.append(li("Cambio", f"{delta_nivel:+.1f} dB ({cambio_txt})" if lang=="es" else f"{delta_nivel:+.1f} dB ({cambio_txt})"))
    items.append(li(tr(lang, "k.mode"), modo))
    items.append(li(tr(lang, "k.room"), f"{ambiente} (idx {a.get('sala_indice','-')})"))
    items.append(li(tr(lang, "k.noise"), f"{a.get('ruido_estimado_dbfs','-')} dBFS ({ruido_conf})"))
    items.append(li(tr(lang, "k.orig"), f"{a.get('nivel_original_dbfs','-')} dBFS"))
    items.append(li(tr(lang, "k.final"), f"{a.get('nivel_final_dbfs','-')} dBFS"))
    items.append(li(tr(lang, "k.clip"), clip_desc))

    return (
        "<div class='report-box'>"
        f"<h3 style='margin:0 0 6px 0;'>{html_escape(tr(lang,'html.title'))}</h3>"
        "<ul class='report-list'>"
        + "".join(items)
        + "</ul>"
        + "</div>"
    )

# =========================
#   ENDPOINT IMPLEMENTATION
# =========================
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
            # Legacy (tu app.js)
            "original_audio_url": original_url,
            "processed_audio_url": processed_url,
            "report_url": report_url,
            "analysis_html": analysis_html,

            # Extra
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