#  AI Payment Agent System

A college assessment project implementing two AI-powered agents:
1. **AI Calling Agent** — Automated payment recovery calls with real-time voice conversation
2. **AI Reconciliation Agent** — Automated data reconciliation across multiple Excel files with email reporting

---

##  Project Structure

```
ai_payment_project/
│
├── calling_agent/
│   ├── __init__.py
│   ├── ai_calling.py          # Reads Excel, initiates calls
│   ├── conversation.py        # Gemini AI response generation
│   ├── twilio_caller.py       # Twilio call creation
│   └── webhook_server.py      # Flask server for real-time conversation
│
├── reconciliation_agent/
│   ├── __init__.py
│   └── reconcile.py           # Reconciliation logic with AI suggestions
│
├── data/
│   ├── input.xlsx             # Customer list for calling agent
│   ├── base.xlsx              # Benchmark file for reconciliation
│   ├── compare.xlsx           # Comparison file for reconciliation
│   └── call_results.csv       # Auto-generated call outcome storage
│
├── output/
│   ├── differences_with_comments.xlsx   # Reconciliation mismatches
│   ├── base_data.xlsx                   # Copy of base data
│   └── input_with_results.xlsx          # Input + call results merged
│
├── database.py                # CSV-based storage (no DB needed)
├── email_sender.py            # Gmail SMTP email with attachments
├── main.py                    # Entry point with interactive menu
├── .env                       # API keys (never commit this!)
├── .gitignore
└── requirements.txt
```

---

##  Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai_payment_project.git
cd ai_payment_project
```

### 2. Create and activate virtual environment
```bash
python3 -m venv myenv
source myenv/bin/activate        # Mac/Linux
myenv\Scripts\activate           # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```bash
cp .env.example .env
```
Fill in your credentials (see Environment Variables section below).

### 5. Install Cloudflare Tunnel (for Twilio webhooks)
```bash
brew install cloudflared          # Mac
# or download from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/
```

---

## Environment Variables

Create a `.env` file in the root directory:

```env
# Twilio (https://console.twilio.com)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx

# Google Gemini (https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_api_key

# Gmail (use App Password, not your real password)
# Enable at: https://myaccount.google.com/apppasswords
EMAIL=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

>  **Never commit `.env` to GitHub.** It is already in `.gitignore`.

---

##  Input Data Format

### `data/input.xlsx` — Calling Agent Input
| Name | Phone | Account | Amount | Email |
|------|-------|---------|--------|-------|
| Anshuman Rathore | +918696872775 | ACC001 | 12500 | anshumanrathore345@gmail.com |

> **Note:** Phone numbers must include country code (e.g. `+91` for India). Twilio trial accounts can only call **verified numbers**.

### `data/base.xlsx` — Reconciliation Benchmark
| Account | Name | Amount | Payment_Date | Status |
|---------|------|--------|-------------|--------|
| ACC001 | Anshuman Rathore | 12500 | 2024-01-15 | Pending |

### `data/compare.xlsx` — Reconciliation Comparison File
Same columns as `base.xlsx`. Differences will be highlighted automatically.

---

## Running the Project

### Step 1 — Start Cloudflare Tunnel (in a separate terminal)
```bash
cloudflared tunnel --url http://localhost:5000
```
Copy the URL shown, e.g. `https://xyz.trycloudflare.com`

### Step 2 — Run the main program
```bash
python3 main.py
```

### Menu Options

```
==================================================
  AI AGENT SYSTEM
==================================================
1. Run Calling Agent
2. Run Reconciliation Agent
3. View Call Results (CSV)
4. Export input_with_results.xlsx
5. Exit
```

---

##  Agent 1: AI Calling Agent

### How it works
1. Reads customer data from `data/input.xlsx`
2. Initiates calls via **Twilio**
3. Plays an opening message and listens for customer speech
4. **Gemini AI** generates contextual responses in real-time
5. Conversation loops until payment is confirmed or a date is given
6. Results saved to `data/call_results.csv`

### Supported Languages
| Code | Language |
|------|----------|
| `en` | English |
| `hi` | Hindi |
| `hinglish` | Hinglish (Hindi + English) |
| `ta` | Tamil |
| `te` | Telugu |

### Call Flow
```
Customer picks up
      ↓
Flask /start_call → Opening message played
      ↓
Customer speaks → Twilio transcribes → Flask /respond
      ↓
Gemini generates reply → Spoken back to customer
      ↓
Loop until: Payment Promised / Date Given / Call Ends
      ↓
Result saved to data/call_results.csv
```

### Call Result Statuses
| Status | Meaning |
|--------|---------|
| `Pending` | Not yet called |
| `PAYMENT_PROMISED` | Customer agreed to pay |
| `DATE_GIVEN:YYYY-MM-DD` | Customer gave next payment date |
| `END` | Call ended without resolution |

---

## 📂 Agent 2: AI Reconciliation Agent

### How it works
1. Reads `data/base.xlsx` (benchmark) and `data/compare.xlsx`
2. Merges on `Account` number
3. Detects mismatches and missing records
4. Adds AI-suggested next steps for each discrepancy
5. Saves two output files and emails them as attachments

### Mismatch Types Detected
| Status | Meaning |
|--------|---------|
| `MATCH` | Record identical in both files |
| `AMOUNT_MISMATCH` | Same account, different amount |
| `MISSING_IN_COMPARE` | Record in base but not in compare |
| `MISSING_IN_BASE` | Record in compare but not in base |

### Output Files
- `output/differences_with_comments.xlsx` — All non-matching records with suggested actions
- `output/base_data.xlsx` — Copy of original base data

### Email Report
Both files are automatically emailed as attachments with subject:
> *"Reconciliation Report — Differences & Base Data"*

---

## requirements.txt

```
twilio
flask
pandas
openpyxl
google-genai
python-dotenv
```

---

## Known Limitations

- **Twilio Trial Account:** Can only call verified phone numbers. Verify numbers at [console.twilio.com/us1/verify/phone-numbers](https://console.twilio.com/us1/verify/phone-numbers)
- **Gemini Free Tier:** Subject to rate limits. The code automatically falls back through multiple models (`gemini-1.5-flash-8b` → `gemini-1.5-flash` → `gemini-2.0-flash-lite`)
- **Cloudflare Tunnel:** URL changes every time you restart `cloudflared`. The app auto-detects it via the metrics API.
- **No persistent database:** All data stored in CSV/Excel files inside the `data/` folder.

---

## Troubleshooting
| Problem | Solution |
|---------|----------|
| `429 RESOURCE_EXHAUSTED` from Gemini | Free quota hit. Wait or use a different API key |
| `21219` Twilio error | Phone number not verified in trial account |
| Cloudflare URL not detected | Check metrics port (20241–20250) or paste URL manually |
| `Connection refused` on tunnel | Start `cloudflared tunnel --url http://localhost:5000` first |
| Gmail auth error | Use App Password not account password. Enable 2FA first |

---

## Author

**Anshuman Rathore**
📧 anshumanrathore345@gmail.com

---

## License

This project is submitted as a college assessment. Not for commercial use.
