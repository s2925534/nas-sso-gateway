import os
import re
import smtplib
import time
from collections import deque
from email.message import EmailMessage
from email.utils import parseaddr

from flask import Flask, jsonify, request

app = Flask(__name__)

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_BODY_LEN = 5000

SMTP_HOST = os.environ.get("CONTACT_EMAIL__HOST", "")
SMTP_PORT = int(os.environ.get("CONTACT_EMAIL__PORT", "587"))
SMTP_USERNAME = os.environ.get("CONTACT_EMAIL__USERNAME", "")
SMTP_PASSWORD = os.environ.get("CONTACT_EMAIL__PASSWORD", "")
SMTP_USE_TLS = os.environ.get("CONTACT_EMAIL__USE_TLS", "true").lower() == "true"
SMTP_USE_SSL = os.environ.get("CONTACT_EMAIL__USE_SSL", "false").lower() == "true"
SMTP_FROM = os.environ.get("CONTACT_EMAIL__FROM", "contact@example.com")

ADMIN_EMAIL = os.environ.get("CONTACT_ADMIN_EMAIL", "")
ALLOWED_ORIGIN = os.environ.get("CONTACT_ALLOWED_ORIGIN", "")

RATE_LIMIT_MAX = int(os.environ.get("CONTACT_RATE_LIMIT_MAX", "5"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("CONTACT_RATE_LIMIT_WINDOW_SECONDS", "3600"))

# Simple in-memory sliding-window rate limiter, keyed by client IP. Resets on
# container restart -- acceptable for a low-volume contact form; not meant to
# stop a determined attacker, just casual spam/bot noise.
_request_log: dict[str, deque] = {}


def _client_ip() -> str:
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr or "unknown"


def _rate_limited(ip: str) -> bool:
    now = time.time()
    log = _request_log.setdefault(ip, deque())
    while log and now - log[0] > RATE_LIMIT_WINDOW_SECONDS:
        log.popleft()
    if len(log) >= RATE_LIMIT_MAX:
        return True
    log.append(now)
    return False


def _sanitize_header_value(value: str) -> str:
    # Strips CR/LF to prevent SMTP header injection via user-supplied fields.
    return value.replace("\r", "").replace("\n", "").strip()


@app.after_request
def add_cors_headers(response):
    if ALLOWED_ORIGIN:
        response.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@app.route("/send", methods=["OPTIONS"])
def send_options():
    return "", 204


@app.route("/send", methods=["POST"])
def send():
    if not ADMIN_EMAIL:
        return jsonify(error="server not configured"), 503
    if not SMTP_HOST:
        return jsonify(error="server not configured"), 503

    if _rate_limited(_client_ip()):
        return jsonify(error="too many requests, try again later"), 429

    data = request.get_json(silent=True) or {}
    sender_email = _sanitize_header_value(str(data.get("email", "")))
    body = str(data.get("body", "")).strip()

    display_name, addr_only = parseaddr(sender_email)
    if not addr_only or not EMAIL_RE.match(addr_only):
        return jsonify(error="a valid email address is required"), 400
    if not body:
        return jsonify(error="message body is required"), 400
    if len(body) > MAX_BODY_LEN:
        return jsonify(error=f"message body must be under {MAX_BODY_LEN} characters"), 400

    msg = EmailMessage()
    msg["Subject"] = "Contact Support — Systems, Not Silos login page"
    msg["From"] = SMTP_FROM
    msg["To"] = ADMIN_EMAIL
    msg["Reply-To"] = addr_only
    msg.set_content(f"From: {addr_only}\n\n{body}")

    try:
        if SMTP_USE_SSL:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
                if SMTP_USE_TLS:
                    server.starttls()
                if SMTP_USERNAME:
                    server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
    except Exception:
        return jsonify(error="failed to send message"), 502

    return jsonify(ok=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
