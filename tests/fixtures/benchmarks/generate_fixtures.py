"""Regenerate the M3 benchmark fixtures in this directory.

Run from the repository root:

    .venv/bin/python tests/fixtures/benchmarks/generate_fixtures.py

Candidate values are the baseline value plus a designed per-seed improvement,
given in units of 1e-3 so that tests can compute exact reference expectations.
The scenario designs are documented in README.md.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent
SEEDS = list(range(1, 11))
BASELINE_F1 = [0.800, 0.805, 0.795, 0.810, 0.790, 0.800, 0.805, 0.795, 0.802, 0.798]
BASE_CONFIG: dict[str, object] = {
    "lr": 0.001,
    "optimizer": "adam",
    "dataset": "imagenet-v1",
    "code_revision": "a1b2c3d",
    "augmentation": "none",
}
TREATMENT = {"augmentation": "mixup"}

# Direction-aware val_f1 improvements per seed, in units of 1e-3.
F1_IMPROVEMENTS = {
    "stable-small-improvement": [12, 9, 11, 10, 8, 14, 10, 9, 11, 7],
    "stable-regression": [-9, -11, -10, -12, -8, -10, -9, -13, -11, -10],
    "single-seed-dominated": [1, -1, 0, 2, -2, 1, -1, 0, 1, 40],
    "increased-variance": [30, -30, 25, -25, 20, -20, 36, -35, 10, -10],
}
# latency_ms improvements (baseline - candidate), in units of 1e-3 ms.
LATENCY_IMPROVEMENTS = [
    -2000,
    -1500,
    -2500,
    500,
    -2000,
    -3000,
    -1500,
    -2000,
    -2500,
    -1000,
]
BASELINE_LATENCY_MS = 20.0


def _run(
    variant: str,
    seed: int,
    config: dict[str, object],
    summary: dict[str, float],
    metrics: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "run_id": f"{variant}-seed-{seed}",
        "variant": variant,
        "seed": seed,
        "config": {"values": config},
        "metrics": metrics or [],
        "summary_metrics": summary,
    }


def _summary_group(
    group_id: str,
    improvements: list[int],
    *,
    candidate_config: dict[str, object] | None = None,
    candidate_seeds: list[int] | None = None,
    latency: bool = False,
) -> dict[str, object]:
    config = candidate_config or {**BASE_CONFIG, **TREATMENT}
    runs = []
    for index, seed in enumerate(SEEDS):
        baseline_summary = {"val_f1": BASELINE_F1[index]}
        candidate_summary = {
            "val_f1": round(BASELINE_F1[index] + improvements[index] / 1000, 6)
        }
        if latency:
            baseline_summary["latency_ms"] = BASELINE_LATENCY_MS
            candidate_summary["latency_ms"] = round(
                BASELINE_LATENCY_MS - LATENCY_IMPROVEMENTS[index] / 1000, 6
            )
        runs.append(_run("baseline", seed, BASE_CONFIG, baseline_summary))
        if candidate_seeds is None or seed in candidate_seeds:
            runs.append(_run("candidate", seed, config, candidate_summary))
    return {"group_id": group_id, "runs": runs}


def _history(points: list[tuple[int, float]]) -> list[dict[str, object]]:
    return [
        {
            "name": "val_loss",
            "points": [
                {"step": step, "value": round(value, 6)} for step, value in points
            ],
        }
    ]


def _checkpoint_group() -> dict[str, object]:
    # Candidate reaches a lower (better) loss at step 20 but ends higher at 30.
    # Seed 10's baseline is shifted by 0.003 so that the per-seed improvements
    # are not symmetric around their mean, which would tie the largest
    # leave-one-out influence between seeds 1 and 10.
    runs = []
    for seed in SEEDS:
        baseline_offset = 0.001 * seed + (0.003 if seed == 10 else 0.0)
        candidate_offset = 0.002 * seed
        baseline = [(10, 0.50), (20, 0.45), (30, 0.40)]
        candidate = [(10, 0.38), (20, 0.33), (30, 0.43)]
        runs.append(
            _run(
                "baseline",
                seed,
                BASE_CONFIG,
                {},
                _history([(s, v + baseline_offset) for s, v in baseline]),
            )
        )
        runs.append(
            _run(
                "candidate",
                seed,
                {**BASE_CONFIG, **TREATMENT},
                {},
                _history([(s, v + candidate_offset) for s, v in candidate]),
            )
        )
    return {"group_id": "checkpoint-dependent", "runs": runs}


def build_fixtures() -> dict[str, dict[str, object]]:
    stable = F1_IMPROVEMENTS["stable-small-improvement"]
    fixtures = {
        name: _summary_group(name, improvements)
        for name, improvements in F1_IMPROVEMENTS.items()
    }
    fixtures["missing-paired-runs"] = _summary_group(
        "missing-paired-runs",
        stable,
        candidate_seeds=[seed for seed in SEEDS if seed not in (4, 9)],
    )
    fixtures["checkpoint-dependent"] = _checkpoint_group()
    fixtures["conflicting-metrics"] = _summary_group(
        "conflicting-metrics", stable, latency=True
    )
    fixtures["incompatible-config"] = _summary_group(
        "incompatible-config",
        stable,
        candidate_config={**BASE_CONFIG, **TREATMENT, "dataset": "imagenet-v2"},
    )
    fixtures["confounded-change"] = _summary_group(
        "confounded-change",
        stable,
        candidate_config={
            **BASE_CONFIG,
            "code_revision": "e4f5a6b",
            "optimizer": "adamw",
        },
    )
    return fixtures


def main() -> None:
    for name, group in build_fixtures().items():
        path = OUTPUT_DIR / f"{name}.json"
        path.write_text(json.dumps(group, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
