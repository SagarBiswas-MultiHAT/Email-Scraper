import os

import pytest

from email_harvester.cli import main

requires_live = pytest.mark.skipif(
    os.getenv("RUN_LIVE_INTEGRATION") != "1",
    reason="Set RUN_LIVE_INTEGRATION=1 to execute live integration tests.",
)


@requires_live
def test_live_help_command_smoke() -> None:
    exit_code = main(["--help"])
    assert exit_code == 0
