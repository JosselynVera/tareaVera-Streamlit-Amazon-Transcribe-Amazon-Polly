import json
import boto3
import base64
import os

polly_client = boto3.client("polly")

NEURAL_VOICES   = {"Lucia", "Mia", "Miguel"}
STANDARD_VOICES = {"Lucia", "Conchita", "Mia", "Miguel", "Penelope"}


def lambda_handler(event, context):
    try:
        # Parsear body — puede llegar como string o como dict
        raw_body = event.get("body", event)
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        elif isinstance(raw_body, dict):
            body = raw_body
        else:
            body = event

        text          = body.get("text", "").strip()
        voice_id      = body.get("voice_id", "Lucia")
        engine        = body.get("engine", "neural")
        output_format = body.get("output_format", "mp3")

        if not text:
            return _response(400, {"error": "El campo 'text' no puede estar vacío.", "received": str(body)})

        if output_format not in ("mp3", "ogg_vorbis"):
            return _response(400, {"error": f"Formato inválido: '{output_format}'."})

        if engine not in ("neural", "standard"):
            return _response(400, {"error": f"Motor inválido: '{engine}'."})

        if engine == "neural" and voice_id not in NEURAL_VOICES:
            engine = "standard"

        response = polly_client.synthesize_speech(
            Text=text,
            VoiceId=voice_id,
            Engine=engine,
            OutputFormat=output_format,
            LanguageCode="es-ES"
        )

        audio_stream = response["AudioStream"].read()
        audio_b64    = base64.b64encode(audio_stream).decode("utf-8")

        mime_map = {"mp3": "audio/mpeg", "ogg_vorbis": "audio/ogg"}

        return _response(200, {
            "audio_base64": audio_b64,
            "content_type": mime_map[output_format],
            "voice_id": voice_id,
            "engine": engine
        })

    except polly_client.exceptions.TextLengthExceededException:
        return _response(400, {"error": "Texto demasiado largo para Amazon Polly (máx. 3000 caracteres)."})

    except Exception as e:
        print(f"[ERROR polly] {str(e)}")
        return _response(500, {"error": str(e)})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }