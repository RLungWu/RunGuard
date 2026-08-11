from pathlib import Path

from runguard.cli.main import main

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
MINIMAL_FIXTURE = FIXTURES_DIR / "minimal-comparison.json"
UNPAIRED_FIXTURE = FIXTURES_DIR / "unpaired-comparison.json"


def test_cli_main_output(capsys) -> None:
    main(
        [
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
        ]
    )

    captured = capsys.readouterr()

    assert captured.out == (
        "Comparison: baseline → candidate\n"
        "Metric: val_f1\n"
        "Paired runs: 3\n"
        "Mean paired difference: +0.008333\n"
    )
