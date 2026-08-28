from pathlib import Path

import pytest

from runguard.cli.main import main

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"
LOWER_IS_BETTER_FIXTURE = FIXTURES_DIR / "lower-is-better-experiment.json"
UNPAIRED_FIXTURE = FIXTURES_DIR / "unpaired-comparison.json"


def test_cli_main_output(capsys) -> None:
    main(
        [
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
        ]
    )

    captured = capsys.readouterr()

    assert captured.out == (
        "Comparison: baseline → candidate\n"
        "Metric: val_f1\n"
        "Value source: summary\n"
        "Direction: higher-is-better\n"
        "Paired runs: 1\n"
        "Mean paired difference: +0.020000\n"
        "Median paired difference: +0.020000\n"
        "Positive pairs: 1/1 (100.00%)\n"
    )


def test_cli_reports_unpaired_seed_error(capsys) -> None:
    with pytest.raises(SystemExit) as error:
        main(
            [
                "compare",
                "--input",
                str(UNPAIRED_FIXTURE),
                "--input-format",
                "m0",
                "--group-id",
                "unpaired-experiment",
                "--baseline",
                "baseline",
                "--candidate",
                "candidate",
                "--metric",
                "val_f1",
                "--pair-by",
                "seed",
            ]
        )

    captured = capsys.readouterr()

    assert error.value.code == 2
    assert captured.out == ""
    assert "error: Unpaired seeds; missing candidate seeds: [2]" in captured.err


def test_cli_reports_lower_is_better_improvement(capsys) -> None:
    main(
        [
            "compare",
            "--input",
            str(LOWER_IS_BETTER_FIXTURE),
            "--baseline",
            "baseline",
            "--candidate",
            "candidate",
            "--metric",
            "val_loss",
            "--pair-by",
            "seed",
            "--direction",
            "lower-is-better",
        ]
    )

    captured = capsys.readouterr()

    assert captured.out == (
        "Comparison: baseline → candidate\n"
        "Metric: val_loss\n"
        "Value source: summary\n"
        "Direction: lower-is-better\n"
        "Paired runs: 1\n"
        "Mean paired difference: -0.050000\n"
        "Median paired difference: -0.050000\n"
        "Positive pairs: 1/1 (100.00%)\n"
    )
