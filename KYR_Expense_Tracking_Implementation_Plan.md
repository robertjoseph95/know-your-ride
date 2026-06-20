# KYR Expense Tracking — Implementation Plan (V1)
### Know Your Ride Technologies LLC
**Version:** 1.0 | **Date:** 19 June 2026 | **Author:** Robert Joseph + Claude Code
**Builds on:** Service Log V1 (commit `4fea937b`, `api/service-log.py`, `user_logs:{email}:{vehicle_id}`)
**Depends on:** Authentication Phase 3A (commit `49541993`, `kyr_session` Bearer → `session:{token}` → email)

> **Concept:** No new core data entry. Expense Tracking *aggregates* the cost already captured per Service Log entry into a per-vehicle ownership-cost view, plus a small set of optional non-service expenses (registration, insurance, fuel). It is a read/compute layer over Service Log + one new optional-expense store.

---

## Recommendations on the open architecture questions (please confirm)

| # | Decision | Recommendation | Why |
|---|---|---|---|
| **D1** | Redis: reuse `user_logs` or new key? | **New key `user_expenses:{email}:{vehicle_id}`** for the *optional* non-service expenses. Service Log stays untouched. | Service entries carry maintenance semantics (mileage, intervals, next-due recompute, the 3-entry free cap). Mixing insurance/registration/fuel into `user_logs` would pollute the service-history list **and** consume service-log free slots. The summary simply reads *both* keys. |
| **D2** | API: extend `service-log.py` or new file? | **New self-contained `api/expenses.py`** (copy `garage.py`/`service-log.py` pattern, no sibling imports — the Phase-2 bundling lesson). | Owns the aggregation + optional-expense CRUD without bloating `service-log.py`. `service-log.py` keeps one job. |
| **D3** | UI placement | **New modal tab `Costs`** (11th tab), immediately after `Service Log`. | Matches the existing `MTABS`/`MLABELS`/fns-map tab architecture; cleaner than cramming a second feature into the log tab. "Near the service log" satisfied by tab adjacency. |
| **D4** | Category mapping | Fixed server-side map (table in §2), `Other` fallback for free-text/unknown. | Deterministic, server-authoritative, adjustable in one dict. |
| **D5** | Cost-per-mile with <2 mileage points | Show **"Not enough data — log 2+ services to compute"** (don't fake it). | Needs a real mileage *range*; one entry = no range. Honest empty state. |
| **D6** | Avg cost / month basis | **First service/expense date → today**, months = `max(1, elapsed)`. | Reflects current run-rate of ownership cost, not a frozen historical window. |
| **D7** | Free user + existing optional expenses | **View yes, create no** (mirrors Service Log Decision 1: never hide data a user created). | Consistent paywall behavior; downgrade never destroys visibility. |
| **D8** | Fuel entry detail | **Minimal**: amount + date + optional note. Gallons/MPG **deferred** to V1.1. | YAGNI; "simple manual entry" per spec. |

---

## 1. Redis schema

**Service costs (existing, read-only here):** `user_logs:{email}:{vehicle_id}` → JSON array of service entries; each has `cost` (float|null), `mileage` (int), `service_type` (string), `date` (`YYYY-MM-DD`).

**Optional expenses (new):** `user_expenses:{email}:{vehicle_id}` → JSON array.

```json
{ "id": "<8-char hex>", "date": "YYYY-MM-DD", "amount": 142.50,
  "expense_type": "insurance", "notes": "6-month premium", "created_at": 1781870000 }
```
- `expense_type` ∈ `registration` | `insurance` | `fuel` | `other` (validated server-side; unknown → `other`).
- `amount` required, `> 0`, ≤ `MAX_AMOUNT` (e.g. 1,000,000). `date` required, `YYYY-MM-DD`.
- **GDPR:** add `user_expenses:{email}:*` to `auth.py` `delete-account`'s purge sweep (one-line addition, mirrors `user_logs:{email}:*`). *Flagged as a build step so erasure stays automatic.*

---

## 2. Expense categories (server-side map)

Service `service_type` → category. Optional expenses map by their `expense_type`.

| Category | Source service types (from client `TYPES`) |
|---|---|
| **Maintenance** | Engine Oil & Filter Change · Air Filter Replacement · Cabin Air Filter Replacement · Spark Plug Replacement · Transmission Service · Coolant Flush · Brake Fluid Flush · Power Steering Service · Fuel Filter Replacement · Serpentine Belt Replacement · Timing Belt / Chain Service · Wiper Blade Replacement · Battery Replacement · Inspection / Multi-Point Check |
| **Repairs** | Brake Pad Replacement (Front) · Brake Pad Replacement (Rear) · Suspension / Struts |
| **Tires** | Tire Rotation · Tire Replacement · Alignment |
| **Other** | `Other` / any free-text/unmatched `service_type` |
| **Fuel** | optional expense `expense_type=fuel` |
| **Insurance** | optional expense `expense_type=insurance` |
| **Registration / Fees** | optional expense `expense_type=registration` |

The 4 service categories satisfy the spec's required breakdown; the 3 optional-expense categories appear only once a user logs them (Pro). Entries with `cost=null` contribute to **count** but not to any spend total.

---

## 3. API — `api/expenses.py` (self-contained)

`POST /api/expenses`, action-dispatched, `Authorization: Bearer <kyr_session>` → `session:{token}` → email (else `401`). Inline Redis client + `_is_pro(r,email)` identical to `service-log.py` (whitelist OR `sub:{email}=="active"` OR `user.tier=="pro"` OR live Stripe).

| Action | Body | Returns |
|---|---|---|
| `summary` | `{vehicle_id}` | Free: `{ok, isPro:false, total_spent, spent_this_year, services_count, has_data}`. Pro: **+** `cost_per_mile, miles_driven, avg_per_month, categories:[{key,label,total}], additional_total, trend:[{ym,total}]` |
| `list` | `{vehicle_id}` | `{ok, entries:[...optional expenses...], count, isPro}` (view always allowed — D7) |
| `create` | `{vehicle_id, entry:{date,amount,expense_type,notes?}}` | `{ok, entry, count}` · or `{ok:false, upgrade:true, message:"Upgrade to Pro to track insurance, registration & fuel — $2.99/month"}` if **not** Pro |
| `delete` | `{vehicle_id, id}` | `{ok, count}` |

**Server-enforced Pro split (§4):** `summary` computes everything but **omits** the Pro fields from the JSON when `isPro` is false — the client never receives them, so the paywall can't be bypassed by editing the DOM. `create` is Pro-only.

**Computation (in `summary`):**
- `total_spent` = Σ service `cost` + Σ optional `amount`.
- `spent_this_year` = same, filtered to entries whose `date` year == current year (`time.gmtime()`).
- `services_count` = `len(user_logs)` (all service entries, regardless of cost).
- `miles_driven` = `max(mileage) − min(mileage)` over service entries **with a numeric mileage** (need ≥2 → else `null`, drives the D5 "not enough data" state).
- `cost_per_mile` = `total_spent / miles_driven` when `miles_driven > 0`, rounded to cents; else `null`.
- `avg_per_month` = `total_spent / months`, `months = max(1, whole months from earliest entry date → today)`.
- `categories` = grouped sums via the §2 map, only categories with `total > 0`, sorted desc.
- `trend` = last-12-month buckets `{ym:"YYYY-MM", total}` (zero-filled), for the bar/spark view.

---

## 4. Free vs Pro (server-enforced)

| Capability | Free | Pro |
|---|---|---|
| Total spent (all time) | ✅ | ✅ |
| Spent this year | ✅ | ✅ |
| Services logged (count) | ✅ | ✅ |
| Cost per mile | — | ✅ |
| Avg cost / month | — | ✅ |
| Category breakdown (bar chart) | — | ✅ |
| Optional expenses — **view** existing | ✅ (D7) | ✅ |
| Optional expenses — **add** (registration/insurance/fuel) | 🔒 upgrade prompt | ✅ |
| Trend over time | — | ✅ |

Source of truth is the server: Pro fields are absent from the `summary` payload for free users; `create` returns the upgrade object instead of saving. Client mirrors purely for UX.

---

## 5. Client UI (`wrench_demo.html`, new `Costs` modal tab)

- **Tab wiring:** add `'costs'` to `MTABS`, `'Costs'` to `MLABELS` (after `'Service Log'`), `costs:renderExpenses` to the fns map, and a lazy loader `kyrExpLoad()` fired on tab open (mirrors `kyrSlLoad()`), reading `Authorization: Bearer <kyr_session>`.
- **Summary cards** (always rendered; Pro cards show a small 🔒 "Pro" pill + upgrade link when locked): Total Spent · This Year · Services Logged | (Pro) Cost/Mile · Avg/Month.
- **Category breakdown (Pro):** pure-CSS horizontal bars — each row `label · $total`, bar width = `total / maxCategoryTotal * 100%`, colored per category, **no external libs**. Honors dark theme (`--bg`/`--dim`/accent vars already in the file).
- **Optional expenses (Pro to add, all to view):** small form (Date default today, Amount, Type `select` registration/insurance/fuel/other, Notes) + a list with delete. Free users see the form replaced by an upgrade CTA.
- **Empty state:** no service costs **and** no optional expenses → *"No expenses yet — log a service with a cost, or add an expense, to see your ownership cost summary."*
- **Cost/mile "not enough data"** (D5) when `miles_driven` is null: *"Log 2+ services with mileage to see cost per mile."*
- **Numbers:** reuse `nf()` for thousands; currency formatted to 2 decimals.
- **Auth-gated:** logged-out tap → Phase 3A login modal; `401` → re-prompt.

---

## 6. Cost-per-mile calculation (detail)

```
miles_driven = max(m) - min(m)   over service entries where mileage is a number, if ≥2 such entries
             = null              otherwise        → UI shows "not enough data" (D5)
cost_per_mile = round(total_spent / miles_driven, 2)   when miles_driven > 0
              = null                                    otherwise (guards divide-by-zero)
```
Optional expenses have no mileage and don't affect `miles_driven`, but their `amount` **is** in `total_spent`, so cost/mile reflects *total* ownership cost over the miles the service history covers. Documented in the UI tooltip so the number isn't mistaken for maintenance-only.

---

## 7. Build order (V1)

1. **`api/expenses.py`** — self-contained `summary`/`list`/`create`/`delete`, `_is_pro`, reads `user_logs` + `user_expenses`, server-side Pro field omission + Pro-only create. `py_compile` + local mocked unit test (summary math: total, this-year, cost/mile range, category grouping, free-vs-Pro payload shape).
2. **`auth.py` purge** — add `user_expenses:{email}:*` to `delete-account` sweep; quick local check it's included.
3. **Client `Costs` tab** — tab wiring + `renderExpenses` + `kyrExpLoad()`; summary cards; empty state.
4. **Pro UI** — CSS category bar chart; optional-expense form/list; upgrade CTAs; cost/mile + not-enough-data states.
5. **Verify end-to-end on a live preview deploy** — signup → session → seed 3 service entries w/ costs+mileage → `summary` as **free** (only basic fields present) → flip to Pro (whitelist) → `summary` shows cost/mile, categories, trend → `create` optional expense (free=upgrade, Pro=saves) → category breakdown updates → `delete` → account-delete purges both keys. Then build pipeline (`04_rebuild_demo.py` + `_deploy_sync_specs.py`) + **production deploy**.

**Out of scope for V1:** editing optional expenses, fuel MPG/gallons & odometer, CSV/PDF export, multi-vehicle rollup ("total across all vehicles"), budget targets/alerts, recurring-expense reminders, currency localization. (V1.1+ candidates.)

---
*Know Your Ride Technologies LLC | hello@knowyourride.net | knowyourride.net*
