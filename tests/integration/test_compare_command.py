import subprocess
from pathlib import Path

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"


def test_compare_command_runs_end_to_end() -> None:
    result = subprocess.run(
        [
            "runguard",
            "compare",
            "--input",
            str(CANONICAL_FIXTURE),
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
        "Value source: summary\n"
        "Direction: higher-is-better\n"
        "Paired runs: 1\n"
        "Mean paired difference: +0.020000\n"
        "Median paired difference: +0.020000\n"
        "Positive pairs: 1/1 (100.00%)\n"
    )
    assert result.stderr == ""
