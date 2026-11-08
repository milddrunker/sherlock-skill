#!/usr/bin/env python3
"""Embedded, standard-library-only username scanner for the sherlock-skill."""

from __future__ import annotations

import argparse
import json
import re
import socket
import ssl
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import (
    HTTPRedirectHandler,
    ProxyHandler,
    Request,
    build_opener,
)


SCHEMA_VERSION = 1
SCANNER_VERSION = "0.2.0"
DEFAULT_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "sites.json"
DEFAULT_TIMEOUT = 10
DEFAULT_WORKERS = 20
MAX_RESPONSE_BYTES = 1024 * 1024
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) "
    "Gecko/20100101 Firefox/132.0"
)
WAF_MARKERS = (
    r".loading-spinner{visibility:hidden}body.no-js .challenge-running{display:none}",
    r'<span id="challenge-error-text">',
    r"AwsWafIntegration.forceRefreshToken",
    r"perimeterxIdentifiers",
)
SUPPORTED_ERROR_TYPES = {"message", "status_code", "response_url"}


class ScanError(RuntimeError):
    """An actionable configuration or input error."""


class NoRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def load_sites(data_file: Path | None = None) -> dict[str, dict[str, Any]]:
    path = (data_file or DEFAULT_DATA_FILE).expanduser().resolve()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ScanError(f"Could not read site data: {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ScanError(f"Invalid JSON in site data: {path}: {exc}") from exc

    if not isinstance(data, dict) or not data:
        raise ScanError(f"Site data must be a non-empty JSON object: {path}")

    data.pop("$schema", None)
    required = {"url", "urlMain", "username_claimed", "errorType"}
    for name, site in data.items():
        if not isinstance(site, dict):
            raise ScanError(f"Site '{name}' must be a JSON object.")
        missing = sorted(required - site.keys())
        if missing:
            raise ScanError(f"Site '{name}' is missing: {', '.join(missing)}")
    return data


def select_sites(
    sites: dict[str, dict[str, Any]],
    requested: list[str] | None = None,
    include_nsfw: bool = False,
) -> list[tuple[str, dict[str, Any]]]:
    requested = requested or []
    by_name = {name.casefold(): (name, info) for name, info in sites.items()}
    if requested:
        selected = []
        missing = []
        seen = set()
        for requested_name in requested:
            key = requested_name.casefold()
            match = by_name.get(key)
            if not match:
                missing.append(requested_name)
                continue
            if key not in seen:
                selected.append(match)
                seen.add(key)
        if missing:
            raise ScanError(
                "Unknown site(s): "
                + ", ".join(sorted(missing))
                + ". Use `list-sites` to inspect supported names."
            )
        return selected

    return [
        (name, info)
        for name, info in sites.items()
        if include_nsfw or not bool(info.get("isNSFW", False))
    ]


def interpolate(value: Any, username: str, *, url_encode: bool = False) -> Any:
    replacement = quote(username, safe="-._~") if url_encode else username
    if isinstance(value, str):
        return value.replace("{}", replacement)
    if isinstance(value, dict):
        return {
            key: interpolate(item, username, url_encode=url_encode)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [
            interpolate(item, username, url_encode=url_encode) for item in value
        ]
    return value


def make_opener(proxy: str | None, follow_redirects: bool):
    handlers = []
    if proxy:
        scheme = urlparse(proxy).scheme.lower()
        if scheme not in {"http", "https"}:
            raise ScanError(
                "The embedded scanner supports HTTP/HTTPS proxies. "
                "Use the agent's network/TUN layer for SOCKS proxies."
            )
        handlers.append(ProxyHandler({"http": proxy, "https": proxy}))
    if not follow_redirects:
        handlers.append(NoRedirectHandler())
    return build_opener(*handlers)


def _decode_body(raw: bytes, content_type: str | None) -> str:
    charset = "utf-8"
    if content_type:
        match = re.search(r"charset=([A-Za-z0-9._-]+)", content_type, re.IGNORECASE)
        if match:
            charset = match.group(1)
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def fetch_site(
    site: dict[str, Any],
    username: str,
    timeout: float,
    proxy: str | None,
) -> dict[str, Any]:
    error_types = site.get("errorType", [])
    if isinstance(error_types, str):
        error_types = [error_types]
    follow_redirects = "response_url" not in error_types
    opener = make_opener(proxy, follow_redirects)

    profile_url = interpolate(site["url"], username, url_encode=True)
    probe_url = interpolate(
        site.get("urlProbe") or site["url"], username, url_encode=True
    )
    method = site.get("request_method")
    if not method:
        method = "HEAD" if "status_code" in error_types else "GET"
    method = str(method).upper()
    if method not in {"GET", "HEAD", "POST", "PUT"}:
        raise ScanError(f"Unsupported request method: {method}")

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/json;q=0.9,*/*;q=0.8",
    }
    for key, value in site.get("headers", {}).items():
        headers[str(key)] = str(value)

    payload = interpolate(site.get("request_payload"), username)
    data = None
    if payload is not None and method not in {"GET", "HEAD"}:
        data = json.dumps(payload).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    request = Request(
        probe_url,
        data=data,
        headers=headers,
        method=method,
    )
    started = time.monotonic()
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read(MAX_RESPONSE_BYTES)
            return {
                "profile_url": profile_url,
                "status_code": response.status,
                "final_url": response.geturl(),
                "text": _decode_body(raw, response.headers.get("Content-Type")),
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "network_error": None,
            }
    except HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES)
        return {
            "profile_url": profile_url,
            "status_code": exc.code,
            "final_url": exc.geturl(),
            "text": _decode_body(raw, exc.headers.get("Content-Type")),
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "network_error": None,
        }
    except (URLError, socket.timeout, TimeoutError, ssl.SSLError, OSError) as exc:
        reason = getattr(exc, "reason", exc)
        return {
            "profile_url": profile_url,
            "status_code": None,
            "final_url": probe_url,
            "text": "",
            "elapsed_seconds": round(time.monotonic() - started, 3),
            "network_error": f"{type(exc).__name__}: {reason}",
        }


def classify_response(site: dict[str, Any], response: dict[str, Any]) -> tuple[str, str]:
    if response["status_code"] is None:
        return "unknown", response.get("network_error") or "Network request failed."

    status_code = int(response["status_code"])
    text = response.get("text") or ""
    if any(marker in text for marker in WAF_MARKERS):
        return "waf", f"Bot-protection page detected (HTTP {status_code})."

    error_types = site.get("errorType", [])
    if isinstance(error_types, str):
        error_types = [error_types]
    unsupported = [
        str(error_type)
        for error_type in error_types
        if error_type not in SUPPORTED_ERROR_TYPES
    ]
    if unsupported:
        return "unknown", f"Unsupported errorType: {', '.join(unsupported)}."

    claimed = False
    available = False
    reasons = []

    if "message" in error_types:
        error_messages = site.get("errorMsg")
        if isinstance(error_messages, str):
            error_messages = [error_messages]
        error_messages = error_messages or []
        if not error_messages:
            reasons.append("No errorMsg configured for message detection.")
        elif any(message in text for message in error_messages):
            available = True
            reasons.append(f"HTTP {status_code}; missing-account marker found.")
        else:
            claimed = True
            reasons.append(f"HTTP {status_code}; no missing-account marker found.")

    if "status_code" in error_types:
        error_codes = site.get("errorCode")
        if isinstance(error_codes, int):
            error_codes = [error_codes]
        if error_codes and status_code in error_codes:
            available = True
            reasons.append(f"HTTP {status_code}; configured missing-account status.")
        elif status_code < 200 or status_code >= 300:
            available = True
            reasons.append(f"HTTP {status_code}; non-success status.")
        else:
            claimed = True
            reasons.append(f"HTTP {status_code}; successful profile response.")

    if "response_url" in error_types:
        if 200 <= status_code < 300:
            claimed = True
            reasons.append(f"HTTP {status_code}; no missing-account redirect.")
        else:
            available = True
            reasons.append(f"HTTP {status_code}; redirect or failure response.")

    if claimed:
        return "claimed", " ".join(reasons)
    if available:
        return "available", " ".join(reasons)
    return "unknown", "No configured detection rule matched."


def scan_site(
    name: str,
    site: dict[str, Any],
    username: str,
    timeout: float,
    proxy: str | None,
) -> dict[str, Any]:
    regex_check = site.get("regexCheck")
    if regex_check:
        try:
            if re.search(str(regex_check), username) is None:
                return {
                    "site": name,
                    "url": interpolate(site["url"], username, url_encode=True),
                    "status": "illegal",
                    "http_status": None,
                    "reason": "Username does not match this site's regexCheck.",
                    "elapsed_seconds": 0.0,
                }
        except re.error as exc:
            return {
                "site": name,
                "url": interpolate(site["url"], username, url_encode=True),
                "status": "unknown",
                "http_status": None,
                "reason": f"Invalid site regexCheck: {exc}",
                "elapsed_seconds": 0.0,
            }

    try:
        response = fetch_site(site, username, timeout, proxy)
    except Exception as exc:
        return {
            "site": name,
            "url": interpolate(site["url"], username, url_encode=True),
            "status": "unknown",
            "http_status": None,
            "reason": f"{type(exc).__name__}: {exc}",
            "elapsed_seconds": 0.0,
        }

    status, reason = classify_response(site, response)
    return {
        "site": name,
        "url": response["profile_url"],
        "status": status,
        "http_status": response["status_code"],
        "reason": reason,
        "elapsed_seconds": response["elapsed_seconds"],
    }


def scan_sites(
    username: str,
    *,
    data_file: Path | None = None,
    site_names: list[str] | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    workers: int = DEFAULT_WORKERS,
    proxy: str | None = None,
    include_nsfw: bool = False,
) -> dict[str, Any]:
    username = username.strip()
    if not username:
        raise ScanError("Username cannot be empty.")
    if timeout <= 0:
        raise ScanError("Timeout must be greater than zero.")
    if workers <= 0:
        raise ScanError("Workers must be greater than zero.")
    if proxy and urlparse(proxy).scheme.lower() not in {"http", "https"}:
        raise ScanError("Proxy must use an http:// or https:// URL.")

    started = time.monotonic()
    all_sites = load_sites(data_file)
    selected = select_sites(all_sites, site_names, include_nsfw)
    results: list[dict[str, Any]] = []

    with ThreadPoolExecutor(max_workers=min(workers, max(1, len(selected)))) as executor:
        futures = {
            executor.submit(scan_site, name, site, username, timeout, proxy): name
            for name, site in selected
        }
        for future in as_completed(futures):
            results.append(future.result())

    order = {name: index for index, (name, _) in enumerate(selected)}
    results.sort(key=lambda result: order.get(result["site"], len(order)))
    counts = {
        status: sum(result["status"] == status for result in results)
        for status in ("claimed", "available", "unknown", "illegal", "waf")
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "scanner": {
            "name": "sherlock-skill",
            "version": SCANNER_VERSION,
            "engine": "embedded-python-stdlib",
            "site_data": str((data_file or DEFAULT_DATA_FILE).resolve()),
        },
        "username": username,
        "scanned_at": utc_now(),
        "duration_seconds": round(time.monotonic() - started, 3),
        "options": {
            "timeout_seconds": timeout,
            "workers": workers,
            "requested_sites": site_names or [],
            "proxy_configured": bool(proxy),
            "include_nsfw": include_nsfw,
        },
        "summary": {
            "sites_scanned": len(results),
            "claimed": counts["claimed"],
            "available": counts["available"],
            "unknown": counts["unknown"],
            "illegal": counts["illegal"],
            "waf": counts["waf"],
        },
        "results": results,
    }


def compact_payload(scan: dict[str, Any], include_all: bool) -> dict[str, Any]:
    payload = dict(scan)
    if include_all:
        payload["results"] = scan["results"]
    else:
        payload["results"] = [
            result for result in scan["results"] if result["status"] == "claimed"
        ]
        payload["issues"] = [
            result
            for result in scan["results"]
            if result["status"] in {"unknown", "illegal", "waf"}
        ]
    return payload


def render_human(scan: dict[str, Any]) -> str:
    lines = [f"[*] Checking username {scan['username']} on:"]
    for result in scan["results"]:
        if result["status"] == "claimed":
            lines.append(f"[+] {result['site']}: {result['url']}")
    summary = scan["summary"]
    lines.append(
        f"[*] Completed: {summary['claimed']} found across "
        f"{summary['sites_scanned']} sites; {summary['unknown']} unknown, "
        f"{summary['waf']} blocked."
    )
    return "\n".join(lines)


def write_json(payload: dict[str, Any], output: Path | None) -> None:
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if output:
        output = output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
    sys.stdout.write(rendered)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Embedded public-username scanner for sherlock-skill."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="Scan a username against bundled sites.")
    scan.add_argument("--username", required=True)
    scan.add_argument("--site", action="append", default=[])
    scan.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT)
    scan.add_argument("--workers", type=int, default=DEFAULT_WORKERS)
    scan.add_argument("--proxy", help="HTTP or HTTPS proxy URL.")
    scan.add_argument("--include-nsfw", action="store_true")
    scan.add_argument("--include-all", action="store_true")
    scan.add_argument("--output", type=Path)
    scan.add_argument("--human", action="store_true")
    scan.add_argument("--data-file", type=Path)

    sites = subparsers.add_parser("list-sites", help="List bundled site names.")
    sites.add_argument("--include-nsfw", action="store_true")
    sites.add_argument("--data-file", type=Path)

    validate = subparsers.add_parser("validate-data", help="Validate bundled site data.")
    validate.add_argument("--data-file", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "list-sites":
            all_sites = load_sites(args.data_file)
            selected = select_sites(all_sites, include_nsfw=args.include_nsfw)
            write_json(
                {
                    "sites": [name for name, _ in selected],
                    "count": len(selected),
                    "data_file": str((args.data_file or DEFAULT_DATA_FILE).resolve()),
                },
                None,
            )
            return 0

        if args.command == "validate-data":
            all_sites = load_sites(args.data_file)
            write_json(
                {
                    "valid": True,
                    "sites": len(all_sites),
                    "data_file": str((args.data_file or DEFAULT_DATA_FILE).resolve()),
                },
                None,
            )
            return 0

        scan = scan_sites(
            args.username,
            data_file=args.data_file,
            site_names=args.site,
            timeout=args.timeout,
            workers=args.workers,
            proxy=args.proxy,
            include_nsfw=args.include_nsfw,
        )
        if args.human:
            rendered = render_human(scan)
            print(rendered)
            if args.output:
                output = args.output.expanduser().resolve()
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(rendered + "\n", encoding="utf-8")
        else:
            write_json(compact_payload(scan, args.include_all), args.output)
        return 0
    except ScanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
