import json
import os
import stat
import sys

import pytest

from legendaria_engine import access
from legendaria_engine.access import Access, AccessError, RateLimiter


@pytest.fixture
def settings(tmp_path):
    return Access(tmp_path / "access.json")


def test_no_password_by_default_and_a_new_one_is_hashed_not_stored(settings):
    assert not settings.has_password and not settings.verify("anything-at-all")
    settings.set_password("correct horse")
    text = settings.path.read_text(encoding="utf-8")
    assert "correct horse" not in text
    data = json.loads(text)
    assert data["password"]["n"] == 2**15 and len(data["password"]["hash"]) == 64
    assert settings.verify("correct horse") and not settings.verify("correct horsf")


@pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")
def test_the_file_is_private(settings):
    settings.set_password("correct horse")
    assert stat.S_IMODE(os.stat(settings.path).st_mode) == 0o600


def test_weak_passwords_are_refused_with_a_code(settings):
    for password, code in [
        ("short", "too_short"),
        ("password", "too_common"),
        ("aaaaaaaaaa", "too_common"),
        ("x" * 200, "too_long"),
    ]:
        with pytest.raises(AccessError) as err:
            settings.set_password(password)
        assert err.value.code == code
    assert not settings.has_password


def test_generated_password_is_typeable_and_accepted():
    for _ in range(50):
        password = access.generate_password()
        assert len(password) == 14 and password.count("-") == 2
        assert set(password.replace("-", "")) <= set(access.ALPHABET)
        assert access.check_password(password) is None
    assert len({access.generate_password() for _ in range(50)}) == 50


def test_session_tokens(settings):
    settings.set_password("correct horse")
    token = settings.make_token(now=1000.0)
    assert settings.check_token(token, now=1001.0)
    assert not settings.check_token(token, now=1000.0 + 31 * 86400), "expired"
    payload, _, signature = token.rpartition(".")
    assert not settings.check_token(payload + "." + "0" * 64, now=1001.0), "wrong signature"
    assert not settings.check_token(
        payload.replace(payload[:4], "9999", 1) + "." + signature, now=1001.0
    ), "tampered expiry"
    for junk in ("", "x", "a.b.c", "1.2.3.4"):
        assert not settings.check_token(junk, now=1001.0)


def test_changing_the_password_signs_everyone_out(settings):
    settings.set_password("correct horse")
    token = settings.make_token()
    settings.set_password("battery staple")
    assert not settings.check_token(token)
    assert settings.check_token(settings.make_token())


def test_no_password_means_no_valid_session(settings):
    settings.set_password("correct horse")
    token = settings.make_token()
    settings.clear_password()
    assert not settings.check_token(token) and not settings.has_password


def test_another_process_changing_the_file_is_seen(tmp_path):
    running = Access(tmp_path / "access.json")
    assert not running.has_password
    Access(tmp_path / "access.json").set_password("correct horse")
    running.refresh()
    assert running.has_password and running.verify("correct horse")
    Access(tmp_path / "access.json").clear_password()
    running.refresh()
    assert not running.has_password


def test_a_broken_file_means_local_only_not_a_crash(tmp_path):
    path = tmp_path / "access.json"
    path.write_text("{not json", encoding="utf-8")
    assert not Access(path).has_password
    path.write_text(json.dumps({"password": {"n": 1}, "lan": "yes"}), encoding="utf-8")
    broken = Access(path)
    assert not broken.has_password and broken.settings["lan"] is True


def test_switches_survive_a_round_trip(settings):
    settings.settings["require_password_here"] = True
    settings.set_password("correct horse")
    again = Access(settings.path)
    assert again.settings["require_password_here"] is True and again.verify("correct horse")


