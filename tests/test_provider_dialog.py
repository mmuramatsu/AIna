from pathlib import Path
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QLineEdit
from PySide6.QtCore import Qt
from src.aina.ProviderSettingsDialog import ProviderSettingsDialog


def test_provider_settings_dialog_loads_active_provider(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    assert dialog.provider_combo.currentText() == "LM Studio (Local)"
    assert dialog.base_url_edit.text() == "http://localhost:1234/v1"
    assert "no API key required" in dialog.hint_label.text()


def test_provider_settings_dialog_switch_provider(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    # Switch to OpenAI (Cloud)
    dialog.provider_combo.setCurrentText("OpenAI (Cloud)")
    assert dialog.base_url_edit.text() == "https://api.openai.com/v1"
    assert dialog.model_edit.text() == "gpt-4o-mini"
    assert "requires an API key" in dialog.hint_label.text()


def test_provider_settings_dialog_toggle_key_visibility(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    assert dialog.api_key_edit.echoMode() == QLineEdit.EchoMode.Password

    dialog.show_key_checkbox.setChecked(True)
    assert dialog.api_key_edit.echoMode() == QLineEdit.EchoMode.Normal

    dialog.show_key_checkbox.setChecked(False)
    assert dialog.api_key_edit.echoMode() == QLineEdit.EchoMode.Password


def test_provider_settings_dialog_test_connection_success(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    with patch("src.aina.ProviderSettingsDialog.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.return_value = MagicMock()

        qtbot.mouseClick(dialog.test_button, Qt.MouseButton.LeftButton)
        assert "Connection successful" in dialog.test_status_label.text()


def test_provider_settings_dialog_test_connection_refused(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    with patch("src.aina.ProviderSettingsDialog.OpenAI") as MockOpenAI:
        mock_client = MockOpenAI.return_value
        mock_client.chat.completions.create.side_effect = ConnectionError("Connection refused by target")

        dialog._test_connection()
        assert "Connection refused" in dialog.test_status_label.text()


def test_provider_settings_dialog_save(qtbot, tmp_config):
    cfg, cfg_file = tmp_config
    dialog = ProviderSettingsDialog(cfg, cfg_file)
    qtbot.addWidget(dialog)

    dialog.provider_combo.setCurrentText("OpenAI (Cloud)")
    dialog.api_key_edit.setText("sk-test-secret-12345")
    dialog.model_edit.setText("gpt-4o")

    dialog._on_save()

    assert cfg["active_provider"] == "OpenAI (Cloud)"
    assert cfg["providers"]["OpenAI (Cloud)"]["api_key"] == "sk-test-secret-12345"
    assert cfg["providers"]["OpenAI (Cloud)"]["model"] == "gpt-4o"
