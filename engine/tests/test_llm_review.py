"""LLM reviewer against a fake OpenAI-compatible server (no network, no GPU)."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import ClassVar

import pytest

from legendaria_engine import cli
from legendaria_engine.events import JsonReporter
from legendaria_engine.review import llm, reviewer
from legendaria_engine.review.glossary import Glossary
from legendaria_engine.schema import Segment, Transcript, Word


def seg(*items):
    ws = [Word(s, e, w, p) for w, s, e, p in items]
    return Segment(ws[0].start, ws[-1].end, " ".join(w.word.strip() for w in ws), ws)


TRANSCRIPT = Transcript(
    "v.mp4",
    "pt",
    10.0,
    "small",
    "cpu",
    [
        seg(
            (" Eu", 0, 0.2, 0.9),
            (" sou", 0.2, 0.4, 0.9),
            (" Mariana", 0.4, 0.8, 0.8),
            (" Nakley.", 0.8, 1.2, 0.2),
        ),
        seg(
            (" Uma", 1.3, 1.5, 0.9),
            (" forma", 1.5, 1.8, 0.9),
            (" perfeito", 1.8, 2.3, 0.95),
            (" e", 2.3, 2.4, 0.9),
            (" rápida.", 2.4, 2.9, 0.9),
        ),
        seg((" fio", 3.0, 3.3, 0.9), (" de", 3.3, 3.4, 0.9), (" polieste.", 3.4, 4.0, 0.44)),
    ],
)

# What the fake model answers: fixes the name and the term, "corrects" grammar, drops a word.
ANSWER = {
    "1": "Eu sou Mariana Enacles.",
    "2": "Uma forma perfeita rápida.",
    "3": "fio de poliéster.",
}


class FakeServer(BaseHTTPRequestHandler):
    answers: ClassVar[list] = []
    prompts: ClassVar[list] = []

    def log_message(self, *args):
        pass

    def _send(self, payload, code=200):
        body = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"data": [{"id": "embed-model"}, {"id": "fake-chat"}]})

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        body = json.loads(self.rfile.read(length))
        FakeServer.prompts.append(body["messages"][0]["content"])
        content = FakeServer.answers.pop(0) if FakeServer.answers else json.dumps({"fixes": ANSWER})
        self._send({"choices": [{"message": {"content": content}}]})


@pytest.fixture
def server():
    FakeServer.answers, FakeServer.prompts = [], []
    httpd = HTTPServer(("127.0.0.1", 0), FakeServer)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}/v1"
    httpd.shutdown()


def client_for(url):
    return llm.LLMClient(llm.LLMSettings(provider="test", base_url=url, model=""))


def test_picks_first_chat_model(server):
    assert client_for(server).pick_model() == "fake-chat"


def test_guard_keeps_real_fixes_and_rejects_rewrites(server, capsys):
    glossary = Glossary(terms=["Mariana Enacles", "Poliéster"])
    found, rejected = reviewer.review(TRANSCRIPT, client_for(server), glossary, JsonReporter())
    pairs = [(s.before, s.after) for s in found]
    assert ("Nakley.", "Enacles.") in pairs
    assert ("polieste.", "poliéster.") in pairs
    assert all("perfeit" not in s.before for s in found)  # confident word: grammar fix rejected
    assert all(s.after for s in found)  # "perfeito e" → "perfeita": one block, rejected
    assert rejected == 1
    assert all(s.source == "llm" for s in found)
    prompt = FakeServer.prompts[0]
    assert "[[Nakley.]]" in prompt and "Mariana Enacles" in prompt


def test_missing_fixes_object_skips_the_batch(server, capsys):
    FakeServer.answers = [json.dumps({"lines": ["only one"]})]
    found, _ = reviewer.review(TRANSCRIPT, client_for(server), Glossary(), JsonReporter())
    assert found == []
    assert "skipped" in capsys.readouterr().out


def test_only_listed_lines_change_and_bad_keys_are_ignored():
    answer = {"fixes": {"2": "b fixed", "9": "out of range", "x": "bad key"}}
    assert reviewer.fixes_by_line(answer, 3) == {1: "b fixed"}
    assert reviewer.fixes_by_line({"fixes": {}}, 3) == {}


def test_parse_json_with_code_fence():
    assert llm.parse_json_object('```json\n{"lines": ["a"]}\n```') == {"lines": ["a"]}
    with pytest.raises(llm.LLMError):
        llm.parse_json_object("no json here")


def test_unreachable_server_in_auto_mode_degrades(tmp_path, capsys):
    source = tmp_path / "v.json"
    TRANSCRIPT.save(source)
    (tmp_path / "legendaria-glossary.txt").write_text("Poliéster\n", encoding="utf-8")
    from legendaria_engine.config import update_user_config

    update_user_config({"review": {"llm": {"enabled": "auto"}}})  # experimental: opt in
    code = cli.main(
        ["--progress", "json", "review", str(source), "--base-url", "http://127.0.0.1:9/v1"]
    )
    out = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0
    assert any(e["event"] == "warning" and "unavailable" in e["message"] for e in out)
    assert out[-1]["suggestions"] == 1  # the glossary still found "polieste"


def test_review_cli_with_fake_llm(server, tmp_path, capsys):
    source = tmp_path / "v.json"
    TRANSCRIPT.save(source)
    (tmp_path / "legendaria-glossary.txt").write_text("Mariana Enacles\n", encoding="utf-8")
    code = cli.main(["--progress", "json", "review", str(source), "--llm", "--base-url", server])
    out = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert code == 0
    suggestions = {e["source"]: e["after"] for e in out if e["event"] == "suggestion"}
    # The glossary (layer 2) already fixes the name, so the LLM's duplicate is dropped;
    # the LLM adds "poliéster", and its grammar change ("perfeita") is rejected.
    assert suggestions == {"glossary": "Mariana Enacles.", "llm": "poliéster."}
    done = out[-1]
    assert done["llm_rejected"] == 1 and done["suggestions"] == 2


def test_llm_check_reports_models(server, capsys):
    assert cli.main(["llm", "check", "--base-url", server]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ok"] and result["model"] == "fake-chat" and "embed-model" in result["models"]


def test_guard_rejects_invented_or_translated_words():
    unsure = [reviewer.Unit(0, 1, "cenoura.", 0.3)]
    glossary = Glossary(terms=["bolsa Beth"])
    assert reviewer.guard(unsure, ["bolsa", "Beth."], glossary, 0.5) is None  # invented
    assert reviewer.guard([reviewer.Unit(0, 1, "fake.", 0.2)], ["falso."], Glossary(), 0.5) is None
    assert reviewer.guard([reviewer.Unit(0, 1, "Nakley.", 0.2)], ["Enacles."], Glossary(), 0.5)
    assert reviewer.guard([reviewer.Unit(0, 1, "voce", 0.9)], ["você"], Glossary(), 0.5)


def test_llm_is_off_by_default():
    from legendaria_engine.config import load_config

    config = load_config()
    assert config["review"]["llm"]["enabled"] is False
    assert cli.wants_llm(config, None) is False
