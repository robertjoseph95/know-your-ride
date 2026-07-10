try:  # Sentry server-side error monitoring (F-D3); inert until SENTRY_DSN is set
    import os as _os, sentry_sdk as _sentry; _sentry.init(dsn=_os.environ.get("SENTRY_DSN"))
except Exception: pass
from http.server import BaseHTTPRequestHandler
from http.cookies import SimpleCookie
import json
import os
import sys
import urllib.parse

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

# Live-mode Stripe Price IDs (provided). Monthly $2.99/mo, Annual $23.99/yr.
PRICES = {
    "monthly": "price_1TbBqzEO4bP64F3bjFk52ek8",
    "annual": "price_1TbT7aEO4bP64F3br8pSws4v",
}
SITE = "https://knowyourride.net"


def _redis():
    # Copy-pasted per endpoint (deliberate): Vercel's Python builder bundles only
    # the entry file, so a sibling `import _shared` fails silently at runtime.
    if Redis is None:
        return None
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    if not (url and token):
        return None
    try:
        return Redis(url=url, token=token)
    except Exception:
        return None


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
        # Bind the checkout to the signed-in KYR account when a session token is
        # present (bearer header or kyr_session cookie). The email is ALWAYS
        # resolved server-side from session:<token> -- never taken from a
        # client-supplied value. Anonymous checkout (no/invalid token) is unchanged.
        email = self._session_email()
        try:
            import stripe
            stripe.api_key = key
            params = dict(
                mode="subscription",
                line_items=[{"price": price_id, "quantity": 1}],
                allow_promotion_codes=True,
                billing_address_collection="auto",
                success_url=SITE + "/?success=true&session_id={CHECKOUT_SESSION_ID}",
                cancel_url=SITE + "/?canceled=true",
            )
            if email:
                # client_reference_id + metadata bind the Checkout Session to the
                # account; subscription_data.metadata propagates the same binding
                # onto the Subscription object so customer.subscription.* events
                # (incl. cancellation) resolve the SAME account email in webhook.py.
                params["client_reference_id"] = email
                params["metadata"] = {"kyr_email": email}
                params["subscription_data"] = {"metadata": {"kyr_email": email}}
                params["customer_email"] = email  # prefill/lock payer email; binding does not depend on it
            try:
                session = stripe.checkout.Session.create(**params)
            except Exception as e:
                if not email:
                    raise
                # Never let account-binding break the payment path: retry once
                # without the identity params (identical to pre-fix behavior).
                print(f"[subscribe] bound checkout failed, retrying anonymous: {e}", file=sys.stderr)
                for k in ("client_reference_id", "metadata", "subscription_data", "customer_email"):
                    params.pop(k, None)
                session = stripe.checkout.Session.create(**params)
        except Exception as e:
            print(f"[subscribe] stripe error: {e}", file=sys.stderr)  # server-side only
            return self._send(502, {"error": "Checkout is temporarily unavailable. Please try again."})
        self.send_response(303)
        self.send_header("Location", session.url)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _session_email(self):
        """Resolve the signed-in user's email from a session token, or None.
        Token comes from Authorization: Bearer OR the kyr_session/kyr_token/session
        cookie only -- deliberately NOT from a URL query param. A ?token= tier would
        be a payment-hijack vector: a crafted /api/subscribe?token=<attacker> link,
        clicked by a victim (no bearer header, no first-party cookie on an external
        nav), would bind the victim's real payment to the attacker's account. Bearer
        and cookie can't be planted via a shared link, so they are safe. Validation
        is the server-side Redis lookup session:<token> -> email; no client-supplied
        email is ever trusted."""
        tok = ""
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            tok = auth[7:].strip()
        if not tok:
            try:
                c = SimpleCookie(self.headers.get("Cookie", "") or "")
                for name in ("kyr_session", "kyr_token", "session"):
                    if name in c and c[name].value:
                        tok = c[name].value.strip()
                        break
            except Exception:
                tok = ""
        if not tok:
            return None
        r = _redis()
        if r is None:
            return None
        try:
            v = r.get("session:" + tok)
        except Exception:
            return None
        return str(v).strip().lower() if v else None

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
