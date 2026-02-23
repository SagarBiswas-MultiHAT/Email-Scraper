import pytest

from email_harvester import cli


def test_parse_args_with_categories() -> None:
    args = cli.parse_args(["--categories", "SEO", "Blogger"])
    assert args.categories == ["SEO", "Blogger"]


def test_parse_args_with_seeds_only() -> None:
    args = cli.parse_args(["--seeds-file", "seeds.txt"])
    assert args.seeds_file == "seeds.txt"


def test_parse_args_requires_source() -> None:
    with pytest.raises(SystemExit):
        cli.parse_args([])


def test_main_returns_zero_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "run_pipeline", lambda config, logger: config.output)
    assert cli.main(["--categories", "SEO"]) == 0


def test_main_returns_two_on_invalid_config() -> None:
    assert cli.main(["--categories", "SEO", "--workers", "0"]) == 2
