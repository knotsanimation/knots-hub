from pathlib import Path

import pytest

_THISDIR = Path(__file__).parent


@pytest.fixture()
def data_dir():
    return _THISDIR / "data"
