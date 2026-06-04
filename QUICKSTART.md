# 🛡 Fin-Theft Detection System — Quick Start Guide

## Installation & Running (2 minutes)

### macOS / Linux
```bash
cd fin_theft_detection
bash run.sh
```

### Windows
```bash
cd fin_theft_detection
run.bat
```

Then open **http://localhost:5000** in your browser.

---

## Testing All Features (5 minutes)

Once the system is running at `http://localhost:5000`:

### 1. Upload a Currency Image
- Click the upload zone or drag a JPG/PNG image
- Any image will work for testing (we'll use a demo image)
- You should see the preview appear below the upload zone

### 2. Fill in Owner Details
- **Owner Name**: Enter any name (e.g., "Daoud")
- **Phone Number**: Enter a phone number (e.g., "+249901234567")
- **Currency Type**: Select USD or any currency
- **Denomination**: Enter "100" or any amount
- **Location**: Enter "Custom Market" or any location
- **Dealer**: Optional
- **Notes**: Optional additional context

### 3. Click "Analyze Currency" Button
- The button should become **enabled** (clickable) once you upload an image
- Click it to send the image to the AI for analysis
- You'll see a spinning animation while analyzing
- After 10–30 seconds, you'll see the results

### 4. View Results
The result card shows:
- **Verdict**: AUTHENTIC, COUNTERFEIT, or SUSPICIOUS
- **Confidence**: 0–100% score
- **Details**: 
  - Serial Pattern
  - Watermark
  - Security Thread
  - Microprint
  - Ink Quality
  - Texture Score
- **AI Summary**: Plain-English explanation
- **SMS Status**: "SMS SIMULATED → your-phone-number"

### 5. Check Scan Log
- Click the **Scan Log** tab
- Your scan appears in the table
- Search by name, currency, or verdict
- Click **Export CSV** to download records

### 6. View Analytics
- Click the **Analytics** tab
- See total scans, authentication rates
- View breakdown by currency type

### 7. Test All Frameworks
- Click **Frameworks** tab to see how RANK, GUARD, CYCLE, TRAIL, HUNT, PRIDE work

---

## Troubleshooting

### Button Doesn't Enable
- Make sure you selected a valid **image file** (JPG, PNG, WEBP)
- Check browser console (F12) for errors
- File size must be under 15 MB

### Scan Button Click Does Nothing
- Check browser console (F12) for error messages
- Make sure you selected a currency type and denomination
- Owner name is optional but recommended

### No Results Appear
- Wait 10–30 seconds — Claude Vision AI takes time
- Without ANTHROPIC_API_KEY set, you get demo results
- Check Flask terminal for error messages

### SMS Not Sending
- Without a real SMS gateway API key, SMS is **simulated** (logged only)
- To enable real SMS, edit `app.py` and add your gateway (Africa's Talking, Twilio, etc.)
- See README.md for integration instructions

---

## Console Logging (F12)

Open browser Developer Tools (F12) to see detailed logs:
- `✓ Backend health: System Online ✓ | Frameworks: RANK · GUARD · CYCLE · TRAIL · HUNT · PRIDE`
- `✓ File ready: filename.jpg — 150.5 KB`
- `📤 Sending scan request to /api/scan`
- `📥 Scan response received: {verdict: "AUTHENTIC", confidence: 92, …}`
- `✓ Records loaded: 1 scan`

---

## API Endpoints (For Advanced Users)

All endpoints are at `http://localhost:5000/api/`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/scan` | Submit image for analysis |
| GET | `/api/records` | Get all scans |
| GET | `/api/records/<id>` | Get single scan |
| DELETE | `/api/records/<id>` | Delete a scan |
| GET | `/api/stats` | Get analytics |
| GET | `/api/health` | System status |

Example with curl:
```bash
curl http://localhost:5000/api/health
```

---

## Demo Mode (No API Key)

Without `ANTHROPIC_API_KEY` set, the system runs in **demo mode**:
- All scans return a placeholder "SUSPICIOUS" verdict
- SMS is simulated and logged
- Database stores all records normally
- Perfect for testing the UI and workflow

To use real AI analysis:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python app.py
```

---

## Next Steps

1. **Add Real SMS**: Edit `app.py`, find `simulate_sms()`, plug in Africa's Talking or Twilio API
2. **Deploy**: Use Flask production server (Gunicorn, uWSGI)
3. **Customize**: Modify `templates/index.html` for your branding
4. **Extend**: Add more currency types, logos, or custom analysis rules

---

**Questions?** Check README.md for full API documentation and framework details.
