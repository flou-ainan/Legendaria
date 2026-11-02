"""Who may use the server (ADR-026): the password gate, remote limits and the network binding."""

import http.client
import json
import re
import shutil
import subprocess
import threading
from pathlib import Path

import pytest

from legendaria_engine import access
from legendaria_engine import server as server_module
from legendaria_engine.access import Access, AccessError
from legendaria_engine.config import load_config
from legendaria_engine.cues import Cue, CueList
from legendaria_engine.project import Project, project_path
from legendaria_engine.server import make_server

pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="needs ffmpeg and ffprobe"
)

PASSWORD = "correct horse"
PHONE = (
    "192.168.1.7"  # a LAN address as a phone would type it; the test still connects from loopback
)


@pytest.fixture
def video(tmp_path):
    clip = tmp_path / "clip.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=160x120:r=10:d=2",
         "-c:v", "libx264", "-pix_fmt", "yuv420p", str(clip)],
        check=True,
    )  # fmt: skip
    cues = CueList("pop", clip.name, "pt", [Cue(0.2, 0.9, "um")])
    Project.new(clip, 2.0, cues).save(project_path(clip))
    return clip


@pytest.fixture
def settings(tmp_path):
    value = Access(tmp_path / "access.json")
    value.set_password(PASSWORD)
    return value


@pytest.fixture
def running(video, settings):
    """A server with a password, bound to loopback so the test does not open the machine's network."""
    srv = make_server(video, 0, load_config(), settings=settings, host="127.0.0.1")
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()
    srv.server_close()


class Client:
    """One request at a time with full control of the `Host` header (a urllib request cannot fake it)."""

    def __init__(self, srv, remote=True):
        self.port = srv.server_address[1]
        self.host = f"{PHONE}:{self.port}" if remote else f"127.0.0.1:{self.port}"
        self.cookies: dict[str, str] = {}

    def __call__(self, method, path, data=None, headers=None, raw=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=10)
        head = {"Host": self.host, **(headers or {})}
        if self.cookies:
            head["Cookie"] = "; ".join(f"{k}={v}" for k, v in self.cookies.items())
        body = raw if raw is not None else (json.dumps(data).encode() if data is not None else None)
        connection.putrequest(method, path, skip_host=True)
        for key, value in head.items():
            connection.putheader(key, value)
        connection.putheader("Content-Length", str(len(body or b"")))
        connection.endheaders(body)
        response = connection.getresponse()
        payload = response.read()
        for cookie in response.msg.get_all("Set-Cookie") or []:
            name, _, rest = cookie.partition("=")
            value = rest.split(";")[0]
            if "Max-Age=0" in cookie:
                self.cookies.pop(name, None)
            else:
                self.cookies[name] = value
        connection.close()
        try:
            parsed = json.loads(payload)
        except ValueError:
            parsed = payload
        return response.status, response.msg, parsed

    def sign_in(self, password=PASSWORD):
        return self("POST", "/api/login", {"password": password})


def test_without_a_password_the_server_listens_on_this_computer_only(tmp_path):
    srv = make_server(None, 0, load_config(), settings=Access(tmp_path / "none.json"))
    assert srv.server_address[0] == "127.0.0.1"
    srv.server_close()


def test_with_a_password_it_listens_on_the_network_unless_told_not_to(settings):
    srv = make_server(None, 0, load_config(), settings=settings)
    assert srv.server_address[0] == "0.0.0.0"
    srv.server_close()
    settings.settings["lan"] = False
    srv = make_server(None, 0, load_config(), settings=settings)
    assert srv.server_address[0] == "127.0.0.1"
    srv.server_close()


def test_the_network_is_never_opened_without_a_password(tmp_path):
    with pytest.raises(AccessError) as err:
        make_server(None, 0, load_config(), settings=Access(tmp_path / "none.json"), host="0.0.0.0")
    assert err.value.code == "no_password"


def test_this_computer_needs_no_password(running):
    status, _, state = Client(running, remote=False)("GET", "/api/state")
    assert status == 200 and state["video"] == "clip.mp4"


def _routes():
    """Every `/api/...` route the server mentions, so a new one cannot slip past the test."""
    source = Path(server_module.__file__).read_text(encoding="utf-8")
    found = set(re.findall(r'"(/api/[\w/.-]+)"', source))
    return sorted(found | {"/api/does-not-exist", "/api/fonts/x.ttf", "/api/jobs/abc/events"})


