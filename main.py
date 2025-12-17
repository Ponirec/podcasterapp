from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import time

import sys
import types
import os
import logging
import hashlib
import uuid

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
METRICS_SALT = os.getenv("METRICS_SALT", "").strip() or "change-me"  # cámbialo en Render

# Intentamos soportar psycopg2 (recomendado) o psycopg (v3)
DB_DRIVER = None
try:
    import psycopg2  # type: ignore
    DB_DRIVER = "psycopg2"
except Exception:
    try:
        import psycopg  # type: ignore
        DB_DRIVER = "psycopg"
    except Exception:
        DB_DRIVER = None

def db_metrics_ready() -> bool:
    if not ENABLE_DB_METRICS:
        return False
    if not DATABASE_URL:
        return False
    if DB_DRIVER is None:
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
    return h[:16]  # corto y suficiente para contar únicos sin guardar IP real

def _exec_sql(sql: str, params: Optional[dict] = None) -> None:
    """
    Ejecuta SQL. Si falla, solo loggea (no rompe flujo).
    """
    if not db_metrics_ready():
        return

    try:
        if DB_DRIVER == "psycopg2":
            import psycopg2  # type: ignore
            conn = psycopg2.connect(DATABASE_URL)
            conn.autocommit = True
            try:
                with conn.cursor() as cur:
                    cur.execute(sql, params)
            finally:
                conn.close()

        elif DB_DRIVER == "psycopg":
            import psycopg  # type: ignore
            with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql, params)

    except Exception as e:
        logger.warning(f"[DB_METRICS] Error ejecutando SQL: {e}")

def init_db() -> None:
    if not db_metrics_ready():
        if ENABLE_DB_METRICS and DB_DRIVER is None:
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

# Servir /media desde FastAPI
app.mount("/media", StaticFiles(directory=str(MEDIA_DIR)), name="media")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.on_event("startup")
def _startup():
    init_db()

# Ruta raíz: sirve index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")

@app.get("/health")
async def health():
    return {
        "ok": True,
        "db_metrics_enabled": ENABLE_DB_METRICS,
        "db_driver": DB_DRIVER,
        "db_url_present": bool(DATABASE_URL),
    }

# =========================
#   LÓGICA DE AUDIO
# =========================
def analizar_audio(audio: AudioSegment) -> Dict[str, Any]:
    """Devuelve métricas básicas del audio original, índice de sala, SNR y clipping."""

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

    if snr >= 55 and ruido_estimado <= -75:
        sala_indice = 0.1
        sala_desc = (
            "muy controlada (poca sala perceptible: micrófono muy cerca o espacio con buena absorción)"
        )
    elif snr >= 35 and ruido_estimado <= -60:
        sala_indice = 0.4
        sala_desc = "bastante controlada (pieza amoblada con varias cosas blandas)"
    elif snr >= 20:
        sala_indice = 0.7
        sala_desc = "con bastante reflexión (típico living o pieza con poco tratamiento)"
    else:
        sala_indice = 1.0
        sala_desc = "muy viva / con mucha reflexión (espacio duro o casi vacío, eco marcado)"

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
        clip_desc = (
            "Se detectan picos muy cercanos al máximo digital de forma repetida. "
            "Es probable que haya algo de distorsión/clip en la grabación original."
        )
    elif peak_ratio > 0.96:
        clip_desc = (
            "Tu señal llega muy cerca del máximo digital. No se ve clip claro, "
            "pero estás al límite: conviene bajar un poco la ganancia."
        )
    else:
        clip_desc = (
            "No se detectan señales claras de clip digital en la grabación."
        )

    return {
        "sala_descripcion": sala_desc,
        "sala_indice": round(sala_indice, 2),
        "ruido_estimado_dbfs": round(ruido_estimado, 1),
        "nivel_original_dbfs": round(nivel_dbfs, 1),
        "snr_db": round(snr, 1),
        "peak_dbfs": round(peak_db, 1),
        "crest_factor_db": round(crest_factor, 1),
        "clip_detectado": clip_detectado,
        "clip_ratio": round(clip_ratio, 5),
        "clip_descripcion": clip_desc,
    }

