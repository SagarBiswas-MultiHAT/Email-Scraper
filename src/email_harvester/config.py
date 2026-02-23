"""Runtime configuration model."""

from __future__ import annotations

from dataclasses import dataclass

from .validation import validate_runtime_constraints

DEFAULT_USER_AGENT = "EmailHarvester/3.0 (+https://github.com/SagarBiswas-MultiHAT/Email-Scraper)"
DEFAULT_REQUEST_TIMEOUT = 15.0
DEFAULT_WORKERS = 8
DEFAULT_MIN_DELAY = 0.9
DEFAULT_MAX_DELAY = 2.2
DEFAULT_MAX_RESULTS_PER_QUERY = 12


@dataclass(frozen=True)
class HarvestConfig:
    """Validated configuration used by the harvesting pipeline."""

    categories: tuple[str, ...]
    seeds: tuple[str, ...]
    output: str
    serpapi_key: str | None = None
    bing_key: str | None = None
    hunter_key: str | None = None
    use_hunter: bool = False
    use_hunter_domain_search: bool = False
    preview_hunter_costs: bool = False
    use_selenium: bool = False
    yes_run_hunter: bool = False
    workers: int = DEFAULT_WORKERS
    min_delay: float = DEFAULT_MIN_DELAY
    max_delay: float = DEFAULT_MAX_DELAY
    max_results_per_query: int = DEFAULT_MAX_RESULTS_PER_QUERY
    max_hunter_verifications: int = 50
    user_agent: str = DEFAULT_USER_AGENT
    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    show_progress: bool = True

    def __post_init__(self) -> None:
        validate_runtime_constraints(
            categories=self.categories,
            seeds=self.seeds,
            workers=self.workers,
            min_delay=self.min_delay,
            max_delay=self.max_delay,
            max_results_per_query=self.max_results_per_query,
            max_hunter_verifications=self.max_hunter_verifications,
        )
