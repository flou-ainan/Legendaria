"""Network access: the password, sessions and who counts as "this computer" (ADR-026, plan 12).

No HTTP in here. The server asks this module three things: is this request from this computer,
does it carry a valid session, and may this peer address connect at all. Everything is kept in
`access.json` in the user config dir (its own file, so `config.json` can be shared in a bug report).
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import secrets
import socket
import threading
import time
from collections import deque
from collections.abc import Collection, Mapping
from pathlib import Path
from typing import Any

from legendaria_engine import paths

ACCESS_FILE = "access.json"
SCRYPT = {
    "n": 2**15,
    "r": 8,
    "p": 1,
}  # ~32 MB and ~0.1 s per check; stored with the hash so it can be raised
SCRYPT_MAXMEM = 64 * 1024 * 1024
MIN_LENGTH = 8
MAX_LENGTH = 128
SESSION_DAYS = 30
# no `l` or `o`, no `0` or `1`: easy to read out and to type on a phone (5 bits per symbol)
ALPHABET = "abcdefghijkmnpqrstuvwxyz23456789"
GENERATED_SYMBOLS = 12  # 60 bits, shown as xxxx-xxxx-xxxx
COMMON = {
    "12345678", "123456789", "1234567890", "password", "password1", "qwertyui", "qwerty123",
    "11111111", "00000000", "abcd1234", "iloveyou", "senha123", "senha1234", "123mudar",
    "brasil123", "12341234", "admin123", "letmein1", "welcome1", "legendaria",
}  # fmt: skip
LOCAL_NAMES = {"127.0.0.1", "localhost", "::1"}
# a request that went through a proxy or a tunnel (ngrok, `tailscale serve`...) is remote even
# though it connects from this computer
PROXY_HEADERS = ("forwarded", "x-forwarded", "x-real-ip", "x-original", "tailscale-", "cf-", "via")
CGNAT = ipaddress.ip_network("100.64.0.0/10")  # Tailscale and Headscale addresses live here
LOGIN_FREE_FAILURES = 5
LOGIN_MAX_DELAY = 900.0  # seconds
GLOBAL_FAILURES = 30  # failures from anywhere within GLOBAL_WINDOW lock every sign-in
GLOBAL_WINDOW = 600.0
DEFAULTS: dict[str, Any] = {
    "lan": True,
    "require_password_here": False,
    "allow_public": False,
    "remote_browse": True,
}


class AccessError(ValueError):
    """A password was refused; `code` is a stable key the interfaces translate."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def access_file() -> Path:
    """`<config dir>/access.json`."""
    return paths.config_dir() / ACCESS_FILE


def check_password(password: str) -> str | None:
    """None when `password` is acceptable, else a code: `too_short`, `too_long` or `too_common`."""
    if len(password) < MIN_LENGTH:
        return "too_short"
    if len(password) > MAX_LENGTH:
        return "too_long"
    if password.lower() in COMMON or len(set(password)) == 1:
        return "too_common"
    return None


def generate_password() -> str:
    """A random password such as `k7mq-x2vd-9tpr` (60 bits), easy to read out and to type."""
    symbols = "".join(secrets.choice(ALPHABET) for _ in range(GENERATED_SYMBOLS))
    return "-".join(symbols[i : i + 4] for i in range(0, GENERATED_SYMBOLS, 4))


def _hash(password: str, salt: bytes, params: Mapping[str, int]) -> bytes:
    return hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=params["n"],
        r=params["r"],
        p=params["p"],
        maxmem=SCRYPT_MAXMEM,
        dklen=32,
    )


class Access:
    """The settings in `access.json`: the password hash, the session secret and the switches.

    A running server calls `refresh()` on each request, so `flosub auth set` or the launcher
    changing the file takes effect (and signs everyone out) without a restart.
    """

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or access_file()
        self.lock = threading.RLock()
        self.password: dict[str, Any] | None = None
        self.secret = secrets.token_hex(32)
        self.settings = dict(DEFAULTS)
        self._stamp: int | None = None
        self._verifying = threading.BoundedSemaphore(2)  # scrypt uses 32 MB: never run many at once
        self.refresh(force=True)

    # --- file ----------------------------------------------------------------

    def refresh(self, force: bool = False) -> None:
        """Re-read the file when it changed on disk."""
        try:
            stamp = self.path.stat().st_mtime_ns
        except OSError:
            stamp = None
        with self.lock:
            if not force and stamp == self._stamp:
                return
            self._stamp = stamp
            data: dict[str, Any] = {}
            if stamp is not None:
                try:
                    data = json.loads(self.path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    data = {}  # unreadable: behave as if no password is set (local only)
            stored = data.get("password")
            valid = isinstance(stored, dict) and {"n", "r", "p", "salt", "hash"} <= stored.keys()
            self.password = stored if valid else None
            if isinstance(data.get("secret"), str) and len(data["secret"]) >= 32:
                self.secret = data["secret"]
            self.settings = {
                key: data[key] if isinstance(data.get(key), bool) else default
                for key, default in DEFAULTS.items()
            }

    def save(self) -> None:
        """Write the file (mode 0600 where the OS has it), replacing it atomically."""
        data = {"password": self.password, "secret": self.secret, **self.settings}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_name(self.path.name + ".tmp")
        descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)
            handle.write("\n")
        os.replace(temp, self.path)
        self._stamp = self.path.stat().st_mtime_ns

    # --- password --------------------------------------------------------------

    @property
    def has_password(self) -> bool:
        """A password is set (the server may then listen on the network)."""
        return self.password is not None

    def set_password(self, password: str) -> None:
        """Store the hash of `password` and rotate the session secret (everyone is signed out)."""
        problem = check_password(password)
        if problem:
            raise AccessError(problem)
        salt = secrets.token_bytes(16)
        with self.lock:
            self.password = {
                **SCRYPT,
                "salt": salt.hex(),
                "hash": _hash(password, salt, SCRYPT).hex(),
            }
            self.secret = secrets.token_hex(32)
            self.save()

    def clear_password(self) -> None:
        """Forget the password (the server goes back to this computer only) and sign everyone out."""
        with self.lock:
            self.password = None
            self.secret = secrets.token_hex(32)
            self.save()

    def verify(self, password: str) -> bool:
        """Constant-time check of `password`; False when none is set."""
        with self.lock:
            stored = self.password
        if stored is None or len(password) > MAX_LENGTH:
            return False
        with self._verifying:
            digest = _hash(password, bytes.fromhex(stored["salt"]), stored)
        return hmac.compare_digest(digest, bytes.fromhex(stored["hash"]))

    # --- sessions --------------------------------------------------------------

    def make_token(self, now: float | None = None) -> str:
        """A session token: an expiry and a random part, signed with the session secret."""
        expiry = int((now if now is not None else time.time()) + SESSION_DAYS * 86400)
        payload = f"{expiry}.{secrets.token_hex(8)}"
        return f"{payload}.{self._sign(payload)}"

    def check_token(self, token: str, now: float | None = None) -> bool:
        """The token was made with this secret and has not expired."""
        if not self.has_password:
            return False
        payload, _, signature = token.rpartition(".")
        if not payload or not hmac.compare_digest(self._sign(payload), signature):
            return False
        try:
            expiry = int(payload.split(".", 1)[0])
        except ValueError:
            return False
        return expiry > (now if now is not None else time.time())

    def _sign(self, payload: str) -> str:
        with self.lock:
            key = bytes.fromhex(self.secret)
        return hmac.new(key, payload.encode(), hashlib.sha256).hexdigest()


