from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse

# Live-mode Stripe Price IDs (provided). Monthly $2.99/mo, Annual $23.99/yr.
PRICES = {
    "monthly": "price_1TbBqzEO4bP64F3bjFk52ek8",
    "annual": "price_1TbT7aEO4bP64F3br8pSws4v",
}
SITE = "https://knowyourride.net"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Browser navigates to /api/subscribe?plan=monthly|annual and we 303-redirect
        # it to the Stripe Checkout hosted page (no card handling on our side).
        key = os.environ.get("STRIPE_SECRET_KEY", "")
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        plan = (q.get("plan") or ["monthly"])[0].lower()
        if not key:
            return self._send(503, {"error": "server not configured (STRIPE_SECRET_KEY)"})
        price_id = PRICES.get(plan)
        if not price_id:
            return self._send(400, {"error": "plan must be 'monthly' or 'annual'"})
        try:
            import stripe
            stripe.api_key = key
            session = stripe.checkout.Session.create(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                allow_promotion_codes=True,
                billing_address_collection="auto",
                success_url=SITE + "/?success=true",
                cancel_url=SITE + "/?canceled=true",
            )
        except Exception as e:
            return self._send(502, {"error": f"stripe error: {e}"})
        self.send_response(303)
        self.send_header("Location", session.url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
