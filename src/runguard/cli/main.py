import argparse
from collections.abc import Sequence
from pathlib import Path

from runguard.comparison.models import MetricDirection
from runguard.comparison.paired import ComparisonError, compare_group
from runguard.sources.local_json import load_local_json


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
            )
        except (ComparisonError, ValueError) as error:
            compare_parser.error(str(error))

        print(f"Comparison: {args.baseline} → {args.candidate}")
        print(f"Metric: {args.metric}")
        print(f"Value source: {result.value_source}")
        print(f"Direction: {result.direction.value}")
        print(f"Paired runs: {len(result.pairs)}")
        print(f"Mean paired difference: {result.mean_difference:+.6f}")
        print(f"Median paired difference: {result.median_difference:+.6f}")
        print(
            "Positive pairs: "
            f"{result.positive_pair_count}/{len(result.pairs)} "
            f"({result.positive_pair_rate:.2%})"
        )


if __name__ == "__main__":
    main()
