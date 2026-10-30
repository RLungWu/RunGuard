import json
from pathlib import Path

import pytest

from runguard.cli.main import main

FIXTURES_DIR = Path(__file__).parents[1] / "fixtures"
CANONICAL_FIXTURE = FIXTURES_DIR / "canonical-experiment.json"
LOWER_IS_BETTER_FIXTURE = FIXTURES_DIR / "lower-is-better-experiment.json"
UNPAIRED_FIXTURE = FIXTURES_DIR / "unpaired-comparison.json"
BENCHMARKS_DIR = FIXTURES_DIR / "benchmarks"
CHECKPOINT_FIXTURE = BENCHMARKS_DIR / "checkpoint-dependent.json"
STABLE_FIXTURE = BENCHMARKS_DIR / "stable-small-improvement.json"


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
        "\n"
        "Evidence (direction-aware improvement):\n"
        "Mean improvement: +0.020000\n"
        "Median improvement: +0.020000\n"
        "Mean minus median: +0.000000\n"
        "Bootstrap interval: insufficient evidence (fewer-than-two-pairs)\n"
        "Effect size (d_z): insufficient evidence (fewer-than-two-pairs)\n"
        "Largest leave-one-pair-out change: insufficient evidence "
        "(fewer-than-two-pairs)\n"
        "\n"
        "Pairs:\n"
        "- seed 1: baseline-seed-1 → candidate-seed-1: improvement +0.020000\n"
        "\n"
        "Limitations:\n"
        "- Seed pairing does not verify dataset, code revision, or configuration "
        "comparability between baseline and candidate runs.\n"
        "- Percentile bootstrap intervals can be discrete or unstable with few "
        "paired observations.\n"
        "- Leave-one-pair-out changes are descriptive influence measurements; they "
        "do not label outliers or establish that one seed dominates the result.\n"
        "- Summary metrics are source-reported values; no checkpoint selection "
        "policy was applied.\n"
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

    assert captured.out.startswith(
        "Comparison: baseline → candidate\n"
        "Metric: val_loss\n"
        "Value source: summary\n"
        "Direction: lower-is-better\n"
        "Paired runs: 1\n"
        "Mean paired difference: -0.050000\n"
        "Median paired difference: -0.050000\n"
        "Positive pairs: 1/1 (100.00%)\n"
    )
    # The raw difference is negative, but the direction-aware improvement is not.
    assert "Mean improvement: +0.050000\n" in captured.out


def _compare_args(path: Path, metric: str, *extra: str) -> list[str]:
    return [
        "compare",
        "--input",
        str(path),
        "--baseline",
        "baseline",
        "--candidate",
        "candidate",
        "--metric",
        metric,
        "--pair-by",
        "seed",
        *extra,
    ]


def test_cli_reports_bootstrap_parameters_and_influence(capsys) -> None:
    main(_compare_args(STABLE_FIXTURE, "val_f1", "--random-seed", "11"))

    out = capsys.readouterr().out

    assert "95% percentile bootstrap interval: [+0." in out
    assert "(10000 resamples, random seed 11)" in out
    assert "Effect size (d_z): +" in out
    assert "Largest leave-one-pair-out change: " in out
    assert "at seed 6 " in out
    assert "- seed 10: baseline-seed-10 → candidate-seed-10: " in out


def test_cli_selects_checkpoint_and_shows_steps(capsys) -> None:
    main(
        _compare_args(
            CHECKPOINT_FIXTURE,
            "val_loss",
            "--direction",
            "lower-is-better",
            "--value-source",
            "history",
            "--checkpoint",
            "final",
        )
    )

    out = capsys.readouterr().out

    assert "Value source: history\nCheckpoint policy: final\n" in out
    assert "- seed 1: baseline-seed-1 @ step 30 → candidate-seed-1 @ step 30: " in out
    assert "Positive pairs: 0/10 (0.00%)" in out
    assert "'final' checkpoint policy" in out


@pytest.mark.parametrize(
    ("extra", "message"),
    [
        (["--checkpoint", "best"], "do not take a checkpoint policy"),
        (["--value-source", "history"], "require a checkpoint policy"),
        (["--resamples", "0"], "Invalid bootstrap configuration"),
    ],
)
def test_cli_rejects_invalid_evidence_options(
    capsys, extra: list[str], message: str
) -> None:
    with pytest.raises(SystemExit) as error:
        main(_compare_args(STABLE_FIXTURE, "val_f1", *extra))

    captured = capsys.readouterr()
    assert error.value.code == 2
    assert captured.out == ""
    assert message in captured.err


def test_cli_json_output_is_marked_experimental(capsys) -> None:
    main(
        _compare_args(
            CHECKPOINT_FIXTURE,
            "val_loss",
            "--direction",
            "lower-is-better",
            "--value-source",
            "history",
            "--checkpoint",
            "best",
            "--format",
            "json",
            "--random-seed",
            "5",
            "--resamples",
            "200",
            "--confidence-level",
            "0.9",
        )
    )

    document = json.loads(capsys.readouterr().out)

    assert document["format"] == "runguard.paired-evidence"
    assert document["stability"] == "experimental"
    evidence = document["evidence"]
    assert evidence["value_source"] == "history"
    assert evidence["checkpoint_policy"] == "best"
    assert evidence["sample_size"] == 10
    assert evidence["bootstrap"]["config"] == {
        "confidence_level": 0.9,
        "resamples": 200,
        "random_seed": 5,
        "method": "percentile",
    }
    assert {(p["baseline_step"], p["candidate_step"]) for p in evidence["pairs"]} == {
        (30, 20)
    }
    conclusion_fields = {"decision", "severity", "verdict", "finding"}
    assert not (set(document) | set(evidence)) & conclusion_fields
