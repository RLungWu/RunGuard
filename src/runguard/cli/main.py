import argparse
from collections.abc import Sequence
from pathlib import Path

from runguard.cli.output import render_json, render_text
from runguard.comparison.models import CheckpointPolicy, MetricDirection, ValueSource
from runguard.comparison.paired import ComparisonError, compare_group
from runguard.sources.local_json import load_local_json
from runguard.statistics.evidence import build_paired_evidence


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="runguard",
        description="Evidence-based regression testing for ML experiments.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare paired experiment runs.",
    )
    compare_parser.add_argument("--input", required=True)
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--candidate", required=True)
    compare_parser.add_argument("--metric", required=True)
    compare_parser.add_argument(
        "--input-format",
        choices=["m0", "nested", "canonical"],
        default="canonical",
        help="Format of the local JSON input (default: canonical).",
    )
    compare_parser.add_argument(
        "--group-id",
        help="Group ID required when --input-format is m0.",
    )
    compare_parser.add_argument(
        "--pair-by",
        required=True,
        choices=["seed"],
    )
    compare_parser.add_argument(
        "--direction",
        choices=[direction.value for direction in MetricDirection],
        default=MetricDirection.HIGHER_IS_BETTER.value,
        help="Whether higher or lower metric values are better.",
    )
    compare_parser.add_argument(
        "--value-source",
        choices=[source.value for source in ValueSource],
        default=ValueSource.SUMMARY.value,
        help="Compare summary metrics or metric history (default: summary).",
    )
    compare_parser.add_argument(
        "--checkpoint",
        choices=[policy.value for policy in CheckpointPolicy],
        help="Checkpoint policy; required with --value-source history.",
    )
    compare_parser.add_argument(
        "--random-seed",
        type=int,
        default=0,
        help="Bootstrap random seed, recorded in the output (default: 0).",
    )
    compare_parser.add_argument(
        "--confidence-level",
        type=float,
        default=0.95,
        help="Bootstrap confidence level (default: 0.95).",
    )
    compare_parser.add_argument(
        "--resamples",
        type=int,
        default=10_000,
        help="Bootstrap resample count (default: 10000).",
    )
    compare_parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help=(
            "Output format (default: text). JSON is experimental and may change "
            "until schema versioning is introduced."
        ),
    )

    args = parser.parse_args(argv)

    if args.command == "compare":
        try:
            input_path = Path(args.input)
            group = load_local_json(
                input_path,
                args.input_format,
                group_id=args.group_id,
            )
            result = compare_group(
                group,
                args.baseline,
                args.candidate,
                args.metric,
                direction=MetricDirection(args.direction),
                value_source=ValueSource(args.value_source),
                checkpoint_policy=(
                    None
                    if args.checkpoint is None
                    else CheckpointPolicy(args.checkpoint)
                ),
            )
            evidence = build_paired_evidence(
                result,
                random_seed=args.random_seed,
                confidence_level=args.confidence_level,
                resamples=args.resamples,
            )
        except (ComparisonError, ValueError) as error:
            compare_parser.error(str(error))

        if args.format == "json":
            print(render_json(evidence), end="")
        else:
            print(render_text(result, evidence), end="")


if __name__ == "__main__":
    main()
