import argparse
from collections.abc import Sequence
from pathlib import Path

from runguard.comparison.minimal import mean_difference, paired_differences


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
        "--pair-by",
        required=True,
        choices=["seed"],
    )

    args = parser.parse_args(argv)

    if args.command == "compare":
        input_path = Path(args.input)
        differences = paired_differences(
            input_path, args.baseline, args.candidate, args.metric
        )

        mean = mean_difference(input_path, args.baseline, args.candidate, args.metric)

        print(f"Comparison: {args.baseline} → {args.candidate}")
        print(f"Metric: {args.metric}")
        print(f"Paired runs: {len(differences)}")
        print(f"Mean paired difference: {mean:+.6f}")


if __name__ == "__main__":
    main()
