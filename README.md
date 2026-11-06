# PayPilot

**AI-assisted payment operations for small businesses, with a PayPal Sandbox checkout prototype.**

PayPilot brings sample order management, payment tracking, and AI-assisted business summaries into one simple dashboard. It was built as a hackathon prototype to demonstrate how small businesses could get a clearer view of orders and payment activity.

<p align="center">
  <a href="https://paypilot-xfcb.onrender.com">Live Demo</a> ·
  <a href="https://paypilot-xfcb.onrender.com/health">Health Check</a> ·
  <a href="https://github.com/feresdouik/paypilot">Source Code</a>
</p>

> **Important:** PayPal integration runs in Sandbox mode only. Transactions are simulated tests, not real payments or revenue. The dashboard's starter orders are fictional sample data.

## What it demonstrates

- **Business overview:** delivered revenue, order counts, pending pipeline, cancelled orders, and average delivered order value.
- **Order management:** add sample orders and update their statuses.
- **PayPal Sandbox checkout:** create a test order, approve it with a Sandbox buyer account, and capture it on return.
- **Payment history:** store and display PayPal order IDs, capture IDs, amounts, timestamps, and statuses.
- **AI assistant:** ask for concise summaries of order records and Sandbox payment activity using Groq (optional).
- **Health endpoint:** check deployment status at `/health`.

## Try the live demo

1. Open the [PayPilot demo](https://paypilot-xfcb.onrender.com).
2. Explore the overview and fictional sample orders.
3. Open **PayPal Sandbox** and create a small test payment in USD.
4. Approve it using a PayPal **Sandbox personal test account**.
5. Return to PayPilot and check the payment history for the captured status.
6. Open **AI Assistant** and ask: `Summarize the business activity and explain the latest Sandbox payment.`

The hosted service may take a short time to wake up if it has been idle. PayPal checkout requires valid Sandbox credentials configured on the server. AI chat requires a Groq API key.

## Run locally

**Requirements:** Python 3.10+

```bash
git clone https://github.com/feresdouik/paypilot.git
cd paypilot
pip install -r requirements.txt
python app.py
```

Then open [http://localhost:5000](http://localhost:5000).

### Environment variables

| Variable | Required for | Description |
|---|---|---|
| `PAYPAL_CLIENT_ID` | PayPal Sandbox checkout | Sandbox REST app client ID |
| `PAYPAL_CLIENT_SECRET` | PayPal Sandbox checkout | Sandbox REST app secret |
| `GROQ_API_KEY` | AI assistant | Groq API key |
| `GROQ_MODEL` | AI assistant | Optional model override |
| `DATABASE_PATH` | Optional | SQLite database path |

PayPal and Groq integrations are optional for starting the dashboard. Without PayPal credentials, the checkout feature will report that Sandbox credentials are not configured. Without `GROQ_API_KEY`, the assistant explains that AI is not connected while the rest of the app remains usable.

**Windows PowerShell example:**

```powershell
$env:PAYPAL_CLIENT_ID="your_sandbox_client_id"
$env:PAYPAL_CLIENT_SECRET="your_sandbox_secret"
$env:GROQ_API_KEY="your_groq_api_key"
$env:GROQ_MODEL="your_available_groq_model"
python app.py
```

Never commit API keys, client secrets, or other credentials to GitHub. Use environment variables or your hosting provider's secret settings.

## Deploy on Render

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `gunicorn app:app`
- Add `PAYPAL_CLIENT_ID` and `PAYPAL_CLIENT_SECRET` as secret environment variables, using Sandbox credentials.
- Add `GROQ_API_KEY` and optionally `GROQ_MODEL` to enable AI chat.
- Use HTTPS for the deployed checkout return URL.
- Verify the deployment at `/health`.

## Technology stack

- Python, Flask, Gunicorn
- SQLite
- PayPal REST API (Sandbox)
- Groq API (optional AI assistant)
- HTML, CSS, JavaScript

## Demo scope and limitations

- PayPal Sandbox transactions are simulated tests; no live payment processing is implemented or enabled.
- Sample order records are fictional and must not be interpreted as real business activity.
- The checkout demo currently supports **USD only**.
- The AI assistant provides analysis; it does not execute payments or modify transaction records.
- The prototype does not yet include user authentication, role-based access controls, or production-grade payment operations.
- SQLite is suitable for this prototype. A production deployment should use persistent managed storage, authentication, access controls, monitoring, and additional payment lifecycle safeguards.

## Hackathon presentation outline (about 90 seconds)

1. **Problem:** small businesses often track orders and payment status across chats, spreadsheets, and manual notes.
2. **Overview:** show how PayPilot organizes sample order activity in one dashboard.
3. **Checkout:** create a small USD Sandbox order, approve it with a Sandbox buyer, and show the resulting payment status.
4. **AI assistant:** ask it to summarize the business activity and latest Sandbox payment.
5. **Transparency:** explain clearly that sample orders are fictional and Sandbox payments are not real revenue.

## Project

**NexoraForge AI** · Solo hackathon project

Built by [Feres Douik](https://github.com/feresdouik).