def calcular_quality(a: Dict[str, Any], modo: str) -> Tuple[int, str]:
    score = 45

    snr = a.get("snr_db", 0.0)
    sala = a.get("sala_indice", 0.5)
    nivel_orig = a.get("nivel_original_dbfs", -24.0)
    clip = a.get("clip_detectado", False)

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

    if "Laptop / Celular" in modo:
        score -= 5
    elif "Micrófono externo" in modo:
        score += 5

    score = int(max(0, min(100, round(score))))

    if score < 40:
        label = "Necesita bastante trabajo antes de publicar"
    elif score < 70:
        label = "Aceptable, pero con margen de mejora"
    elif score < 85:
        label = "Listo para podcast con pequeños ajustes"
    else:
        label = "Nivel muy sólido / casi profesional"

    return score, label

def recortar_final_despues_de_voz(
    audio: AudioSegment,
    chunk_ms: int = 150,
    umbral_rel_db: float = 25.0,
    margen_ms: int = 400,
    min_silencio_ms: int = 2000,
) -> AudioSegment:
    dur = len(audio)
    if dur <= chunk_ms * 2:
        return audio

    max_db = audio.max_dBFS if audio.max_dBFS != float("-inf") else -90.0
    limite_db = max_db - umbral_rel_db

    ultimo_util_ms = None

    for inicio in range(dur - chunk_ms, -1, -chunk_ms):
        trozo = audio[inicio: inicio + chunk_ms]
        nivel = trozo.dBFS if trozo.dBFS != float("-inf") else -90.0

        if nivel > limite_db:
            ultimo_util_ms = inicio + chunk_ms
            break

    if ultimo_util_ms is None:
        return audio

    silencio_ms = dur - ultimo_util_ms

    if silencio_ms < min_silencio_ms:
        return audio

    corte_ms = min(dur, ultimo_util_ms + margen_ms)
    return audio[:corte_ms]

def limpiar_golpe_tecla_final(
    audio: AudioSegment,
    ventana_ms: int = 180,
    umbral_db: float = -25.0,
    diferencia_db: float = 8.0,
) -> AudioSegment:
    dur = len(audio)
    if dur < ventana_ms * 2:
        return audio

    inicio_ultima = dur - ventana_ms
    inicio_prev = dur - 2 * ventana_ms

    bloque_prev = audio[inicio_prev:inicio_ultima]
    bloque_ult = audio[inicio_ultima:dur]

    prev_db = bloque_prev.dBFS if bloque_prev.dBFS != float("-inf") else -90.0
    ult_db = bloque_ult.dBFS if bloque_ult.dBFS != float("-inf") else -90.0

    if (ult_db > umbral_db) and (ult_db - prev_db >= diferencia_db):
        return audio[:inicio_ultima]

    return audio

def procesar_audio_core(original_path: Path, modo: str) -> Tuple[Path, Dict[str, Any]]:
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

    # 🔽 NUEVO: pequeño fade out global al final (120 ms aprox)
    audio_proc = audio_proc.fade_out(120)

    analisis["nivel_final_dbfs"] = round(
        float(audio_proc.dBFS) if audio_proc.dBFS != float("-inf") else -90.0, 1
    )
    analisis["modo"] = (
        "Laptop / Celular"
        if modo == "LAPTOP_CELULAR"
        else "Micrófono externo (USB / interfaz)"
    )
    analisis["duracion_original_s"] = round(dur_ms / 1000.0, 2)
    analisis["duracion_procesada_s"] = round(len(audio_proc) / 1000.0, 2)

    quality_score, quality_label = calcular_quality(analisis, analisis["modo"])
    analisis["quality_score"] = quality_score
    analisis["quality_label"] = quality_label

    processed_name = f"{original_path.stem}_PROCESADO.wav"
    processed_path = PROCESSED_DIR / processed_name
    audio_proc.export(processed_path, format="wav")

    return processed_path, analisis

