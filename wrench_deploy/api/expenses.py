"""
expenses.py — Per-vehicle ownership-cost view (V1).

Aggregates the cost already captured on each Service Log entry, plus an optional
set of non-service expenses (registration / insurance / fuel / other), into a
per-vehicle cost summary. No new core data entry — this is a read/compute layer
over Service Log + one small optional-expense store.

Routes (POST with `action` field in body):
- summary { vehicle_id }   -> Free:  { ok, isPro:false, total_spent, spent_this_year,
                                        services_count, has_data }
                              Pro:   + cost_per_mile, miles_driven, avg_per_month,
                                        categories:[{key,label,total}], additional_total,
                                        trend:[{ym,total}]
- list    { vehicle_id }   -> { ok, entries:[...optional expenses...], count, isPro }
- create  { vehicle_id, entry:{date, amount, expense_type, notes?} }
                           -> { ok, entry, count }   (Pro only)
                              or { ok:false, upgrade:true, message }   (free)
- delete  { vehicle_id, id } -> { ok, count }

Bearer auth required (Authorization: Bearer <session_token>); email is derived from
the session, never trusted from the body.

Redis schema:
- user_logs:{email}:{vehicle_id}      -> JSON array of Service Log entries (read-only here;
                                          fields used: cost, mileage, service_type, date)
- user_expenses:{email}:{vehicle_id}  -> JSON array of optional expenses (created here;
                                          purged by auth.py delete-account's
                                          `user_expenses:{email}:*` sweep -> GDPR-automatic)

Optional expense shape:
  { id, date, amount, expense_type, notes, created_at }

Free tier: basic totals only (Pro fields omitted from the JSON, so the paywall cannot be
bypassed client-side). Pro tier: full breakdown + optional-expense creation. Enforced
server-side. Self-contained on purpose — Vercel's Python builder does not bundle siblings.
"""

from http.server import BaseHTTPRequestHandler
import json
import os
import re
import time
import secrets

try:
    from upstash_redis import Redis
except Exception:
    Redis = None

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MAX_AMOUNT = 1_000_000
EXPENSE_TYPES = ("registration", "insurance", "fuel", "other")

# --- Category mapping (single adjustable dict; tweak here if users find a grouping odd) ---
# Service Log service_type -> category key. Unknown/free-text/"Other" falls through to "other".
CATEGORY_MAP = {
    "Engine Oil & Filter Change": "maintenance",
    "Air Filter Replacement": "maintenance",
    "Cabin Air Filter Replacement": "maintenance",
    "Spark Plug Replacement": "maintenance",
    "Transmission Service": "maintenance",
    "Coolant Flush": "maintenance",
    "Brake Fluid Flush": "maintenance",          # a fluid service -> Maintenance
    "Power Steering Service": "maintenance",
    "Fuel Filter Replacement": "maintenance",
    "Serpentine Belt Replacement": "maintenance",
    "Timing Belt / Chain Service": "maintenance",
    "Wiper Blade Replacement": "maintenance",
    "Battery Replacement": "maintenance",
    "Inspection / Multi-Point Check": "maintenance",
    "Brake Pad Replacement (Front)": "repairs",  # wear-part replacement -> Repairs
    "Brake Pad Replacement (Rear)": "repairs",
    "Suspension / Struts": "repairs",
    "Tire Rotation": "tires",
    "Tire Replacement": "tires",
    "Alignment": "tires",                        # tire-related -> Tires
}
CATEGORY_LABELS = {
    "maintenance": "Maintenance", "repairs": "Repairs", "tires": "Tires", "other": "Other",
    "fuel": "Fuel", "insurance": "Insurance", "registration": "Registration & Fees",
}
# Optional expense_type -> category key (its own bucket).
EXPENSE_CATEGORY = {"fuel": "fuel", "insurance": "insurance", "registration": "registration", "other": "other"}


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


def _whitelist():
    return {e.strip().lower() for e in os.environ.get("PRO_WHITELIST", "").split(",") if e.strip()}


def _bearer(headers):
    auth = headers.get("Authorization") or headers.get("authorization") or ""
    return auth[7:].strip() if auth.lower().startswith("bearer ") else ""


def _session_email(r, token):
    if not r or not token:
        return None
    try:
        return r.get("session:" + token) or None
    except Exception:
        return None


