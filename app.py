import streamlit as st
import requests
import base64
import json
from audio_recorder_streamlit import audio_recorder

# ============================================================
# URLs de API Gateway
# ============================================================
LAMBDA_UPLOAD_URL     = "https://h5v2om90wd.execute-api.us-east-1.amazonaws.com/prod/upload"
LAMBDA_TRANSCRIBE_URL = "https://h5v2om90wd.execute-api.us-east-1.amazonaws.com/prod/transcribe"
LAMBDA_POLLY_URL      = "https://h5v2om90wd.execute-api.us-east-1.amazonaws.com/prod/polly"

# ============================================================
# Configuración de la página
# ============================================================
st.set_page_config(
    page_title="VozIA - Transcribe & Sintetiza",
    page_icon="🔊",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #0d0f14;
        color: #c8cdd8;
    }
    .stApp {
        background: linear-gradient(135deg, #0d0f14 0%, #111520 50%, #0d0f14 100%);
    }
    .app-header {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
        margin-bottom: 2rem;
    }
    .app-header h1 {
        font-family: 'Space Mono', monospace;
        font-size: 2.4rem;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -1px;
        margin: 0;
    }
    .app-header h1 span { color: #4ecca3; }
    .app-header p {
        color: #6b7280;
        font-size: 0.95rem;
        margin-top: 0.4rem;
        font-weight: 300;
        letter-spacing: 0.5px;
    }
    .panel-label {
        font-family: 'Space Mono', monospace;
        font-size: 0.7rem;
        letter-spacing: 3px;
        text-transform: uppercase;
        color: #4ecca3;
        margin-bottom: 0.3rem;
    }
    .panel-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: #f0f4ff;
        margin-bottom: 1rem;
    }
    .divider {
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .divider-line {
        width: 2px;
        min-height: 400px;
        background: linear-gradient(to bottom, transparent, #232a3a 20%, #4ecca3 50%, #232a3a 80%, transparent);
    }
    .stButton > button {
        font-family: 'Space Mono', monospace !important;
        font-size: 0.78rem !important;
        letter-spacing: 1.5px !important;
        text-transform: uppercase !important;
        background: linear-gradient(135deg, #4ecca3, #2a9d8f) !important;
        color: #0d0f14 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.55rem 1.2rem !important;
        font-weight: 700 !important;
        transition: all 0.2s ease !important;
        width: 100% !important;
    }
    .stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(78, 204, 163, 0.35) !important;
    }
    .stButton > button:disabled {
        background: #232a3a !important;
        color: #4a5568 !important;
        transform: none !important;
        box-shadow: none !important;
    }
    .stTextArea textarea {
        background-color: #0d0f14 !important;
        color: #c8cdd8 !important;
        border: 1px solid #2a3347 !important;
        border-radius: 8px !important;
        font-family: 'DM Sans', sans-serif !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    .stTextArea textarea:focus {
        border-color: #4ecca3 !important;
        box-shadow: 0 0 0 2px rgba(78, 204, 163, 0.15) !important;
    }
    .stSelectbox > div > div {
        background-color: #0d0f14 !important;
        border: 1px solid #2a3347 !important;
        border-radius: 8px !important;
        color: #c8cdd8 !important;
    }
    .alert {
        padding: 0.65rem 1rem;
        border-radius: 7px;
        font-size: 0.87rem;
        margin: 0.4rem 0;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .alert-ok  { background: #0d2a20; border-left: 3px solid #4ecca3; color: #7ee8c5; }
    .alert-err { background: #2a0d0d; border-left: 3px solid #e74c3c; color: #f5a4a4; }
    .transcript-box {
        background: #0d1420;
        border: 1px solid #2a3347;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-top: 0.8rem;
        color: #d4daea;
        font-size: 0.95rem;
        line-height: 1.65;
        min-height: 60px;
    }
    .stFileUploader > div {
        background: #0d0f14 !important;
        border: 1px dashed #2a3347 !important;
        border-radius: 8px !important;
    }
    div[data-testid="column"] {
        background: transparent !important;
        padding: 0 !important;
    }
    .stDownloadButton > button {
        background: #161b26 !important;
        color: #4ecca3 !important;
        border: 1px solid #4ecca3 !important;
        font-family: 'Space Mono', monospace !important;
        font-size: 0.75rem !important;
        letter-spacing: 1px !important;
        border-radius: 8px !important;
    }
    .stDownloadButton > button:hover {
        background: #4ecca3 !important;
        color: #0d0f14 !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Header
# ============================================================
st.markdown("""
<div class="app-header">
    <h1>Voz<span>IA</span></h1>
    <p>Transcripción de audio con Amazon Transcribe · Síntesis de voz con Amazon Polly</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# Helper: parsear respuesta de API Gateway
# ============================================================
def parse_lambda_response(r):
    """
    API Gateway siempre retorna HTTP 200 aunque Lambda devuelva error.
    Esta función extrae el statusCode y body reales de Lambda.
    """
    try:
        raw = r.json()
    except Exception:
        return 500, {"error": f"Respuesta no es JSON: {r.text}"}

    # Si API Gateway pasa la respuesta de Lambda directamente
    if "statusCode" in raw:
        real_status = int(raw["statusCode"])
        body = raw.get("body", "{}")
        if isinstance(body, str):
            try:
                body = json.loads(body)
            except Exception:
                body = {"error": body}
        return real_status, body

    # Si ya viene el body directo (integración proxy desactivada)
    return r.status_code, raw


# ============================================================
# Layout
# ============================================================
col_left, col_mid, col_right = st.columns([6, 1, 6])

# ─────────────────────────────────────
# COLUMNA IZQUIERDA — Audio → Texto
# ─────────────────────────────────────
with col_left:
    st.markdown('<div class="panel-label">Módulo 01</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">🎙 Audio → Texto</div>', unsafe_allow_html=True)

    input_mode = st.radio(
        "Fuente de audio",
        ["Grabar audio", "Subir archivo de audio"],
        horizontal=True
    )

    audio_bytes = None

    if input_mode == "Grabar audio":
        st.caption("Haz clic en el micrófono para iniciar/detener la grabación")
        audio_bytes = audio_recorder(
            text="",
            recording_color="#e74c3c",
            neutral_color="#4ecca3",
            icon_name="microphone",
            icon_size="2x",
        )
        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav")
    else:
        uploaded = st.file_uploader(
            "Arrastra tu archivo aquí",
            type=["wav", "mp3", "m4a"],
            label_visibility="collapsed"
        )
        if uploaded:
            audio_bytes = uploaded.read()
            st.audio(audio_bytes)

    transcribe_btn = st.button(
        "⚡ Transcribir Audio",
        disabled=(audio_bytes is None),
        key="btn_transcribe"
    )

    if transcribe_btn:
        status_area = st.container()
        
        # Verificar que el audio tiene contenido real
        if not audio_bytes or len(audio_bytes) < 1000:
            st.warning(f"⚠️ El audio grabado parece estar vacío ({len(audio_bytes) if audio_bytes else 0} bytes). Intenta grabar de nuevo.")
            st.stop()
        
        with st.spinner("Procesando con AWS..."):
            try:
                # ── Paso 1: subir a S3 ──────────────────────────
                audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
                payload_upload = json.dumps({"audio_base64": audio_b64})

                r = requests.post(
                    LAMBDA_UPLOAD_URL,
                    data=payload_upload,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )

                status_upload, upload_data = parse_lambda_response(r)

                if status_upload == 200:
                    status_area.markdown(
                        '<div class="alert alert-ok">✓ Audio almacenado en Amazon S3</div>',
                        unsafe_allow_html=True
                    )

                    # ── Paso 2: transcribir ─────────────────────
                    payload_transcribe = json.dumps({
                        "bucket": upload_data["bucket"],
                        "s3_key": upload_data["s3_key"]
                    })

                    r2 = requests.post(
                        LAMBDA_TRANSCRIBE_URL,
                        data=payload_transcribe,
                        headers={"Content-Type": "application/json"},
                        timeout=120
                    )

                    status_transcribe, transcribe_data = parse_lambda_response(r2)

                    if status_transcribe == 200:
                        status_area.markdown(
                            '<div class="alert alert-ok">✓ Transcripción completada con Amazon Transcribe</div>',
                            unsafe_allow_html=True
                        )
                        transcript = transcribe_data.get("transcript", "")
                        st.session_state["transcript_text"] = transcript
                        st.markdown(
                            f'<div class="transcript-box">{transcript}</div>',
                            unsafe_allow_html=True
                        )
                    else:
                        status_area.markdown(
                            f'<div class="alert alert-err">✗ Error Transcribe: {transcribe_data.get("error","desconocido")}</div>',
                            unsafe_allow_html=True
                        )
                        st.code(json.dumps(transcribe_data, indent=2), language="json")
                else:
                    status_area.markdown(
                        f'<div class="alert alert-err">✗ Error Upload S3: {upload_data.get("error","desconocido")}</div>',
                        unsafe_allow_html=True
                    )
                    st.code(json.dumps(upload_data, indent=2), language="json")

            except Exception as e:
                st.error("Error inesperado durante la ejecución")
                st.exception(e)

# ─────────────────────────────────────
# COLUMNA CENTRAL — Separador
# ─────────────────────────────────────
with col_mid:
    st.markdown("""
    <div class="divider">
        <div class="divider-line"></div>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────
# COLUMNA DERECHA — Texto → Audio
# ─────────────────────────────────────
with col_right:
    st.markdown('<div class="panel-label">Módulo 02</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">🔊 Texto → Audio</div>', unsafe_allow_html=True)

    default_text = st.session_state.get("transcript_text", "")
    text_input = st.text_area(
        "Escribe o pega el texto a convertir",
        value=default_text,
        height=160,
        placeholder="El texto de la transcripción aparecerá aquí automáticamente, o puedes escribir el tuyo..."
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        voice = st.selectbox("Voz", ["Lucia", "Conchita", "Mia", "Miguel", "Penelope"])
    with c2:
        engine = st.selectbox("Motor", ["neural", "standard"])
    with c3:
        fmt = st.selectbox("Formato", ["mp3", "ogg_vorbis"])

    polly_btn = st.button(
        "🎵 Sintetizar Voz",
        disabled=(not text_input.strip()),
        key="btn_polly"
    )

    if polly_btn:
        status_polly = st.container()
        with st.spinner("Generando audio con Amazon Polly..."):
            try:
                payload_polly = json.dumps({
                    "text": text_input,
                    "voice_id": voice,
                    "engine": engine,
                    "output_format": fmt
                })

                r = requests.post(
                    LAMBDA_POLLY_URL,
                    data=payload_polly,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )

                status_polly_code, polly_data = parse_lambda_response(r)

                if status_polly_code == 200:
                    status_polly.markdown(
                        '<div class="alert alert-ok">✓ Audio generado correctamente con Amazon Polly</div>',
                        unsafe_allow_html=True
                    )
                    audio_out_bytes = base64.b64decode(polly_data["audio_base64"])
                    mime = "audio/mpeg" if fmt == "mp3" else "audio/ogg"

                    st.audio(audio_out_bytes, format=mime)
                    st.download_button(
                        "⬇ Descargar archivo de audio",
                        data=audio_out_bytes,
                        file_name=f"vozIA_output.{fmt}",
                        mime=mime
                    )
                else:
                    status_polly.markdown(
                        f'<div class="alert alert-err">✗ Error Polly: {polly_data.get("error","desconocido")}</div>',
                        unsafe_allow_html=True
                    )
                    st.code(json.dumps(polly_data, indent=2), language="json")

            except Exception as e:
                status_polly.markdown(
                    '<div class="alert alert-err">✗ Error de conexión con la API</div>',
                    unsafe_allow_html=True
                )
                st.exception(e)