import json
import shutil
import subprocess
import threading
import urllib.error
import urllib.request

import pytest

from legendaria_engine.config import load_config
from legendaria_engine.cues import Cue, CueList
from legendaria_engine.project import Project, project_path

pytestmark = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe")), reason="needs ffmpeg and ffprobe"
)


@pytest.fixture
def server(tmp_path):
    from legendaria_engine.server import make_server

    video = tmp_path / "clip.mp4"
    subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-f",
            "lavfi",
            "-i",
            "testsrc=s=160x120:r=10:d=4",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(video),
        ],
        check=True,
    )
    cues = CueList("pop", video.name, "pt", [Cue(0.5, 1.5, "um"), Cue(2.5, 3.5, "dois")])
    Project.new(video, 4.0, cues).save(project_path(video))
    srv = make_server(video, 0, load_config())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv, f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def call(url, method="GET", data=None, headers=None):
    body = json.dumps(data).encode() if data is not None else None
    request = urllib.request.Request(url, body, headers or {}, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, dict(response.headers), response.read()


def test_state_and_isolation_headers(server):
    _, base = server
    status, headers, body = call(base + "/api/state")
    state = json.loads(body)
    assert status == 200 and headers["Cross-Origin-Embedder-Policy"] == "require-corp"
    assert state["video"] == "clip.mp4" and len(state["project"]["cues"]) == 2
    assert state["media"]["width"] == 160


def test_media_range(server):
    _, base = server
    status, headers, body = call(base + "/api/media", headers={"Range": "bytes=0-99"})
    assert status == 206 and len(body) == 100 and headers["Content-Range"].startswith("bytes 0-99/")


def test_foreign_origin_is_rejected(server):
    _, base = server
    with pytest.raises(urllib.error.HTTPError) as err:
        call(base + "/api/state", headers={"Origin": "https://evil.example"})
    assert err.value.code == 403


def test_save_cut_and_export_srt(server, tmp_path):
    _, base = server
    project = json.loads(call(base + "/api/state")[2])["project"]
    project["keep"] = [[0, 2], [3, 4]]
    _, _, saved = call(base + "/api/project", "PUT", project)
    assert json.loads(saved)["keep"] == [[0, 2], [3, 4]]
    job = json.loads(call(base + "/api/export", "POST", {"format": "srt"})[2])["job"]
    _, _, stream = call(f"{base}/api/jobs/{job}/events")
    events = [
        json.loads(line[6:]) for line in stream.decode().splitlines() if line.startswith("data:")
    ]
    assert events[-1]["event"] == "done", events
    srt = (tmp_path / "clip.edited.srt").read_text(encoding="utf-8")
    # "dois" (2.5-3.5) loses 2.5-3 to the cut and moves back by 1 s: 2.0-2.5
    assert "00:00:02,000 --> 00:00:02,500\ndois" in srt


def test_invalid_project_is_rejected(server):
    _, base = server
    with pytest.raises(urllib.error.HTTPError) as err:
        call(base + "/api/project", "PUT", {"format": "nope"})
    assert err.value.code == 400


def test_preview_ass_is_in_source_time(server):
    _, base = server
    text = call(base + "/api/preview.ass")[2].decode()
    assert "Dialogue: 0,0:00:02.50,0:00:03.50" in text


def test_look_changes_the_preview_and_bundled_fonts_are_served(server):
    _, base = server
    state = json.loads(call(base + "/api/state")[2])
    assert "Anton" in [f["family"] for f in state["fonts"]] and state["base"]["y"] > 0
    project = state["project"] | {"look": {"font": "Anton", "size": 2.0, "y": 0.9}}
    call(base + "/api/project", "PUT", project)
    text = call(base + "/api/preview.ass")[2].decode()
    assert (
        "Style: Default,Anton," in text and "\\pos(80,12)" in text
    )  # 160x120: x centre, y near the top
    status, _, body = call(base + "/api/font")
    assert status == 200 and len(body) > 10000
    assert call(base + "/api/fonts/Anton.ttf")[0] == 200
    with pytest.raises(urllib.error.HTTPError) as err:
        call(base + "/api/fonts/passwd.ttf")
    assert err.value.code == 404


def test_peaks_are_a_curve_per_100th_of_a_second(server):
    _, base = server
    data = json.loads(call(base + "/api/peaks")[2])
    assert data["per_sec"] == 100 and abs(len(data["peaks"]) - 400) <= 2
    assert all(0 <= v <= 1 for v in data["peaks"])


def test_review_suggests_glossary_fixes_in_the_saved_cues(server, tmp_path):
    _, base = server
    (tmp_path / "legendaria-glossary.txt").write_text("um -> UM!\n", encoding="utf-8")
    suggestions = json.loads(call(base + "/api/review")[2])["suggestions"]
    assert [(s["cue"], s["before"], s["after"]) for s in suggestions] == [(0, "um", "UM!")]


@pytest.fixture
def empty_server():
    from legendaria_engine.server import make_server

    srv = make_server(None, 0, load_config())
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{srv.server_address[1]}"
    srv.shutdown()
    srv.server_close()


def test_starts_without_a_video_and_offers_choices(empty_server):
    state = json.loads(call(empty_server + "/api/state")[2])
    assert state["video"] is None and "small" in [m["name"] for m in state["models"]]
    assert {"code": "pt", "name": "Português (Brasil / Portugal)"} in state["languages"]
    with pytest.raises(urllib.error.HTTPError) as err:
        call(empty_server + "/api/peaks")
    assert err.value.code == 409


def test_browse_lists_folders_and_media_only(empty_server, tmp_path):
    (tmp_path / "sub").mkdir()
    (tmp_path / "a.mp4").write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("no")
    (tmp_path / ".hidden.mp4").write_bytes(b"x")
    data = json.loads(
        call(empty_server + "/api/browse?path=" + str(tmp_path).replace(" ", "%20"))[2]
    )
    assert [(e["name"], e["dir"]) for e in data["entries"]] == [("sub", True), ("a.mp4", False)]


def test_open_by_path_and_by_upload(empty_server, tmp_path):
    video = tmp_path / "v.mp4"
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=s=64x48:r=10:d=1", str(video)],
        check=True,
    )
    state = json.loads(call(empty_server + "/api/open", "POST", {"path": str(video)})[2])
    assert state["video"] == "v.mp4" and state["project"] is None
    with pytest.raises(urllib.error.HTTPError) as err:
        call(empty_server + "/api/open", "POST", {"path": str(tmp_path / "missing.mp4")})
    assert err.value.code == 400
    # the project file opens its video, and the browser lists it
    again = json.loads(
        call(empty_server + "/api/open", "POST", {"path": str(video) + ".legendaria.json"})[2]
    )
    assert again["video"] == "v.mp4"
    (tmp_path / "v.mp4.legendaria.json").write_text("{}", encoding="utf-8")
    listing = json.loads(call(empty_server + f"/api/browse?path={tmp_path}")[2])
    assert "v.mp4.legendaria.json" in [e["name"] for e in listing["entries"]]
    request = urllib.request.Request(
        empty_server + "/api/upload?name=dropped.mp4", video.read_bytes(), method="POST"
    )
    uploaded = json.loads(urllib.request.urlopen(request, timeout=10).read())
    assert uploaded["video"] == "dropped.mp4"


def test_glossary_add_import_export(empty_server):
    state = json.loads(call(empty_server + "/api/glossary")[2])
    assert state["active"] == "default" and state["text"] == ""
    added = json.loads(
        call(empty_server + "/api/glossary/add", "POST", {"entry": "polieste -> poliéster"})[2]
    )
    assert added["added"] is True
    again = json.loads(
        call(empty_server + "/api/glossary/add", "POST", {"entry": "polieste -> poliéster"})[2]
    )
    assert again["added"] is False
    imported = json.loads(
        call(
            empty_server + "/api/glossary/import",
            "POST",
            {"name": "Mariana", "text": "Beth\n# c\nbolsa bet -> bolsa Beth\n"},
        )[2]
    )
    assert imported["active"] == "Mariana" and "bolsa bet -> bolsa Beth" in imported["text"]
    exported = call(empty_server + "/api/glossary/export?name=Mariana")
    assert "attachment" in exported[1]["Content-Disposition"] and b"Beth" in exported[2]
