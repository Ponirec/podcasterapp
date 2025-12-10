from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
from typing import Dict, Any, Tuple
import time

# audioop estándar (Python <= 3.12) o audioop-lts (Python 3.13+ en Render)
try:
    import audioop  # stdlib
except ImportError:  # en Render con Python 3.13
    import audioop_lts as audioop  # type: ignore[import]


from pydub import AudioSegment, effects


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


# Ruta raíz: sirve index.html
@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = STATIC_DIR / "index.html"
    return index_path.read_text(encoding="utf-8")

# =========================
#   LÓGICA DE AUDIO
# =========================

def analizar_audio(audio: AudioSegment) -> Dict[str, Any]:
    """Devuelve métricas básicas del audio original, índice de sala, SNR y clipping."""

    dur_ms = len(audio)

    # Nivel global de la grabación (voz + ruido)
    nivel_dbfs = float(audio.dBFS) if audio.dBFS != float("-inf") else -90.0

    # Estimar ruido mirando el 25% más bajo de los trozos
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

    # No dejamos que baje de -80 dBFS para no sobrerrepresentar silencio digital
    ruido_estimado = max(ruido_estimado, -80.0)

    # Relación señal/ruido (SNR) en dB
    snr = nivel_dbfs - ruido_estimado  # ambos negativos

    # Clasificación de sala
    if snr >= 55 and ruido_estimado <= -75:
        # Escenario muy "seco": puede ser cabina o simplemente mic muy cerca
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

    # --------------------
    # Detección de clip
    # --------------------
    # Miramos los samples crudos para ver qué tan cerca están del máximo digital
    sample_width = audio.sample_width  # bytes
    max_possible = float((1 << (8 * sample_width - 1)) - 1)

    samples = audio.get_array_of_samples()
    if samples:
        max_abs = max(abs(s) for s in samples)
        peak_ratio = max_abs / max_possible  # 1.0 == full scale
        clip_samples = sum(1 for s in samples if abs(s) >= 0.98 * max_possible)
        clip_ratio = clip_samples / len(samples)
    else:
        peak_ratio = 0.0
        clip_ratio = 0.0

    # Nivel pico en dBFS (pydub ya lo trae)
    peak_db = audio.max_dBFS if audio.max_dBFS != float("-inf") else -90.0

    # Crest factor aproximado: diferencia entre pico y nivel medio
    crest_factor = peak_db - nivel_dbfs

    # Heurística simple de clip
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
    """
    Calcula un puntaje de calidad 0–100 y una etiqueta textual
    en base a SNR, sala, nivel, clipping y dispositivo.
    """
    score = 45  # base un poco más baja

    snr = a.get("snr_db", 0.0)
    sala = a.get("sala_indice", 0.5)
    nivel_orig = a.get("nivel_original_dbfs", -24.0)
    clip = a.get("clip_detectado", False)

    # A) SNR: más SNR, más puntos (máx +20)
    snr_clamped = max(10.0, min(40.0, snr))
    snr_contrib = (snr_clamped - 10.0) * (20.0 / 30.0)  # 10 → 0 pts, 40 → +20 pts
    score += snr_contrib

    # B) Sala: 0.0 (pro) → +15, 1.0 (horrible) → 0
    score += (1.0 - min(max(sala, 0.0), 1.0)) * 15.0

    # C) Nivel original (ideal aprox -24 a -18 dBFS)
    if -26 <= nivel_orig <= -16:
        score += 10  # nivel muy sano
    elif -32 <= nivel_orig < -26 or -16 < nivel_orig <= -10:
        score += 5   # aceptable
    else:
        score -= 5   # nivel muy bajo o muy al límite

    # D) Clipping: castigo más fuerte,
    # y además reducimos el peso del buen SNR (que se ve inflado en audios muy calientes)
    if clip:
        score -= 30               # castigo base fuerte
        score -= snr_contrib * 0.3  # penalizar un poco el "SNR bonito" con clip

    # E) Dispositivo: penalizar un poco laptop, premiar mic externo
    if "Laptop / Celular" in modo:
        score -= 5
    elif "Micrófono externo" in modo:
        score += 5

    # Normalizar a 0–100
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
    """
    Recorre el audio desde el final hacia atrás y busca el último trozo
    que esté claramente por encima del "nivel fuerte".

    Solo recorta si hay al menos ~2 segundos de cola después de la última parte fuerte.
    """
    dur = len(audio)
    if dur <= chunk_ms * 2:
        return audio  # muy corto, no tocamos

    # Nivel máximo aproximado del audio
    max_db = audio.max_dBFS if audio.max_dBFS != float("-inf") else -90.0
    limite_db = max_db - umbral_rel_db

    # Recorremos desde el final hacia atrás
    ultimo_util_ms = None

    for inicio in range(dur - chunk_ms, -1, -chunk_ms):
        trozo = audio[inicio: inicio + chunk_ms]
        nivel = trozo.dBFS if trozo.dBFS != float("-inf") else -90.0

        if nivel > limite_db:
            ultimo_util_ms = inicio + chunk_ms
            break

    if ultimo_util_ms is None:
        # No encontramos nada "fuerte": no recortamos
        return audio

    # ¿Cuánto hay desde la última parte "fuerte" hasta el final?
    silencio_ms = dur - ultimo_util_ms

    # Si la cola es corta (menos que min_silencio_ms), mejor no recortar nada
    if silencio_ms < min_silencio_ms:
        return audio

    # Si la cola es larga, sí recortamos dejando un margen
    corte_ms = min(dur, ultimo_util_ms + margen_ms)
    return audio[:corte_ms]