def test_every_route_refuses_an_anonymous_remote_client(running):
    public = {("GET", "/api/access"), ("POST", "/api/login"), ("POST", "/api/logout")}
    routes = _routes()
    assert "/api/browse" in routes and "/api/open" in routes and "/api/upload" in routes
    for route in routes:
        for method in ("GET", "POST", "PUT", "DELETE"):
            if (method, route) in public:
                continue
            status, _, body = Client(running)(method, route)
            assert status in (401, 501), (method, route, status)
            if status == 401:
                assert body["code"] == "sign_in"


def test_the_app_files_are_public_but_the_data_is_not(running):
    status, *_ = Client(running)("GET", "/")
    assert status not in (401, 403)  # 200, or 404 when the web build is absent in this checkout
    assert Client(running)("GET", "/api/state")[0] == 401


def test_a_remote_client_is_refused_when_no_password_is_set(video, tmp_path):
    srv = make_server(video, 0, load_config(), settings=Access(tmp_path / "none.json"))
    srv.allow_hosts = {"phone.example"}
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        for path in ("/", "/api/state", "/api/access"):
            status, _, body = Client(srv)("GET", path)
            assert status == 403, path
        status, _, body = Client(srv)("GET", "/api/state", headers={"Host": "phone.example"})
        assert status == 403 and body["code"] == "no_password"
    finally:
        srv.shutdown()
        srv.server_close()


def test_sign_in_gives_a_private_cookie_and_opens_the_api(running):
    client = Client(running)
    status, headers, body = client.sign_in()
    assert status == 200 and body == {"ok": True}
    cookies = " | ".join(headers.get_all("Set-Cookie"))
    assert "legendaria_auth=" in cookies and "HttpOnly" in cookies and "SameSite=Strict" in cookies
    assert "Secure" not in cookies, "plain HTTP: a Secure cookie would never come back"
    assert client("GET", "/api/state")[0] == 200
    assert Client(running)("GET", "/api/state")[0] == 401, "another browser is not signed in"


def test_a_cookie_over_https_is_marked_secure(running):
    status, headers, _ = Client(running)(
        "POST", "/api/login", {"password": PASSWORD}, headers={"X-Forwarded-Proto": "https"}
    )
    assert status == 200 and "; Secure" in " | ".join(headers.get_all("Set-Cookie"))


def test_wrong_password_and_forged_cookies_are_refused(running):
    client = Client(running)
    status, _, body = client.sign_in("not the password")
    assert status == 401 and body["code"] == "wrong_password"
    assert body["error"] == "Wrong password.", "the same answer whatever was wrong"
    client.cookies["legendaria_auth"] = "9999999999.00.deadbeef"
    assert client("GET", "/api/state")[0] == 401


def test_wrong_passwords_are_slowed_down_even_for_the_right_one(running):
    client = Client(running)
    for _ in range(access.LOGIN_FREE_FAILURES):
        assert client.sign_in("nope nope nope")[0] == 401
    status, headers, body = client.sign_in(PASSWORD)
    assert status == 429 and body["code"] == "too_many" and int(headers["Retry-After"]) >= 1
    assert client("GET", "/api/state")[0] == 401


def test_a_signed_in_phone_cannot_browse_or_open_the_computers_files(running, video):
    client = Client(running)
    client.sign_in()
    for method, path, data in [
        ("GET", "/api/browse", None),
        ("GET", "/api/browse?path=/", None),
        ("POST", "/api/open", {"path": str(video)}),
    ]:
        status, _, body = client(method, path, data)
        assert status == 403 and body["code"] == "computer_only", path
    assert Client(running, remote=False)("GET", "/api/browse")[0] == 200


def test_a_signed_in_phone_can_upload_and_use_its_own_video(running, video):
    client = Client(running)
    client.sign_in()
    status, _, state = client("POST", "/api/upload?name=phone.mp4", raw=video.read_bytes())
    assert status == 200 and state["video"] == "phone.mp4"
    assert client("GET", "/api/media", headers={"Range": "bytes=0-9"})[0] == 206
    assert "uploads" in state["path"]


