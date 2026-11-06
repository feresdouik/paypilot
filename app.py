import os
import sqlite3
import json
import math
import requests
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, render_template, redirect
from groq import Groq

app = Flask(__name__)
DB = os.getenv("DATABASE_PATH", "paypilot.db")
PAYPAL_BASE = "https://api-m.sandbox.paypal.com"


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer TEXT,product TEXT,amount REAL,status TEXT,created_at TEXT)")
        c.execute("""CREATE TABLE IF NOT EXISTS payments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            paypal_order_id TEXT UNIQUE,
            capture_id TEXT,
            description TEXT,
            amount REAL NOT NULL,
            currency TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )""")
        if c.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            demo = [("Amira", "Streetwear hoodie", 89, "Delivered"), ("Youssef", "Classic T-shirt", 45, "Pending"), ("Sarra", "Oversized shirt", 65, "Processing"), ("Malek", "Cargo pants", 110, "Delivered")]
            c.executemany("INSERT INTO orders(customer,product,amount,status,created_at) VALUES(?,?,?,?,?)", [(a, b, v, s, datetime.utcnow().isoformat()) for a, b, v, s in demo])


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok", app="PayPilot", paypal_mode="sandbox")


def get_orders():
    with conn() as c:
        return [dict(x) for x in c.execute("SELECT * FROM orders ORDER BY id DESC")]


def summarize(orders):
    by_product = defaultdict(lambda: {"delivered_revenue": 0.0, "pipeline_value": 0.0, "cancelled_value": 0.0, "delivered_orders": 0, "pipeline_orders": 0, "cancelled_orders": 0})
    for order in orders:
        item = by_product[order["product"]]
        amount = float(order["amount"] or 0)
        status = order["status"]
        if status == "Delivered":
            item["delivered_revenue"] += amount
            item["delivered_orders"] += 1
        elif status in ("Pending", "Processing"):
            item["pipeline_value"] += amount
            item["pipeline_orders"] += 1
        elif status == "Cancelled":
            item["cancelled_value"] += amount
            item["cancelled_orders"] += 1
    products = []
    for name, values in by_product.items():
        products.append({"product": name, **{key: round(value, 2) if key.endswith("_value") or key.endswith("_revenue") else value for key, value in values.items()}})
    products.sort(key=lambda x: x["delivered_revenue"], reverse=True)
    delivered = [o for o in orders if o["status"] == "Delivered"]
    pipeline = [o for o in orders if o["status"] in ("Pending", "Processing")]
    cancelled = [o for o in orders if o["status"] == "Cancelled"]
    delivered_revenue = round(sum(float(o["amount"] or 0) for o in delivered), 2)
    return {"total_orders": len(orders), "delivered_orders": len(delivered), "pipeline_orders": len(pipeline), "cancelled_orders": len(cancelled), "delivered_revenue": delivered_revenue, "average_delivered_order_value": round(delivered_revenue / len(delivered), 2) if delivered else 0, "pipeline_value": round(sum(float(o["amount"] or 0) for o in pipeline), 2), "cancelled_value": round(sum(float(o["amount"] or 0) for o in cancelled), 2), "products": products}


@app.get("/api/summary")
def summary():
    orders = get_orders()
    stats = summarize(orders)
    return jsonify(orders=orders, revenue=stats["delivered_revenue"], order_count=stats["total_orders"], pending=stats["pipeline_orders"], currency="USD", **stats)