def construir_informe_texto(nombre_original: str, a: Dict[str, Any]) -> str:
    lineas = []
    lineas.append("=== Informe de procesamiento de audio ===")
    lineas.append("")
    lineas.append(f"Archivo: {nombre_original}")
    lineas.append("")
    lineas.append("== Resumen general ==")

    delta_nivel = a["nivel_final_dbfs"] - a["nivel_original_dbfs"]

    lineas.append(
        f"Procesamos tu audio en modo {a['modo']}. "
        f"Tu sala se evalúa como {a['sala_descripcion']} (índice {a['sala_indice']}). "
        f"El ruido de fondo estimado está en torno a {a['ruido_estimado_dbfs']} dBFS. "
        f"La voz quedó aproximadamente {delta_nivel:+.1f} dB respecto de la grabación original "
        f"después del procesamiento."
    )
    lineas.append("")
    lineas.append(
        "Como parte del proceso, recortamos automáticamente un pequeño tramo al inicio "
        "y, cuando el audio es lo suficientemente largo, otro pequeño tramo al final para "
        "limpiar clics, ruidos de inicio/stop y silencios innecesarios."
    )
    lineas.append("")

    lineas.append("== Datos clave ==")
    lineas.append(f"- Modo: {a['modo']}")
    lineas.append(f"- Sala: {a['sala_descripcion']} (índice {a['sala_indice']})")
    lineas.append(f"- Ruido estimado: {a['ruido_estimado_dbfs']} dBFS")
    lineas.append(f"- Nivel de voz original: {a['nivel_original_dbfs']} dBFS")
    lineas.append(f"- Nivel de voz final: {a['nivel_final_dbfs']} dBFS")
    lineas.append(f"- Relación señal/ruido aproximada: {a.get('snr_db', 0.0)} dB")
    lineas.append(f"- Pico máximo aproximado: {a.get('peak_dbfs', 0.0)} dBFS")
    lineas.append(f"- Crest factor aproximado: {a.get('crest_factor_db', 0.0)} dB")
    lineas.append(
        f"- Clips / distorsión digital: "
        f"{'Probables' if a.get('clip_detectado') else 'No se detectan claros indicios'}"
    )
    lineas.append(
        f"- Puntaje de calidad: {a.get('quality_score', '-')} / 100 "
        f"({a.get('quality_label', '')})"
    )
    lineas.append("")

    lineas.append("== Qué hizo la app con tu archivo ==")
    lineas.append("- Analizó el nivel de tu voz, el ruido de fondo y el comportamiento de la sala.")
    lineas.append("- Recortó un pequeño tramo al inicio para limpiar ruidos de arranque y respiraciones muy pegadas.")
    lineas.append(
        "- Cuando la duración lo permitió, recortó ligeramente el final para reducir clics de stop y silencios largos."
    )
    lineas.append("- Aplicó un filtro pasa altos suave para limpiar graves innecesarios.")
    lineas.append("- Ajustó el nivel global para dejar tu voz en un rango más cómodo para escucha tipo podcast.")
    lineas.append("")

    lineas.append("== Comentario sobre clipping ==")
    lineas.append(a.get("clip_descripcion", "Sin datos de clipping."))
    lineas.append("")

    modo = a.get("modo", "")
    nivel_orig = a.get("nivel_original_dbfs", -20.0)
    snr = a.get("snr_db", 0.0)
    sala_ind = a.get("sala_indice", 0.5)
    clip = a.get("clip_detectado", False)

    recomendaciones = []

    if "Laptop" in modo:
        recomendaciones.append(
            "Estás grabando con el micrófono del equipo (laptop / celular). "
            "Si puedes, da el salto a un micrófono externo sencillo (USB o interfaz), "
            "vas a notar una mejora grande en claridad y ruido."
        )
    else:
        recomendaciones.append(
            "Estás grabando con un micrófono externo. Es una muy buena base para lograr "
            "un sonido de podcast más profesional."
        )

    if nivel_orig <= -30:
        recomendaciones.append(
            "Tu nivel de voz original llegó bastante bajo. Para la próxima, acércate un poco más "
            "al micrófono y/o sube la ganancia del preamp hasta que tu voz quede alrededor de "
            "-24 a -18 dBFS en los picos normales de habla."
        )
    elif -24 <= nivel_orig <= -16:
        if clip:
            recomendaciones.append(
                "Aunque el nivel medio de tu voz no es extremo, se detecta distorsión por estar muy al límite. "
                "Baja un poco la ganancia de entrada o aléjate unos centímetros del micrófono para evitar clip digital."
            )
        else:
            recomendaciones.append(
                "El nivel de voz original está dentro de un rango saludable para mezcla. "
                "Solo necesitas mantener la distancia y el volumen que usaste al grabar."
            )
    elif nivel_orig > -16:
        recomendaciones.append(
            "Tu nivel de voz original llegó bastante alto. Si en algún momento escuchas distorsión, "
            "baja un poco la ganancia del micrófono o aléjate unos centímetros para evitar el clipeo."
        )

    if snr < 18:
        recomendaciones.append(
            "Hay bastante ruido de fondo (baja relación señal/ruido). Revisa si puedes apagar ventiladores, "
            "PC muy ruidosos, o cerrar ventanas para reducir tráfico y ruidos de ambiente."
        )
    elif 18 <= snr < 30:
        recomendaciones.append(
            "El ruido de fondo es moderado. Para mejorar todavía más, intenta grabar cuando el entorno esté "
            "más silencioso (noche / horarios tranquilos) o aléjate de fuentes de ruido constantes."
        )
    else:
        recomendaciones.append(
            "La relación señal/ruido es buena: tu voz está claramente por encima del ruido de fondo. "
            "Es un buen punto de partida para procesar sin artefactos agresivos."
        )

    if sala_ind >= 0.75:
        recomendaciones.append(
            "La sala suena bastante viva (muchas reflexiones). Para mejorar, suma absorción casera alrededor: "
            "frazadas, colchones, sofás, cortinas gruesas, alfombras y ropa ayudan mucho a matar el eco."
        )
    elif 0.4 < sala_ind < 0.75:
        recomendaciones.append(
            "Tu sala tiene algo de reflexión, pero está en un rango manejable. Si quieres un sonido aún más seco, "
            "añade un poco más de material blando alrededor del punto de grabación."
        )
    else:
        recomendaciones.append(
            "Tu sala está bastante controlada en reflexiones. Es un muy buen entorno para grabar voz, "
            "solo cuida el nivel de ruido de fondo y la distancia al micrófono."
        )

    if abs(delta_nivel) < 1.0:
        recomendaciones.append(
            "La app casi no tuvo que corregir el nivel global porque tu grabación ya venía bien "
            "equilibrada en volumen."
        )
    elif delta_nivel > 0:
        recomendaciones.append(
            "La app subió el nivel general de la voz para llevarla a un rango más consistente de escucha."
        )
    else:
        recomendaciones.append(
            "La app bajó el nivel general de la voz para evitar picos demasiado altos y dejar más margen "
            "para la mezcla y master."
        )

    if clip:
        recomendaciones.append(
            "Al detectar probable clip digital, es recomendable repetir la toma con un poco menos de ganancia "
            "si se trata de un material importante (entrevista, episodio principal, etc.)."
        )

    recomendaciones.append(
        "Para aprovechar mejor la app, deja alrededor de 1 segundo de silencio antes de empezar a hablar "
        "y otro segundo al terminar. Eso ayuda a limpiar clics de teclado, ruidos de stop y respiraciones bruscas."
    )

    lineas.append("== Cómo mejorar tu próxima grabación ==")
    for rec in recomendaciones:
        lineas.append(f"- {rec}")
    lineas.append("")

    return "\n".join(lineas)

