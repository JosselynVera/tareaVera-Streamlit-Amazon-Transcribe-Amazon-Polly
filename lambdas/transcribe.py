import json
import boto3
import time
import uuid
import os

transcribe_client = boto3.client("transcribe")
s3_client = boto3.client("s3")

OUTPUT_BUCKET = os.environ.get("S3_BUCKET_NAME", "audio-transcribir")
MAX_WAIT_SECONDS = int(os.environ.get("MAX_WAIT_SECONDS", "90"))


def lambda_handler(event, context):
    try:
        # Parsear body — puede llegar como string o como dict
        raw_body = event.get("body", event)
        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        elif isinstance(raw_body, dict):
            body = raw_body
        else:
            body = event  # fallback: el evento completo es el body

        bucket  = body.get("bucket")
        s3_key  = body.get("s3_key")

        if not bucket or not s3_key:
            return _response(400, {
                "error": "Se requieren los campos 'bucket' y 's3_key'.",
                "received": str(body)
            })

        media_uri = f"s3://{bucket}/{s3_key}"
        job_name  = f"transcribe-job-{uuid.uuid4()}"

        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": media_uri},
            MediaFormat="wav",
            LanguageCode="es-ES",
            OutputBucketName=OUTPUT_BUCKET,
            Settings={
                "ShowSpeakerLabels": False,
                "ChannelIdentification": False
            }
        )

        # Polling hasta que termine
        elapsed = 0
        poll_interval = 5
        status = "IN_PROGRESS"

        while status == "IN_PROGRESS" and elapsed < MAX_WAIT_SECONDS:
            time.sleep(poll_interval)
            elapsed += poll_interval

            job_response = transcribe_client.get_transcription_job(
                TranscriptionJobName=job_name
            )
            status = job_response["TranscriptionJob"]["TranscriptionJobStatus"]

        if status == "COMPLETED":
            output_key = f"{job_name}.json"
            s3_obj = s3_client.get_object(Bucket=OUTPUT_BUCKET, Key=output_key)
            transcript_json = json.loads(s3_obj["Body"].read().decode("utf-8"))
            transcript_text = (
                transcript_json
                .get("results", {})
                .get("transcripts", [{}])[0]
                .get("transcript", "")
            )
            return _response(200, {"transcript": transcript_text, "job_name": job_name})

        elif status == "FAILED":
            failure_reason = job_response["TranscriptionJob"].get("FailureReason", "Razón desconocida")
            return _response(500, {"error": "El job de Transcribe falló.", "detail": failure_reason})

        else:
            return _response(504, {"error": f"Tiempo de espera superado ({MAX_WAIT_SECONDS}s)."})

    except Exception as e:
        print(f"[ERROR transcribe] {str(e)}")
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