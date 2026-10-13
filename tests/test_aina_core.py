from pathlib import Path
from src.aina.AIna import AIna


def _prompt(project_root: Path, language: str, level: str) -> str:
    return str(project_root / "assets" / "prompts" / f"AIna-prompt-{language}-{level}.txt")


def test_aina_init_english(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    aina = AIna(
        language="en-US",
        language_level="Basic",
        prompt_path=str(prompt_path),
    )

    assert aina.language == "en-US"
    assert aina.language_level == "Basic"
    # The user starts the conversation: only the system prompt is present
    assert len(aina.history) == 1
    assert aina.history[0]["role"] == "system"
    assert aina.history[0]["content"] == prompt_path.read_text(encoding="utf-8")


def test_aina_init_japanese(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-ja-Basic.txt"
    aina = AIna(
        language="ja",
        language_level="Basic",
        prompt_path=str(prompt_path),
    )

    assert aina.language == "ja"
    assert len(aina.history) == 1
    assert aina.history[0]["role"] == "system"


def test_has_conversation(project_root: Path):
    aina = AIna(prompt_path=_prompt(project_root, "en-US", "Basic"))
    assert aina.has_conversation is False

    aina.history.append({"role": "user", "content": "Hi!"})
    assert aina.has_conversation is True


def test_set_profile_without_conversation(project_root: Path):
    aina = AIna("en-US", "Basic", _prompt(project_root, "en-US", "Basic"))

    new_prompt = _prompt(project_root, "ja", "Advanced")
    aina.set_profile("ja", "Advanced", new_prompt)

    assert aina.language == "ja"
    assert aina.language_level == "Advanced"
    assert len(aina.history) == 1
    # No transition note when nothing was said yet
    assert aina.history[0]["content"] == Path(new_prompt).read_text(encoding="utf-8")


def test_set_profile_mid_conversation(project_root: Path):
    aina = AIna("en-US", "Basic", _prompt(project_root, "en-US", "Basic"))
    aina.history.append({"role": "user", "content": "Hello"})
    aina.history.append({"role": "assistant", "content": "Hi there!"})

    aina.set_profile("ja", "Basic", _prompt(project_root, "ja", "Basic"))

    system = aina.history[0]
    assert system["role"] == "system"
    assert "earlier messages in this conversation were in English (Basic)" in system["content"]
    assert "continue the conversation in Japanese at the Basic level" in system["content"]
    # Previous turns are preserved
    assert aina.history[1:] == [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]
    assert aina.language == "ja"


def test_set_profile_note_not_stacked(project_root: Path):
    aina = AIna("en-US", "Basic", _prompt(project_root, "en-US", "Basic"))
    aina.history.append({"role": "user", "content": "Hello"})

    aina.set_profile("ja", "Basic", _prompt(project_root, "ja", "Basic"))
    aina.set_profile("en-US", "Advanced", _prompt(project_root, "en-US", "Advanced"))

    content = aina.history[0]["content"]
    assert content.count("Note: earlier messages") == 1
    assert "were in Japanese (Basic)" in content
    assert "continue the conversation in English at the Advanced level" in content


def test_set_provider_keeps_history(project_root: Path):
    aina = AIna(prompt_path=_prompt(project_root, "en-US", "Basic"))
    aina.history.append({"role": "user", "content": "Hello"})
    history_before = list(aina.history)

    aina.set_provider({
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "model": "llama3.2",
    })

    assert str(aina.client.base_url).startswith("http://localhost:11434/v1")
    assert aina.model_name == "llama3.2"
    assert aina.history == history_before


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

    assert len(aina.history) == 21
    aina.trim_history()
    assert len(aina.history) == 21


def test_history_trimming_over_limit(project_root: Path):
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    aina = AIna(prompt_path=str(prompt_path))

    # Add 80 messages (exceeding MAX_HISTORY_MESSAGES = 50)
    for i in range(80):
        aina.history.append({"role": "user", "content": f"msg {i}"})

    initial_len = len(aina.history)
    assert initial_len == 81

    aina.trim_history()

    # System prompt + 50 recent messages = 51
    assert len(aina.history) == AIna.MAX_HISTORY_MESSAGES + 1
    assert aina.history[0]["role"] == "system"
    # Ensure newest messages were preserved (last message should be msg 79)
    assert aina.history[-1]["content"] == "msg 79"
