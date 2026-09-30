from pathlib import Path
import json
from src.aina.startup import (
    DEFAULT_CONFIG,
    save_config,
    load_config,
    get_config_path,
    _deep_merge,
)


def test_default_config_structure():
    assert "theme" in DEFAULT_CONFIG
    assert "language" in DEFAULT_CONFIG
    assert "language_level" in DEFAULT_CONFIG
    assert "auto_send" in DEFAULT_CONFIG
    assert "active_provider" in DEFAULT_CONFIG
    assert "providers" in DEFAULT_CONFIG

    providers = DEFAULT_CONFIG["providers"]
    assert "LM Studio (Local)" in providers
    assert "Ollama (Local)" in providers
    assert "OpenAI (Cloud)" in providers
    assert "Google Gemini (Cloud)" in providers
    assert "Custom (OpenAI-Compatible)" in providers


def test_save_and_load_config(tmp_path: Path):
    cfg_file = tmp_path / "test_config.json"
    custom_config = dict(DEFAULT_CONFIG)
    custom_config["theme"] = "dark"
    custom_config["language"] = "日本語"

    save_config(custom_config, cfg_file)
    assert cfg_file.exists()

    loaded = load_config(cfg_file)
    assert loaded["theme"] == "dark"
    assert loaded["language"] == "日本語"
    assert "providers" in loaded


def test_deep_merge_preserves_user_settings():
    defaults = {
        "theme": "light",
        "providers": {
            "OpenAI": {"api_key": "", "model": "gpt-4o-mini"},
            "Ollama": {"base_url": "http://localhost:11434/v1"},
        },
    }
    user_overrides = {
        "theme": "dark",
        "providers": {
            "OpenAI": {"api_key": "sk-secret-123"},
        },
    }

    merged = _deep_merge(defaults, user_overrides)
    assert merged["theme"] == "dark"
    assert merged["providers"]["OpenAI"]["api_key"] == "sk-secret-123"
    assert merged["providers"]["OpenAI"]["model"] == "gpt-4o-mini"
    assert merged["providers"]["Ollama"]["base_url"] == "http://localhost:11434/v1"


def test_deep_merge_adds_new_provider():
    defaults = {
        "providers": {
            "LM Studio": {"base_url": "http://localhost:1234/v1"},
            "Gemini": {"base_url": "https://generativelanguage.googleapis.com"},
        }
    }
    user_config = {
        "providers": {
            "LM Studio": {"base_url": "http://127.0.0.1:1234/v1"},
        }
    }

    merged = _deep_merge(defaults, user_config)
    assert merged["providers"]["LM Studio"]["base_url"] == "http://127.0.0.1:1234/v1"
    assert "Gemini" in merged["providers"]


def test_corrupt_json_fallback(tmp_path: Path):
    cfg_file = tmp_path / "corrupt.json"
    cfg_file.write_text("{ this is not valid json :", encoding="utf-8")

    loaded = load_config(cfg_file)
    assert loaded["theme"] == DEFAULT_CONFIG["theme"]
    assert "providers" in loaded


def test_nonexistent_file_returns_defaults(tmp_path: Path):
    cfg_file = tmp_path / "nonexistent.json"
    loaded = load_config(cfg_file)
    assert loaded["theme"] == DEFAULT_CONFIG["theme"]
    assert loaded["active_provider"] == DEFAULT_CONFIG["active_provider"]


def test_get_config_path():
    path = get_config_path("AInaTestApp")
    assert isinstance(path, Path)
    assert path.name == "config.json"
    assert path.parent.exists()