def _is_pro(r, email):
    """Same email-based Pro model as the paid-endpoint gate and service-log.py:
    PRO_WHITELIST, then sub:{email} cache, then user record tier, then live Stripe."""
    if email in _whitelist():
        return True
    try:
        v = r.get("sub:" + email)
        if v == "active":
            return True
        if v == "inactive":
            return False
    except Exception:
        pass
    try:
        raw = r.get("user:" + email)
        if raw and json.loads(raw).get("tier") == "pro":
            return True
    except Exception:
        pass
    key = os.environ.get("STRIPE_SECRET_KEY", "")
    if key:
        try:
            import stripe
            stripe.api_key = key
            for c in stripe.Customer.list(email=email, limit=20).data:
                for status in ("active", "trialing"):
                    if stripe.Subscription.list(customer=c.id, status=status, limit=1).data:
                        try:
                            r.set("sub:" + email, "active", ex=60 * 60 * 6)
                        except Exception:
                            pass
                        return True
            try:
                r.set("sub:" + email, "inactive", ex=60 * 30)
            except Exception:
                pass
        except Exception:
            pass
    return False


def _logs_key(email, vehicle_id):
    return "user_logs:%s:%s" % (email, vehicle_id)


def _exp_key(email, vehicle_id):
    return "user_expenses:%s:%s" % (email, vehicle_id)


def _load(r, key):
    try:
        raw = r.get(key)
        data = json.loads(raw) if raw else []
        return data if isinstance(data, list) else []
    except Exception:
        return []


def _save(r, key, entries):
    r.set(key, json.dumps(entries))


def _num(v):
    try:
        if v in (None, ""):
            return None
        return float(v)
    except Exception:
        return None


def _year(date_str):
    return str(date_str)[:4]


def _ym(date_str):
    return str(date_str)[:7]


def _months_since(date_str, now):
    """Whole months from an earliest YYYY-MM-DD to now (inclusive run-rate), floored at 1."""
    try:
        sy, sm = int(date_str[:4]), int(date_str[5:7])
    except Exception:
        return 1
    months = (now.tm_year - sy) * 12 + (now.tm_mon - sm) + 1
    return months if months >= 1 else 1


