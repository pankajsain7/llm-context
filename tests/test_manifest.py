import pandas as pd

from jitctx.manifest import flag_duplicates


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
