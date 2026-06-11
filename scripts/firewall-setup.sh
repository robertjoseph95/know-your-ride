#!/usr/bin/env bash
# Know Your Ride - Vercel Firewall setup (rate limits for abuse-prone endpoints)
#
# Prereqs:
#   npm i -g vercel
#   vercel link            # project: project-sj4at (already linked via .vercel/)
#
# IMPORTANT: these commands only STAGE rules, and they stage them in LOG mode
# (they block NOTHING yet). Review real traffic in the dashboard first, THEN
# enforce. Nothing here is irreversible without your explicit `publish`.
#
# DDoS protection is already on and free for the project - no action needed.
set -euo pipefail

echo "Staging Know Your Ride firewall rules (LOG mode - blocks nothing yet)..."

# (1) AI cost endpoints - highest priority. Each call costs real money
#     (Claude / YouTube APIs); a bot hammering these runs up the bill.
vercel firewall rules add "Rate limit AI endpoints" \
  --condition '{"type":"path","op":"pre","value":"/api/identify-part"}' \
  --or --condition '{"type":"path","op":"pre","value":"/api/guide"}' \
  --or --condition '{"type":"path","op":"pre","value":"/api/youtube"}' \
  --action rate_limit --rate-limit-window 300 --rate-limit-requests 30 \
  --rate-limit-keys ip --rate-limit-action log --yes

# (2) Promo-code enumeration / brute-force.
vercel firewall rules add "Rate limit promo" \
  --condition '{"type":"path","op":"pre","value":"/api/promo"}' \
  --action rate_limit --rate-limit-window 600 --rate-limit-requests 15 \
  --rate-limit-keys ip --rate-limit-action log --yes

# (3) Checkout - generous limit so real buyers are never blocked.
vercel firewall rules add "Rate limit checkout" \
  --condition '{"type":"path","op":"pre","value":"/api/subscribe"}' \
  --or --condition '{"type":"path","op":"pre","value":"/api/verify-subscription"}' \
  --action rate_limit --rate-limit-window 300 --rate-limit-requests 30 \
  --rate-limit-keys ip --rate-limit-action log --yes

cat <<'NEXT'

Staged 3 rules in LOG mode. Next steps (you run these):

  vercel firewall diff            # review what will change
  vercel firewall publish --yes   # publish - still LOG only, blocks nothing

Watch the Firewall dashboard for a few days. If only abusers are hitting the
limits (not real users / SEO crawlers), enforce each rule:

  vercel firewall rules edit "Rate limit AI endpoints"  --rate-limit-action rate_limit --yes
  vercel firewall rules edit "Rate limit promo"         --rate-limit-action rate_limit --yes
  vercel firewall rules edit "Rate limit checkout"      --rate-limit-action rate_limit --yes
  vercel firewall publish --yes

DO NOT add a rule for /api/webhook - Stripe calls it and webhook.py already
verifies the Stripe signature; a rate limit could drop legitimate retries.

For general bot defense, enable the managed "Bot Protection" ruleset in the
dashboard (Firewall tab) - it uses verified-bot signals instead of brittle
user-agent string blocks.
NEXT
