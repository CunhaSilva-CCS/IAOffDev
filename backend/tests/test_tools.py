from pathlib import Path

from app.tools import list_directory, read_file, resolve_workspace, search_files, write_file


def test_workspace_roundtrip(tmp_path: Path):
    root = resolve_workspace(str(tmp_path))
    write_file(root, "src/hello.py", "print('oi')\n")
    assert "print('oi')" in read_file(root, "src/hello.py")
    entries = list_directory(root, ".")
    assert any(e["name"] == "src" and e["is_dir"] for e in entries)
    hits = search_files(root, "print")
    assert hits and hits[0]["path"] == "src/hello.py"


def test_blocks_path_escape(tmp_path: Path):
    root = resolve_workspace(str(tmp_path))
    try:
        read_file(root, "../outside.txt")
        assert False, "deveria falhar"
    except ValueError:
        pass
