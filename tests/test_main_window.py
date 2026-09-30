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

    assert win.initialize_button is not None
    assert win.record_button is not None
    assert win.send_button is not None
    assert win.provider_combo_box is not None
    assert "Profile: <b>None</b>" in win.status_message.text()
    assert "LM Studio (Local)" in win.status_message.text()


def test_main_window_send_message_dispatches(qtbot, tmp_config, project_root: Path):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    # Initialize mock profile
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


def test_main_window_provider_change_updates_status_bar(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    win = MainWindow(cfg, config_path=cfg_file)
    qtbot.addWidget(win)

    assert "LM Studio (Local)" in win.status_message.text()

    # Change combo box to Ollama (Local)
    win.provider_combo_box.setCurrentText("Ollama (Local)")
    assert "Ollama (Local)" in win.status_message.text()
    assert win.config["active_provider"] == "Ollama (Local)"


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
