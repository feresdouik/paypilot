# PayPilot

**An AI-powered payment operations assistant for small businesses.**

PayPilot is an early-stage prototype exploring how small businesses can organize payment records, understand payment status, and turn transaction data into clearer business decisions.

> **Project status:** The current codebase is an adapted dashboard MVP. It currently manages demo order records and provides AI-assisted business analysis. PayPal API integration and real payment processing are **not implemented yet**.

## The problem

Small businesses often track orders and payment status across chats, spreadsheets, and manual notes. This makes it difficult to see what has been paid, what is still pending, and where follow-up is needed.

## The proposed solution

PayPilot aims to bring payment visibility and AI-assisted insights into one simple workspace. The first development phase focuses on a clear transaction dashboard; later phases will explore a secure PayPal Sandbox integration.

## Current prototype features

- Dashboard summary based on sample order records
- Add orders and update their statuses
- Separate delivered amounts from pending/processing pipeline amounts
- AI assistant that analyzes aggregated business figures
- SQLite storage and a health-check endpoint

## Planned development

1. Rebrand and separate this project from BizPilot.
2. Evolve order records into payment/transaction records with clear statuses.
3. Add PayPal Developer Sandbox integration using server-side environment variables.
4. Demonstrate payment creation and status verification in Sandbox, subject to the hackathon requirements.
5. Improve validation, error handling, and deployment readiness.

## Technology stack

- **Backend:** Python, Flask, Gunicorn
- **Database:** SQLite
- **AI inference:** Groq API
- **Frontend:** HTML, CSS, JavaScript
- **Planned payment integration:** PayPal Developer APIs (not yet connected)

## Run locally

Requirements: Python 3.10 or newer.

1. Clone this repository:
   ```bash
   git clone https://github.com/feresdouik/paypilot.git
   cd paypilot
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. (Optional) Configure Groq for AI analysis:
   - Set `GROQ_API_KEY` to your private API key.
   - Set `GROQ_MODEL` to a model available to your account.
4. Start the app:
   ```bash
   python app.py
   ```
5. Open http://localhost:5000.

### Windows PowerShell

```powershell
$env:GROQ_API_KEY="your_groq_api_key"
$env:GROQ_MODEL="your_available_groq_model"
python app.py
```

Never commit API keys or other secrets to GitHub. Use environment variables or the hosting provider's secret settings.

## Deploy on Render

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- Configure `GROQ_API_KEY` and `GROQ_MODEL` as environment variables if AI chat is required.
- Verify the `/health` endpoint after deployment.

## Important limitations

- Demo records are fictional sample data, not real customer transactions.
- The current prototype does not connect to PayPal, move money, charge customers, issue refunds, or verify real payments.
- AI output is analysis only; it does not execute actions.
- Current sample amounts are displayed as USD.
- SQLite is suitable for this prototype; production deployment should use persistent managed storage and stronger operational safeguards.

## Team

**NexoraForge AI** — Solo project
