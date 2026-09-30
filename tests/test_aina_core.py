from pathlib import Path
from src.aina.AIna import AIna


def test_aina_init_english(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    aina = AIna(
        language="en-US",
        language_level="Basic",
        prompt_path=str(prompt_path),
    )

    assert aina.language == "en-US"
    assert aina.language_level == "Basic"
    assert len(aina.history) == 2
    assert aina.history[0]["role"] == "system"
    assert aina.history[1]["role"] == "user"
    assert "Greet your new speaker" in aina.history[1]["content"]


def test_aina_init_japanese(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-ja-Basic.txt"
    aina = AIna(
        language="ja",
        language_level="Basic",
        prompt_path=str(prompt_path),
    )

    assert aina.language == "ja"
    assert len(aina.history) == 2
    assert aina.history[0]["role"] == "system"
    assert "会話を始めましょう" in aina.history[1]["content"]


def test_aina_custom_provider_config(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    provider_config = {
        "base_url": "http://localhost:11434/v1",
        "api_key": "custom-key-123",
        "model": "llama3.2:latest",
    }
    aina = AIna(
        language="en-US",
        language_level="Basic",
        prompt_path=str(prompt_path),
        provider_config=provider_config,
    )

    assert aina.model_name == "llama3.2:latest"
    assert str(aina.client.base_url).startswith("http://localhost:11434/v1")
    assert aina.client.api_key == "custom-key-123"


def test_history_trimming_under_limit(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    aina = AIna(prompt_path=str(prompt_path))

    # Add 20 conversation messages
    for i in range(20):
        aina.history.append({"role": "user", "content": f"msg {i}"})

    assert len(aina.history) == 22
    aina.trim_history()
    assert len(aina.history) == 22


def test_history_trimming_over_limit(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    aina = AIna(prompt_path=str(prompt_path))

    # Add 80 messages (exceeding MAX_HISTORY_MESSAGES = 50)
    for i in range(80):
        aina.history.append({"role": "user", "content": f"msg {i}"})

    initial_len = len(aina.history)
    assert initial_len == 82

    aina.trim_history()

    # System prompt + 50 recent messages = 51
    assert len(aina.history) == AIna.MAX_HISTORY_MESSAGES + 1
    assert aina.history[0]["role"] == "system"
    # Ensure newest messages were preserved (last message should be msg 79)
    assert aina.history[-1]["content"] == "msg 79"
