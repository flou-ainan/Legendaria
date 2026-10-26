import json

import pytest

from legendaria_engine import cli, paths
from legendaria_engine.config import load_config
from legendaria_engine.review import glossary


def run(args, capsys):
    code = cli.main(["--progress", "json", *args])
    out = capsys.readouterr().out
    return code, out


def test_default_active_glossary_and_legacy_migration():
    assert glossary.active_name() == "default"
    paths.config_dir().mkdir(parents=True, exist_ok=True)
    (paths.config_dir() / "glossary.txt").write_text("Poliéster\n", encoding="utf-8")
    assert glossary.list_names() == ["default"]  # old single file became "default"
    assert glossary.global_file() == glossary.library_file("default")
    assert glossary.load().terms == ["Poliéster"]


def test_new_use_add_and_list(capsys):
    assert run(["glossary", "new", "Crochê"], capsys)[0] == 0
    assert run(["glossary", "use", "Crochê"], capsys)[0] == 0
    assert load_config()["review"]["glossary"] == "Crochê"
    assert run(["glossary", "add", "bolsa Beth"], capsys)[0] == 0  # goes to the active one
    assert glossary.load().terms == ["bolsa Beth"]
    _code, out = run(["glossary", "list"], capsys)
    data = json.loads(out)
    assert data["active"] == "Crochê"
    assert [(g["name"], g["active"], g["terms"]) for g in data["glossaries"]] == [
        ("Crochê", True, 1)
    ]


def test_import_export_delete(tmp_path, capsys):
    source = tmp_path / "Canal Mariana.txt"
    source.write_text("Mariana Enacles\nNakley -> Enacles\n", encoding="utf-8")
    assert run(["glossary", "import", str(source)], capsys)[0] == 0
    assert "Canal Mariana" in glossary.list_names()
    assert run(["glossary", "import", str(source)], capsys)[0] == 1  # already exists
    assert run(["glossary", "import", str(source), "--overwrite"], capsys)[0] == 0
    out_file = tmp_path / "shared.txt"
    assert run(["glossary", "export", "Canal Mariana", "--to", str(out_file)], capsys)[0] == 0
    assert "Nakley -> Enacles" in out_file.read_text(encoding="utf-8")
    assert run(["glossary", "delete", "Canal Mariana"], capsys)[0] == 0
    assert "Canal Mariana" not in glossary.list_names()


def test_glossary_option_accepts_names_and_files(tmp_path):
    glossary.create("Termos")
    glossary.add_entry(glossary.library_file("Termos"), "crochê")
    loose = tmp_path / "solto.txt"
    loose.write_text("Poliéster\n", encoding="utf-8")
    merged = glossary.load(["Termos", str(loose)])
    assert merged.terms == ["crochê", "Poliéster"]
    with pytest.raises(FileNotFoundError):
        glossary.load(["nao-existe"])


def test_invalid_names_are_rejected():
    for bad in ("", "../x", "a/b", ".oculto", 'a"b'):
        with pytest.raises(ValueError):
            glossary.safe_name(bad)
    assert glossary.safe_name("  Canal Mariana ") == "Canal Mariana"
