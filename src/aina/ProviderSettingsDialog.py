from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QCheckBox,
    QDialogButtonBox,
    QWidget,
)
from PySide6.QtCore import Qt
from openai import OpenAI
from pathlib import Path
from .startup import save_config


class ProviderSettingsDialog(QDialog):
    """
    Dialog for configuring LLM providers, credentials, and model names.
    Supports both local (LM Studio, Ollama) and cloud (OpenAI, Gemini, Custom) providers.
    """

    def __init__(
        self,
        config: dict,
        config_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.config = config
        self.config_path = config_path
        # Create a working copy of providers
        self.providers = {
            name: dict(data)
            for name, data in self.config.get("providers", {}).items()
        }
        self.current_provider_name = self.config.get(
            "active_provider", "LM Studio (Local)"
        )

        self.setWindowTitle("LLM Provider Settings")
        self.setMinimumWidth(480)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Header description
        info_label = QLabel(
            "Select an LLM provider and configure its connection settings.\n"
            "Cloud providers require an API key, which is saved locally."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # Form layout
        form_layout = QFormLayout()

        # Provider Selector
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(self.providers.keys()))
        idx = self.provider_combo.findText(self.current_provider_name)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form_layout.addRow("Provider:", self.provider_combo)

        # Base URL field
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText("https://api.openai.com/v1")
        form_layout.addRow("Base URL:", self.base_url_edit)

        # API Key field with show/hide toggle
        api_key_layout = QHBoxLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Enter API Key (if required)")
        api_key_layout.addWidget(self.api_key_edit)

        self.show_key_checkbox = QCheckBox("Show")
        self.show_key_checkbox.toggled.connect(self._toggle_key_visibility)
        api_key_layout.addWidget(self.show_key_checkbox)
        form_layout.addRow("API Key:", api_key_layout)

        # Model field
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g. gpt-4o-mini, llama3.2")
        form_layout.addRow("Model Name:", self.model_edit)

        # Requirements hint label
        self.hint_label = QLabel()
        self.hint_label.setStyleSheet("color: gray; font-size: 11px;")
        form_layout.addRow("", self.hint_label)

        layout.addLayout(form_layout)

        # Test Connection button and status label
        test_layout = QHBoxLayout()
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_button)

        self.test_status_label = QLabel("")
        self.test_status_label.setWordWrap(True)
        test_layout.addWidget(self.test_status_label, 1)
        layout.addLayout(test_layout)

        # Dialog Buttons (Save / Cancel)
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        self.button_box.accepted.connect(self._on_save)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        # Populate current fields
        self._load_provider_fields(self.current_provider_name)

    def _toggle_key_visibility(self, checked: bool) -> None:
        if checked:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Normal)
        else:
            self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)

    def _save_current_fields_to_state(self) -> None:
        if self.current_provider_name in self.providers:
            self.providers[self.current_provider_name]["base_url"] = (
                self.base_url_edit.text().strip()
            )
            self.providers[self.current_provider_name]["api_key"] = (
                self.api_key_edit.text().strip()
            )
            self.providers[self.current_provider_name]["model"] = (
                self.model_edit.text().strip()
            )

    def _load_provider_fields(self, provider_name: str) -> None:
        self.test_status_label.setText("")
        data = self.providers.get(provider_name, {})

        self.base_url_edit.setText(data.get("base_url", ""))
        self.api_key_edit.setText(data.get("api_key", ""))
        self.model_edit.setText(data.get("model", ""))

        requires_key = data.get("requires_api_key", False)
        if requires_key:
            self.hint_label.setText("⚠ This provider requires an API key.")
        else:
            self.hint_label.setText("✓ Local provider: no API key required.")

    def _on_provider_changed(self, new_provider_name: str) -> None:
        self._save_current_fields_to_state()
        self.current_provider_name = new_provider_name
        self._load_provider_fields(new_provider_name)

    def _test_connection(self) -> None:
        self.test_status_label.setText("Testing connection...")
        self.test_status_label.setStyleSheet("color: orange;")

        base_url = self.base_url_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        model = self.model_edit.text().strip()

        if not api_key:
            api_key = "none"

        try:
            client = OpenAI(
                base_url=base_url if base_url else None,
                api_key=api_key,
                timeout=8.0,
            )
            # Lightweight test: request 1 token completion
            client.chat.completions.create(
                model=model if model else "model-identifier",
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1,
            )
            self.test_status_label.setText("✓ Connection successful!")
            self.test_status_label.setStyleSheet("color: green;")
        except Exception as e:
            err_msg = str(e)
            if "Connection refused" in err_msg or "Failed to connect" in err_msg:
                self.test_status_label.setText(
                    "✗ Connection refused. Ensure the local server is running."
                )
            elif "Incorrect API key" in err_msg or "401" in err_msg:
                self.test_status_label.setText("✗ Authentication failed: Invalid API key.")
            else:
                self.test_status_label.setText(f"✗ Error: {err_msg[:60]}...")
            self.test_status_label.setStyleSheet("color: red;")

    def _on_save(self) -> None:
        self._save_current_fields_to_state()
        self.config["active_provider"] = self.current_provider_name
        self.config["providers"] = self.providers
        save_config(self.config, self.config_path)
        self.accept()
