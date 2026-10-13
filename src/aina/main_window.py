import os
import sys
from pathlib import Path

import numpy as np
import sounddevice as sd
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QPushButton,
    QVBoxLayout,
    QLabel,
    QHBoxLayout,
    QFormLayout,
    QTextEdit,
    QFrame,
    QSizePolicy,
    QComboBox,
    QCheckBox,
    QStatusBar,
    QMessageBox,
)
from PySide6.QtGui import QPixmap, QTextCursor, QAction, QKeyEvent, QKeySequence
from PySide6.QtCore import Qt, Signal, SIGNAL
import qdarktheme
import wavio

from .ErrorHandler import ErrorHandler
from .AIna import AIna
from .AnimatedButton import AnimatedButton
from .GPTClient import GPTClient
from .SpeakerThread import SpeakerThread
from .SpeechThread import SpeechThread
from .startup import get_config_path, save_config, load_config
from .StylishLineEdit import StylishLineEdit
from .AspectImageLabel import AspectImageLabel
from .ProviderSettingsDialog import ProviderSettingsDialog


# Get the absolute path of the directory where the script is located
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

# Path of the config values
CONFIG_PATH = get_config_path("AIna")


class MainWindow(QMainWindow):
    """
    The main application window that manages the user interface and core logic.

    This class handles UI initialization, theming, audio recording, speech
    recognition, and communication with the GPT model. It also manages
    thread execution and response handling for asynchronous operations.
    """

    # Slot to connect to the thread to send signals from this class to the worker thread
    stop_worker_signal = Signal()

    def __init__(self, config: dict, config_path: Path | None = None):
        """
        Initialize the UI class

        Args:
            config (dict): Application configuration dictionary.
            config_path (Path, optional): Path to the configuration JSON file.
        """

        super().__init__()

        self.config = config
        self.config_path = Path(config_path) if config_path is not None else CONFIG_PATH
        self.init_ui()

        # Creates "temp" folder if not exists.
        if not os.path.isdir(os.path.join(BASE_DIR, "temp")):
            os.makedirs(os.path.join(BASE_DIR, "temp"))

    def init_ui(self) -> None:
        """
        Initializes the user interface and configures initial settings.

        Sets up all GUI elements, layouts, and widget properties. Also
        initializes configuration variables to prepare the interface for
        interaction.
        """

        self.setWindowTitle("AIna - Beta")
        self.resize(1150, 680)
        self.setMinimumSize(950, 580)

        self.language_dict = {"English": "en-US", "日本語": "ja"}
        self.language = self.language_dict.get(
            self.config.get("language", "English"), "en-US"
        )
        self.language_level = self.config.get("language_level", "Basic")
        self.auto_send = self.config.get("auto_send", False)
        self.AIna = None
        self.has_reply = False

        os.environ["AINA_BASE_DIR"] = BASE_DIR

        mic_path = get_asset_path("mic.png", "icons")
        image_path = get_asset_path("aina.png", "images")
        send_path = get_asset_path("send.png", "icons")
        self.repeat_path = get_asset_path("repeat.png", "icons")
        self.stop_path = get_asset_path("stop.png", "icons")

        # Setting a central widget to the MainWindow
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Main horizontal layout
        main_layout = QHBoxLayout(central_widget)

        # Left Panel: Configuration
        config_layout = QFormLayout()

        # Create and populate the QComboBox
        self.language_combo_box = QComboBox()
        self.language_combo_box.addItems(["English", "日本語"])
        self.language_combo_box.setToolTip(
            "Choose the language AIna will speak to you"
        )
        index = self.language_combo_box.findText(
            self.config["language"], Qt.MatchFixedString
        )
        self.language_combo_box.setCurrentIndex(index)
        self.language_combo_box.currentTextChanged.connect(self._on_profile_changed)

        # Create and populate the QComboBox
        self.language_level_combo_box = QComboBox()
        self.language_level_combo_box.addItems(["Basic", "Advanced"])
        self.language_level_combo_box.setToolTip(
            "Choose the language level AIna will speak to you"
        )
        index = self.language_level_combo_box.findText(
            self.config["language_level"], Qt.MatchFixedString
        )
        self.language_level_combo_box.setCurrentIndex(index)
        self.language_level_combo_box.currentTextChanged.connect(self._on_profile_changed)

        # Add the QComboBox to the form layout with a label
        config_layout.addRow("Select Language:", self.language_combo_box)

        # Add the QComboBox to the form layout with a label
        config_layout.addRow("Language level:", self.language_level_combo_box)

        # Provider selection
        self.provider_combo_box = QComboBox()
        providers = list(self.config.get("providers", {}).keys())
        self.provider_combo_box.addItems(providers)
        self.provider_combo_box.setToolTip("Choose the LLM provider for AIna")
        active_provider = self.config.get("active_provider", "LM Studio (Local)")
        idx = self.provider_combo_box.findText(active_provider, Qt.MatchFixedString)
        if idx >= 0:
            self.provider_combo_box.setCurrentIndex(idx)
        self.provider_combo_box.currentTextChanged.connect(self._on_provider_changed)
        config_layout.addRow("Provider:", self.provider_combo_box)

        # Provider configure button
        self.configure_provider_button = QPushButton("Configure Provider...")
        self.configure_provider_button.setToolTip("Configure LLM provider settings and API keys")
        self.configure_provider_button.clicked.connect(self.open_provider_settings)
        config_layout.addRow(self.configure_provider_button)

        # Create the Auto-send checkbox
        self.auto_send_checkbox = QCheckBox("Auto-send")
        self.auto_send_checkbox.setToolTip(
            "Automatically send the transcribed audio message"
        )
        self.auto_send_checkbox.setChecked(self.config["auto_send"])
        self.auto_send_checkbox.toggled.connect(self._on_auto_send_toggled)
        config_layout.addRow(self.auto_send_checkbox)

        # Create the New Conversation button
        self.new_conversation_button = QPushButton("New Conversation")
        self.new_conversation_button.clicked.connect(self.new_conversation)
        self.new_conversation_button.setToolTip("Start a new conversation (Ctrl+N)")
        config_layout.addRow(self.new_conversation_button)

        # Create the configuration frame and set its properties
        config_frame = QFrame()
        config_frame.setLayout(config_layout)
        config_frame.setFrameShape(QFrame.StyledPanel)
        config_frame.setFixedWidth(220)
        config_frame.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # Center Panel: Image and Button
        self.image_label = AspectImageLabel(image_path)

        # Create the animated microphone button
        self.record_button = AnimatedButton(mic_path)
        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)
        self.record_button.setToolTip(
            "Hold to record an audio to transcribe to text"
        )
        self.record_button.setEnabled(True)

        # Input field and send button
        self.input_field = StylishLineEdit("Your message")
        self.input_field.textChanged.connect(self.toggle_button_state)

        # Create the animated send button
        self.send_button = AnimatedButton(send_path)
        self.send_button.clicked.connect(self.send_message)
        self.send_button.setToolTip("Send message to AIna")
        self.send_button.setEnabled(False)

        # Create the animated microphone button
        self.repeat_button = AnimatedButton(
            icon_path=self.repeat_path, icon_size=16, size=30, colorless=True
        )
        self.repeat_button.clicked.connect(self.handle_repeat_button)
        self.repeat_button.setToolTip(
            "Make AIna repeat what she said / Stop AIna for reasoning or talking."
        )
        self.repeat_button.setEnabled(False)

        # Layout for input field and send button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.repeat_button)

        center_layout = QVBoxLayout()
        center_layout.addWidget(self.image_label)
        center_layout.addWidget(
            self.record_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        center_layout.addLayout(input_layout)
        center_frame = QFrame()
        center_frame.setLayout(center_layout)
        center_frame.setFrameShape(QFrame.StyledPanel)
        center_frame.setMinimumWidth(400)
        center_frame.setSizePolicy(
            QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding
        )

        # Right Panel: Log
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFontPointSize(16)
        log_frame = QFrame()
        log_frame.setLayout(QVBoxLayout())
        log_frame.layout().addWidget(self.log_text_edit)
        log_frame.setFrameShape(QFrame.StyledPanel)
        log_frame.setMinimumWidth(350)
        log_frame.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )

        # Add panels to main layout
        main_layout.addWidget(config_frame, 0)
        main_layout.addWidget(center_frame, 0)
        main_layout.addWidget(log_frame, 1)

        central_widget.setLayout(main_layout)

        # Create the menu bar
        menu_bar = self.menuBar()

        # Add "File" menu
        file_menu = menu_bar.addMenu("File")
        self.new_conversation_action = QAction("New Conversation", self)
        self.new_conversation_action.setShortcut(QKeySequence.StandardKey.New)
        self.new_conversation_action.triggered.connect(self.new_conversation)
        file_menu.addAction(self.new_conversation_action)

        # Add "View" menu
        view_menu = menu_bar.addMenu("View")

        # Create actions for light and dark themes
        light_theme_action = QAction("Light Mode", self)
        dark_theme_action = QAction("Dark Mode", self)

        # Connect actions to the theme toggle method
        light_theme_action.triggered.connect(lambda: self.toggle_theme("light"))
        dark_theme_action.triggered.connect(lambda: self.toggle_theme("dark"))

        # Add actions to the "View" menu
        view_menu.addAction(light_theme_action)
        view_menu.addAction(dark_theme_action)

        # Add "Settings" menu
        settings_menu = menu_bar.addMenu("Settings")
        provider_settings_action = QAction("LLM Providers...", self)
        provider_settings_action.triggered.connect(self.open_provider_settings)
        settings_menu.addAction(provider_settings_action)

        # Status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_message = QLabel()
        active_provider = self.config.get("active_provider", "LM Studio (Local)")
        self.status_message.setText(
            f"Profile: <b>AIna-{self.language}-{self.language_level}</b> | Provider: <b>{active_provider}</b> | Status: <b>Ready</b>"
        )
        status_bar.addPermanentWidget(self.status_message)

        # Link to a external site
        site_link = QLabel(
            'Developed by: <a href="https://mmuramatsu.com">mmuramatsu</a>'
        )
        site_link.setOpenExternalLinks(True)
        status_bar.addPermanentWidget(site_link)

        # Recording variables
        self.samplerate = 44100
        self.channels = 1
        self.recording = False
        self.frames = []

        # Thread references
        self.speech_thread = None
        self.gpt_thread = None
        self.speaker_thread = None

        # Control variables
        self.is_processing = False
        self.log_add_flag = False
        self.last_user_message = None

        self._update_log_placeholder()

        self.current_theme = None
        self.toggle_theme(self.config["theme"], save=False)

    def apply_theme(self, theme_name: str) -> None:
        """
        Applies the specified theme by loading and setting the QSS stylesheet.

        Loads the corresponding `.qss` file based on the theme name and updates
        the application's appearance accordingly.

        Args:
            theme_name (str): The name of the theme to load ('light' or 'dark').
        """

        # Load the base theme stylesheet
        base_stylesheet = qdarktheme.load_stylesheet(theme_name)

        qss_path = get_asset_path(f"{theme_name}.qss", "styles")
        with open(qss_path, "r") as file:
            custom_stylesheet = file.read()

        # Combine and apply the stylesheets
        self.setStyleSheet(base_stylesheet + custom_stylesheet)

    def toggle_theme(self, theme_name: str, save: bool = True) -> None:
        """
        Toggles the application theme and updates all GUI widgets.

        Sets the current theme (e.g., 'light' or 'dark'), applies the theme
        to all relevant widgets, and delegates the stylesheet application
        to `apply_theme`.

        Args:
            theme_name (str): The name of the theme to apply ('light' or 'dark').
            save (bool, optional): Whether to persist the theme change to disk. Defaults to True.
        """

        if theme_name != self.current_theme:
            self.current_theme = theme_name

            # Update the stylish widgets
            self.input_field.setProperty("theme", self.current_theme)
            self.input_field.style().unpolish(self.input_field)
            self.input_field.style().polish(self.input_field)
            self.input_field.update()

            self.record_button.setProperty("theme", self.current_theme)
            self.record_button.style().unpolish(self.record_button)
            self.record_button.style().polish(self.record_button)
            self.record_button.update()

            self.send_button.setProperty("theme", self.current_theme)
            self.send_button.style().unpolish(self.send_button)
            self.send_button.style().polish(self.send_button)
            self.send_button.update()

            self.repeat_button.setProperty("theme", self.current_theme)
            self.repeat_button.style().unpolish(self.repeat_button)
            self.repeat_button.style().polish(self.repeat_button)
            self.repeat_button.update()

            self.apply_theme(theme_name)

            if save:
                self.save_config()

    def _update_log_placeholder(self) -> None:
        """
        Sets placeholder text in the log explaining how to start chatting.
        """
        if self.language == "ja":
            self.log_text_edit.setPlaceholderText("AInaに話しかけて、会話を始めましょう！")
        else:
            self.log_text_edit.setPlaceholderText("Say hi to AIna to start a conversation!")

    def _on_auto_send_toggled(self, checked: bool) -> None:
        """
        Updates auto_send flag and persists to config.
        """
        self.auto_send = checked
        self.config["auto_send"] = checked
        self.save_config()

    def _ensure_api_key(self, provider_name: str) -> bool:
        """
        Checks if provider requires an API key and prompts the user if missing.
        Returns True if ready to proceed, False if aborted.
        """
        provider_cfg = self.config.get("providers", {}).get(provider_name, {})
        if provider_cfg.get("requires_api_key", False) and not provider_cfg.get("api_key", "").strip():
            msg_box = QMessageBox(
                QMessageBox.Icon.Warning,
                "API Key Required",
                f"The provider '{provider_name}' requires an API key to function.\n\n"
                "Would you like to configure your API key now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                self,
            )
            if msg_box.exec() == QMessageBox.StandardButton.Yes:
                self.open_provider_settings()
                provider_cfg = self.config.get("providers", {}).get(provider_name, {})
                if not provider_cfg.get("api_key", "").strip():
                    return False
            else:
                return False
        return True

    def _ensure_session(self) -> bool:
        """
        Ensures that an AIna session exists. If not, initializes one lazily.
        Returns True if session is ready, False if initialization failed or aborted.
        """
        active_provider = self.provider_combo_box.currentText()
        if not self._ensure_api_key(active_provider):
            return False

        if self.AIna is not None:
            return True

        provider_cfg = self.config.get("providers", {}).get(active_provider, {})
        prompt_filename = f"AIna-prompt-{self.language}-{self.language_level}.txt"
        prompt_path = get_asset_path(prompt_filename, "prompts")

        try:
            self.AIna = AIna(
                language=self.language,
                language_level=self.language_level,
                prompt_path=prompt_path,
                provider_config=provider_cfg,
            )
        except Exception as e:
            ErrorHandler.handle_exception({"error": e}, 5)
            return False

        self.change_status("Idle")
        return True

    def _on_profile_changed(self) -> None:
        """
        Handles changes to language or language level dropdowns.
        If a session exists and has a conversation, hot-swaps the prompt and
        appends a transition divider to the log.
        """
        old_lang = self.language
        old_level = self.language_level

        self.language = self.language_dict.get(
            self.language_combo_box.currentText(), "en-US"
        )
        self.language_level = self.language_level_combo_box.currentText()
        self.save_config()
        self._update_log_placeholder()

        if self.AIna is not None:
            prompt_filename = f"AIna-prompt-{self.language}-{self.language_level}.txt"
            prompt_path = get_asset_path(prompt_filename, "prompts")
            had_conversation = self.AIna.has_conversation
            self.AIna.set_profile(self.language, self.language_level, prompt_path)

            if had_conversation and (old_lang != self.language or old_level != self.language_level):
                lang_display = self.language_combo_box.currentText()
                self.log_text_edit.append(
                    f"— Switched to {lang_display} · {self.language_level} —\n"
                )

            self.change_status("Idle")
        else:
            self.change_status("Ready")

    def new_conversation(self) -> None:
        """
        Resets the conversation: clears the chat log, deletes the current AIna session,
        resets flags, disables Repeat button, and readies the UI for the next message.
        """
        if self.is_processing:
            return

        self.AIna = None
        self.last_user_message = None
        self.has_reply = False
        self.log_text_edit.clear()
        self._update_log_placeholder()
        self.repeat_button.setEnabled(False)
        self.change_status("Ready")
        self.input_field.setFocus()

    def _callback(self, indata, frames, time, status):
        """
        Callback function used during audio recording to collect input data.

        Called automatically by the audio stream for each audio block.
        Appends recorded audio data to an internal buffer for later saving.

        Args:
            indata (numpy.ndarray): The recorded audio data.
            frames (int): Number of frames in this block.
            time (CData): Timestamps and timing info for the audio block.
            status (CallbackFlags): Status information or warnings during recording.
        """

        if self.recording:
            self.frames.append(indata.copy())

    def start_recording(self) -> None:
        """
        Starts recording audio from the microphone.

        Initializes the audio input stream and begins capturing data.
        The audio chunks are collected through the `_callback` function.
        """

        self.frames = []
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            callback=self._callback,
        )
        self.stream.start()

    def stop_recording(self, filename: str = "input.wav") -> None:
        """
        Stops the audio recording and saves the captured data to a WAV file.

        Terminates the audio stream and writes the collected audio data
        to the specified file.

        Args:
            filename (str, optional): Name of the output WAV file. Defaults to
                                   "input.wav".
        """

        filename = os.path.join(BASE_DIR, "temp", filename)

        self.recording = False
        self.stream.stop()
        self.stream.close()
        audio_data = np.concatenate(self.frames, axis=0)
        wavio.write(filename, audio_data, self.samplerate, sampwidth=2)

        self.process_speech()

    def process_speech(self) -> None:
        """
        Starts the SpeechThread to convert audio input into text.

        This function initializes and runs a background thread that
        listens for audio, processes it using speech recognition,
        and emits the transcribed text when complete.
        """

        self.disable_all_buttons()
        self.input_field.setEnabled(False)

        self.speech_thread = SpeechThread(self.language)
        self.speech_thread.finished_signal.connect(self.process_speech_finished)

        # Start the worker thread
        self.speech_thread.start()

    def process_speech_finished(self, message: dict, error_status: int) -> None:
        """
        Callback function executed when the SpeechThread finishes.

        Handles the transcribed text returned by the speech recognition
        process and checks for any errors that occurred during execution.

        Args:
            message (dict): A dictionary containing the transcribed text and related metadata.
            error_status (int): An error code indicating the status of the speech process (0 means no error).
        """

        if error_status != 0:
            # Showing the error to the user
            ErrorHandler.handle_exception(message, error_status)

            # Revert GUI changes
            self.enable_all_buttons()
            self.input_field.setEnabled(True)
        else:
            text = message["message"]

            self.input_field.setText(text)

            self.enable_all_buttons()
            self.input_field.setEnabled(True)

            if self.auto_send:
                self.send_message()

    def process_message(self, AIna: AIna) -> None:
        """
        Starts a GPTClient thread to send a message to the GPT model and
        receive its response.

        Args:
            AIna (AIna): An instance that manages the GPT model interaction,
                      including sending the prompt and receiving the answer.
        """

        self.disable_all_buttons()
        self.is_processing = True
        self.change_status("Busy")

        self.log_text_edit.append("Thinking...")

        # Connecting the signals to the GPTClient
        self.gpt_thread = GPTClient(AIna)
        self.gpt_thread.finished_signal.connect(self.process_message_finished)
        self.stop_worker_signal.connect(self.gpt_thread.stop)

        # Changing the repeat_button icon
        self.repeat_button.set_icon(self.stop_path, 22)
        self.repeat_button.setEnabled(True)

        # Start the worker thread
        self.gpt_thread.start()

    def process_message_finished(self, message: dict, error_status: int) -> None:
        """
        Callback function executed when the GPTClient thread finishes.

        Handles the result of the message exchange, checks for any errors,
        and calls additional actions like playing a notification sound.

        Args:
            message (dict): The response data received from the GPT model.
            error_status (int): An error code indicating if an error occurred
                             during the request (0 means no error and -1 if the
                             user canceled the action).
        """

        # Safely disconnect stop signal to avoid stale connections
        try:
            if self.receivers(SIGNAL("stop_worker_signal()")) > 0:
                self.stop_worker_signal.disconnect()
        except RuntimeError:
            pass

        # Canceled by the user
        if error_status == -1:
            if self.AIna and self.AIna.history and self.AIna.history[-1]["role"] == "user":
                del self.AIna.history[-1]

            # Resetting the interface
            self.repeat_button.set_icon(self.repeat_path, 16)
            self.erase_log()
            self.erase_last_user_message()
            self.enable_all_buttons()
            self.is_processing = False

        # If some error occur
        elif error_status != 0:
            # Revert GUI changes and erase "Thinking..." and unsent message from log
            self.erase_log()
            self.erase_last_user_message()
            self.repeat_button.set_icon(self.repeat_path, 16)
            self.enable_all_buttons()
            self.is_processing = False
            self.change_status("Idle")

            # Roll back unanswered user message from history to prevent state corruption
            if (
                self.log_add_flag
                and self.AIna
                and self.AIna.history
                and self.AIna.history[-1]["role"] == "user"
            ):
                del self.AIna.history[-1]

            # Ask user if they wish to retry
            should_retry = ErrorHandler.handle_retryable_exception(
                message, error_status, self
            )

            if should_retry:
                self.resend_last_message()
                return
            else:
                # Restore the failed message to input field so user does not lose it
                if self.last_user_message and not self.input_field.text():
                    self.input_field.setText(self.last_user_message)
                    self.input_field.selectAll()

        else:
            self.last_user_message = None  # Clear on success
            if message["content"] != "":
                self.AIna.history.append(message)
                self.has_reply = True

                self.erase_log()
                self.log_text_edit.append(f"AIna: {message['content']}\n")

                self.play_sound()

        self.change_status("Idle")
        self.log_add_flag = False

    def play_sound(self) -> None:
        """
        Starts a SpeakerThread thread to play the model's audio response.
        """

        # Connecting the signals to the SpeakerThread
        self.speaker_thread = SpeakerThread()
        self.speaker_thread.finished_signal.connect(self.play_sound_finished)
        self.stop_worker_signal.connect(self.speaker_thread.stop)

        # Changing the repeat_button icon
        self.repeat_button.set_icon(self.stop_path, 22)
        self.repeat_button.setEnabled(True)

        # Start the worker thread
        self.speaker_thread.start()

    def play_sound_finished(self, message: dict, error_status: int) -> None:
        """
        Callback function executed when the SpeakerThread thread finishes.

        This function checks for any errors and it's responsible for preparing
        the interface for the next round of messages.

        Args:
            message (dict): Dict that will store the error message if there is
                         one, otherwise it will be an empty dict.
            error_status (int): The error number.
        """

        # Safely disconnect stop signal to avoid stale connections
        try:
            if self.receivers(SIGNAL("stop_worker_signal()")) > 0:
                self.stop_worker_signal.disconnect()
        except RuntimeError:
            pass

        if error_status != 0:
            # Showing the error to the user
            ErrorHandler.handle_exception(message, error_status)

        self.is_processing = False
        self.repeat_button.set_icon(self.repeat_path, 16)
        self.enable_all_buttons()

    def enable_all_buttons(self) -> None:
        """
        Enables all buttons and controls in the interface when idle.
        """
        self.new_conversation_button.setEnabled(True)
        if hasattr(self, "new_conversation_action"):
            self.new_conversation_action.setEnabled(True)
        self.language_combo_box.setEnabled(True)
        self.language_level_combo_box.setEnabled(True)
        self.provider_combo_box.setEnabled(True)
        self.configure_provider_button.setEnabled(True)
        self.record_button.setEnabled(True)
        self.repeat_button.setEnabled(self.has_reply)

        if bool(self.input_field.text().strip()):
            self.send_button.setEnabled(True)

    def disable_all_buttons(self) -> None:
        """
        Disables controls in the interface during background processing.
        """
        self.record_button.setEnabled(False)
        self.send_button.setEnabled(False)
        self.repeat_button.setEnabled(False)
        self.new_conversation_button.setEnabled(False)
        if hasattr(self, "new_conversation_action"):
            self.new_conversation_action.setEnabled(False)
        self.language_combo_box.setEnabled(False)
        self.language_level_combo_box.setEnabled(False)
        self.provider_combo_box.setEnabled(False)
        self.configure_provider_button.setEnabled(False)

    def send_message(self) -> None:
        """
        Sends a message to the model to be processed. Initializes the AIna session
        lazily if not already created.
        """
        message = self.input_field.text().strip()
        if not message:
            return

        if not self._ensure_session():
            return

        self.last_user_message = message
        self.input_field.add_to_history(message)
        self.input_field.setText("")

        self.AIna.history.append({"role": "user", "content": message})
        self.log_text_edit.append(f"You: {message}\n")
        self.log_add_flag = True

        self.process_message(self.AIna)

    def resend_last_message(self) -> None:
        """
        Re-sends the last failed user message to the model.
        """

        if self.AIna is None or not self.last_user_message:
            return

        # Ensure user message is in history
        if (
            not self.AIna.history
            or self.AIna.history[-1]["role"] != "user"
            or self.AIna.history[-1]["content"] != self.last_user_message
        ):
            self.AIna.history.append(
                {"role": "user", "content": self.last_user_message}
            )

        self.log_text_edit.append(f"You: {self.last_user_message}\n")
        self.log_add_flag = True
        self.process_message(self.AIna)

    def erase_last_user_message(self) -> None:
        """
        Removes the last 'You: <message>' entry from the conversation log UI.
        """

        if not self.last_user_message:
            return

        target_text = f"You: {self.last_user_message}"
        plain_text = self.log_text_edit.toPlainText().rstrip()
        if plain_text.endswith(target_text):
            idx = plain_text.rfind(target_text)
            cursor = self.log_text_edit.textCursor()
            cursor.movePosition(QTextCursor.End)
            cursor.setPosition(idx, QTextCursor.KeepAnchor)
            cursor.removeSelectedText()
            self.log_text_edit.setFontPointSize(16)

    def erase_log(self, lenght: int = 0) -> None:
        """
        Erase characters from log text.

        Args:
            lenght (int): Represents the length of the string that will be
                       erased. Defaults to 0.
        """

        cursor = self.log_text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)  # Move cursor to the end

        if lenght == 0:
            if len(self.log_text_edit.toPlainText()) < 12:
                cursor.setPosition(
                    cursor.position() - 11, QTextCursor.KeepAnchor
                )  # Select the last 11 characters ("Thinking...")
            else:
                cursor.setPosition(
                    cursor.position() - 12, QTextCursor.KeepAnchor
                )  # This case also remove the "\n"
        else:
            if len(self.log_text_edit.toPlainText()) < (lenght + 13):
                cursor.setPosition(
                    cursor.position() - (lenght + 12), QTextCursor.KeepAnchor
                )  # Select the last message
            else:
                cursor.setPosition(
                    cursor.position() - (lenght + 13), QTextCursor.KeepAnchor
                )  # This case also remove the "\n"
        cursor.removeSelectedText()  # Remove "Thinking..."

        self.log_text_edit.setFontPointSize(16)

    def toggle_button_state(self, text: str) -> None:
        """
        Enable the send button if there's text and not currently processing.

        Args:
            text (str): text in the EditLine.
        """
        if not self.is_processing:
            self.send_button.setEnabled(bool(text.strip()))

    def handle_repeat_button(self) -> None:
        """
        Sets the action of the repeat button. It varies between repeating the
        audio and stopping the worker thread from executing.
        """

        is_running = (
            (self.gpt_thread is not None and self.gpt_thread.isRunning())
            or (self.speaker_thread is not None and self.speaker_thread.isRunning())
        )

        if not is_running:
            self.disable_all_buttons()
            self.play_sound()
        else:
            self.stop_worker_signal.emit()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """
        Handles key press events. If the Enter/Return key is pressed
        without any modifiers and the send button is enabled, it simulates
        a click on the send button.

        Args:
            event (QKeyEvent): The key event object containing information about
                            the key that was pressed, including the key code and
                            any modifier keys (e.g., Shift, Ctrl).
        """

        if (
            event.key() in (Qt.Key_Return, Qt.Key_Enter)
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
            and self.send_button.isEnabled()
        ):
            self.send_button.click()  # Simulate button click

    def change_status(self, status: str) -> None:
        """
        Change the status displayed in the status bar.

        Args:
            status (str): Represents the state of the profile ('Ready', 'Idle', 'Busy').
        """
        provider_name = self.config.get("active_provider", "LM Studio (Local)")

        if status == "Busy":
            self.status_message.setText(
                f"Profile: <b>AIna-{self.language}-{self.language_level}</b> | Provider: <b>{provider_name}</b> | Status: <b>Busy</b>"
            )
        elif status == "Idle":
            self.status_message.setText(
                f"Profile: <b>AIna-{self.language}-{self.language_level}</b> | Provider: <b>{provider_name}</b> | Status: <b>Idle</b>"
            )
        else:
            self.status_message.setText(
                f"Profile: <b>AIna-{self.language}-{self.language_level}</b> | Provider: <b>{provider_name}</b> | Status: <b>Ready</b>"
            )

    def _on_provider_changed(self, provider_name: str) -> None:
        """
        Handles changing the active provider from the sidebar dropdown.
        Hot-swaps the provider client on an existing session while preserving history.
        """
        self.config["active_provider"] = provider_name
        self.save_config()
        if self.AIna is not None:
            provider_cfg = self.config.get("providers", {}).get(provider_name, {})
            self.AIna.set_provider(provider_cfg)
            self.change_status("Idle")
        else:
            self.change_status("Ready")

    def open_provider_settings(self) -> None:
        """
        Opens the dialog to configure LLM providers, credentials, and models.
        """
        dialog = ProviderSettingsDialog(self.config, self.config_path, self)
        if dialog.exec():
            active = self.config.get("active_provider", "LM Studio (Local)")
            idx = self.provider_combo_box.findText(active, Qt.MatchFixedString)
            if idx >= 0:
                self.provider_combo_box.setCurrentIndex(idx)
            self._on_provider_changed(active)

    def save_config(self) -> None:
        """
        Saves the configuration defined in the configuration JSON.
        """

        # Set the new values to the config dict
        self.config["theme"] = self.current_theme
        self.config["language"] = self.language_combo_box.currentText()
        self.config["language_level"] = (
            self.language_level_combo_box.currentText()
        )
        self.config["auto_send"] = self.auto_send_checkbox.isChecked()
        self.config["active_provider"] = self.provider_combo_box.currentText()

        save_config(self.config, self.config_path)


def get_asset_path(filename: str, asset_type: str) -> str:
    """
    Get correct path for assets in both development and frozen (exe) mode.

    Args:
        filename (str): Name of the file to be loaded.
        asset_type (str): The type of the file, it varies between "icons", "images",
                 "prompts" and "styles".

    Returns:
        str: The corret path for the file.
    """

    if getattr(sys, "frozen", False):  # Running as .exe
        base_path = os.path.join(sys._MEIPASS, "assets", asset_type)
    else:
        base_path = os.path.join(BASE_DIR, "assets", asset_type)

    return os.path.join(base_path, filename)
