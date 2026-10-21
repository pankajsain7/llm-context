"""Synthetic tests of chronology assignment and the train/validation access boundary."""

from pathlib import Path

import pandas as pd
import pytest
import split_analysis as sa


def metadata():
    # Shared SHAs across projects and tied times must not mix identities or depend on labels.
    return pd.DataFrame({
        "project": ["p", "p", "p", "p", "q", "q"],
        "commit": ["d", "a", "c", "b", "a", "d"],
        "t": [3, 1, 2, 1, 1, 2],
        "split": ["train", "valid", "train", "train", "train", "valid"],
        "y": [0, 1, 0, 0, 0, 1],
    })


def test_chronological_repartition_preserves_sizes_and_uses_time_then_sha():
    original = metadata()
    result = sa.chronological_train_valid(original)
    assert result.groupby("project").strict_tv.value_counts().to_dict() == (
        original.groupby("project").split.value_counts().to_dict())
    assert list(result[result.project == "p"].commit) == ["a", "b", "c", "d"]
    assert list(result[result.strict_tv == "valid"].commit) == ["d", "d"]
    assert "strict_tv" not in original  # caller-owned feature/metadata rows are unchanged
    flipped = sa.chronological_train_valid(original.assign(y=1 - original.y))
    pd.testing.assert_series_equal(result.strict_tv, flipped.strict_tv)


def test_feature_repartition_moves_actual_rows_and_preserves_project_identity():
    d = metadata()
    raw = {s: d[d.split == s].rename(columns={"commit": "commit_hash"}).copy()
           for s in ("train", "valid")}
    new = sa.chronological_features(raw, sa.chronological_train_valid(d))
    assert list(zip(new["valid"].project, new["valid"].commit_hash)) == [("p", "d"), ("q", "d")]
    assert ("p", "a") in set(zip(new["train"].project, new["train"].commit_hash))
    assert new["valid"].y.tolist() == [0, 1]
    assert len(new["train"]) + len(new["valid"]) == len(d)


def test_feature_repartition_rejects_mismatched_identity():
    d = metadata()
    raw = {s: d[d.split == s].rename(columns={"commit": "commit_hash"}).copy()
           for s in ("train", "valid")}
    raw["valid"].loc[raw["valid"].index[0], "commit_hash"] = "unknown"
    with pytest.raises(ValueError, match="identities"):
        sa.chronological_features(raw, sa.chronological_train_valid(d))


def test_chronology_rejects_duplicate_and_test_records():
    d = metadata()
    with pytest.raises(ValueError, match="Duplicate"):
        sa.chronological_train_valid(pd.concat([d, d.iloc[:1]]))
    with pytest.raises(ValueError, match="Only train and valid"):
        sa.chronological_train_valid(d.assign(split="test"))


@pytest.mark.parametrize("loader", [sa.load, sa._features])
def test_test_pickle_is_rejected_before_file_access(loader):
    # An absent root would cause FileNotFoundError if file access happened first.
    with pytest.raises(ValueError, match="Only train and valid"):
        loader(Path("does-not-exist"), "test")
