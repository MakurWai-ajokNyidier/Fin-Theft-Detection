"""
╔══════════════════════════════════════════════════════════════════════╗
║          FIN-THEFT DETECTION SYSTEM  ·  Backend API v2.1            ║
║                                                                      ║
║  Copyright © 2024 Fin-Theft Detection Project                        ║
║  Developed to protect citizens like Daoud from black-market          ║
║  currency fraud in frontier markets.                                 ║
║                                                                      ║
║  Frameworks: RANK · GUARD · CYCLE · TRAIL · HUNT · PRIDE            ║
║                                                                      ║
║  License: MIT — free to use, modify, and distribute with attribution ║
║  Author:  Fin-Theft Detection Team                                   ║
║  Contact: fintheft@example.org                                       ║
╚══════════════════════════════════════════════════════════════════════╝

ARCHITECTURE
────────────
  Frontend  ──HTTP──▶  Flask API  ──HTTP──▶  Anthropic Claude API
                           │
                           ▼
                     SQLite Database
                    (scan_ledger.db)

ENDPOINTS
─────────
  GET  /                      — Serve main UI
  POST /api/scan               — Submit currency image for analysis
  GET  /api/records            — Fetch all scan records
  GET  /api/records/<id>       — Fetch single record
  DELETE /api/records/<id>     — Delete a record
  GET  /api/stats              — Aggregated analytics
  POST /api/sms/simulate       — Simulate SMS dispatch log
  GET  /api/health             — System health check
"""

import os
import json
import uuid
import sqlite3
import base64
import datetime
import urllib.request
import urllib.error
import re
import logging
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, render_template

# ── Security: Logging Setup ────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('fin_theft.log'),  # Audit log
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ── Configuration ──────────────────────────────────────────────────────────────

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
DB_PATH     = os.path.join(BASE_DIR, "data", "scan_ledger.db")
STATIC_DIR  = os.path.join(BASE_DIR, "static")
TEMPLATE_DIR= os.path.join(BASE_DIR, "templates")

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL   = "claude-sonnet-4-20250514"
ANTHROPIC_ENDPOINT= "https://api.anthropic.com/v1/messages"

# ── App Init ───────────────────────────────────────────────────────────────────

app = Flask(__name__, static_folder=STATIC_DIR, template_folder=TEMPLATE_DIR)
app.config["MAX_CONTENT_LENGTH"] = 15 * 1024 * 1024  # 15 MB upload limit

# ── Security Configuration ─────────────────────────────────────────────────────

app.config["SESSION_COOKIE_SECURE"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Strict"
app.config["PERMANENT_SESSION_LIFETIME"] = 3600

# Security headers middleware
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; "
        "font-src 'self'; "
        "connect-src 'self' https://api.anthropic.com"
    )
    return response

# Rate limiting decorator
REQUEST_COUNTS = {}
RATE_LIMIT_REQUESTS = 30
RATE_LIMIT_WINDOW = 60

def rate_limit(f):
    """Simple rate limiter to prevent abuse."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        ip = request.remote_addr
        now = datetime.datetime.now()
        
        # Clean old entries
        REQUEST_COUNTS[ip] = [t for t in REQUEST_COUNTS.get(ip, [])
                              if (now - t).seconds < RATE_LIMIT_WINDOW]
        
        # Check limit
        if len(REQUEST_COUNTS.get(ip, [])) >= RATE_LIMIT_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP {ip}")
            return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
        
        REQUEST_COUNTS.setdefault(ip, []).append(now)
        return f(*args, **kwargs)
    return decorated_function


# ── Database (CYCLE Engine) ────────────────────────────────────────────────────

def get_db():
    """Return a SQLite connection with row_factory enabled."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS scan_records (
                id              TEXT PRIMARY KEY,
                timestamp       TEXT NOT NULL,
                owner_name      TEXT,
                owner_phone     TEXT,
                currency_type   TEXT,
                denomination    TEXT,
                location        TEXT,
                dealer          TEXT,
                notes           TEXT,
                verdict         TEXT NOT NULL,
                confidence      INTEGER,
                alert_severity  TEXT,
                serial_pattern  TEXT,
                watermark       TEXT,
                security_thread TEXT,
                microprint      TEXT,
                ink_quality     TEXT,
                texture_score   INTEGER,
                ai_summary      TEXT,
                image_thumb     TEXT
            );

            CREATE TABLE IF NOT EXISTS sms_log (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id     TEXT NOT NULL,
                phone       TEXT NOT NULL,
                message     TEXT NOT NULL,
                sent_at     TEXT NOT NULL,
                status      TEXT NOT NULL
            );
        """)


# ── HUNT Protocol — AI Analysis ────────────────────────────────────────────────

HUNT_PROMPT = """You are HUNT — a forensic currency authentication AI integrated
into the Fin-Theft Detection System, protecting citizens from black-market fraud.

Analyze the provided currency image with forensic precision. Examine:
1. Serial number — font consistency, spacing, ink bleed
2. Watermark — presence, positioning, translucency
3. Security thread — embedded strip, holographic elements
4. Microprinting — sharpness under simulated magnification
5. Ink quality — colour saturation, intaglio depth cues
6. Paper texture — cotton-fibre pattern clues from image quality
7. Border engraving — crispness, geometric precision
8. Print registration — alignment of front/back overlay

Currency declared: {currency_type} {denomination}
Location: {location}
Dealer reported: {dealer}
Owner notes: {notes}

Respond ONLY with valid JSON — no markdown, no extra text:
{{
  "verdict": "AUTHENTIC" | "COUNTERFEIT" | "SUSPICIOUS",
  "confidence": <integer 0-100>,
  "serial_pattern": "PASS" | "FAIL" | "INCONCLUSIVE",
  "watermark": "DETECTED" | "MISSING" | "INCONCLUSIVE",
  "security_thread": "PRESENT" | "ABSENT" | "INCONCLUSIVE",
  "microprint": "CLEAR" | "BLURRED" | "ABSENT",
  "ink_quality": "EXCELLENT" | "GOOD" | "POOR" | "SUSPECT",
  "texture_score": <integer 0-10>,
  "summary": "<2–3 sentences: what was found and what the owner should do>",
  "alert_severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
}}"""


def call_anthropic(image_b64: str, image_mime: str, context: dict) -> dict:
    """
    HUNT Protocol: Send image + prompt to Claude Vision.
    Returns structured analysis dict.
    Uses stdlib urllib so no extra packages needed.
    """
    if not ANTHROPIC_API_KEY:
        # Fallback demo result when no API key is configured
        return {
            "verdict": "SUSPICIOUS",
            "confidence": 55,
            "serial_pattern": "INCONCLUSIVE",
            "watermark": "INCONCLUSIVE",
            "security_thread": "INCONCLUSIVE",
            "microprint": "INCONCLUSIVE",
            "ink_quality": "INCONCLUSIVE",
            "texture_score": 5,
            "summary": (
                "No Anthropic API key configured. "
                "Set ANTHROPIC_API_KEY in your environment and restart. "
                "This is a demo verdict only — do not act on it."
            ),
            "alert_severity": "MEDIUM",
        }

    prompt = HUNT_PROMPT.format(**context)
    payload = json.dumps({
        "model": ANTHROPIC_MODEL,
        "max_tokens": 800,
        "messages": [{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image_mime,
                        "data": image_b64,
                    },
                },
                {"type": "text", "text": prompt},
            ],
        }],
    }).encode()

    req = urllib.request.Request(
        ANTHROPIC_ENDPOINT,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        raw = "".join(b.get("text", "") for b in data.get("content", []))
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(raw)
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"Anthropic API error {e.code}: {body}")
    except json.JSONDecodeError as e:
        raise RuntimeError(f"JSON parse error: {e}")


# ── TRAIL Framework — SMS Simulation ──────────────────────────────────────────

def simulate_sms(scan_id: str, phone: str, owner: str, result: dict,
                 currency: str, denom: str) -> dict:
    """
    TRAIL: Log simulated SMS dispatch.
    In production, replace body with real gateway call
    (Africa's Talking, Twilio, etc.)
    """
    emoji = {"AUTHENTIC": "✅", "COUNTERFEIT": "🚨", "SUSPICIOUS": "⚠️"}.get(
        result["verdict"], "ℹ️"
    )
    message = (
        f"[FIN-THEFT] {emoji} {result['verdict']}\n"
        f"Hi {owner}, your {currency} {denom} scan ({scan_id}): "
        f"{result['verdict']} ({result['confidence']}% confidence).\n"
        f"{result['summary']}\nRef: {scan_id}"
    )
    sent_at = datetime.datetime.utcnow().isoformat()
    status  = "SIMULATED" if not os.environ.get("SMS_GATEWAY_KEY") else "SENT"

    with get_db() as conn:
        conn.execute(
            "INSERT INTO sms_log (scan_id, phone, message, sent_at, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (scan_id, phone, message, sent_at, status),
        )
    return {"phone": phone, "status": status, "sent_at": sent_at, "message": message}


# ── API Routes ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(TEMPLATE_DIR, "index.html")


@app.route("/api/health")
def health():
    """PRIDE: System health endpoint."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM scan_records").fetchone()[0]
    return jsonify({
        "status": "online",
        "version": "2.1.0",
        "api_key_set": bool(ANTHROPIC_API_KEY),
        "total_scans": total,
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "frameworks": ["RANK", "GUARD", "CYCLE", "TRAIL", "HUNT", "PRIDE"],
    })


@app.route("/api/scan", methods=["POST"])
@rate_limit
def scan():
    """
    HUNT + RANK + GUARD + TRAIL
    Security: Rate limited, input validated, file size checked
    Accept multipart/form-data with:
      - image        : file upload (JPG/PNG/WEBP, max 15 MB)
      - owner_name   : str (max 100 chars)
      - owner_phone  : str (phone format)
      - currency_type: str (whitelist)
      - denomination : str (numeric)
      - location     : str (max 200 chars)
      - dealer       : str (max 200 chars)
      - notes        : str (max 500 chars)
    """
    
    # ── Security: Validate image file ──────────────────────────────────────────
    if "image" not in request.files:
        logger.warning("Scan attempted without image")
        return jsonify({"error": "No image file provided"}), 400

    img_file  = request.files["image"]
    img_bytes = img_file.read()
    img_mime  = img_file.content_type or "image/jpeg"

    # Validate MIME type (prevent arbitrary uploads)
    allowed_mimes = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if img_mime not in allowed_mimes:
        logger.warning(f"Invalid MIME type: {img_mime}")
        return jsonify({"error": "Invalid image type. Use JPG, PNG, or WEBP."}), 400

    if len(img_bytes) == 0:
        logger.warning("Empty image file uploaded")
        return jsonify({"error": "Empty image file"}), 400

    img_b64  = base64.b64encode(img_bytes).decode()
    # thumbnail: first 300 chars of b64 for log display
    img_thumb = img_b64[:300]

    # ── Security: Validate form fields ─────────────────────────────────────────
    def sanitize_string(s, max_len=100):
        """Remove potentially dangerous characters."""
        if not s:
            return ""
        # Remove null bytes and control characters
        s = s.replace('\x00', '')
        s = ''.join(c for c in s if ord(c) >= 32 or c in '\n\r\t')
        return s[:max_len].strip()

    def validate_phone(phone):
        """Validate phone number format."""
        if not phone:
            return ""
        # Simple regex: +XXX or numbers and dashes
        if re.match(r'^[\+]?[0-9\s\-\(\)]{7,20}$', phone):
            return sanitize_string(phone, 20)
        logger.warning(f"Invalid phone format: {phone[:10]}")
        return ""

    def validate_currency(currency):
        """Whitelist of allowed currencies."""
        allowed = {"USD", "SDG", "SSP", "ETB", "KES", "EUR", "GBP", "EGP", "OTHER"}
        if currency in allowed:
            return currency
        logger.warning(f"Invalid currency: {currency}")
        return "OTHER"

    # Extract and sanitize fields
    owner_name   = sanitize_string(request.form.get("owner_name", "Unknown"), 100) or "Unknown"
    owner_phone  = validate_phone(request.form.get("owner_phone", ""))
    currency_type= validate_currency(request.form.get("currency_type", "USD"))
    denomination = sanitize_string(request.form.get("denomination", ""), 20)
    location     = sanitize_string(request.form.get("location", ""), 200)
    dealer       = sanitize_string(request.form.get("dealer", ""), 200)
    notes        = sanitize_string(request.form.get("notes", ""), 500)

    # Validate denomination is numeric
    if denomination and not re.match(r'^[0-9\.]{1,20}$', denomination):
        logger.warning(f"Invalid denomination: {denomination}")
        return jsonify({"error": "Denomination must be numeric"}), 400

    ctx = {
        "currency_type": currency_type,
        "denomination":  denomination or "unspecified",
        "location":      location or "not specified",
        "dealer":        dealer  or "not reported",
        "notes":         notes   or "none",
    }

    # --- HUNT: AI analysis ---
    try:
        result = call_anthropic(img_b64, img_mime, ctx)
    except RuntimeError as e:
        return jsonify({"error": str(e)}), 502

    # --- GUARD: safety rail ---
    if result.get("confidence", 100) < 45:
        result["verdict"] = "SUSPICIOUS"
        result["alert_severity"] = "HIGH"
        result["summary"] = (
            "[GUARD] Confidence too low for definitive verdict. "
            + result.get("summary", "")
        )

    # --- RANK: generate scan ID ---
    scan_id   = "FT-" + str(uuid.uuid4())[:8].upper()
    timestamp = datetime.datetime.utcnow().isoformat()

    # --- CYCLE: persist to DB ---
    with get_db() as conn:
        conn.execute("""
            INSERT INTO scan_records VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            scan_id, timestamp,
            owner_name, owner_phone,
            currency_type, denomination,
            location, dealer, notes,
            result.get("verdict"),
            result.get("confidence"),
            result.get("alert_severity"),
            result.get("serial_pattern"),
            result.get("watermark"),
            result.get("security_thread"),
            result.get("microprint"),
            result.get("ink_quality"),
            result.get("texture_score"),
            result.get("summary"),
            img_thumb,
        ))

    # --- TRAIL: SMS dispatch ---
    sms_info = {}
    if owner_phone:
        sms_info = simulate_sms(
            scan_id, owner_phone, owner_name,
            result, currency_type, denomination
        )

    return jsonify({
        "scan_id":  scan_id,
        "timestamp": timestamp,
        "verdict":  result.get("verdict"),
        "confidence": result.get("confidence"),
        "alert_severity": result.get("alert_severity"),
        "details": {
            "serial_pattern":  result.get("serial_pattern"),
            "watermark":       result.get("watermark"),
            "security_thread": result.get("security_thread"),
            "microprint":      result.get("microprint"),
            "ink_quality":     result.get("ink_quality"),
            "texture_score":   result.get("texture_score"),
        },
        "summary": result.get("summary"),
        "sms":     sms_info,
    })


@app.route("/api/records")
def get_records():
    """CYCLE: Return all scan records (newest first)."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM scan_records ORDER BY timestamp DESC"
        ).fetchall()
    return jsonify([dict(r) for r in rows])


