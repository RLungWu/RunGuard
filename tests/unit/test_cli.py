from pathlib import Path

from runguard.cli.main import main

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"


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