class RateLimiter:
    """Slows down wrong passwords: per address, and across all of them."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.failures: dict[
            str, tuple[int, float]
        ] = {}  # address -> (consecutive failures, last failure)
        self.recent: deque[float] = deque()

    def wait(self, key: str, now: float | None = None) -> float:
        """Seconds to wait before `key` may try again (0 when it may)."""
        now = time.monotonic() if now is None else now
        with self.lock:
            while self.recent and self.recent[0] <= now - GLOBAL_WINDOW:
                self.recent.popleft()
            wait = 0.0
            if len(self.recent) >= GLOBAL_FAILURES:
                wait = self.recent[0] + GLOBAL_WINDOW - now
            count, last = self.failures.get(key, (0, 0.0))
            if count >= LOGIN_FREE_FAILURES:
                delay = min(LOGIN_MAX_DELAY, 5.0 * 2 ** (count - LOGIN_FREE_FAILURES))
                wait = max(wait, last + delay - now)
            return max(0.0, wait)

    def fail(self, key: str, now: float | None = None) -> None:
        """Record a wrong password from `key`."""
        now = time.monotonic() if now is None else now
        with self.lock:
            count, _ = self.failures.get(key, (0, 0.0))
            self.failures[key] = (count + 1, now)
            self.recent.append(now)
            if len(self.failures) > 1000:  # a flood of addresses must not grow memory without end
                oldest = min(self.failures, key=lambda k: self.failures[k][1])
                del self.failures[oldest]

    def success(self, key: str) -> None:
        """`key` signed in: its failures are forgotten."""
        with self.lock:
            self.failures.pop(key, None)


def _address(value: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        address = ipaddress.ip_address(value.strip("[]").split("%")[0])
    except ValueError:
        return None
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        return address.ipv4_mapped
    return address


def is_private(value: str) -> bool:
    """`value` is an IP literal on a private network: loopback, LAN, link-local or Tailscale (CGNAT)."""
    address = _address(value)
    if address is None:
        return False
    return bool(
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or (isinstance(address, ipaddress.IPv4Address) and address in CGNAT)
    )


def peer_allowed(peer: str, allow_public: bool = False) -> bool:
    """A connection from this address may be served: private networks only, unless `allow_public`."""
    return allow_public or is_private(peer)


def host_name(header: str) -> str:
    """The name in a `Host` (or `Origin`) value, without port or brackets, lower case."""
    value = header.strip().lower()
    if value.startswith("["):
        return value[1:].split("]", 1)[0]
    return value.rsplit(":", 1)[0] if value.count(":") == 1 else value


def host_allowed(name: str, extra: Collection[str] = ()) -> bool:
    """May a request addressed to `name` be served?

    Loopback names, any private IP literal (someone typed the address), this computer's own host
    name and `<host name>.local`, and the names given with `--allow-host`. Any other name is
    refused: that is what stops DNS rebinding.
    """
    if name in LOCAL_NAMES or name in extra or is_private(name):
        return True
    machine = socket.gethostname().lower()
    return name in (machine, f"{machine}.local")


def is_local(peer: str, host: str, headers: Mapping[str, str]) -> bool:
    """The request comes from a browser on this computer, not over the network or through a proxy."""
    address = _address(peer)
    if address is None or not address.is_loopback or host not in LOCAL_NAMES:
        return False
    return not any(key.lower().startswith(PROXY_HEADERS) for key in headers)


def lan_addresses() -> list[str]:
    """This computer's private IPv4 addresses, the main one first (what to open on the phone)."""
    found: list[str] = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(
                ("192.0.2.1", 9)
            )  # no packet is sent: it only picks the outgoing interface
            found.append(probe.getsockname()[0])
    except OSError:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            found.append(str(info[4][0]))
    except OSError:
        pass
    unique = dict.fromkeys(ip for ip in found if is_private(ip) and not ip.startswith("127."))
    return list(unique)
