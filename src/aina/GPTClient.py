from PySide6.QtCore import QThread, Signal, Slot

from .SpeechProcessor import SpeechProcessor

from .AIna import AIna


class GPTClient(QThread):
    """
    Threaded client for communicating with a GPT model and generating audio.

    This class runs in a separate thread to send a prompt to a GPT model,
    receive the response, and process that response into audio output.
    It supports asynchronous execution and can be gracefully stopped via
    a connected Slot.
    """

    finished_signal = Signal(dict, int)

    def __init__(self, AIna: AIna | None = None):
        """
        Initializes the GPTClient thread.

        Args:
            AIna (AIna, optional): The GPT model to be used for generating responses.
        """
        super().__init__()

        self.AIna = AIna
        self._should_stop = False

    def run(self):
        """
        Runs the thread logic to send a request to the GPT model and generate audio.

        This method handles communication with the model and performs text-to-speech
        conversion based on the model's response. Executed when the thread starts.
        """

        new_message = {"role": "assistant", "content": ""}

        try:
            completion = self.AIna.client.chat.completions.create(
                model="model-identifier",
                messages=self.AIna.history,
                temperature=1.2,
                stream=True,
            )

            for chunk in completion:
                if self._should_stop:
                    # Stream stopped by user.
                    self.finished_signal.emit({}, -1)
                    return

                if chunk.choices[0].delta.content:
                    new_message["content"] += chunk.choices[0].delta.content
        except Exception as e:
            # Can't make a connection or lost the connectio with the GPT model
            self.finished_signal.emit({"error": e}, 1)
            return

        # Turning AIna's answer into speech
        if not self._should_stop:
            try:
                SpeechProcessor.text_to_speech(
                    new_message["content"], self.AIna.language
                )
            except Exception as e:
                # Handles some error during text to speech process.
                self.finished_signal.emit({"error": e}, 2)
                return
        else:
            # Stream stopped by user.
            self.finished_signal.emit({}, -1)
            return

        # If no error occur, send the message back to the main thread.
        self.finished_signal.emit(new_message, 0)

    @Slot()
    def stop(self):
        """
        Stops the GPTClient thread.

        This Slot can be connected to external signals to safely interrupt and stop
        the thread's execution.
        """

        self._should_stop = True
