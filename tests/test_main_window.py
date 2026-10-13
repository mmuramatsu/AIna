from pathlib import Path
from unittest.mock import patch, MagicMock
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox
from src.aina.main_window import MainWindow
from src.aina.AIna import AIna


def test_main_window_init(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    assert win.new_conversation_button is not None
    assert win.new_conversation_action is not None
    assert win.AIna is None
    assert win.record_button.isEnabled() is True
    assert win.send_button.isEnabled() is False
    assert win.repeat_button.isEnabled() is False
    assert "Profile: <b>AIna-en-US-Basic</b>" in win.status_message.text()
    assert "Status: <b>Ready</b>" in win.status_message.text()
    assert "LM Studio (Local)" in win.status_message.text()
    assert "Say hi to AIna" in win.log_text_edit.placeholderText()


def test_first_message_creates_session(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    assert win.AIna is None

    win.input_field.setText("Hello AIna")
    assert win.send_button.isEnabled() is True

    with patch.object(win, "process_message") as mock_process:
        win.send_message()

        assert win.AIna is not None
        assert win.AIna.language == "en-US"
        assert len(win.AIna.history) == 2
        assert win.AIna.history[1]["content"] == "Hello AIna"
        assert "You: Hello AIna" in win.log_text_edit.toPlainText()
        assert win.input_field.text() == ""
        assert "Status: <b>Idle</b>" in win.status_message.text()
        mock_process.assert_called_once()


def test_first_message_missing_api_key_declined(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    # Switch to cloud provider with missing API key
    win.provider_combo_box.setCurrentText("OpenAI (Cloud)")
    win.input_field.setText("My unsent message")

    with patch.object(QMessageBox, "exec", return_value=QMessageBox.StandardButton.No):
        win.send_message()

    # Session was not created, input field text was preserved
    assert win.AIna is None
    assert win.input_field.text() == "My unsent message"


def test_main_window_send_message_dispatches(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    # Pre-existing session
    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))

    win.input_field.setText("Can you help me with idioms?")

    with patch.object(win, "process_message") as mock_process:
        win.send_message()

        assert "You: Can you help me with idioms?" in win.log_text_edit.toPlainText()
        assert win.input_field.text() == ""
        assert win.last_user_message == "Can you help me with idioms?"
        mock_process.assert_called_once()


def test_main_window_error_rollback_and_restore_on_cancel(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    initial_history_len = len(win.AIna.history)

    win.input_field.setText("What does 'break a leg' mean?")
    with patch.object(win, "process_message"):
        win.send_message()

    assert len(win.AIna.history) == initial_history_len + 1
    assert "You: What does 'break a leg' mean?" in win.log_text_edit.toPlainText()

    # User cancels retry dialog
    with patch("src.aina.main_window.ErrorHandler.handle_retryable_exception", return_value=False):
        win.process_message_finished({"error": "Connection error"}, 1)

    # Unsent user message must be removed from log and history
    assert "You: What does 'break a leg' mean?" not in win.log_text_edit.toPlainText()
    assert len(win.AIna.history) == initial_history_len

    # Message must be restored to input field
    assert win.input_field.text() == "What does 'break a leg' mean?"


def test_main_window_error_retry_flow(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))

    win.input_field.setText("Try again message")
    with patch.object(win, "process_message"):
        win.send_message()

    # User clicks Retry in dialog
    with patch("src.aina.main_window.ErrorHandler.handle_retryable_exception", return_value=True), \
         patch.object(win, "resend_last_message") as mock_resend:
        win.process_message_finished({"error": "Timeout"}, 1)
        mock_resend.assert_called_once()


def test_language_change_mid_conversation(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    win.AIna.history.append({"role": "user", "content": "Hello"})
    win.AIna.history.append({"role": "assistant", "content": "Hi!"})

    win.language_combo_box.setCurrentText("日本語")

    assert win.language == "ja"
    assert win.AIna.language == "ja"
    assert "Switched to 日本語 · Basic" in win.log_text_edit.toPlainText()
    assert "continue the conversation in Japanese" in win.AIna.history[0]["content"]
    assert "AIna-ja-Basic" in win.status_message.text()


def test_language_change_before_conversation(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    win.language_combo_box.setCurrentText("日本語")

    assert win.language == "ja"
    assert win.AIna is None
    assert "Switched to" not in win.log_text_edit.toPlainText()
    assert "AInaに話しかけて" in win.log_text_edit.placeholderText()
    assert "Profile: <b>AIna-ja-Basic</b>" in win.status_message.text()
    assert "Status: <b>Ready</b>" in win.status_message.text()


def test_provider_change_mid_conversation(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    win.AIna.history.append({"role": "user", "content": "Hello"})
    initial_len = len(win.AIna.history)

    # Switch to Ollama
    win.provider_combo_box.setCurrentText("Ollama (Local)")

    assert "Ollama (Local)" in win.status_message.text()
    assert win.AIna.model_name == "llama3.2"
    assert str(win.AIna.client.base_url).startswith("http://localhost:11434/v1")
    assert len(win.AIna.history) == initial_len


def test_new_conversation_resets_state(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    win.has_reply = True
    win.repeat_button.setEnabled(True)
    win.last_user_message = "Remember this"
    win.log_text_edit.setText("Some conversation text")

    win.new_conversation_button.click()

    assert win.AIna is None
    assert win.has_reply is False
    assert win.repeat_button.isEnabled() is False
    assert win.last_user_message is None
    assert win.log_text_edit.toPlainText() == ""
    assert "Status: <b>Ready</b>" in win.status_message.text()


def test_ctrl_n_triggers_new_conversation(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    win.log_text_edit.setText("Chatting...")

    win.new_conversation_action.trigger()

    assert win.AIna is None
    assert win.log_text_edit.toPlainText() == ""
    assert "Status: <b>Ready</b>" in win.status_message.text()


def test_new_conversation_ignored_while_processing(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    prompt_path = project_root / "assets" / "prompts" / "AIna-prompt-en-US-Basic.txt"
    win.AIna = AIna(prompt_path=str(prompt_path))
    win.is_processing = True

    win.new_conversation()

    assert win.AIna is not None


def test_auto_send_checkbox_updates_flag(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    assert win.auto_send is False
    win.auto_send_checkbox.setChecked(True)
    assert win.auto_send is True
    assert win.config["auto_send"] is True


def test_main_window_config_isolation(qtbot, tmp_path: Path):
    """Verify that MainWindow saves into its injected config_path and does not touch global CONFIG_PATH."""
    from src.aina.startup import load_config, DEFAULT_CONFIG
    custom_cfg_file = tmp_path / "custom_appdata" / "config.json"
    custom_cfg_file.parent.mkdir(parents=True, exist_ok=True)

    cfg = dict(DEFAULT_CONFIG)
    cfg["theme"] = "dark"

    win = MainWindow(cfg, config_path=custom_cfg_file)
    qtbot.addWidget(win)

    win.provider_combo_box.setCurrentText("OpenAI (Cloud)")
    win.save_config()

    saved = load_config(custom_cfg_file)
    assert saved["active_provider"] == "OpenAI (Cloud)"
    assert win.config_path == custom_cfg_file
