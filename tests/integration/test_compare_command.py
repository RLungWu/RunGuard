import subprocess
from pathlib import Path

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
MINIMAL_FIXTURE = FIXTURES_DIR / "minimal-comparison.json"


def test_compare_command_runs_end_to_end() -> None:
    result = subprocess.run(
        [
            "runguard",
            "compare",
            "--input",
            str(MINIMAL_FIXTURE),
            "--baseline",
            "baseline",
            "--candidate",
            "candidate",
            "--metric",
            "val_f1",
            "--pair-by",
            "seed",
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == (
        "Comparison: baseline → candidate\n"
        "Metric: val_f1\n"
        "Paired runs: 3\n"
        "Mean paired difference: +0.008333\n"
    )
    assert result.stderr == ""
