try:  # Sentry server-side error monitoring (F-D3); inert until SENTRY_DSN is set
    import os as _os, sentry_sdk as _sentry; _sentry.init(dsn=_os.environ.get("SENTRY_DSN"))
except Exception: pass
from http.server import BaseHTTPRequestHandler
import json
import os
import sys

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

# Subscription state lives in Redis keyed by email (sub:<email> = active|inactive),
# kept long enough for the feature endpoints to read. Stripe is the source of truth;
# verify-subscription re-checks Stripe directly when needed.
ACTIVE_EVENTS = {
    "checkout.session.completed",
    "customer.subscription.created",
    "customer.subscription.updated",
    "invoice.paid",
    "invoice.payment_succeeded",
}
INACTIVE_EVENTS = {
    "customer.subscription.deleted",
    "customer.subscription.canceled",
    "invoice.payment_failed",
}


def _redis():
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
    def do_POST(self):
        key = os.environ.get("STRIPE_SECRET_KEY", "")
        secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
        if not (key and secret):
            return self._send(503, {"error": "server not configured (STRIPE_SECRET_KEY / STRIPE_WEBHOOK_SECRET)"})
        length = int(self.headers.get("Content-Length", 0) or 0)
        payload = self.rfile.read(length) if length > 0 else b""
        sig = self.headers.get("Stripe-Signature", "")
        try:
            import stripe
            stripe.api_key = key
            event = stripe.Webhook.construct_event(payload, sig, secret)
        except Exception as e:
            print(f"[webhook] signature verification failed: {e}", file=sys.stderr)  # server-side only
            return self._send(400, {"error": "signature verification failed"})

        etype = event["type"]
        obj = event["data"]["object"]
        r = _redis()
        try:
            # Idempotency: Stripe may deliver the same event more than once. Skip if already handled.
            evid = str(event.get("id") or "")
            if r is not None and evid and r.get("evt:" + evid):
                return self._send(200, {"received": True, "duplicate": True})
            # Prefer the KYR account email bound at checkout creation (subscribe.py:
            # client_reference_id / metadata.kyr_email, propagated onto the Subscription
            # via subscription_data.metadata) over the Stripe payer email, so paying
            # under a different email still unlocks Pro on the right account.
            email = self._bound_email(obj) or self._email_for(stripe, obj)
            if email and r:
                if etype in INACTIVE_EVENTS:
                    r.set("sub:" + email, "inactive", ex=60 * 60 * 24 * 40)
                elif etype in ACTIVE_EVENTS:
                    active = True
                    if etype.startswith("customer.subscription"):
                        active = obj.get("status") in ("active", "trialing")
                    r.set("sub:" + email, "active" if active else "inactive", ex=60 * 60 * 24 * 40)
            if r is not None and evid:
                r.set("evt:" + evid, "1", ex=60 * 60 * 24 * 3)  # remember 3 days (Stripe's retry window)
        except Exception:
            pass
        # Always 200 so Stripe doesn't retry on our bookkeeping hiccups; verify-subscription
        # re-checks Stripe directly (the source of truth) if a cache write was ever missed.
        return self._send(200, {"received": True})

    def _bound_email(self, obj):
        """KYR account email bound to the Stripe object at checkout creation, or None.
        Priority: client_reference_id (Checkout Session), then metadata.kyr_email
        (Checkout Session AND Subscription objects, the latter via
        subscription_data.metadata). Lowercased to match the sub:{email} convention.
        Returns None for unbound/legacy checkouts so _email_for keeps working."""
        v = str(obj.get("client_reference_id") or "").strip().lower()
        if v and "@" in v:
            return v
        meta = obj.get("metadata") or {}
        v = str(meta.get("kyr_email") or "").strip().lower()
        if v and "@" in v:
            return v
        return None

    def _email_for(self, stripe, obj):
        det = obj.get("customer_details") or {}
        if det.get("email"):
            return det["email"].strip().lower()
        if obj.get("email"):
            return obj["email"].strip().lower()
        cust = obj.get("customer")
        if cust:
            try:
                c = stripe.Customer.retrieve(cust)
                if c and c.get("email"):
                    return c["email"].strip().lower()
            except Exception:
                pass
        return None

    def _send(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
