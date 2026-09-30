import os
import sys
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

from src.aina.startup import DEFAULT_CONFIG, save_config


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
