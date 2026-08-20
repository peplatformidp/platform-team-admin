"""Fetch secrets from Bitwarden via the bw CLI.

Lookups match item name exactly. `bw get item` and `bw list items --search`
are fuzzy and also match notes and custom fields, so a query such as
"Pulumi Secrets" can hit "GitHub Secrets" when the latter's notes mention
Pulumi. That matches secrets-setup/inject_secrets.sh.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

ENV_FILE = Path(__file__).parent / ".env"
GITHUB_SECRETS_ITEM = "GitHub Secrets"
FIELD_OWNER = "pulumi-github-owner"
FIELD_TOKEN = "pulumi-github-token"


def _load_env_file(path: Path) -> None:
    """Load KEY=value pairs from .env into os.environ."""
    if not path.is_file():
        raise FileNotFoundError(
            f"Bitwarden credentials file not found: {path}\n"
            "Copy .env_example to .env and add BW_CLIENTID, BW_CLIENTSECRET, BW_PASSWORD."
        )

    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[7:].strip()
            if line.startswith("-") or "=" not in line:
                continue

            key, _, value = line.partition("=")
            os.environ[key.strip()] = value.strip().strip("'\"")


def _run_bw(args: list[str], *, session: str | None = None) -> str:
    cmd = ["bw", *args]
    if session:
        cmd.extend(["--session", session])

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Bitwarden CLI failed ({' '.join(cmd)}): {detail}")

    return result.stdout.strip()


def _get_bw_session() -> str:
    if session := os.environ.get("BW_SESSION"):
        return session

    _load_env_file(ENV_FILE)

    for var in ("BW_CLIENTID", "BW_CLIENTSECRET", "BW_PASSWORD"):
        if not os.environ.get(var):
            raise RuntimeError(f"{var} is not set in {ENV_FILE}")

    login_check = subprocess.run(
        ["bw", "login", "--check"],
        capture_output=True,
        text=True,
        check=False,
    )
    if login_check.returncode != 0:
        _run_bw(["login", "--apikey"])

    session = _run_bw(["unlock", "--passwordenv", "BW_PASSWORD", "--raw"])
    if not session:
        raise RuntimeError("Failed to unlock Bitwarden vault. Check BW_PASSWORD in .env.")

    return session


def _get_item_by_exact_name(item_name: str, session: str) -> dict[str, Any]:
    """Return the vault item whose name equals item_name.

    Raises if none or more than one item has that exact name so callers never
    read an ambiguous or notes-matched cipher.
    """
    raw = _run_bw(["list", "items"], session=session) or "[]"
    items = json.loads(raw)
    matches = [item for item in items if item.get("name") == item_name]

    if not matches:
        raise KeyError(
            f"Bitwarden item '{item_name}' not found. "
            "Run secrets-setup/inject_secrets.sh to sync secrets-setup/*.json."
        )

    if len(matches) > 1:
        ids = ", ".join(str(item.get("id", "?")) for item in matches)
        raise RuntimeError(
            f"Found {len(matches)} Bitwarden items named '{item_name}' "
            f"(ids: {ids}). Delete the duplicates in the vault, then retry."
        )

    return matches[0]


def _field_value(item: dict[str, Any], field_name: str) -> str:
    item_name = str(item.get("name", ""))
    for field in item.get("fields") or []:
        if field.get("name") == field_name:
            value = field.get("value")
            if value:
                return str(value)

    raise KeyError(
        f"Field '{field_name}' not found in Bitwarden item '{item_name}'. "
        "Run secrets-setup/inject_secrets.sh to sync github_secrets.json."
    )


def get_github_credentials() -> tuple[str, str]:
    """Return (owner, token) from CI env vars or the GitHub Secrets item in Bitwarden."""
    owner = os.environ.get("PULUMI_GITHUB_OWNER")
    token = os.environ.get("PULUMI_GITHUB_TOKEN")
    if owner and token:
        return owner, token

    had_session = bool(os.environ.get("BW_SESSION"))
    session = _get_bw_session()
    try:
        _run_bw(["sync"], session=session)
        item = _get_item_by_exact_name(GITHUB_SECRETS_ITEM, session)
        owner = _field_value(item, FIELD_OWNER)
        token = _field_value(item, FIELD_TOKEN)
        return owner, token
    finally:
        if not had_session:
            subprocess.run(["bw", "lock"], capture_output=True, check=False)
