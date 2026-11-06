import sys
from typing import TYPE_CHECKING

import pytest

from nmr.web.bridge import Settings

if TYPE_CHECKING:
    from reccy.pytest_plugin import SampleConfigRegression

if sys.version_info >= (3, 13):
    pytest_plugins = ["reccy.pytest_plugin"]


@pytest.mark.skipif(sys.version_info < (3, 13), reason="reccy requires Python 3.13")
def test_sample_config(sample_config_regression: "SampleConfigRegression") -> None:
    sample_config_regression(Settings)