def limpiar_golpe_tecla_final(
    audio: AudioSegment,
    ventana_ms: int = 180,
    umbral_db: float = -25.0,
    diferencia_db: float = 8.0,
) -> AudioSegment:
    """
    Detecta un golpe corto y fuerte al final (ej: tecla al detener grabación) y lo corta.
    """
    dur = len(audio)
    if dur < ventana_ms * 2:
        return audio  # muy corto, no hacemos nada

    inicio_ultima = dur - ventana_ms
    inicio_prev = dur - 2 * ventana_ms

    bloque_prev = audio[inicio_prev:inicio_ultima]
    bloque_ult = audio[inicio_ultima:dur]

    prev_db = bloque_prev.dBFS if bloque_prev.dBFS != float("-inf") else -90.0
    ult_db = bloque_ult.dBFS if bloque_ult.dBFS != float("-inf") else -90.0

    # Condición: último bloque bastante fuerte y mucho más fuerte que el anterior
    if (ult_db > umbral_db) and (ult_db - prev_db >= diferencia_db):
        # Consideramos esto un golpe de tecla y lo cortamos
        return audio[:inicio_ultima]

    return audio


def procesar_audio_core(original_path: Path, modo: str) -> Tuple[Path, Dict[str, Any]]:
    """
    Carga el audio, recorta 300 ms al inicio y ~700 ms al final,
    aplica filtro pasa altos + normalización y devuelve
    ruta del archivo procesado + datos de análisis.
    """
    audio = AudioSegment.from_file(original_path)

    # Análisis siempre sobre el audio original completo
    analisis = analizar_audio(audio)

    # 1) Recorte inicio / final (fijo)
    TRIM_INICIO_MS = 300   # 0,3 s al inicio
    TRIM_FINAL_MS = 700    # ~0,7 s al final

    dur_ms = len(audio)

    if dur_ms > (TRIM_INICIO_MS + TRIM_FINAL_MS):
        audio_proc_base = audio[TRIM_INICIO_MS : dur_ms - TRIM_FINAL_MS]
    elif dur_ms > TRIM_INICIO_MS:
        audio_proc_base = audio[TRIM_INICIO_MS:]
    else:
        audio_proc_base = audio

    # 2) Filtro + normalización
    audio_proc_base = audio_proc_base.high_pass_filter(80)
    audio_proc = effects.normalize(audio_proc_base)

       # 🔽 NUEVO: pequeño fade out global al final (120 ms aprox)
    audio_proc = audio_proc.fade_out(120)

    # Métricas finales
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

    # Score de calidad global
    quality_score, quality_label = calcular_quality(analisis, analisis["modo"])
    analisis["quality_score"] = quality_score
    analisis["quality_label"] = quality_label

    # Guardar archivo procesado
    processed_name = f"{original_path.stem}_PROCESADO.wav"
    processed_path = PROCESSED_DIR / processed_name
    audio_proc.export(processed_path, format="wav")

    return processed_path, analisis


def construir_informe_texto(nombre_original: str, a: Dict[str, Any]) -> str:
    """Texto amigable para el .txt de informe, con recomendaciones dinámicas."""
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

    # =========================
    #   RECOMENDACIONES DINÁMICAS
    # =========================

    modo = a.get("modo", "")
    nivel_orig = a.get("nivel_original_dbfs", -20.0)
    snr = a.get("snr_db", 0.0)
    sala_ind = a.get("sala_indice", 0.5)
    clip = a.get("clip_detectado", False)

    recomendaciones = []

    # 1) Comentario según modo
    if "Laptop" in modo:
        recomendaciones.append(
            "Estás grabando con el micrófono del equipo (laptop / celular). "
            "Si puedes, da el salto a un micrófono externo sencillo (USB o interfaz), "
            "vas a notar una mejora grande en claridad y ruido."
        )
    else:  # Micrófono externo
        recomendaciones.append(
            "Estás grabando con un micrófono externo. Es una muy buena base para lograr "
            "un sonido de podcast más profesional."
        )

    # 2) Nivel de voz (ganancia / distancia)
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

    # 3) Ruido / SNR
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

    # 4) Comportamiento de la sala
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

    # 5) Cómo respondió la app al nivel (delta de procesado)
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

    # 6) Recomendación explícita si hay clip
    if clip:
        recomendaciones.append(
            "Al detectar probable clip digital, es recomendable repetir la toma con un poco menos de ganancia "
            "si se trata de un material importante (entrevista, episodio principal, etc.)."
        )

    # 7) Tip de uso pensando en el recorte auto
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
    audio_file: UploadFile = File(...),
    mode: str = Form(...),
):
    # Guardar original
    raw_bytes = await audio_file.read()
    safe_suffix = audio_file.filename.replace(" ", "_")
    safe_name = f"{int(time.time())}_{safe_suffix}"

    original_path = ORIGINAL_DIR / safe_name
    with original_path.open("wb") as f:
        f.write(raw_bytes)

    # Procesar
    processed_path, analysis = procesar_audio_core(original_path, mode)

    # Informe
    report_name = f"{processed_path.stem}_report.txt"
    report_path = REPORT_DIR / report_name
    report_text = construir_informe_texto(safe_name, analysis)
    report_path.write_text(report_text, encoding="utf-8")

    return JSONResponse(
        {
            "original_url": f"/media/original/{safe_name}",
            "processed_url": f"/media/processed/{processed_path.name}",
            "report_url": f"/media/reports/{report_name}",
            "original_filename": audio_file.filename,
            "analysis": analysis,
        }
    )
