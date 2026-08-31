import json
import logging
import os
import re
import smtplib
import time
import urllib.parse
import urllib.request
from collections import deque
from email.message import EmailMessage
from email.utils import parseaddr

from flask import Flask, jsonify, request

app = Flask(__name__)

logger = logging.getLogger("contact-relay")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MAX_BODY_LEN = 5000

# --- Google reCAPTCHA v3 -----------------------------------------------------
# This form is embedded in the SSO login page (served by authentik) and posts
# here cross-service, so it is a public, unauthenticated endpoint -- exactly
# the kind of thing bots scrape and spam. reCAPTCHA v3 is scored/invisible: the
# browser calls grecaptcha.execute(...) with the action "contact" and sends the
# resulting token as `g-recaptcha-response`; we verify it server-side below.
#
# The SITE key is public and is safe to embed in served HTML/JS. The SECRET key
# is server-side ONLY -- it must never be sent to the browser or committed.
RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "").strip()
RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "").strip()
RECAPTCHA_MIN_SCORE = float(os.environ.get("RECAPTCHA_MIN_SCORE", "0.5"))
RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_EXPECTED_ACTION = "contact"
# Host the token must have been solved on. Accept the production apex and any
# subdomain of it (sso.systemsnotsilos.com etc.), plus localhost for dev.
RECAPTCHA_ALLOWED_HOST_SUFFIX = "systemsnotsilos.com"
RECAPTCHA_DEV_HOSTS = {"localhost", "127.0.0.1"}


def _recaptcha_configured() -> bool:
    return bool(RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY)


def _hostname_ok(hostname: str) -> bool:
    hostname = (hostname or "").lower()
    if hostname in RECAPTCHA_DEV_HOSTS:
        return True
    return (
        hostname == RECAPTCHA_ALLOWED_HOST_SUFFIX
        or hostname.endswith("." + RECAPTCHA_ALLOWED_HOST_SUFFIX)
    )


def verify_recaptcha(token: str, remote_ip: str) -> tuple[bool, str]:
    """Verify a reCAPTCHA v3 token against Google's siteverify API.

    Returns (ok, reason). This is a HIGH-RISK / anti-abuse gate on a public
    endpoint, so it FAILS CLOSED: any verification failure or network error
    returns (False, ...) and the caller rejects the request.

    If keys are UNSET (local dev), verification is SKIPPED with a warning so
    developers are not hard-blocked -- do not run that way in production.

    NOTE: the token and the secret are never logged.
    """
    if not _recaptcha_configured():
        logger.warning(
            "reCAPTCHA keys not set (RECAPTCHA_SITE_KEY/RECAPTCHA_SECRET_KEY) -- "
            "SKIPPING verification. Set both before exposing this publicly."
        )
        return True, "skipped-unconfigured"

    if not token:
        return False, "missing-token"

    payload = {"secret": RECAPTCHA_SECRET_KEY, "response": token}
    if remote_ip:
        payload["remoteip"] = remote_ip
    data = urllib.parse.urlencode(payload).encode("utf-8")

    try:
        req = urllib.request.Request(RECAPTCHA_VERIFY_URL, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except Exception:
        # Network/parse error -> fail closed. Do not leak details that could
        # include the token; log only a generic message.
        logger.warning("reCAPTCHA siteverify request failed; rejecting (fail-closed).")
        return False, "verify-request-failed"

    if not result.get("success"):
        # error-codes may include "invalid-input-secret" (secret is v2/wrong) or
        # "invalid-input-response" (token bad/expired). "Invalid key type" seen
        # in the BROWSER from grecaptcha.execute means the SITE key was
        # registered as reCAPTCHA v2, not v3 -- re-register the key pair as v3.
        return False, "not-successful:" + ",".join(result.get("error-codes", []) or [])

    action = result.get("action")
    if action != RECAPTCHA_EXPECTED_ACTION:
        return False, f"action-mismatch:{action}"

    if not _hostname_ok(result.get("hostname", "")):
        return False, "hostname-not-allowed"

    score = result.get("score")
    if score is None or float(score) < RECAPTCHA_MIN_SCORE:
        return False, f"low-score:{score}"

    return True, "ok"

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

    # reCAPTCHA v3 gate. Fail closed: if verification does not pass, reject the
    # request before doing any work. Skipped only when keys are unset (dev).
    token = str(data.get("g-recaptcha-response", "")).strip()
    ok, reason = verify_recaptcha(token, _client_ip())
    if not ok:
        logger.info("Rejecting /send: reCAPTCHA verification failed (%s)", reason)
        return jsonify(error="captcha verification failed"), 403

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


@app.route("/config", methods=["GET"])
def config():
    # Exposes ONLY the public reCAPTCHA site key so the (authentik-served) login
    # page can load the v3 script without hardcoding the key in a template it
    # doesn't own. The secret key is never included here. Empty string when
    # reCAPTCHA is not configured, so the frontend can gracefully skip it.
    return jsonify(recaptcha_site_key=RECAPTCHA_SITE_KEY)


@app.route("/health", methods=["GET"])
def health():
    return jsonify(status="ok")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))
