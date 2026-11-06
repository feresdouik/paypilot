import os
import sqlite3
import json
import math
from datetime import datetime
from collections import defaultdict
from flask import Flask, request, jsonify, render_template
from groq import Groq

app = Flask(__name__)
DB = os.getenv("DATABASE_PATH", "paypilot.db")


def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c


def init():
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,customer TEXT,product TEXT,amount REAL,status TEXT,created_at TEXT)")
        if c.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 0:
            demo = [("Amira", "Streetwear hoodie", 89, "Delivered"), ("Youssef", "Classic T-shirt", 45, "Pending"), ("Sarra", "Oversized shirt", 65, "Processing"), ("Malek", "Cargo pants", 110, "Delivered")]
            c.executemany("INSERT INTO orders(customer,product,amount,status,created_at) VALUES(?,?,?,?,?)", [(a, b, v, s, datetime.utcnow().isoformat()) for a, b, v, s in demo])


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify(status="ok", app="PayPilot")


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


@app.post("/api/chat")
def chat():
    msg = str(request.get_json(force=True).get("message", "")).strip()
    if not msg:
        return jsonify(error="Enter a message"), 400
    orders = get_orders()
    stats = summarize(orders)
    key = os.getenv("GROQ_API_KEY")
    if not key:
        return jsonify(reply="AI is not connected yet. Add GROQ_API_KEY to the deployment environment. Your dashboard and order manager work without it.")
    model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
    system_prompt = (
        "You are PayPilot, a careful payment and small-business operations analyst. Use only the supplied business snapshot. "
        "All order amounts are denominated in US dollars (USD). Always label monetary figures as USD or $. "
        "delivered_revenue includes ONLY Delivered orders. pipeline_value is Pending plus Processing orders and is NOT earned revenue. "
        "Cancelled orders are excluded from revenue and pipeline. Never add pipeline value to delivered revenue. "
        "The dataset has no costs, fees, ad spend, stock quantities, dates or customer-contact permissions. "
        "Do not calculate profit, margin, ROI, or a sales trend; explain what additional data is needed. "
        "Do not recommend contacting named customers, sending emails, applying discounts, or claim to execute actions. "
        "Give practical low-risk recommendations that can be done manually. Rank products by delivered revenue and separately mention pipeline value. "
        "Be concise and format answers in Markdown with headings, bullets, and a compact table when useful. "
        "Business snapshot (aggregated; no customer names): " + json.dumps(stats, ensure_ascii=False)
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
