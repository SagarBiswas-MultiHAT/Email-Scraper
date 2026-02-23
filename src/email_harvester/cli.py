"""CLI entrypoint for email-harvester."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence

from .config import (
    DEFAULT_MAX_DELAY,
    DEFAULT_MAX_RESULTS_PER_QUERY,
    DEFAULT_MIN_DELAY,
    DEFAULT_WORKERS,
    HarvestConfig,
)
from .errors import ConfigError
from .logging_utils import configure_logging, get_logger
from .pipeline import run_pipeline
from .validation import load_lines_from_file


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    parser = argparse.ArgumentParser(
        description="Email Harvester - multi-backend search, polite crawling, optional Hunter integration."
    )
    source_group = parser.add_mutually_exclusive_group(required=False)
    source_group.add_argument("--categories", nargs="+", help="Category keywords.")
    source_group.add_argument(
        "--categories-file", help="Path to category file (one category per line)."
    )
    parser.add_argument("--seeds-file", help="Path to seed URL file (skips search).")
    parser.add_argument(
        "--serpapi-key", help="SerpApi key (optional, fallback backend priority #1)."
    )
    parser.add_argument("--bing-key", help="Bing key (optional, fallback backend priority #2).")
    parser.add_argument(
        "--use-selenium", action="store_true", help="Use Selenium for JS-heavy sites."
    )
    parser.add_argument("--use-hunter", action="store_true", help="Enable Hunter integration.")
    parser.add_argument("--hunter-key", help="Hunter key (or set HUNTER_API_KEY env var).")
    parser.add_argument(
        "--use-hunter-domain-search",
        action="store_true",
        help="Use Hunter domain search per discovered domain.",
    )
    parser.add_argument(
        "--preview-hunter-costs",
        action="store_true",
        help="Preview mode: estimate Hunter usage without verification calls.",
    )
    parser.add_argument(
        "--max-hunter-verifications",
        type=int,
        default=50,
        help="Upper limit for Hunter verification calls.",
    )
    parser.add_argument(
        "--yes-run-hunter",
        action="store_true",
        help="Safety confirmation to run actual Hunter verification calls.",
    )
    parser.add_argument("--output", default="emails_output.csv", help="Output CSV path.")
    parser.add_argument(
        "--workers", type=int, default=DEFAULT_WORKERS, help="Number of worker threads."
    )
    parser.add_argument(
        "--min-delay",
        type=float,
        default=DEFAULT_MIN_DELAY,
        help="Minimum polite delay between requests.",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=DEFAULT_MAX_DELAY,
        help="Maximum polite delay between requests.",
    )
    parser.add_argument(
        "--max-results-per-query",
        type=int,
        default=DEFAULT_MAX_RESULTS_PER_QUERY,
        help="Search results per query.",
    )
    parser.add_argument("--no-progress", action="store_true", help="Disable tqdm progress bars.")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging.")
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse and pre-validate CLI input."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not (args.categories or args.categories_file or args.seeds_file):
        parser.error("Provide --categories, --categories-file, or --seeds-file.")
    return args


def _materialize_categories(args: argparse.Namespace) -> tuple[str, ...]:
    if args.categories:
        return tuple(args.categories)
    if args.categories_file:
        return tuple(load_lines_from_file(args.categories_file))
    return tuple()


def _materialize_seeds(args: argparse.Namespace) -> tuple[str, ...]:
    if args.seeds_file:
        return tuple(load_lines_from_file(args.seeds_file))
    return tuple()


def namespace_to_config(args: argparse.Namespace) -> HarvestConfig:
    """Convert CLI args to validated HarvestConfig."""
    logger = get_logger()
    categories = _materialize_categories(args)
    seeds = _materialize_seeds(args)
    serpapi_key = args.serpapi_key or os.getenv("SERPAPI_KEY")
    bing_key = args.bing_key or os.getenv("BING_API_KEY")
    hunter_key = args.hunter_key or os.getenv("HUNTER_API_KEY")

    if args.use_hunter and not hunter_key:
        logger.warning(
            "--use-hunter was provided but no Hunter key was found. "
            "Set HUNTER_API_KEY or pass --hunter-key."
        )
    if args.use_hunter_domain_search and not hunter_key:
        logger.warning(
            "Hunter domain search requested without key; domain search will be disabled."
        )

    preview_hunter_costs = bool(
        args.preview_hunter_costs or (args.use_hunter and not args.yes_run_hunter)
    )
    if args.use_hunter and preview_hunter_costs and not args.preview_hunter_costs:
        logger.info("Hunter enabled without --yes-run-hunter. Running in preview mode.")

    return HarvestConfig(
        categories=categories,
        seeds=seeds,
        output=args.output,
        serpapi_key=serpapi_key,
        bing_key=bing_key,
        hunter_key=hunter_key,
        use_hunter=bool(args.use_hunter and hunter_key),
        use_hunter_domain_search=bool(args.use_hunter_domain_search and hunter_key),
        preview_hunter_costs=preview_hunter_costs,
        use_selenium=args.use_selenium,
        yes_run_hunter=bool(args.yes_run_hunter),
        workers=args.workers,
        min_delay=args.min_delay,
        max_delay=args.max_delay,
        max_results_per_query=args.max_results_per_query,
        max_hunter_verifications=args.max_hunter_verifications,
        show_progress=not args.no_progress,
    )


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger = get_logger()
    try:
        config = namespace_to_config(args)
    except ConfigError as exc:
        logger.error("Invalid configuration: %s", exc)
        return 2

    output = run_pipeline(config, logger=logger)
    logger.info("Wrote results to %s", output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
