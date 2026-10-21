import csv
import json

import pytest

from jitctx import cli
from jitctx.conditions import Config
from jitctx.tokens import TOKENIZER


def manifest_row(**changes):
    return {"project": "synthetic", "split": "valid", "commit": "abc", "parent": "parent",
            "eligible": "True", "t_c0": "100", "diff_cap": "16000", "tokenizer": TOKENIZER, **changes}


def write_manifest(path, row):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


@pytest.mark.parametrize("changes", [{"diff_cap": "1000"}, {"tokenizer": "cl100k_base"},
                                     {"diff_cap": ""}, {"tokenizer": ""}, {"t_c0": "16001"},
                                     {"t_c0": "nan"}])
def test_manifest_config_mismatch_rejected_before_output_is_opened(tmp_path, changes):
    source, out = tmp_path / "manifest.csv", tmp_path / "contexts.jsonl"
    write_manifest(source, manifest_row(**changes))
    # An existing output is protected too, rather than being truncated by a rejected request.
    out.write_text("keep previous output", encoding="utf-8")
    with pytest.raises(SystemExit):
        cli.main(["make-contexts", "--manifest", str(source), "--repos", str(tmp_path), "--out", str(out)])
    assert out.read_text(encoding="utf-8") == "keep previous output"


def test_legacy_manifest_is_rejected():
    row = manifest_row()
    del row["diff_cap"]
    with pytest.raises(ValueError, match="rebuild"):
        cli.validate_manifest([row], Config())


def test_stale_token_count_is_recorded_as_error_without_context(tmp_path, monkeypatch):
    source, out = tmp_path / "manifest.csv", tmp_path / "contexts.jsonl"
    write_manifest(source, manifest_row())
    monkeypatch.setattr(cli.gitrepo, "head_revision", lambda _: "synthetic")
    monkeypatch.setattr(cli, "build_commit", lambda *_: [{"t_c0": 99, "condition": "C0", "prompt": "unsafe"}])
    cli.main(["make-contexts", "--manifest", str(source), "--repos", str(tmp_path), "--out", str(out)])
    record = json.loads(out.read_text(encoding="utf-8"))
    assert record["status"] == "error" and record["condition"] == "ALL"
    assert "disagrees with manifest" in record["error"] and "prompt" not in record


def test_test_split_is_locked_before_any_manifest_read(tmp_path):
    with pytest.raises(SystemExit, match="Gate 4"):
        cli.main(["make-contexts", "--manifest", str(tmp_path / "absent.csv"), "--split", "test",
                  "--repos", str(tmp_path), "--out", str(tmp_path / "out.jsonl")])


def test_build_manifest_uses_config_cap(tmp_path, monkeypatch):
    from jitctx import manifest

    config = tmp_path / "config.toml"
    config.write_text('[contexts]\ndiff_cap = 1234\n', encoding="utf-8")
    seen = []

    def build(root, splits, cap, log):
        import pandas as pd

        seen.append(cap)
        return pd.DataFrame(columns=["split"]), pd.DataFrame()

    monkeypatch.setattr(manifest, "build", build)
    args = ["build-manifest", "--root", str(tmp_path), "--config", str(config), "--splits", "valid",
            "--out", str(tmp_path / "manifest.csv")]
    cli.main(args)
    cli.main([*args, "--cap", "2345"])
    assert seen == [1234, 2345]
