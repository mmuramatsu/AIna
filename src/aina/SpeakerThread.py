import os

import pygame
from PySide6.QtCore import QThread, Signal, Slot


class SpeakerThread(QThread):
    """
    Threaded class for playing audio files on speaker.

    This class runs in a separate thread to load and play an audio on speaker.
    It supports asynchronous execution and can be gracefully stopped via a connected Slot.
    """

    finished_signal = Signal(dict, int)

    def __init__(self) -> None:
        """
        Initializes the SpeakerThread.
        """

        super().__init__()

        self.BASE_DIR = os.environ.get("AINA_BASE_DIR")

        self._should_stop = False

    def run(self) -> None:
        """
        Runs the thread logic to load and play an audio on speaker.

        This method load and play an audio file using `pygame.mixer`.
        Executed when the thread starts.
        """

        filename = os.path.join(self.BASE_DIR, "temp", "output.mp3")

        try:
            # Initialize the mixer module
            pygame.mixer.init()

            # Load the MP3 file
            pygame.mixer.music.load(filename)

            # Play the MP3 file
            pygame.mixer.music.play()

            # Wait for the music to finish playing
            while pygame.mixer.music.get_busy() and not self._should_stop:
                pygame.time.Clock().tick(10)

            pygame.mixer.music.unload()
        except Exception as e:
            self.finished_signal.emit({"error": e}, 3)
            return

        # Emit the finished signal
        self.finished_signal.emit({}, 0)

    @Slot()
    def stop(self) -> None:
        """
        Stops the SpeakerThread thread.

        This Slot can be connected to external signals to safely interrupt and stop
        the thread's execution.
        """

        self._should_stop = True
