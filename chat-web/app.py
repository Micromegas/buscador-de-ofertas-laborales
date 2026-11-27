import os

import bleach
import markdown
import requests
from flask import Flask, jsonify, render_template, request


app = Flask(__name__)

N8N_CHAT_WEBHOOK_URL = os.environ.get("N8N_CHAT_WEBHOOK_URL", "").strip()
N8N_CHAT_TIMEOUT = int(os.environ.get("N8N_CHAT_TIMEOUT", "180"))

ALLOWED_TAGS = set(bleach.sanitizer.ALLOWED_TAGS).union(
    {
        "p", "br", "hr", "h1", "h2", "h3", "h4", "h5", "h6",
        "ul", "ol", "li", "blockquote", "pre", "code", "strong",
        "em", "del", "table", "thead", "tbody", "tr", "th", "td",
    }
)
ALLOWED_ATTRIBUTES = {"a": ["href", "title"]}


def extract_reply(payload):
    """Find the assistant text in common n8n Chat Trigger response shapes."""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, list):
        if not payload:
            return "No recibí una respuesta del asistente."
        job_records = [item for item in payload if is_job_record(item)]
        if job_records:
            return "\n\n---\n\n".join(format_job_record(item) for item in job_records)
        return extract_reply(payload[0])
    if isinstance(payload, dict):
        if is_job_record(payload):
            return format_job_record(payload)
        for key in ("output", "text", "reply", "response", "message"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, (dict, list)):
                nested = extract_reply(value)
                if nested:
                    return nested
        for key in ("data", "body"):
            if key in payload:
                return extract_reply(payload[key])
        return str(payload)
    return str(payload)


def is_job_record(value):
    return (
        isinstance(value, dict)
        and bool(value.get("title"))
        and bool(value.get("job_id") or value.get("id"))
    )


def format_job_record(job):
    title = str(job.get("title") or "Aviso laboral").strip()
    modality = str(job.get("remote_modality") or "No especificada").strip()
    modality_labels = {
        "hybrid": "Híbrido",
        "fully_remote": "Remoto",
        "remote_local": "Remoto con restricción geográfica",
        "no_remote": "Presencial",
    }
    modality = modality_labels.get(modality, modality.replace("_", " ").capitalize())

    lines = [f"## {title}", "", f"**Modalidad:** {modality}"]

    country = job.get("country")
    countries = job.get("countries")
    if country:
        lines.append(f"**País:** {country}")
    elif isinstance(countries, list) and countries:
        lines.append(f"**País:** {', '.join(str(item) for item in countries)}")

    description = str(job.get("description") or "").strip()
    if description:
        lines.extend(["", "### Descripción", "", description])

    public_url = str(job.get("public_url") or job.get("url") or "").strip()
    if public_url:
        if public_url.startswith("[") and "](" in public_url:
            link = public_url
        else:
            link = f"[Ver aviso original]({public_url})"
        lines.extend(["", link])

    lines.extend(["", "_Aviso guardado en PostgreSQL._"])
    return "\n".join(lines)


def render_markdown(text):
    html = markdown.markdown(text, extensions=["extra", "sane_lists"])
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols={"http", "https", "mailto"},
        strip=True,
    )


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.post("/api/chat")
def chat():
    body = request.get_json(silent=True) or {}
    message = str(body.get("message", "")).strip()
    session_id = str(body.get("sessionId", "")).strip()

    if not message:
        return jsonify({"error": "Escribí un mensaje para iniciar la búsqueda."}), 400
    if len(message) > 4000:
        return jsonify({"error": "El mensaje es demasiado largo (máximo 4000 caracteres)."}), 400
    if not N8N_CHAT_WEBHOOK_URL:
        return jsonify({"error": "Falta configurar N8N_CHAT_WEBHOOK_URL en el archivo .env."}), 503

    try:
        response = requests.post(
            N8N_CHAT_WEBHOOK_URL,
            params={"action": "sendMessage"},
            json={"chatInput": message, "sessionId": session_id},
            timeout=N8N_CHAT_TIMEOUT,
        )
        response.raise_for_status()
    except requests.Timeout:
        return jsonify({"error": "La respuesta tardó demasiado. Probá de nuevo en unos segundos."}), 504
    except requests.RequestException as exc:
        detail = "No se pudo contactar con el flujo de n8n. Revisá que esté activo y que la Chat URL sea correcta."
        if getattr(exc, "response", None) is not None:
            detail = f"n8n respondió con estado {exc.response.status_code}. Revisá la ejecución del Chat Trigger."
        app.logger.warning("Chat Trigger request failed: %s", exc)
        return jsonify({"error": detail}), 502

    try:
        payload = response.json()
    except ValueError:
        payload = response.text

    reply = extract_reply(payload)
    return jsonify({"reply": reply, "replyHtml": render_markdown(reply)})
