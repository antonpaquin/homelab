#! /bin/sh

set -e

PUBLIC_IP="$(curl ifconfig.co)"

CONFIG="$(cat "$CONFIG_FILE")"
NAMECHEAP_API_URL="$(echo "$CONFIG" | jq -r '.namecheap.api_url')"
TLS_EMAIL="$(echo "$CONFIG" | jq -r '.tls.email')"
TLS_TEST="$(echo "$CONFIG" | jq -r '.tls.test')"
CERT_DOMAIN="$(echo "$CONFIG" | jq -r '.tls.domain')"

if [[ "$TLS_TEST" == "false" ]]; then
  TEST_OPT=""
else
  TEST_OPT="--test-cert"
fi

certbot certonly $TEST_OPT \
  --certbot-namecheap:auth-namecheap-api-url="$NAMECHEAP_API_URL" \
  --certbot-namecheap:auth-api-key="$NAMECHEAP_API_KEY" \
  --certbot-namecheap:auth-api-user="$NAMECHEAP_API_USER" \
  --certbot-namecheap:auth-public-ip="$PUBLIC_IP" \
  -a certbot-namecheap:auth \
  --email="$TLS_EMAIL" \
  --no-eff-email \
  --agree-tos \
  -d "$CERT_DOMAIN"

python /opt/upload_certs.py
