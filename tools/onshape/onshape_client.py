#!/usr/bin/env python3
"""Small Onshape API helper for project CAD documentation.

The client uses Onshape API-key request signing. Credentials are read from
environment variables and are never written to the repository.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import json
import os
import secrets
import string
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://cad.onshape.com"
JSON_CONTENT_TYPE = "application/json"


class OnshapeError(RuntimeError):
    """Raised for API setup or response failures."""


def _env(name: str, fallback: str | None = None) -> str:
    value = os.environ.get(name, fallback)
    if not value:
        raise OnshapeError(f"Missing environment variable: {name}")
    return value


def _nonce(length: int = 25) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _http_date() -> str:
    now = dt.datetime.now(dt.timezone.utc)
    return now.strftime("%a, %d %b %Y %H:%M:%S GMT")


def _signature(
    method: str,
    url: str,
    nonce: str,
    auth_date: str,
    content_type: str,
    access_key: str,
    secret_key: str,
) -> str:
    parsed = urllib.parse.urlsplit(url)
    message = (
        f"{method}\n{nonce}\n{auth_date}\n{content_type}\n"
        f"{parsed.path}\n{parsed.query}\n"
    ).lower()
    digest = hmac.new(
        secret_key.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    encoded = base64.b64encode(digest).decode("ascii")
    return f"On {access_key}:HmacSHA256:{encoded}"


def document_ids_from_url(url: str) -> dict[str, str]:
    """Extract did/wid/vid/eid tokens from a normal Onshape URL."""
    parsed = urllib.parse.urlsplit(url)
    parts = [part for part in parsed.path.split("/") if part]
    ids: dict[str, str] = {}

    for index, part in enumerate(parts):
        if part == "documents" and index + 1 < len(parts):
            ids["did"] = parts[index + 1]
        elif part in {"w", "v", "m", "e"} and index + 1 < len(parts):
            ids[part] = parts[index + 1]

    if "did" not in ids:
        raise OnshapeError("Could not find a document ID in the supplied URL")
    return ids


class OnshapeClient:
    def __init__(self, base_url: str, access_key: str, secret_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key

    @classmethod
    def from_env(cls) -> "OnshapeClient":
        return cls(
            base_url=_env("ONSHAPE_BASE_URL", DEFAULT_BASE_URL),
            access_key=_env("ONSHAPE_ACCESS_KEY"),
            secret_key=_env("ONSHAPE_SECRET_KEY"),
        )

    def request(
        self,
        method: str,
        path: str,
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
        accept: str = JSON_CONTENT_TYPE,
    ) -> tuple[bytes, str]:
        url = self._url(path, query)
        data = None if body is None else json.dumps(body).encode("utf-8")
        return self._request_url(method, url, data, accept)

    def _url(self, path: str, query: dict[str, str] | None = None) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            base = path
        else:
            base = f"{self.base_url}/{path.lstrip('/')}"
        if not query:
            return base
        return f"{base}?{urllib.parse.urlencode(query)}"

    def _request_url(
        self,
        method: str,
        url: str,
        data: bytes | None,
        accept: str,
    ) -> tuple[bytes, str]:
        method = method.upper()
        content_type = JSON_CONTENT_TYPE
        headers = self._headers(method, url, content_type, accept)
        request = urllib.request.Request(url, data=data, method=method, headers=headers)

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read(), response.headers.get("Content-Type", "")
        except urllib.error.HTTPError as exc:
            if exc.code in {301, 302, 303, 307, 308} and exc.headers.get("Location"):
                redirect_url = urllib.parse.urljoin(url, exc.headers["Location"])
                redirect_method = "GET" if exc.code == 303 else method
                redirect_data = None if redirect_method == "GET" else data
                return self._request_url(redirect_method, redirect_url, redirect_data, accept)
            detail = exc.read().decode("utf-8", errors="replace")
            raise OnshapeError(f"HTTP {exc.code} from Onshape: {detail}") from exc
        except urllib.error.URLError as exc:
            raise OnshapeError(f"Onshape request failed: {exc}") from exc

    def _headers(
        self,
        method: str,
        url: str,
        content_type: str,
        accept: str,
    ) -> dict[str, str]:
        nonce = _nonce()
        auth_date = _http_date()
        return {
            "Date": auth_date,
            "On-Nonce": nonce,
            "Content-Type": content_type,
            "Accept": accept,
            "Authorization": _signature(
                method,
                url,
                nonce,
                auth_date,
                content_type,
                self.access_key,
                self.secret_key,
            ),
        }


def _print_json(payload: bytes) -> None:
    parsed = json.loads(payload.decode("utf-8"))
    print(json.dumps(parsed, indent=2, sort_keys=True))


def cmd_parse_url(args: argparse.Namespace) -> int:
    print(json.dumps(document_ids_from_url(args.url), indent=2, sort_keys=True))
    return 0


def cmd_list_documents(args: argparse.Namespace) -> int:
    client = OnshapeClient.from_env()
    query = {"limit": str(args.limit)}
    payload, _ = client.request("GET", "/api/documents", query=query)
    _print_json(payload)
    return 0


def cmd_document(args: argparse.Namespace) -> int:
    client = OnshapeClient.from_env()
    ids = document_ids_from_url(args.url) if args.url else {"did": args.did}
    payload, _ = client.request("GET", f"/api/documents/{ids['did']}")
    _print_json(payload)
    return 0


def cmd_elements(args: argparse.Namespace) -> int:
    client = OnshapeClient.from_env()
    ids = document_ids_from_url(args.url)
    workspace = ids.get("w")
    if not workspace:
        raise OnshapeError("The URL must contain a workspace ID (`/w/...`) for elements")
    payload, _ = client.request(
        "GET",
        f"/api/documents/d/{ids['did']}/w/{workspace}/elements",
    )
    _print_json(payload)
    return 0


def cmd_export_partstudio_step(args: argparse.Namespace) -> int:
    client = OnshapeClient.from_env()
    ids = document_ids_from_url(args.url)
    workspace = ids.get("w")
    element = ids.get("e")
    if not workspace or not element:
        raise OnshapeError("The URL must contain workspace and element IDs (`/w/.../e/...`)")

    body = {
        "formatName": "STEP",
        "storeInDocument": False,
        "stepVersionString": args.step_version,
    }
    payload, content_type = client.request(
        "POST",
        f"/api/partstudios/d/{ids['did']}/w/{workspace}/e/{element}/translations",
        body=body,
        accept="application/json,application/octet-stream,*/*",
    )

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    if content_type.lower().startswith("application/json"):
        metadata_path = output.with_suffix(output.suffix + ".translation.json")
        metadata_path.write_bytes(payload)
        print(f"Translation started; metadata written to {metadata_path}")
        print("If Onshape returned an asynchronous translation ID, download it after it completes.")
    else:
        output.write_bytes(payload)
        print(f"Wrote {output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Onshape API helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_url = subparsers.add_parser("parse-url", help="extract did/wid/eid from a URL")
    parse_url.add_argument("url")
    parse_url.set_defaults(func=cmd_parse_url)

    list_docs = subparsers.add_parser("list-documents", help="list accessible documents")
    list_docs.add_argument("--limit", type=int, default=20)
    list_docs.set_defaults(func=cmd_list_documents)

    document = subparsers.add_parser("document", help="show document metadata")
    document.add_argument("--url")
    document.add_argument("--did")
    document.set_defaults(func=cmd_document)

    elements = subparsers.add_parser("elements", help="list elements in a workspace")
    elements.add_argument("url")
    elements.set_defaults(func=cmd_elements)

    export = subparsers.add_parser("export-partstudio-step", help="export a Part Studio as STEP")
    export.add_argument("url")
    export.add_argument("output")
    export.add_argument("--step-version", default="AP214")
    export.set_defaults(func=cmd_export_partstudio_step)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "document" and not args.url and not args.did:
        parser.error("document requires --url or --did")
    try:
        return args.func(args)
    except OnshapeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