def test_rate_limit_grows_and_forgets():
    limit = RateLimiter()
    for i in range(4):
        limit.fail("a", now=100.0 + i)
    assert limit.wait("a", now=104.0) == 0, "the first failures are free"
    limit.fail("a", now=104.0)
    assert limit.wait("a", now=104.0) == pytest.approx(5.0)
    limit.fail("a", now=110.0)
    assert limit.wait("a", now=110.0) == pytest.approx(10.0)
    assert limit.wait("a", now=121.0) == 0
    assert limit.wait("b", now=110.0) == 0, "another address is not slowed down"
    for i in range(20):
        limit.fail("a", now=200.0 + i)
    assert limit.wait("a", now=219.0) == pytest.approx(access.LOGIN_MAX_DELAY)
    limit.success("a")
    assert limit.wait("a", now=220.0) == 0


def test_many_addresses_together_lock_everyone():
    limit = RateLimiter()
    for i in range(access.GLOBAL_FAILURES):
        limit.fail(f"10.0.0.{i}", now=100.0)
    assert limit.wait("10.9.9.9", now=101.0) == pytest.approx(access.GLOBAL_WINDOW - 1.0)
    assert limit.wait("10.9.9.9", now=100.0 + access.GLOBAL_WINDOW + 1) == 0


def test_the_failure_table_has_a_limit():
    limit = RateLimiter()
    for i in range(1500):
        limit.fail(f"host-{i}", now=float(i))
    assert len(limit.failures) <= 1001


@pytest.mark.parametrize(
    "peer, ok",
    [
        ("127.0.0.1", True), ("::1", True), ("192.168.0.20", True), ("10.1.2.3", True),
        ("172.16.5.5", True), ("100.79.129.119", True), ("169.254.1.1", True), ("fe80::1", True),
        ("fd00::1", True), ("::ffff:192.168.1.5", True),
        ("8.8.8.8", False), ("1.1.1.1", False), ("100.128.0.1", False), ("2001:4860:4860::8888", False),
        ("::ffff:8.8.8.8", False), ("not-an-ip", False), ("", False),
    ],
)  # fmt: skip
def test_only_private_peers_connect(peer, ok):
    assert access.peer_allowed(peer) is ok
    assert access.peer_allowed(peer, allow_public=True) is True


def test_local_means_loopback_peer_loopback_host_and_no_proxy():
    local = access.is_local
    assert local("127.0.0.1", "127.0.0.1", {"Host": "x"})
    assert local("::1", "localhost", {})
    assert local("::ffff:127.0.0.1", "localhost", {})
    assert not local("192.168.0.20", "127.0.0.1", {}), "a phone cannot say it is local"
    assert not local("127.0.0.1", "192.168.0.5", {}), "someone using this computer's LAN address"
    assert not local("127.0.0.1", "mymachine.tail1234.ts.net", {})
    for header in (
        "X-Forwarded-For",
        "Forwarded",
        "X-Real-IP",
        "Tailscale-User-Login",
        "CF-Connecting-IP",
        "Via",
        "x-forwarded-proto",
    ):
        assert not local("127.0.0.1", "127.0.0.1", {header: "1.2.3.4"}), header


@pytest.mark.parametrize(
    "header, name",
    [
        ("127.0.0.1:8765", "127.0.0.1"),
        ("LocalHost:80", "localhost"),
        ("[::1]:8765", "::1"),
        ("[::1]", "::1"),
        ("::1", "::1"),
        ("Phone.local", "phone.local"),
    ],
)
def test_host_name(header, name):
    assert access.host_name(header) == name


def test_host_allowlist(monkeypatch):
    monkeypatch.setattr(access.socket, "gethostname", lambda: "Flou-Desktop")
    allowed = access.host_allowed
    for name in (
        "127.0.0.1",
        "localhost",
        "192.168.1.7",
        "100.79.129.119",
        "flou-desktop",
        "flou-desktop.local",
    ):
        assert allowed(name), name
    for name in ("evil.example", "8.8.8.8", "192.168.1.7.evil.example", "other.local", ""):
        assert not allowed(name), name
    assert allowed("flou-desktop.tail1.ts.net", {"flou-desktop.tail1.ts.net"})


def test_lan_addresses_are_private_and_not_loopback():
    for address in access.lan_addresses():
        assert access.is_private(address) and not address.startswith("127.")
