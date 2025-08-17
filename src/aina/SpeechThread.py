from PySide6.QtCore import QThread, Signal

from .SpeechProcessor import SpeechProcessor


class SpeechThread(QThread):
    """
    Threaded class to run the `speech_to_text` function from `SpeechProcessor`.

    This class runs in a separate thread to call `speech_to_text` function,
    avoiding locking the main thread during this process.
    """

    finished_signal = Signal(dict, int)

    def __init__(self, language: str) -> None:
        """
        Initializes the SpeechThread.

        Args:
            language (str): The language code for the speech recognition
                (e.g., "en-US" for English, "ja" for Japanese).
        """

        super().__init__()
        self.language = language

    def run(self) -> None:
        """
        Call `speech_to_text` function from `SpeechProcessor` and send back to
        the main thread the text
        """

        try:
            text = SpeechProcessor.speech_to_text(self.language)
        except Exception as e:
            self.finished_signal.emit({"error": text}, 4)
            return

        # Emit the finished signal
        self.finished_signal.emit({"message": text}, 0)
