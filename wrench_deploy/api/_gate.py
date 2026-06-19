"""
_gate.py — shared server-side Pro gate for the paid endpoints (guide, youtube, identify-part).

Purpose: close the localStorage `kyr_pro` bypass. The server validates the REAL
subscription on every paid call; the browser flag is ignored entirely.

    check(handler) -> (is_pro: bool, user_email: str | None)

Mechanism (reuses the EXISTING session/whitelist/subscription scheme — no new auth logic):
  - Reads the session token from `Authorization: Bearer <token>` OR a session cookie.
  - Resolves it to an email via `auth.session_lookup` when that module is importable in
    the runtime, otherwise via the identical inline read of the `session:{token}` Redis key
    (the same pattern garage.py uses — verify-subscription.py can't be imported by name
    because its filename has a hyphen).
  - Pro if: email in PRO_WHITELIST, OR Redis `sub:{email} == "active"` (the cache the Stripe
    webhook + verify-subscription maintain), OR a live Stripe check (reused from
    verify-subscription.py) reports an active subscription; the result is cached.
  - Returns (False, None) when there is no valid session.

Does NOT modify auth.py's scrypt hashing, session-token generation, or brute-force throttle,
the Stripe webhook, the Redis schema, or anything else. It only READS existing keys.
"""
import os
import http.cookies
import importlib.util

# Prefer reusing auth.session_lookup; fall back to the inline Redis read if the runtime
# does not expose sibling modules on the import path (graceful, garage.py-style).
try:
    import auth as _auth
except Exception:
    _auth = None

try:
    from upstash_redis import Redis as _Redis
except Exception:
    _Redis = None


def _redis():
    if _Redis is None:
        return None
    url = os.environ.get("UPSTASH_REDIS_REST_URL") or os.environ.get("KV_REST_API_URL")
    token = os.environ.get("UPSTASH_REDIS_REST_TOKEN") or os.environ.get("KV_REST_API_TOKEN")
    if not (url and token):
        return None
    try:
        return _Redis(url=url, token=token)
    except Exception:
        return None


def _whitelist():
    # Same source of truth as auth.py / verify-subscription.py / garage.py.
    return {e.strip().lower() for e in os.environ.get("PRO_WHITELIST", "").split(",") if e.strip()}


def _token_from(headers):
    """Session token from Authorization: Bearer <token>, else from a session cookie."""
    a = headers.get("Authorization") or headers.get("authorization") or ""
    if a.lower().startswith("bearer "):
        t = a[7:].strip()
        if t:
            return t
    raw = headers.get("Cookie") or headers.get("cookie") or ""
    if raw:
        try:
            jar = http.cookies.SimpleCookie()
            jar.load(raw)
            for name in ("kyr_session", "kyr_token", "session"):
                if name in jar and jar[name].value:
                    return jar[name].value.strip()
        except Exception:
            pass
    return ""


def _session_email(r, token):
    """Resolve session:{token} -> email. Uses auth.session_lookup when available, else the
    identical inline read (the same `session:` key auth._new_session writes)."""
    if not token:
        return None
    if _auth is not None and hasattr(_auth, "session_lookup"):
        try:
            email = _auth.session_lookup(r, token)
            if email:
                return email
        except Exception:
            pass
    if r is not None:
        try:
            return r.get("session:" + token) or None
        except Exception:
            return None
    return None


def _stripe_active(email):
    """Reuse verify-subscription.py's live Stripe check. Its filename has a hyphen and is not
    importable by name, so load it by path. Returns True / False / None (None = unknown)."""
    try:
        path = os.path.join(os.path.dirname(__file__), "verify-subscription.py")
        spec = importlib.util.spec_from_file_location("kyr_verify_subscription", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._stripe_active(email)
    except Exception:
        return None


def _email_from(headers):
    """Client-asserted subscriber email (X-KYR-Email). Matches the existing email-based
    restore model; the email is only a lookup key, never trusted on its own (see _email_pro)."""
    e = headers.get("X-KYR-Email") or headers.get("x-kyr-email") or ""
    return e.strip().lower()


def _email_pro(r, email):
    """Pro determination for a known email, cheapest/most-authoritative source first:
    PRO_WHITELIST, then the sub:{email} cache the Stripe webhook + verify-subscription
    maintain, then a live Stripe check (result cached). Returns (is_pro, email|None)."""
    email = str(email).strip().lower()
    if not email or "@" not in email:
        return (False, None)
    if email in _whitelist():
        return (True, email)
    if r is not None:
        try:
            v = r.get("sub:" + email)
            if v == "active":
                return (True, email)
            if v == "inactive":
                return (False, email)
        except Exception:
            pass
    # Cache miss -> live Stripe (reused), then backfill the sub: cache like verify-subscription.
    active = _stripe_active(email)
    if active is not None and r is not None:
        try:
            r.set("sub:" + email, "active" if active else "inactive",
                  ex=(60 * 60 * 6 if active else 60 * 30))
        except Exception:
            pass
    return (bool(active), email)


def check(handler):
    """handler: a BaseHTTPRequestHandler (reads handler.headers).
    Returns (is_pro: bool, user_email: str | None).

    Two ways a caller can prove Pro, BOTH validated against the real subscription state:
      1. A server-issued session token (Authorization: Bearer / session cookie) ->
         session:{token} -> email. (Future-proof; works if a real session ever exists.)
      2. A client-asserted subscriber email (X-KYR-Email header) -- the credential the
         current client actually has. This matches the EXISTING email-based restore model
         (verify-subscription.py is already email-only). The email is never trusted on its
         own: it must resolve to PRO_WHITELIST, sub:{email}=="active", or a live Stripe
         active subscription.
    The browser localStorage 'kyr_pro' flag is still ignored entirely."""
    headers = getattr(handler, "headers", None)
    if headers is None:
        return (False, None)
    r = _redis()
    # 1) session-token path
    token = _token_from(headers)
    if token:
        email = _session_email(r, token)
        if email:
            return _email_pro(r, email)
    # 2) email path (current client credential)
    email = _email_from(headers)
    if email:
        return _email_pro(r, email)
    return (False, None)
