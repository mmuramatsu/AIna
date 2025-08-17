import os
import sys

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
    QTextEdit,
    QComboBox,
    QCheckBox,
    QStatusBar,
)
from PySide6.QtGui import QPixmap, QTextCursor, QAction, QKeyEvent
from PySide6.QtCore import Qt, Signal
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

    def __init__(self, config: dict):
        """
        Initialize the UI class

        Args:
            config (dict): _description_
        """

        super().__init__()

        self.config = config
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
        self.setGeometry(100, 100, 1000, 600)

        self.language_dict = {"English": "en-US", "日本語": "ja"}

        os.environ["AINA_BASE_DIR"] = BASE_DIR

        mic_path = get_asset_path("mic.png", "icons")
        image_path = get_asset_path("AIna.png", "images")
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

        # Add the QComboBox to the form layout with a label
        config_layout.addRow("Select Language:", self.language_combo_box)

        # Add the QComboBox to the form layout with a label
        config_layout.addRow("Language level:", self.language_level_combo_box)

        # Create the Auto-send checkbox
        self.auto_send_checkbox = QCheckBox("Auto-send")
        self.auto_send_checkbox.setToolTip(
            "Automatically send the transcribed audio message"
        )
        self.auto_send_checkbox.setChecked(self.config["auto_send"])
        config_layout.addRow(self.auto_send_checkbox)

        # Create the Initialize button
        self.initialize_button = QPushButton("Initialize AIna")
        self.initialize_button.pressed.connect(self.initialize_model)
        self.initialize_button.setToolTip("Initialize AIna's model")
        config_layout.addRow(self.initialize_button)

        # Create the configuration frame and set its properties
        config_frame = QFrame()
        config_frame.setLayout(config_layout)
        config_frame.setFrameShape(QFrame.StyledPanel)
        config_frame.setMinimumWidth(200)
        # config_frame.setMaximumWidth(150)
        config_frame.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # Center Panel: Image and Button
        image_label = QLabel()
        pixmap = QPixmap(image_path)  # Replace with your image path
        image_label.setPixmap(pixmap)
        image_label.setScaledContents(True)

        # Create the animated microphone button
        self.record_button = AnimatedButton(mic_path)
        self.record_button.pressed.connect(self.start_recording)
        self.record_button.released.connect(self.stop_recording)
        self.record_button.setToolTip(
            "Hold to record an audio to transcribe to text"
        )
        self.record_button.setEnabled(False)

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
        center_layout.addWidget(image_label)
        center_layout.addWidget(
            self.record_button, alignment=Qt.AlignmentFlag.AlignCenter
        )
        center_layout.addLayout(input_layout)
        center_frame = QFrame()
        center_frame.setLayout(center_layout)
        center_frame.setFrameShape(QFrame.StyledPanel)
        # center_frame.setMinimumWidth(200)
        center_frame.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # Right Panel: Log
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        self.log_text_edit.setFontPointSize(16)
        log_frame = QFrame()
        log_frame.setLayout(QVBoxLayout())
        log_frame.layout().addWidget(self.log_text_edit)
        log_frame.setFrameShape(QFrame.StyledPanel)
        log_frame.setMinimumWidth(200)
        log_frame.setMinimumWidth(400)
        log_frame.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding
        )

        # Add panels to main layout
        main_layout.addWidget(config_frame, 1)
        main_layout.addWidget(center_frame, 2)
        main_layout.addWidget(log_frame, 1)

        central_widget.setLayout(main_layout)

        # Create the menu bar
        menu_bar = self.menuBar()

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

        # Status bar
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self.status_message = QLabel()
        self.status_message.setText(
            'Model: <b>None</b> | Status: <span style="color:red;"><b>Not Loaded</b></span>'
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

        self.auto_send = False
        self.AIna = None

        # Control variables
        self.is_processing = False
        self.log_add_flag = False

        self.current_theme = None
        self.toggle_theme(self.config["theme"])

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

    def toggle_theme(self, theme_name: str) -> None:
        """
        Toggles the application theme and updates all GUI widgets.

        Sets the current theme (e.g., 'light' or 'dark'), applies the theme
        to all relevant widgets, and delegates the stylesheet application
        to `apply_theme`.

        Args:
            theme_name (str): The name of the theme to apply ('light' or 'dark').
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

            self.save_config()

    def initialize_model(self) -> None:
        """
        Initialize the AIna model based on the settings. Any errors that occur
        will be handled and displayed to the user.
        """

        self.language = self.language_dict[
            self.language_combo_box.currentText()
        ]
        self.language_level = self.language_level_combo_box.currentText()
        self.auto_send = self.auto_send_checkbox.isChecked()

        self.log_text_edit.setText("")

        error = False

        try:
            self.AIna = AIna(
                self.language,
                self.language_level,
                get_asset_path(
                    f"AIna-prompt-{self.language}-{self.language_level}.txt",
                    "prompts",
                ),
            )
        except Exception as e:
            # Showing the error to the user
            ErrorHandler.handle_exception({"error": e}, 5)
            error = True

        if not error:
            self.save_config()
            self.change_status("Idle")
            self.process_message(self.AIna)

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

        self.worker_thread = SpeechThread(self.language)
        self.worker_thread.finished_signal.connect(self.process_speech_finished)

        # Start the worker thread
        self.worker_thread.start()

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

            if self.auto_send == True:
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
        self.worker_thread = GPTClient(AIna)
        self.worker_thread.finished_signal.connect(self.process_message_finished)
        self.stop_worker_signal.connect(self.worker_thread.stop)

        # Changing the repeat_button icon
        self.repeat_button.set_icon(self.stop_path, 22)
        self.repeat_button.setEnabled(True)

        # Start the worker thread
        self.worker_thread.start()

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

        # Canceled by the user
        if error_status == -1:
            # Getting the user's message lenght to remove from the log
            if self.log_add_flag:
                message_len = len(f"You: {self.AIna.history[-1]["content"]}\n")
            else:
                message_len = len("")

            del self.AIna.history[-1]

            # Reseting the interface
            self.repeat_button.set_icon(self.repeat_path, 16)
            self.stop_worker_signal.disconnect()
            self.erase_log(message_len)
            self.enable_all_buttons()
            self.is_processing = False

        # If some error occur
        elif error_status != 0:
            # Showing the error to the user
            ErrorHandler.handle_exception(message, error_status)

            # Revert GUI changes
            self.erase_log()
            self.enable_all_buttons()
            self.is_processing = False
        else:
            if message["content"] != "":
                self.AIna.history.append(message)

                self.erase_log()
                self.log_text_edit.append(f"AIna: {message["content"]}\n")

                self.play_sound()

        self.change_status("Idle")
        self.log_add_flag = False

    def play_sound(self) -> None:
        """
        Starts a SpeakerThread thread to play the model's audio response.
        """

        # Connecting the signals to the SpeakerThread
        self.worker_thread = SpeakerThread()
        self.worker_thread.finished_signal.connect(self.play_sound_finished)
        self.stop_worker_signal.connect(self.worker_thread.stop)

        # Changing the repeat_button icon
        self.repeat_button.set_icon(self.stop_path, 22)
        self.repeat_button.setEnabled(True)

        # Start the worker thread
        self.worker_thread.start()

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

        if error_status != 0:
            # Showing the error to the user
            ErrorHandler.handle_exception(message, error_status)

        self.is_processing = False
        self.repeat_button.set_icon(self.repeat_path, 16)
        self.enable_all_buttons()

    def enable_all_buttons(self) -> None:
        """
        Enables all buttons in the interface.
        """

        self.record_button.setEnabled(True)
        self.initialize_button.setEnabled(True)

        # If there is text in the input_field, enable it
        if self.input_field.text() != "":
            self.send_button.setEnabled(True)

        self.repeat_button.setEnabled(True)

    def disable_all_buttons(self) -> None:
        """
        Disables all buttons in the interface.
        """

        self.record_button.setEnabled(False)
        self.initialize_button.setEnabled(False)
        self.send_button.setEnabled(False)
        self.repeat_button.setEnabled(False)

    def send_message(self) -> None:
        """
        Sends a message to the model to be processed.
        """

        message = self.input_field.text()
        self.input_field.setText("")

        self.AIna.history.append({"role": "user", "content": message})
        self.log_text_edit.append(f"You: {message}\n")
        self.log_add_flag = True

        self.process_message(self.AIna)

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
        Enable the button if there's text; otherwise, disable it.

        Args:
            text (str): text in the EditLine.
        """

        # Enable the button only if there's a model loaded and is not processing something
        if self.AIna != None and not self.is_processing:
            self.send_button.setEnabled(bool(text.strip()))

    def handle_repeat_button(self) -> None:
        """
        Sets the action of the repeat button. It varies between repeating the
        audio and stopping the worker thread from executing.
        """

        if not self.worker_thread.isRunning():
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
        Change the status of the model.

        Args:
            status (str): Represents the state of the model. It varies between
                       "Idle" and "Busy".
        """

        if status == "Busy":
            self.status_message.setText(
                f"Model: <b>AIna-{self.language}-{self.language_level}</b> | Status: <b>Busy</b>"
            )
        else:
            self.status_message.setText(
                f"Model: <b>AIna-{self.language}-{self.language_level}</b> | Status: <b>Idle</b>"
            )

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

        save_config(self.config, CONFIG_PATH)


def get_asset_path(filename: str, type: str) -> str:
    """
    Get correct path for assets in both development and frozen (exe) mode.

    Args:
        filename (str): Name of the file to be loaded.
        type (str): The type of the file, it varies between "icons", "images",
                 "prompts" and "styles".

    Returns:
        str: The corret path for the file.
    """

    if getattr(sys, "frozen", False):  # Running as .exe
        base_path = os.path.join(sys._MEIPASS, "assets", type)
    else:
        base_path = os.path.join(BASE_DIR, "assets", type)

    return os.path.join(base_path, filename)
