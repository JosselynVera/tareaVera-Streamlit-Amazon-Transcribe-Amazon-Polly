import json
import boto3
import base64
import uuid
import os

s3_client = boto3.client("s3")

BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "audio-transcribir")


def lambda_handler(event, context):
    """
    Recibe un audio en base64 desde el body del request,
    lo decodifica y lo sube a Amazon S3.

    Body esperado (JSON):
        { "audio_base64": "<string base64>" }

    Respuesta exitosa (JSON):
        { "bucket": "<nombre>", "s3_key": "<clave>" }
    """
    try:
        body = json.loads(event.get("body", "{}"))
        audio_b64 = body.get("audio_base64")

        if not audio_b64:
            return _response(400, {"error": "Falta el campo 'audio_base64' en el body."})

        # Decodificar audio
        audio_bytes = base64.b64decode(audio_b64)

        # Generar clave única en S3
        s3_key = f"uploads/{uuid.uuid4()}.wav"

        # Subir a S3
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Body=audio_bytes,
            ContentType="audio/wav"
        )

        return _response(200, {
            "message": "Audio subido exitosamente a S3.",
            "bucket": BUCKET_NAME,
            "s3_key": s3_key
        })

    except Exception as e:
        print(f"[ERROR upload] {str(e)}")
        return _response(500, {"error": str(e)})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }