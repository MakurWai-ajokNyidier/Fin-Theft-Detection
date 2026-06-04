# 🛡 Fin-Theft Detection System v2.1

**Copyright © 2024 Fin-Theft Detection Project — MIT License**

> *Built for Daoud and every citizen who has lost money to black-market currency fraud.*

---

## What This System Does

Upload a photo of any banknote → AI forensically analyzes it → verdict displayed on screen → SMS sent to the owner's phone instantly. Every scan is stored in a local SQLite database with full audit trail.

## Architecture

```
Browser (HTML/JS)
      │  HTTP multipart/form-data
      ▼
Flask Python Backend  ──── Anthropic Claude Vision API
      │
      ▼
SQLite Database (data/scan_ledger.db)
```

## Frameworks

| Framework | Full Name | Role |
|-----------|-----------|------|
| **RANK**  | Risk Assessment & Notification Kernel | Scores 6 forensic vectors, maps to verdict |
| **GUARD** | Grounded Universal Anomaly & Risk Defense | Safety rail — blocks low-confidence verdicts |
| **CYCLE** | Centralized Yield & Currency Ledger Engine | SQLite persistent scan ledger |
| **TRAIL** | Transaction Record & Alert Inference Layer | Owner phone → SMS dispatch |
| **HUNT**  | Heuristic UV & Note Tracker | Claude Vision AI analysis |
| **PRIDE** | Performance & Risk Intelligence Dashboard Engine | Analytics & KPI dashboard |

---

## Quick Start

### 1 — Install dependencies
```bash
pip install -r requirements.txt
```

### 2 — Set your Anthropic API key
```bash
# Linux / macOS
export ANTHROPIC_API_KEY=sk-ant-...

# Windows (Command Prompt)
set ANTHROPIC_API_KEY=sk-ant-...

# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-..."
```

> **Don't have a key?** The system still runs in demo mode — you'll get placeholder verdicts.
> Get a key at https://console.anthropic.com

### 3 — Run the server
```bash
python app.py
```

### 4 — Open the app
```
http://localhost:5000
```

---

## SMS Integration (Production)

The TRAIL framework currently **simulates** SMS (logs to database). To enable real SMS:

### Africa's Talking (recommended for East Africa / South Sudan)
```python
# In app.py, replace simulate_sms body with:
import africastalking
africastalking.initialize('your_username', os.environ['AT_API_KEY'])
sms = africastalking.SMS
response = sms.send(message, [phone])
```

### Twilio
```python
from twilio.rest import Client
client = Client(os.environ['TWILIO_SID'], os.environ['TWILIO_TOKEN'])
client.messages.create(body=message, from_='+1XXXXXXXXXX', to=phone)
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET    | `/`                   | Serve frontend UI |
| POST   | `/api/scan`           | Submit image for analysis |
| GET    | `/api/records`        | All scan records |
| GET    | `/api/records/<id>`   | Single record |
| DELETE | `/api/records/<id>`   | Delete record |
| GET    | `/api/stats`          | Aggregated analytics |
| GET    | `/api/health`         | System health check |

### POST /api/scan — Form Fields

| Field | Type | Description |
|-------|------|-------------|
| `image` | file | Currency image (JPG/PNG/WEBP, max 15MB) |
| `owner_name` | text | Name of currency owner |
| `owner_phone` | text | Phone number for SMS alert |
| `currency_type` | text | USD, SSP, SDG, KES, etc. |
| `denomination` | text | Face value (e.g. "100") |
| `location` | text | Market or location |
| `dealer` | text | Dealer/source (optional) |
| `notes` | text | Additional context |

---

## Project Structure

```
fin_theft_detection/
├── app.py              ← Flask backend (RANK · GUARD · CYCLE · TRAIL · HUNT · PRIDE)
├── requirements.txt    ← Python dependencies
├── README.md           ← This file
├── templates/
│   └── index.html      ← Frontend UI (single page)
├── static/             ← Static assets (empty by default)
└── data/
    └── scan_ledger.db  ← SQLite database (auto-created on first run)
```

---

## License

MIT License — free to use, modify, and distribute with attribution.

© 2024 Fin-Theft Detection Project  
Contact: fintheft@example.org

---

*"Technology should protect the most vulnerable — not just those who can afford it."*
