#!/usr/bin/env python3
"""Collect authentication cookies from https://x.com via the Chrome DevTools Protocol."""

from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import secrets
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

REMOTE_DEBUGGING_PORT = 9222
REMOTE_DEBUGGING_HOST = "127.0.0.1"
REMOTE_DEBUGGING_BASE = f"http://{REMOTE_DEBUGGING_HOST}:{REMOTE_DEBUGGING_PORT}"
CHROME_EXECUTABLE_CANDIDATES = (
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
)
COOKIE_URLS = (
    "https://x.com",
    "https://twitter.com",
    "https://api.x.com",
)


def _request(path: str, *, method: str = "GET", expect_json: bool = True) -> dict:
    url = f"{REMOTE_DEBUGGING_BASE}{path}"
    data: bytes | None = b"" if method in {"POST", "PUT"} else None
    request = urllib.request.Request(url=url, data=data, method=method)
    with urllib.request.urlopen(request, timeout=2) as response:
        payload = response.read()
        if not expect_json:
            return {}
        return json.loads(payload.decode("utf-8"))


def _is_debug_port_available() -> bool:
    try:
        _request("/json/version")
        return True
    except urllib.error.URLError:
        return False


def _launch_chrome() -> subprocess.Popen:
    chrome_path = os.environ.get("GOOGLE_CHROME_BIN")
    if chrome_path and not pathlib.Path(chrome_path).exists():
        chrome_path = None

    if not chrome_path:
        for candidate in CHROME_EXECUTABLE_CANDIDATES:
            chrome_path = shutil.which(candidate)
            if chrome_path:
                break
    if not chrome_path:
        raise RuntimeError(
            "Could not find Chrome executable. Install Chrome or set the GOOGLE_CHROME_BIN environment variable."
        )

    user_data_dir = pathlib.Path.home() / ".chrome-devtools"
    user_data_dir.mkdir(parents=True, exist_ok=True)

    return subprocess.Popen(
        [
            chrome_path,
            f"--remote-debugging-port={REMOTE_DEBUGGING_PORT}",
            f"--user-data-dir={user_data_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def _ensure_debug_port_ready() -> subprocess.Popen | None:
    if _is_debug_port_available():
        return None

    chrome_proc = _launch_chrome()
    for _ in range(30):
        if _is_debug_port_available():
            return chrome_proc
        time.sleep(0.25)

    chrome_proc.terminate()
    raise RuntimeError("Chrome did not expose the debugging port in time")


def _collect_tokens_from_target(target_info: dict) -> dict | None:
    websocket_url = target_info.get("webSocketDebuggerUrl")
    if not websocket_url:
        return None

    target_id = target_info.get("id")
    if target_id:
        try:
            _request(f"/json/activate/{target_id}", expect_json=False)
        except (urllib.error.URLError, urllib.error.HTTPError):
            pass

    try:
        with _SimpleWebSocket(websocket_url) as ws:
            ws.call("Page.enable")
            ws.call("Runtime.enable")
            ws.call("Network.enable")
            _await_runtime_context(ws)
            return _collect_twitter_tokens(ws)
    except Exception as exc:  # pragma: no cover - best-effort navigation
        raise RuntimeError("Failed to collect authentication cookies") from exc
    return None


def _await_runtime_context(ws: _SimpleWebSocket, timeout: float = 8.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            ws.call(
                "Runtime.evaluate",
                {"expression": "void 0", "returnByValue": True},
                timeout=2,
            )
            return
        except RuntimeError as err:
            if "Cannot find context" in str(err):
                time.sleep(0.25)
                continue
            raise
    raise RuntimeError("Runtime execution context was not ready in time")


def _collect_twitter_tokens(ws: _SimpleWebSocket) -> dict:
    response = ws.call(
        "Network.getCookies",
        {"urls": list(COOKIE_URLS)},
        timeout=5,
    )
    payload = response.get("result", {})
    cookies = payload.get("cookies", []) if isinstance(payload, dict) else []

    formatted_cookies: list[dict[str, object]] = []
    header_parts: list[str] = []
    cookie_lookup: dict[str, str] = {}

    for cookie in cookies:
        if not isinstance(cookie, dict):
            continue
        name = cookie.get("name")
        value = cookie.get("value")
        if not isinstance(name, str) or not isinstance(value, str):
            continue

        formatted = {
            "name": name,
            "value": value,
            "domain": cookie.get("domain"),
            "path": cookie.get("path"),
            "expires": cookie.get("expires"),
            "httpOnly": bool(cookie.get("httpOnly")),
            "secure": bool(cookie.get("secure")),
            "sameSite": cookie.get("sameSite"),
            "priority": cookie.get("priority"),
            "sourcePort": cookie.get("sourcePort"),
            "sourceScheme": cookie.get("sourceScheme"),
            "cookieString": _format_cookie_string(cookie),
        }
        formatted_cookies.append(formatted)

        if name not in cookie_lookup:
            cookie_lookup[name] = value
            header_parts.append(f"{name}={value}")

    essentials = {
        key: cookie_lookup[key]
        for key in ("auth_token", "ct0", "twid", "guest_id", "att")
        if key in cookie_lookup
    }

    return {
        "cookies": formatted_cookies,
        "cookieHeader": "; ".join(header_parts),
        "essentials": essentials,
    }


def _format_cookie_string(cookie: dict) -> str:
    name = cookie.get("name", "")
    value = cookie.get("value", "")
    parts = [f"{name}={value}"]

    domain = cookie.get("domain")
    if isinstance(domain, str) and domain:
        parts.append(f"Domain={domain}")

    path = cookie.get("path")
    if isinstance(path, str) and path:
        parts.append(f"Path={path}")

    expires = cookie.get("expires")
    if isinstance(expires, (int, float)) and expires > 0:
        try:
            expiry = datetime.fromtimestamp(expires, tz=timezone.utc)
            parts.append(expiry.strftime("Expires=%a, %d %b %Y %H:%M:%S GMT"))
        except (OverflowError, ValueError):
            pass

    same_site = cookie.get("sameSite")
    if isinstance(same_site, str) and same_site:
        parts.append(f"SameSite={same_site}")

    if cookie.get("secure"):
        parts.append("Secure")
    if cookie.get("httpOnly"):
        parts.append("HttpOnly")

    return "; ".join(parts)


class _SimpleWebSocket:
    """Minimal WebSocket client for communicating with Chrome's CDP endpoint."""

    def __init__(self, url: str):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "ws":
            raise ValueError(f"Unsupported WebSocket scheme in {url}")

        host = parsed.hostname or REMOTE_DEBUGGING_HOST
        port = parsed.port or REMOTE_DEBUGGING_PORT
        path = parsed.path or "/"
        if parsed.query:
            path = f"{path}?{parsed.query}"

        self._sock = socket.create_connection((host, port), timeout=5)
        self._sock.settimeout(5)
        self._buffer = bytearray()
        self._next_id = 1
        self._handshake(host, port, path)

    def __enter__(self) -> _SimpleWebSocket:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def close(self) -> None:
        try:
            self._sock.close()
        finally:
            self._buffer.clear()

    def call(
        self, method: str, params: dict | None = None, *, timeout: float = 5
    ) -> dict:
        message_id = self._next_id
        self._next_id += 1
        payload = {"id": message_id, "method": method}
        if params:
            payload["params"] = params
        self._send_text(json.dumps(payload))
        response = self._wait_for_response(message_id, timeout=timeout)
        if "error" in response:
            error = response["error"]
            description = (
                error.get("message", str(error))
                if isinstance(error, dict)
                else str(error)
            )
            raise RuntimeError(f"{method} failed: {description}")
        return response

    def _wait_for_response(self, command_id: int, *, timeout: float) -> dict:
        end_time = time.time() + timeout
        while True:
            remaining = end_time - time.time()
            if remaining <= 0:
                raise TimeoutError("Timed out waiting for CDP response")
            self._sock.settimeout(remaining)
            message = self._receive_message()
            if not message:
                continue
            data = json.loads(message)
            if data.get("id") == command_id:
                return data

    def _handshake(self, host: str, port: int, path: str) -> None:
        key = base64.b64encode(secrets.token_bytes(16)).decode("ascii")
        handshake = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host}:{port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self._sock.sendall(handshake.encode("utf-8"))

        response = self._read_http_headers()
        if not response.startswith("HTTP/1.1 101"):
            raise ConnectionError(
                f"Unexpected WebSocket handshake response: {response.splitlines()[0]}"
            )

    def _read_http_headers(self) -> str:
        while b"\r\n\r\n" not in self._buffer:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket handshake failed: connection closed")
            self._buffer.extend(chunk)
        header_bytes, remainder = self._buffer.split(b"\r\n\r\n", 1)
        self._buffer = bytearray(remainder)
        return header_bytes.decode("iso-8859-1")

    def _send_text(self, message: str) -> None:
        payload = message.encode("utf-8")
        header = bytearray()
        header.append(0x81)  # FIN + text frame
        payload_len = len(payload)
        if payload_len <= 125:
            header.append(0x80 | payload_len)
        elif payload_len <= 0xFFFF:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", payload_len))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", payload_len))

        mask_key = secrets.token_bytes(4)
        header.extend(mask_key)
        masked_payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(header + masked_payload)

    def _receive_message(self) -> str | None:
        opcode, payload = self._read_frame()
        if opcode == 0x1:  # text
            return payload.decode("utf-8")
        if opcode == 0x8:  # close
            self.close()
            return None
        if opcode == 0x9:  # ping
            self._send_control_frame(0xA, payload)
            return None
        return None

    def _send_control_frame(self, opcode: int, payload: bytes) -> None:
        header = bytearray()
        header.append(0x80 | opcode)
        payload_len = len(payload)
        header.append(0x80 | payload_len)
        mask_key = secrets.token_bytes(4)
        header.extend(mask_key)
        masked_payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(header + masked_payload)

    def _read_frame(self) -> tuple[int, bytes]:
        self._require_bytes(2)
        first_byte = self._buffer[0]
        second_byte = self._buffer[1]
        masked = second_byte & 0x80
        payload_len = second_byte & 0x7F
        index = 2

        if payload_len == 126:
            self._require_bytes(index + 2)
            payload_len = struct.unpack("!H", self._buffer[index : index + 2])[0]
            index += 2
        elif payload_len == 127:
            self._require_bytes(index + 8)
            payload_len = struct.unpack("!Q", self._buffer[index : index + 8])[0]
            index += 8

        if masked:
            raise ConnectionError("Received masked frame from server")

        self._require_bytes(index + payload_len)
        payload = bytes(self._buffer[index : index + payload_len])
        del self._buffer[: index + payload_len]
        opcode = first_byte & 0x0F
        return opcode, payload

    def _require_bytes(self, size: int) -> None:
        while len(self._buffer) < size:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket connection closed unexpectedly")
            self._buffer.extend(chunk)


def open_x() -> dict | None:
    chrome_proc = _ensure_debug_port_ready()
    try:
        target_url = urllib.parse.quote("https://x.com", safe=":/?=&%")
        new_tab_path = f"/json/new?{target_url}"
        last_error: urllib.error.HTTPError | None = None
        target_info: dict | None = None
        for method in ("PUT", "POST", "GET"):
            try:
                target_info = _request(new_tab_path, method=method)
                break
            except urllib.error.HTTPError as err:
                last_error = err
                if err.code != 405:
                    raise
        else:
            if last_error:
                raise last_error

        tokens: dict | None = None
        if target_info:
            tokens = _collect_tokens_from_target(target_info)
        return tokens
    finally:
        # If we started Chrome, leave it running. The caller can close it when done.
        if chrome_proc:
            print(
                "Chrome was launched with remote debugging enabled. Close it manually when finished."
            )
    return None


if __name__ == "__main__":
    argparse.ArgumentParser(
        description="Collect authentication cookies from an existing X session"
    ).parse_args()

    try:
        tokens = open_x()
        if tokens:
            print(json.dumps(tokens, indent=2))
        else:
            print(
                "No cookies were collected. Verify you are logged in to X in the dedicated profile.",
                file=sys.stderr,
            )
    except Exception as exc:  # pragma: no cover - command line tool
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