# =========================
#   ENDPOINT
# =========================
@app.post("/api/process_audio")
async def process_audio(
    request: Request,
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    mode: str = Form(...),
):
    t0 = time.perf_counter()

    raw_bytes = await audio_file.read(MAX_FILE_SIZE_BYTES + 1)

    if len(raw_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                f"El archivo es demasiado pesado. "
                f"Tamaño máximo permitido: {MAX_FILE_SIZE_MB} MB. "
                "Prueba subiendo un extracto más corto de tu audio."
            ),
        )

    safe_suffix = audio_file.filename.replace(" ", "_")
    safe_name = f"{int(time.time())}_{safe_suffix}"

    original_path = ORIGINAL_DIR / safe_name
    with original_path.open("wb") as f:
        f.write(raw_bytes)

    processed_path, analysis = procesar_audio_core(original_path, mode)

    report_name = f"{processed_path.stem}_report.txt"
    report_path = REPORT_DIR / report_name
    report_text = construir_informe_texto(safe_name, analysis)
    report_path.write_text(report_text, encoding="utf-8")

    processing_ms = int(round((time.perf_counter() - t0) * 1000.0))

    # --- MÉTRICAS (NO ROMPEN FLUJO) ---
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

    return JSONResponse(
        {
            "original_url": f"/media/original/{safe_name}",
            "processed_url": f"/media/processed/{processed_path.name}",
            "report_url": f"/media/reports/{report_name}",
            "original_filename": audio_file.filename,
            "analysis": analysis,
        }
    )
