#!/usr/bin/env python3
"""Live connect почты из корневого .env → POST /api/email/accounts/connect."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND.parent
DEFAULT_API = "http://127.0.0.1:8000"


def _load_env() -> None:
	try:
		from dotenv import load_dotenv

		load_dotenv(BACKEND / ".env")
		load_dotenv(REPO_ROOT / ".env", override=True)
		front_env = REPO_ROOT / "frontend" / ".env"
		if front_env.is_file():
			load_dotenv(front_env, override=False)
	except ImportError:
		pass


def _api_key() -> str:
	return (os.getenv("SMARTCRM_API_KEY") or os.getenv("PUBLIC_SMARTCRM_API_KEY") or "").strip()


def _accounts_from_env() -> list[dict]:
	pwd = (os.getenv("EMAIL_APP_PASSWORD") or os.getenv("EMAIL_PASSWORD") or "").strip()
	if not pwd:
		return []
	imap = os.getenv("EMAIL_IMAP_HOST", "imap.yandex.com").strip()
	smtp = os.getenv("EMAIL_SMTP_HOST", "smtp.yandex.com").strip()
	use_ssl = os.getenv("EMAIL_USE_SSL", "1").strip().lower() not in ("0", "false", "no")
	out = []
	only = (os.getenv("EMAIL_CONNECT_ONLY") or "").strip()
	indices = [int(only)] if only.isdigit() else [1, 2]
	for i in indices:
		user = (os.getenv(f"EMAIL_ACCOUNT_{i}_USER") or "").strip()
		if not user:
			continue
		out.append(
			{
				"name": (os.getenv(f"EMAIL_ACCOUNT_{i}_NAME") or user).strip(),
				"provider": "yandex",
				"username": user,
				"password": pwd,
				"imap_server": (os.getenv(f"EMAIL_ACCOUNT_{i}_IMAP_HOST") or imap).strip(),
				"imap_port": int(os.getenv(f"EMAIL_ACCOUNT_{i}_IMAP_PORT") or os.getenv("EMAIL_IMAP_PORT", "993")),
				"smtp_server": (os.getenv(f"EMAIL_ACCOUNT_{i}_SMTP_HOST") or smtp).strip(),
				"smtp_port": int(os.getenv(f"EMAIL_ACCOUNT_{i}_SMTP_PORT") or os.getenv("EMAIL_SMTP_PORT", "465")),
				"use_ssl": use_ssl,
			}
		)
	return out


def _post_connect(api_base: str, key: str, body: dict) -> dict:
	data = json.dumps(body).encode()
	headers = {"Content-Type": "application/json"}
	if key:
		headers["X-API-Key"] = key
	req = urllib.request.Request(
		f"{api_base.rstrip('/')}/api/email/accounts/connect",
		data=data,
		method="POST",
		headers=headers,
	)
	timeout = int(os.environ.get("EMAIL_CONNECT_TIMEOUT_SEC", "300"))
	with urllib.request.urlopen(req, timeout=timeout) as resp:
		return json.loads(resp.read().decode())


def main() -> int:
	_load_env()
	api = os.environ.get("EMAIL_SMOKE_API_URL", DEFAULT_API).rstrip("/")
	key = _api_key()
	accounts = _accounts_from_env()
	if not accounts:
		print("smoke_email_connect: skip (заполните EMAIL_APP_PASSWORD и EMAIL_ACCOUNT_*_USER в .env)")
		return 0

	ok = 0
	for acc in accounts:
		try:
			res = _post_connect(api, key, acc)
			sync = res.get("sync") or {}
			print(
				f"OK {acc['username']}: imported={sync.get('imported', '?')} "
				f"total={sync.get('total', '?')}"
			)
			ok += 1
		except urllib.error.HTTPError as e:
			detail = e.read().decode(errors="replace")[:400]
			print(f"FAIL {acc['username']}: HTTP {e.code} {detail}")
		except OSError as e:
			print(f"FAIL {acc['username']}: {e}")
			return 1

	return 0 if ok == len(accounts) else 1


if __name__ == "__main__":
	raise SystemExit(main())
