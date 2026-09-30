import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock
import pytest

# Ensure headless Qt for all test runs
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure project root is in sys.path and AINA_BASE_DIR is set
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ["AINA_BASE_DIR"] = str(PROJECT_ROOT)

# Isolate APPDATA immediately so module-level imports never touch user APPDATA
_SESSION_APPDATA_SANDBOX = Path(tempfile.mkdtemp(prefix="aina_test_appdata_"))
os.environ["APPDATA"] = str(_SESSION_APPDATA_SANDBOX)

from src.aina.startup import DEFAULT_CONFIG, save_config


@pytest.fixture(autouse=True)
def isolate_app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Autouse fixture ensuring every test runs with an isolated, temporary APPDATA directory
    and that MainWindow.CONFIG_PATH never points to the user's real configuration file.
    """
    fake_appdata = tmp_path / "fake_appdata"
    fake_appdata.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("APPDATA", str(fake_appdata))

    fake_config = fake_appdata / "AIna" / "config.json"
    fake_config.parent.mkdir(parents=True, exist_ok=True)
    save_config(dict(DEFAULT_CONFIG), fake_config)

    import src.aina.main_window as mw
    monkeypatch.setattr(mw, "CONFIG_PATH", fake_config)

    yield fake_config


@pytest.fixture
def project_root() -> Path:
    """Returns the project root directory path."""
    return PROJECT_ROOT


@pytest.fixture
def tmp_config(tmp_path: Path):
    """
    Creates an isolated config.json file initialized with DEFAULT_CONFIG in a temp directory.
    """
    config_file = tmp_path / "config.json"
    cfg = dict(DEFAULT_CONFIG)
    save_config(cfg, config_file)
    return cfg, config_file


class DummyChunkDelta:
    def __init__(self, content: str = ""):
        self.content = content


class DummyChunkChoice:
    def __init__(self, content: str = ""):
        self.delta = DummyChunkDelta(content)


class DummyChunk:
    def __init__(self, content: str = ""):
        self.choices = [DummyChunkChoice(content)]


def make_mock_streaming_chunks(words: list[str]):
    """
    Creates an iterable of mock stream chunks matching OpenAI API chunk format.
    """
    return [DummyChunk(w) for w in words]
