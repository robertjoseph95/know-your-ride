#!/usr/bin/env bash
SITE="https://knowyourride.net"
code(){ curl -sS -o /dev/null -w '%{http_code}' "$1"; }
ct(){ curl -sS -o /dev/null -w '%{http_code} %{content_type}' "$1"; }

# Wait for the onboarding deploy to be live
for i in $(seq 1 30); do
  ob=$(curl -sS "$SITE/" | grep -c 'Search for your car above')
  if [ "$ob" -ge 1 ]; then echo "DEPLOY LIVE (onboarding present) after ~$((i*10))s"; break; fi
  sleep 10
done

echo "=========== KNOW YOUR RIDE HEALTH CHECK ==========="
B=$(curl -sS "$SITE/")
echo "[PAGE] / -> $(code "$SITE/") | size $(echo "$B" | wc -c)b"
echo "  onboarding CTA: $(echo "$B" | grep -c 'Search for your car above') | placeholder: $(echo "$B" | grep -c 'Type your car') | meta-3360: $(echo "$B" | grep -c 'specs for 3,360 vehicles') | navP0420: $(echo "$B" | grep -c 'x=\"316\" y=\"80\"')"
echo "[STATIC ASSETS]"
for f in favicon.ico icon-192.png icon-512.png manifest.json sw.js logo.svg robots.txt sitemap.xml; do
  echo "  /$f -> $(ct "$SITE/$f")"
done
echo "[API - functional]"
echo "  subscribe?plan=monthly -> $(code "$SITE/api/subscribe?plan=monthly")  (expect 303 -> Stripe)"
echo "  subscribe?plan=annual  -> $(code "$SITE/api/subscribe?plan=annual")  (expect 303 -> Stripe)"
echo "  verify owner   -> $(curl -sS "$SITE/api/verify-subscription?email=robert.joseph95@yahoo.com")"
echo "  verify control -> $(curl -sS "$SITE/api/verify-subscription?email=nobody@example.com")"
echo "  promo BETA2026 -> $(curl -sS -X POST -H 'Content-Type: application/json' -d '{"code":"BETA2026","token":"healthcheck"}' "$SITE/api/promo")"
echo "  promo invalid  -> $(curl -sS -X POST -H 'Content-Type: application/json' -d '{"code":"NOPE"}' "$SITE/api/promo")"
echo "  recalls h/a/2020 -> $(curl -sS "$SITE/api/recalls?make=honda&model=accord&year=2020" | head -c 90)"
echo "[API - availability only (no paid op triggered)]"
echo "  vin/SHORT       -> $(code "$SITE/api/vin/SHORT")  (expect 400)"
echo "  guide bogus vid -> $(code "$SITE/api/guide/99999999/oil-change")  (expect 404)"
echo "  youtube no-svc  -> $(code "$SITE/api/youtube?year=2020&make=honda&model=accord")  (expect 400)"
echo "  identify-part GET -> $(code "$SITE/api/identify-part")  (expect 405/501)"
echo "=========== END ==========="
