from pathlib import Path

import pytest

from runguard.comparison.minimal import load_runs, mean_difference, paired_differences

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
MINIMAL_FIXTURE = FIXTURES_DIR / "minimal-comparison.json"
UNPAIRED_FIXTURE = FIXTURES_DIR / "unpaired-comparison.json"


def test_load_runs() -> None:
    data = load_runs(MINIMAL_FIXTURE)

    assert data["format_version"] == 1
    assert len(data["runs"]) == 6
    assert data["runs"][0]["id"] == "baseline-seed-1"


def test_paired_differences() -> None:

    differences = paired_differences(MINIMAL_FIXTURE)

    assert differences == pytest.approx([0.02, -0.005, 0.01])


def test_mean_difference() -> None:
    mean = mean_difference(MINIMAL_FIXTURE)

    assert mean == pytest.approx(0.008333333333333333)


def test_paired_differences_rejects_unpaired_seeds() -> None:
    with pytest.raises(ValueError, match="seeds do not match"):
        paired_differences(UNPAIRED_FIXTURE)
