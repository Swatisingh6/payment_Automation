"""
app.py
------
Flask merchant backend integrated with Razorpay India (Test Mode, INR).
Supports creating INR orders for multiple sample products and verifying
Razorpay payment signatures server-side.
"""

import os
import razorpay
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

KEY_ID = os.getenv("RAZORPAY_KEY_ID")
KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

if not KEY_ID or not KEY_SECRET:
    raise RuntimeError("Razorpay API keys are missing from .env")

client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

# Sample Indian catalog (amounts in paise; currency strictly INR)
PRODUCTS = {
    "starter": {
        "id": "starter",
        "name": "Starter Digital Pass",
        "amount_paise": 5000,
        "display_amount": "₹50",
        "description": "Single-user digital access pass (INR)",
    },
    "pro": {
        "id": "pro",
        "name": "Pro Merchant Toolkit",
        "amount_paise": 49900,
        "display_amount": "₹499",
        "description": "Monthly analytics & payout automation suite (INR)",
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Enterprise Settlement Pack",
        "amount_paise": 149900,
        "display_amount": "₹1,499",
        "description": "High-volume multi-rail settlement pack (INR)",
    },
}


@app.route("/")
def home():
    product_id = request.args.get("product", "starter")
    selected = PRODUCTS.get(product_id, PRODUCTS["starter"])
    return render_template(
        "index.html",
        key_id=KEY_ID,
        products=list(PRODUCTS.values()),
        selected_product=selected,
    )


@app.route("/create-order", methods=["POST"])
def create_order():
    try:
        payload = request.get_json(silent=True) or {}
        product_id = payload.get("product_id", "starter")
        product = PRODUCTS.get(product_id, PRODUCTS["starter"])
        amount = int(payload.get("amount", product["amount_paise"]))

        order = client.order.create(
            data={
                "amount": amount,
                "currency": "INR",
                "receipt": f"rcpt_in_{product['id']}",
                "notes": {"country": "IN", "product": product["name"]},
            }
        )

        return jsonify(
            {
                "order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"],
                "product_name": product["name"],
            }
        )
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


@app.route("/verify-payment", methods=["POST"])
def verify_payment():
    data = request.get_json(silent=True) or {}

    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "razorpay_signature": data["razorpay_signature"],
            }
        )

        return jsonify(
            {
                "status": "success",
                "message": "Payment verified successfully!",
                "razorpay_order_id": data["razorpay_order_id"],
                "razorpay_payment_id": data["razorpay_payment_id"],
                "currency": "INR",
            }
        )
    except Exception:
        return (
            jsonify(
                {
                    "status": "failed",
                    "message": "Payment verification failed!",
                }
            ),
            400,
        )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
