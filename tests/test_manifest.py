import pandas as pd

from jitctx import manifest
from jitctx.manifest import flag_duplicates
from jitctx.tokens import TOKENIZER


def test_duplicate_flags_follow_split_order():
    # chronological order; patch ids: a = train+valid, b = valid+test, c = train+test, d = twice in valid, e = unique
    m = pd.DataFrame({
        "commit": ["t1", "t2", "v1", "v2", "v3", "v4", "x1", "x2", "v5", "n1"],
        "split": ["train", "train", "valid", "valid", "valid", "valid", "test", "test", "valid", "test"],
        "patch_id": ["a", "c", "a", "b", "d", "d", "b", "c", "e", None]})
    f = flag_duplicates(m).set_index("commit")
    assert list(f.index[f.dup_earlier_split]) == ["v1", "x1", "x2"]  # valid copy of train; test copies
    assert not f.loc[["t1", "t2", "v2", "v5", "n1"]].dup_earlier_split.any()  # first split of a group stays
    assert list(f.index[~f.dup_keep]) == ["v4"]  # within-split duplicate: the later one goes
    assert f.loc["v1"].dup_other_split and f.loc["v2"].dup_other_split and not f.loc["v5"].dup_other_split
    assert f.loc["n1"].dup_group_size == 1 and f.loc["v3"].dup_group_size == 2


def test_manifest_records_actual_eligibility_cap_and_tokenizer(tmp_path, monkeypatch):
    def load(_, split):
        return pd.DataFrame([{"project": "synthetic", "commit": "abc", "ds_parent": "parent",
                              "split": split, "la": 1, "ld": 1, "author_time": 1}]), None

    def audit(_, df):
        return [{"commit": row.commit, "exists": True, "parent": "parent", "parent_ok": True,
                 "numstat_ok": True, "n_java_files": 1, "t_c0": 301, "patch_id": "patch"}
                for row in df.itertuples()]

    monkeypatch.setattr(manifest, "load_split", load)
    monkeypatch.setattr(manifest, "audit_commits", audit)
    result, labels = manifest.build(tmp_path, splits=("valid",), cap=300, log=lambda _: None)
    assert result.iloc[0].diff_cap == 300 and result.iloc[0].tokenizer == TOKENIZER
    assert not result.iloc[0].within_cap and not result.iloc[0].eligible and labels.empty
