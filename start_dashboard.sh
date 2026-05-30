#!/bin/sh
set -eu

cd "$(dirname "$0")"
exec python3 scripts/dashboard_server.py
