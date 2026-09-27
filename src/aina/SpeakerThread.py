import os

from playsound3 import playsound
from PySide6.QtCore import QThread, Signal, Slot


class SpeakerThread(QThread):
    """
    Threaded class for playing audio files on speaker.

    This class runs in a separate thread to load and play an audio on speaker.
    It supports asynchronous execution and can be gracefully stopped via a connected Slot.
    """

    finished_signal = Signal(dict, int)

    def __init__(self, base_dir: str | None = None) -> None:
        """
        Initializes the SpeakerThread.
        """

        super().__init__()

        self.BASE_DIR = base_dir or os.environ.get("AINA_BASE_DIR")
        self._sound = None
        self._should_stop = False

    def run(self) -> None:
        """
        Runs the thread logic to load and play an audio on speaker.

        This method loads and plays an audio file using `playsound3`.
        Executed when the thread starts.
        """

        filename = os.path.join(self.BASE_DIR, "temp", "output.mp3")

        try:
            self._sound = playsound(filename, block=False)

            while self._sound.is_alive() and not self._should_stop:
                self.msleep(50)

            if self._should_stop and self._sound is not None:
                self._sound.stop()
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
        if self._sound is not None:
            try:
                self._sound.stop()
            except Exception:
                pass
