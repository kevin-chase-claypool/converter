#!/usr/bin/env python3
"""Local-only, allowlisted settings API for the XY-Theta HMI."""

import json
import pathlib
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BACKLIGHT = pathlib.Path(
    "/sys/class/backlight/panel_backlight@1/brightness"
)
TIMEOUT_FILE = pathlib.Path(
    "/var/lib/xytheta-settings/timeout-minutes.json"
)
ALLOWED_TIMEOUTS = (0, 1, 5, 10, 30)
ALLOWED_ORIGINS = {
    "http://127.0.0.1:8766",
    "http://localhost:8766",
}
SYSTEM_ACTIONS = {
    "/reboot": ("reboot", "RESTART"),
    "/poweroff": ("poweroff", "POWER OFF"),
}
SYSTEM_ACTION_LOCK = threading.Lock()


def read_timeout():
    try:
        value = json.loads(TIMEOUT_FILE.read_text())["minutes"]
        return value if type(value) is int and value in ALLOWED_TIMEOUTS else 1
    except (OSError, ValueError, KeyError, TypeError):
        return 1


def nm(*args, timeout=15):
    result = subprocess.run(
        ["/usr/bin/nmcli", *args],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode:
        raise ValueError((result.stderr or result.stdout).strip()[:300])
    return result.stdout


def wifi_device():
    for line in nm("-t", "-f", "DEVICE,TYPE", "device").splitlines():
        fields = line.split(":")
        if len(fields) >= 2 and fields[1] == "wifi":
            return fields[0]
    raise ValueError("No Wi-Fi device managed by NetworkManager")


def request_system_action(action):
    if not SYSTEM_ACTION_LOCK.acquire(blocking=False):
        return False

    def worker():
        time.sleep(0.35)
        try:
            subprocess.run(
                ["/usr/bin/systemctl", "--no-block", action],
                check=True,
                capture_output=True,
                text=True,
                timeout=10,
            )
        except Exception as error:
            print(
                f"XYTheta system action {action!r} failed: {error}",
                file=sys.stderr,
                flush=True,
            )

    threading.Thread(target=worker, daemon=True).start()
    return True


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def respond(self, code, data):
        raw = json.dumps(data).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_OPTIONS(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return self.respond(403, dict(error="Origin not allowed"))
        self.respond(200, {})

    def do_GET(self):
        try:
            if self.path == "/timeout":
                return self.respond(200, dict(minutes=read_timeout()))
            if self.path == "/status":
                brightness = (
                    int(BACKLIGHT.read_text()) if BACKLIGHT.exists() else 15
                )
                try:
                    device = wifi_device()
                    active = nm(
                        "-g", "GENERAL.CONNECTION", "device", "show", device
                    ).strip()
                    mode = (
                        nm(
                            "-g",
                            "802-11-wireless.mode",
                            "connection",
                            "show",
                            active,
                        ).strip()
                        if active and active != "--"
                        else "disconnected"
                    )
                except Exception:
                    device = "—"
                    active = "Unavailable"
                    mode = "unknown"
                return self.respond(
                    200,
                    dict(
                        active=active,
                        interface=device,
                        mode=mode,
                        brightness=brightness,
                    ),
                )
            if self.path == "/scan":
                device = wifi_device()
                current = nm(
                    "-g", "GENERAL.CONNECTION", "device", "show", device
                ).strip()
                if current and current != "--":
                    mode = nm(
                        "-g",
                        "802-11-wireless.mode",
                        "connection",
                        "show",
                        current,
                    ).strip()
                    if mode == "ap":
                        raise ValueError(
                            "Wi-Fi AP is active; scanning disabled to avoid "
                            "disrupting clients"
                        )
                output = nm(
                    "-t",
                    "-f",
                    "SSID,SIGNAL,SECURITY",
                    "device",
                    "wifi",
                    "list",
                    "ifname",
                    device,
                    "--rescan",
                    "yes",
                    timeout=25,
                )
                seen = set()
                networks = []
                for line in output.splitlines():
                    fields = re.split(r"(?<!\\):", line)
                    if len(fields) < 3:
                        continue
                    ssid = fields[0].replace("\\:", ":").strip()
                    if not ssid or ssid in seen:
                        continue
                    seen.add(ssid)
                    networks.append(
                        dict(
                            ssid=ssid,
                            label=(
                                f"{ssid}   ·   {fields[1]}%   ·   "
                                f"{fields[2]}"
                            ),
                        )
                    )
                return self.respond(200, dict(networks=networks))
            return self.respond(404, dict(error="Unknown endpoint"))
        except Exception as error:
            return self.respond(400, dict(error=str(error)))

    def do_POST(self):
        origin = self.headers.get("Origin")
        if origin is not None and origin not in ALLOWED_ORIGINS:
            return self.respond(403, dict(error="Origin not allowed"))
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 4096:
                raise ValueError("Request too large")
            body = json.loads(self.rfile.read(length))
            if self.path == "/timeout":
                value = body.get("minutes")
                if type(value) is not int or value not in ALLOWED_TIMEOUTS:
                    raise ValueError("Invalid timeout")
                TIMEOUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                TIMEOUT_FILE.write_text(json.dumps({"minutes": value}))
                return self.respond(200, dict(minutes=value))
            if self.path == "/brightness":
                value = body.get("value")
                if type(value) is not int or not 1 <= value <= 31:
                    raise ValueError("Brightness must be 1-31")
                BACKLIGHT.write_text(str(value))
                return self.respond(200, dict(message="Brightness updated"))
            if self.path == "/connect":
                device = wifi_device()
                ssid = body.get("ssid", "")
                password = body.get("password", "")
                if (
                    not isinstance(ssid, str)
                    or not 1 <= len(ssid.encode()) <= 32
                    or "\x00" in ssid
                ):
                    raise ValueError("Invalid SSID")
                if not isinstance(password, str) or len(password) > 128:
                    raise ValueError("Invalid password")
                current = nm(
                    "-g", "GENERAL.CONNECTION", "device", "show", device
                ).strip()
                if current and current != "--":
                    mode = nm(
                        "-g",
                        "802-11-wireless.mode",
                        "connection",
                        "show",
                        current,
                    ).strip()
                    if mode == "ap":
                        raise ValueError(
                            "Wi-Fi is serving the plotter access point. "
                            "Switching this radio would disconnect clients."
                        )
                command = [
                    "device",
                    "wifi",
                    "connect",
                    ssid,
                    "ifname",
                    device,
                ]
                if password:
                    command += ["password", password]
                nm(*command, timeout=40)
                return self.respond(
                    200, dict(message="Connected to " + ssid)
                )
            action = SYSTEM_ACTIONS.get(self.path)
            if action:
                systemctl_action, required_confirmation = action
                if body.get("confirm") != required_confirmation:
                    raise ValueError("Explicit confirmation required")
                scheduled = request_system_action(systemctl_action)
                if not scheduled:
                    return self.respond(
                        409, dict(error="Another system action is pending")
                    )
                return self.respond(
                    202,
                    dict(message=f"{systemctl_action.title()} requested"),
                )
            return self.respond(404, dict(error="Unknown endpoint"))
        except Exception as error:
            return self.respond(400, dict(error=str(error)))


ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
