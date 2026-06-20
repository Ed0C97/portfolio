# Portfolio excerpt, adapted.

import os
import stripe
from flask import Blueprint, request, jsonify, current_app

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

stripe_bp = Blueprint("stripe", __name__)

# per-deployment redirect base; defaults to the vite dev server
CHECKOUT_DOMAIN = os.getenv("CHECKOUT_DOMAIN", "http://localhost:5173")


@stripe_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """Create a hosted Checkout session and return its URL."""
    try:
        data = request.get_json() or {}
        amount = data.get("amount")
        payment_method = data.get("paymentMethod")

        # the client can't be trusted, so re-check Stripe's 1-unit minimum here
        if not amount or float(amount) < 1:
            return jsonify(error={"message": "Invalid amount."}), 400

        amount_in_cents = int(float(amount) * 100)

        payment_method_types = ["card", "paypal"]
        if payment_method == "paypal":
            payment_method_types = ["paypal"]

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=payment_method_types,
            line_items=[
                {
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": "Reader contribution",
                            "description": "Support for ad-free, quality content.",
                        },
                        # price comes from the server-validated amount, not a client product id
                        "unit_amount": amount_in_cents,
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            success_url=CHECKOUT_DOMAIN + "/donate/success",
            cancel_url=CHECKOUT_DOMAIN + "/donate/cancelled",
        )
        return jsonify({"url": checkout_session.url})

    except Exception as e:
        current_app.logger.error(f"Checkout session creation failed: {e}")
        return jsonify(error=str(e)), 500


# -----
# One bundle ships to web and to iOS/Android via Capacitor; there is no separate
# native payment path. The React frontend posts to the route above and opens the
# returned URL, which works in both a browser and the Capacitor WebView.
#
#   const res = await apiFetch(`${apiUrl}/api/stripe/create-checkout-session`, {
#     method: 'POST',
#     headers: { 'Content-Type': 'application/json' },
#     body: JSON.stringify({ amount: parseFloat(amount), paymentMethod }),
#   });
#   const session = await res.json();
#   if (session.url) window.location.href = session.url;  // works in web + Capacitor WebView
#
# Capacitor wraps the same `dist/` into the native apps:
#
#   // frontend/capacitor.config.json
#   {
#     "appId": "com.example.magazine",
#     "appName": "Magazine",
#     "webDir": "dist",
#     "server": { "androidScheme": "https", "iosScheme": "https" }
#   }
#
# Build, then sync into the native projects:
#   pnpm run build && npx cap sync ios     // @capacitor/ios, @capacitor/android ^8
# -----
