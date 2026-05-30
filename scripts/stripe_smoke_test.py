#!/usr/bin/env python3
"""Check UsefulOps Stripe restricted-key access without printing secrets."""

from __future__ import annotations

import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SECRET_ENV = ROOT / "local" / "secrets" / "stripe.env"


ENDPOINTS = {
    "payment_links": "/v1/payment_links?limit=3",
    "checkout_sessions": "/v1/checkout/sessions?limit=1",
    "customers": "/v1/customers?limit=1",
    "subscriptions": "/v1/subscriptions?limit=1",
}


def load_key() -> str:
    key = os.environ.get("STRIPE_API_KEY", "").strip()
    if key:
        return key

    if DEFAULT_SECRET_ENV.exists():
        for line in DEFAULT_SECRET_ENV.read_text().splitlines():
            if line.startswith("STRIPE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")

    raise SystemExit(
        "Missing STRIPE_API_KEY. Set it in the environment or local/secrets/stripe.env."
    )


def stripe_get(key: str, path: str) -> tuple[int, dict]:
    token = base64.b64encode(f"{key}:".encode()).decode()
    request = urllib.request.Request(
        f"https://api.stripe.com{path}",
        headers={"Authorization": f"Basic {token}"},
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = response.read().decode()
            return response.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body) if body else {}
        except json.JSONDecodeError:
            parsed = {}
        return exc.code, parsed


def summarize(name: str, status: int, body: dict) -> dict:
    result = {
        "endpoint": name,
        "http": status,
        "ok": 200 <= status < 300,
    }
    if isinstance(body.get("data"), list):
        result["object_count"] = len(body["data"])
    if body.get("object"):
        result["object"] = body["object"]
    if isinstance(body.get("error"), dict):
        error = body["error"]
        result["error_type"] = error.get("type")
        result["error_code"] = error.get("code")
    return result


def main() -> int:
    key = load_key()
    results = []
    for name, path in ENDPOINTS.items():
        status, body = stripe_get(key, path)
        results.append(summarize(name, status, body))

    print(json.dumps(results, indent=2))
    required = {"payment_links", "checkout_sessions", "customers"}
    ok_names = {item["endpoint"] for item in results if item["ok"]}
    return 0 if required.issubset(ok_names) else 1


if __name__ == "__main__":
    sys.exit(main())