@app.post("/api/orders")
def add():
    d = request.get_json(force=True)
    try:
        amount = float(d.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    customer = str(d.get("customer", "")).strip()
    product = str(d.get("product", "")).strip()
    if not customer or not product or not math.isfinite(amount) or amount <= 0:
        return jsonify(error="Enter customer, product and a positive amount."), 400
    with conn() as c:
        cur = c.execute("INSERT INTO orders(customer,product,amount,status,created_at) VALUES(?,?,?,?,?)", (customer, product, amount, "Pending", datetime.utcnow().isoformat()))
    return jsonify(id=cur.lastrowid), 201


@app.patch("/api/orders/<int:i>")
def update(i):
    status = request.get_json(force=True).get("status")
    if status not in ("Pending", "Processing", "Delivered", "Cancelled"):
        return jsonify(error="Invalid status"), 400
    with conn() as c:
        cur = c.execute("UPDATE orders SET status=? WHERE id=?", (status, i))
        if not cur.rowcount:
            return jsonify(error="Order not found"), 404
    return jsonify(ok=True)


def paypal_access_token():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    secret = os.getenv("PAYPAL_CLIENT_SECRET")
    if not client_id or not secret:
        raise RuntimeError("PayPal Sandbox credentials are not configured.")
    response = requests.post(
        PAYPAL_BASE + "/v1/oauth2/token",
        auth=(client_id, secret),
        data={"grant_type": "client_credentials"},
        headers={"Accept": "application/json", "Accept-Language": "en_US"},
        timeout=20
    )
    response.raise_for_status()
    return response.json()["access_token"]


@app.get("/api/payments")
def payments():
    with conn() as c:
        rows = [dict(x) for x in c.execute("SELECT * FROM payments ORDER BY id DESC LIMIT 50")]
    return jsonify(payments=rows, configured=bool(os.getenv("PAYPAL_CLIENT_ID") and os.getenv("PAYPAL_CLIENT_SECRET")))


@app.post("/api/paypal/create-order")
def paypal_create_order():
    data = request.get_json(force=True)
    description = str(data.get("description", "PayPilot demo payment")).strip()[:120]
    try:
        amount = float(data.get("amount", 0))
    except (TypeError, ValueError):
        amount = 0
    currency = str(data.get("currency", "USD")).upper()
    if not math.isfinite(amount) or amount < 1 or amount > 10000:
        return jsonify(error="Enter an amount between 1 and 10,000."), 400
    if currency != "USD":
        return jsonify(error="The current demo supports USD only."), 400
    try:
        token = paypal_access_token()
        root = request.url_root.rstrip("/")
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "description": description or "PayPilot demo payment",
                "amount": {"currency_code": currency, "value": f"{amount:.2f}"}
            }],
            "payment_source": {
                "paypal": {
                    "experience_context": {
                        "brand_name": "PayPilot Demo",
                        "user_action": "PAY_NOW",
                        "return_url": root + "/?paypal=return",
                        "cancel_url": root + "/?paypal=cancel"
                    }
                }
            }
        }
        response = requests.post(
            PAYPAL_BASE + "/v2/checkout/orders",
            json=payload,
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            timeout=25
        )
        response.raise_for_status()
        result = response.json()
        order_id = result["id"]
        approval = next((link["href"] for link in result.get("links", []) if link.get("rel") == "payer-action"), None)
        if not approval:
            approval = next((link["href"] for link in result.get("links", []) if link.get("rel") == "approve"), None)
        if not approval:
            return jsonify(error="PayPal did not return an approval link."), 502
        with conn() as c:
            c.execute(
                "INSERT INTO payments(paypal_order_id,description,amount,currency,status,created_at) VALUES(?,?,?,?,?,?)",
                (order_id, description, amount, currency, "CREATED", datetime.utcnow().isoformat())
            )
        return jsonify(approval_url=approval, order_id=order_id), 201
    except requests.RequestException:
        app.logger.exception("PayPal create order failed")
        return jsonify(error="PayPal Sandbox request failed. Check credentials and Render logs."), 502
    except RuntimeError as error:
        return jsonify(error=str(error)), 503
    except Exception:
        app.logger.exception("Unexpected PayPal create-order error")
        return jsonify(error="Could not create PayPal order."), 500


@app.post("/api/paypal/capture-order")
def paypal_capture_order():
    order_id = str(request.get_json(force=True).get("order_id", "")).strip()
    if not order_id:
        return jsonify(error="Missing PayPal order ID."), 400
    with conn() as c:
        existing = c.execute("SELECT * FROM payments WHERE paypal_order_id=?", (order_id,)).fetchone()
    if not existing:
        return jsonify(error="This PayPal order was not created by this PayPilot demo."), 404
    if existing["status"] == "COMPLETED":
        return jsonify(status="COMPLETED", message="This payment was already captured.")
    try:
        token = paypal_access_token()
        response = requests.post(
            PAYPAL_BASE + f"/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
            json={},
            timeout=25
        )
        response.raise_for_status()
        result = response.json()
        status = result.get("status", "UNKNOWN")
        capture_id = None
        for unit in result.get("purchase_units", []):
            for capture in unit.get("payments", {}).get("captures", []):
                capture_id = capture.get("id") or capture_id
        with conn() as c:
            c.execute("UPDATE payments SET status=?,capture_id=? WHERE paypal_order_id=?", (status, capture_id, order_id))
        return jsonify(status=status, capture_id=capture_id)
    except requests.RequestException:
        app.logger.exception("PayPal capture failed")
        return jsonify(error="PayPal could not capture this order. Check its status in Sandbox."), 502
    except RuntimeError as error:
        return jsonify(error=str(error)), 503


@app.post("/api/chat")
def chat():
    msg = str(request.get_json(force=True).get("message", "")).strip()
    if not msg:
        return jsonify(error="Enter a message"), 400
    orders = get_orders()
    stats = summarize(orders)
    with conn() as c:
        payment_rows = [dict(x) for x in c.execute("SELECT amount,currency,status FROM payments ORDER BY id DESC LIMIT 100")]
    completed_payments = [p for p in payment_rows if p["status"] == "COMPLETED"]
    payment_snapshot = {
        "paypal_sandbox_payments": len(payment_rows),
        "completed_sandbox_amount_usd": round(sum(float(p["amount"]) for p in completed_payments if p["currency"] == "USD"), 2),
        "pending_or_other_sandbox_payments": len(payment_rows) - len(completed_payments)
    }
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return jsonify(reply="AI is not connected yet. Add GROQ_API_KEY to the deployment environment. The dashboard and PayPal Sandbox features work independently.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    system_prompt = (
        "You are PayPilot, a careful payment and small-business operations analyst. Use only the supplied snapshot. "
        "Order amounts are USD. Distinguish sample order records from PayPal Sandbox transactions. "
        "Sandbox payments are tests, not real business revenue. Never describe them as real money received. "
        "Do not calculate profit, margin, or ROI because cost and fee data are not collected. "
        "Never claim to execute payments or change records. Give concise, practical recommendations in Markdown. "
        "Order snapshot: " + json.dumps(stats, ensure_ascii=False) +
        " PayPal Sandbox snapshot: " + json.dumps(payment_snapshot, ensure_ascii=False)
    )
    try:
        client = Groq(api_key=key)
        out = client.chat.completions.create(model=model, messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": msg}], temperature=0.2, max_tokens=900)
        return jsonify(reply=out.choices[0].message.content)
    except Exception:
        app.logger.exception("Groq error")
        return jsonify(error="AI service unavailable. Check the Render logs for the Groq error."), 502


init()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
