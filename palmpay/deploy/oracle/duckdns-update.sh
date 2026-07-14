#!/usr/bin/env bash
# DuckDNS IP updater — run from cron every 5 minutes.
# Fill in your values from https://www.duckdns.org/
set -euo pipefail

DOMAIN="your-subdomain"   # without .duckdns.org
TOKEN="your-duckdns-token"

curl -fsS "https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}&ip=" \
  && echo " DuckDNS updated for ${DOMAIN}.duckdns.org"
