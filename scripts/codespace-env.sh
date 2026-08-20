#!/usr/bin/env bash
#
# The forwarded URLs of a GitHub Codespace — derived, never hard-coded.
#
# In a Codespace nothing is reached over loopback. The browser is on another
# machine (a phone, usually) and each forwarded port gets its own https origin:
#
#     https://<CODESPACE_NAME>-<port>.app.github.dev
#
# Three things break at once unless they are told, and all three were found the
# hard way (B079, docs/RUNBOOK-LOCAL.md): the React app calls the api FROM THE
# BROWSER, the api refuses an origin that is not on its allow list, and the
# design window embeds a preview by URL.
#
# Sourced by scripts/dev-up.sh when $CODESPACE_NAME is set, and by every login
# shell in the Codespace (post-start puts it in .bashrc). Every value goes
# through ${VAR:-...}, so anything already in the environment wins — including
# a port made public by hand.
#
# shellcheck shell=bash

_cs_domain="${GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN:-app.github.dev}"
_cs_app_port="${SCIO_APP_PORT:-5173}"
_cs_api_port="${SCIO_API_PORT:-3000}"
_cs_url() { printf 'https://%s-%s.%s' "${CODESPACE_NAME}" "$1" "$_cs_domain"; }

export APP_PUBLIC_URL="${APP_PUBLIC_URL:-$(_cs_url "$_cs_app_port")}"
export API_PUBLIC_URL="${API_PUBLIC_URL:-$(_cs_url "$_cs_api_port")}"

# The app is a static bundle in the browser: this is the address IT dials.
export VITE_API_URL="${VITE_API_URL:-$API_PUBLIC_URL}"
# The api's CORS allow list, and the origin the marking bridge posts to.
export CORS_ORIGINS="${CORS_ORIGINS:-$APP_PUBLIC_URL}"
export APP_ORIGIN="${APP_ORIGIN:-$APP_PUBLIC_URL}"

# A port is only forwarded if something listens on every interface.
export SCIO_APP_HOST="${SCIO_APP_HOST:-0.0.0.0}"
export SCIO_PREVIEW_HOST="${SCIO_PREVIEW_HOST:-0.0.0.0}"

# Previews get a port picked at random, so the engine is given the SHAPE of a
# forwarded URL rather than one URL (apps/engine/.../core/public_url.py).
# Built in two steps on purpose: the {port} placeholder inside a ${VAR:-default}
# closes the expansion at the wrong brace, which is exactly the silent kind of
# wrong — https://name-{port.app.github.dev} — that still looks like a URL.
_cs_template="https://${CODESPACE_NAME}-{port}.${_cs_domain}"
export SCIO_PUBLIC_URL_TEMPLATE="${SCIO_PUBLIC_URL_TEMPLATE:-$_cs_template}"

unset _cs_domain _cs_app_port _cs_api_port _cs_template
unset -f _cs_url