@app.route("/api/records/<scan_id>")
def get_record(scan_id):
    """CYCLE: Return a single scan record by ID."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM scan_records WHERE id = ?", (scan_id,)
        ).fetchone()
    if not row:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(dict(row))


@app.route("/api/records/<scan_id>", methods=["DELETE"])
def delete_record(scan_id):
    """CYCLE: Delete a scan record."""
    with get_db() as conn:
        conn.execute("DELETE FROM scan_records WHERE id = ?", (scan_id,))
        conn.execute("DELETE FROM sms_log WHERE scan_id = ?", (scan_id,))
    return jsonify({"deleted": scan_id})


@app.route("/api/stats")
def stats():
    """PRIDE: Aggregated analytics."""
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM scan_records").fetchone()[0]
        by_verdict = conn.execute(
            "SELECT verdict, COUNT(*) as n FROM scan_records GROUP BY verdict"
        ).fetchall()
        by_currency = conn.execute(
            "SELECT currency_type, verdict, COUNT(*) as n "
            "FROM scan_records GROUP BY currency_type, verdict"
        ).fetchall()
        recent = conn.execute(
            "SELECT id, timestamp, owner_name, verdict, confidence "
            "FROM scan_records ORDER BY timestamp DESC LIMIT 5"
        ).fetchall()

    verdict_map = {r["verdict"]: r["n"] for r in by_verdict}
    currency_map = {}
    for r in by_currency:
        c = r["currency_type"]
        if c not in currency_map:
            currency_map[c] = {"AUTHENTIC": 0, "COUNTERFEIT": 0, "SUSPICIOUS": 0}
        currency_map[c][r["verdict"]] = r["n"]

    return jsonify({
        "total": total,
        "authentic":   verdict_map.get("AUTHENTIC", 0),
        "counterfeit": verdict_map.get("COUNTERFEIT", 0),
        "suspicious":  verdict_map.get("SUSPICIOUS", 0),
        "by_currency": currency_map,
        "recent": [dict(r) for r in recent],
        "fake_rate": round(
            (verdict_map.get("COUNTERFEIT", 0) / total * 100) if total else 0, 1
        ),
    })


# ── Run ────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    init_db()
    port = int(os.environ.get("PORT", 5000))
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║   FIN-THEFT DETECTION SYSTEM  ·  v2.1                        ║
║   http://localhost:{port}                                        ║
║   API key set: {'YES ✓' if ANTHROPIC_API_KEY else 'NO — set ANTHROPIC_API_KEY'}                          ║
╚══════════════════════════════════════════════════════════════╝
""")
    app.run(host="0.0.0.0", port=port, debug=False)