def _trend_buckets(now):
    """Last 12 (year, month) pairs, oldest -> newest, as 'YYYY-MM' keys."""
    keys = []
    y, m = now.tm_year, now.tm_mon
    for _ in range(12):
        keys.append("%04d-%02d" % (y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    keys.reverse()
    return keys


def _sorted_desc(entries):
    return sorted(entries, key=lambda e: (str(e.get("date") or ""), int(e.get("created_at") or 0)), reverse=True)


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0) or 0)
            body = json.loads(self.rfile.read(length) or b"{}") if length else {}
        except Exception:
            return self._send(400, {"ok": False, "error": "Invalid JSON."})

        r = _redis()
        if r is None:
            return self._send(503, {"ok": False, "error": "Expense backend not configured."})

        token = _bearer(self.headers) or str(body.get("token") or "")
        email = _session_email(r, token)
        if not email:
            return self._send(401, {"ok": False, "error": "Sign in required."})

        vid = body.get("vehicle_id")
        vid = str(vid).strip() if vid not in (None, "") else ""
        if not vid:
            return self._send(400, {"ok": False, "error": "vehicle_id is required."})

        action = str(body.get("action") or "").strip().lower()
        if action == "summary":
            return self._summary(r, email, vid)
        if action == "list":
            return self._list(r, email, vid)
        if action == "create":
            return self._create(r, email, vid, body.get("entry") or {})
        if action == "delete":
            return self._delete(r, email, vid, str(body.get("id") or "").strip())
        return self._send(400, {"ok": False, "error": "Unknown action."})

    # ---- summary: the aggregation. Pro fields omitted from JSON for free users. ----
    def _summary(self, r, email, vid):
        services = _load(r, _logs_key(email, vid))
        extras = _load(r, _exp_key(email, vid))
        pro = _is_pro(r, email)
        now = time.gmtime()
        cur_year = str(now.tm_year)

        total = 0.0
        this_year = 0.0
        for s in services:
            c = _num(s.get("cost"))
            if c is not None:
                total += c
                if _year(s.get("date")) == cur_year:
                    this_year += c
        for x in extras:
            a = _num(x.get("amount"))
            if a is not None:
                total += a
                if _year(x.get("date")) == cur_year:
                    this_year += a

        out = {
            "ok": True,
            "isPro": pro,
            "total_spent": round(total, 2),
            "spent_this_year": round(this_year, 2),
            "services_count": len(services),
            "has_data": bool(services) or bool(extras),
        }
        if not pro:
            return self._send(200, out)

        # --- Pro-only computations ---
        mileages = [m for m in (self._to_int(s.get("mileage")) for s in services) if m is not None]
        miles_driven = None
        if len(mileages) >= 2:
            span = max(mileages) - min(mileages)
            miles_driven = span if span > 0 else None
        out["miles_driven"] = miles_driven
        out["cost_per_mile"] = round(total / miles_driven, 2) if miles_driven else None

        all_dates = [str(s.get("date")) for s in services if s.get("date")] + \
                    [str(x.get("date")) for x in extras if x.get("date")]
        if all_dates:
            out["avg_per_month"] = round(total / _months_since(min(all_dates), now), 2)
        else:
            out["avg_per_month"] = None

        cats = {}
        for s in services:
            c = _num(s.get("cost"))
            if c is None:
                continue
            key = CATEGORY_MAP.get(str(s.get("service_type") or ""), "other")
            cats[key] = cats.get(key, 0.0) + c
        for x in extras:
            a = _num(x.get("amount"))
            if a is None:
                continue
            key = EXPENSE_CATEGORY.get(str(x.get("expense_type") or "other"), "other")
            cats[key] = cats.get(key, 0.0) + a
        out["categories"] = [
            {"key": k, "label": CATEGORY_LABELS.get(k, k.title()), "total": round(v, 2)}
            for k, v in sorted(cats.items(), key=lambda kv: kv[1], reverse=True) if v > 0
        ]

        out["additional_total"] = round(sum((_num(x.get("amount")) or 0.0) for x in extras), 2)

        buckets = {k: 0.0 for k in _trend_buckets(now)}
        for s in services:
            c = _num(s.get("cost"))
            if c is None:
                continue
            ym = _ym(s.get("date"))
            if ym in buckets:
                buckets[ym] += c
        for x in extras:
            a = _num(x.get("amount"))
            if a is None:
                continue
            ym = _ym(x.get("date"))
            if ym in buckets:
                buckets[ym] += a
        out["trend"] = [{"ym": k, "total": round(buckets[k], 2)} for k in _trend_buckets(now)]

        return self._send(200, out)

    def _to_int(self, v):
        try:
            return int(v)
        except Exception:
            return None

    def _list(self, r, email, vid):
        entries = _sorted_desc(_load(r, _exp_key(email, vid)))
        return self._send(200, {"ok": True, "entries": entries, "count": len(entries), "isPro": _is_pro(r, email)})

    def _create(self, r, email, vid, entry):
        if not _is_pro(r, email):
            return self._send(200, {
                "ok": False, "upgrade": True,
                "message": "Upgrade to Pro to track insurance, registration & fuel costs — $2.99/month"})

        date = str(entry.get("date") or "").strip()
        if not DATE_RE.match(date):
            return self._send(400, {"ok": False, "error": "A valid date (YYYY-MM-DD) is required."})
        amount = _num(entry.get("amount"))
        if amount is None:
            return self._send(400, {"ok": False, "error": "Amount is required and must be a number."})
        if amount <= 0 or amount > MAX_AMOUNT:
            return self._send(400, {"ok": False, "error": "Amount is out of plausible range."})
        etype = str(entry.get("expense_type") or "").strip().lower()
        if etype not in EXPENSE_TYPES:
            etype = "other"

        entries = _load(r, _exp_key(email, vid))
        rec = {
            "id": secrets.token_hex(4),
            "date": date,
            "amount": round(amount, 2),
            "expense_type": etype,
            "notes": (str(entry.get("notes") or "").strip()[:2000]),
            "created_at": int(time.time()),
        }
        entries.append(rec)
        try:
            _save(r, _exp_key(email, vid), entries)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not save the expense."})
        return self._send(200, {"ok": True, "entry": rec, "count": len(entries)})

    def _delete(self, r, email, vid, entry_id):
        if not entry_id:
            return self._send(400, {"ok": False, "error": "Entry id is required."})
        entries = _load(r, _exp_key(email, vid))
        kept = [e for e in entries if str(e.get("id")) != entry_id]
        if len(kept) == len(entries):
            return self._send(404, {"ok": False, "error": "Expense not found."})
        try:
            _save(r, _exp_key(email, vid), kept)
        except Exception:
            return self._send(503, {"ok": False, "error": "Could not delete the expense."})
        return self._send(200, {"ok": True, "count": len(kept)})

    def _send(self, code, obj):
        payload = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "https://knowyourride.net")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return