def test_a_proxy_makes_a_loopback_request_remote(running):
    for header in ("X-Forwarded-For", "Tailscale-User-Login", "Forwarded", "CF-Connecting-IP"):
        status, *_ = Client(running, remote=False)("GET", "/api/state", headers={header: "1.2.3.4"})
        assert status == 401, header


def test_an_unknown_host_or_a_foreign_origin_is_refused_even_when_signed_in(running):
    client = Client(running)
    client.sign_in()
    assert client("GET", "/api/state", headers={"Host": "evil.example"})[0] == 403
    assert client("GET", "/api/state", headers={"Origin": "http://evil.example"})[0] == 403
    assert (
        client("GET", "/api/state", headers={"Origin": f"http://{PHONE}:{client.port}"})[0] == 200
    )
    assert client("GET", "/api/state", headers={"Origin": "null"})[0] == 403


def test_tailscale_and_tunnel_names_work_with_the_same_password(running):
    running.allow_hosts = {"flou-desktop.tail1.ts.net"}
    client = Client(running)
    client.host = "flou-desktop.tail1.ts.net"
    headers = {"Tailscale-User-Login": "someone@example.com", "X-Forwarded-Proto": "https"}
    assert client("GET", "/api/state", headers=headers)[0] == 401
    assert client("POST", "/api/login", {"password": PASSWORD}, headers=headers)[0] == 200
    assert client("GET", "/api/state", headers=headers)[0] == 200


def test_a_public_address_is_refused_even_with_the_password(running, monkeypatch):
    client = Client(running)
    client.sign_in()
    monkeypatch.setattr(server_module.Handler, "_peer", lambda self: "8.8.8.8")
    status, _, body = client("GET", "/api/state")
    assert status == 403 and body["error"] == "This address is not allowed."
    running.access.settings["allow_public"] = True
    assert client("GET", "/api/state")[0] == 200


def test_this_computer_can_be_made_to_ask_for_the_password_too(running):
    running.access.settings["require_password_here"] = True
    client = Client(running, remote=False)
    assert client("GET", "/api/state")[0] == 401
    client.sign_in()
    assert client("GET", "/api/state")[0] == 200
    assert client("GET", "/api/browse")[0] == 200, "still this computer: it may browse"


def test_changing_the_password(running, settings):
    client = Client(running)
    client.sign_in()
    old_cookie = dict(client.cookies)
    status, _, body = client(
        "POST", "/api/access/password", {"current": "wrong wrong", "new": "battery staple"}
    )
    assert status == 401 and body["code"] == "wrong_password"
    status, _, body = client("POST", "/api/access/password", {"current": PASSWORD, "new": "short"})
    assert status == 400 and body["code"] == "too_short"
    status, *_ = client(
        "POST", "/api/access/password", {"current": PASSWORD, "new": "battery staple"}
    )
    assert status == 200
    assert client("GET", "/api/state")[0] == 200, "this browser got a fresh session"
    stale = Client(running)
    stale.cookies.update(old_cookie)
    assert stale("GET", "/api/state")[0] == 401, "the other sessions were signed out"
    assert Client(running).sign_in(PASSWORD)[0] == 401
    assert Client(running).sign_in("battery staple")[0] == 200


def test_the_password_changed_on_disk_takes_effect_without_a_restart(running, settings):
    client = Client(running)
    client.sign_in()
    assert client("GET", "/api/state")[0] == 200
    Access(settings.path).set_password("battery staple")  # `flosub auth set` in another terminal
    assert client("GET", "/api/state")[0] == 401
    assert Client(running).sign_in("battery staple")[0] == 200


def test_sign_out(running):
    client = Client(running)
    client.sign_in()
    assert client("POST", "/api/logout")[0] == 200
    assert client("GET", "/api/state")[0] == 401


def test_the_access_status_tells_a_stranger_nothing(running):
    status, _, body = Client(running)("GET", "/api/access")
    assert status == 200
    assert body == {
        "password_set": True,
        "signed_in": False,
        "remote": True,
        "can_browse": False,
        "addresses": [],
    }
    here = Client(running, remote=False)("GET", "/api/access")[2]
    assert here["signed_in"] and here["can_browse"] and not here["remote"]


def test_security_headers(running):
    _, headers, _ = Client(running, remote=False)("GET", "/api/state")
    assert (
        headers["X-Content-Type-Options"] == "nosniff"
        and headers["Referrer-Policy"] == "no-referrer"
    )
