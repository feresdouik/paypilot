# PayPilot

**An AI-powered payment operations assistant for small businesses, with a PayPal Sandbox checkout prototype.**

PayPilot helps small businesses organize order records, test a PayPal checkout flow, review payment statuses, and explore AI-assisted business insights.

> **Project status:** The repository now includes a server-side PayPal Sandbox create-order and capture flow. It is a test integration only: use PayPal Sandbox accounts and credentials. No live payments are enabled.

## Problem

Small businesses often track orders and payment status across chats, spreadsheets, and manual notes. This makes it difficult to see what is paid, what is pending, and where follow-up is needed.

## Current features

- Business dashboard with sample order metrics
- Add order records and update their statuses
- PayPal Sandbox checkout: create an order, redirect to PayPal approval, return, and capture the approved order
- Store PayPal order IDs, capture IDs, amounts, timestamps, and statuses in SQLite
- Payment history table in the dashboard
- Server-side PayPal OAuth token exchange; client secrets never enter browser code
- AI assistant can summarize order records and clearly distinguish Sandbox tests from real revenue
- `/health` endpoint for deployment checks

## PayPal Sandbox setup

1. Open the [PayPal Developer Dashboard](https://developer.paypal.com/dashboard/).
2. Create or select a **Sandbox** REST app.
3. Copy its Sandbox Client ID and Secret.
4. Configure these environment variables on the server (for example, in Render):
   - `PAYPAL_CLIENT_ID` — Sandbox app client ID
   - `PAYPAL_CLIENT_SECRET` — Sandbox app secret
5. Deploy the app over HTTPS and open the PayPal Sandbox section.
6. Create a test payment. PayPilot redirects to PayPal Sandbox for approval; after approval, it returns to PayPilot and captures the order.
7. Use a Sandbox personal test account as the payer. Do not use real payment credentials.

The current checkout demo supports **USD** only. It uses PayPal's Sandbox API base URL and does not offer live payment processing.

## Run locally

Requirements: Python 3.10 or newer.

```bash
git clone https://github.com/feresdouik/paypilot.git
cd paypilot
pip install -r requirements.txt
python app.py
```

Optional AI assistant configuration:

- `GROQ_API_KEY`
- `GROQ_MODEL`

PayPal Sandbox configuration:

- `PAYPAL_CLIENT_ID`
- `PAYPAL_CLIENT_SECRET`

On Windows PowerShell, set values in the current terminal session:

```powershell
$env:PAYPAL_CLIENT_ID="your_sandbox_client_id"
$env:PAYPAL_CLIENT_SECRET="your_sandbox_secret"
$env:GROQ_API_KEY="your_groq_api_key"
$env:GROQ_MODEL="your_available_groq_model"
python app.py
```

Never commit API keys, client secrets, or other credentials to GitHub. Configure secrets as environment variables in your deployment platform.

## Deploy on Render

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- Add `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` as secret environment variables using Sandbox credentials.
- Add `GROQ_API_KEY` and `GROQ_MODEL` if AI chat is required.
- Use HTTPS for the deployed checkout return URL.
- Verify `/health` after deployment.

## Technology stack

- Python, Flask, Gunicorn
- SQLite
- PayPal REST API (Sandbox)
- Groq API for optional AI analysis
- HTML, CSS, JavaScript

## Important limitations and safety

- Sandbox transactions are simulated tests, not real customer payments or revenue.
- Live PayPal processing is not implemented or enabled.
- Sample order records are fictional demo data.
- The current prototype supports USD only.
- AI provides analysis; it does not execute payments or change transaction records.
- SQLite is suitable for this prototype. A production service needs persistent managed storage, authentication, access controls, monitoring, and additional payment lifecycle safeguards.
- Never expose the PayPal client secret in frontend code or commit it to the repository.

## Team

**NexoraForge AI** — Solo project
