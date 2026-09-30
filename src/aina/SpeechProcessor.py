import os

from gtts import gTTS
import speech_recognition as sr


class SpeechProcessor:
    """
    Utility class for processing text and audio files.

    This class has methods specialized in turn text into audio files and audio file to text.
    """

    @staticmethod
    def speech_to_text(language: str = "en-US", base_dir: str = None) -> None:
        """
        Converts spoken audio into text using the SpeechRecognition library.

        Load an audio file and transcribes it into text using a speech recognition
        engine (e.g., Google Speech Recognition).

        Args:
            language (str, optional): The language code for the speech recognition
                (e.g., "en-US" for English, "ja" for Japanese). Defaults to "en-US".
            base_dir (str, optional): Base directory of the application. Falls back
                to AINA_BASE_DIR env var if not provided.
        """

        if base_dir is None:
            base_dir = os.environ.get("AINA_BASE_DIR")
        if base_dir is None:
            raise ValueError("base_dir not provided and AINA_BASE_DIR env var not set")
        filename = os.path.join(base_dir, "temp", "input.wav")

        r = sr.Recognizer()

        input_file = sr.AudioFile(filename)
        with input_file as source:
            audio = r.record(source)

        s = r.recognize_google(audio, language=language)

        return s

    @staticmethod
    def text_to_speech(text: str, language: str, base_dir: str = None) -> None:
        """
        Converts text into spoken audio using the gTTS library and saves it as an MP3 file.

        Uses Google Text-to-Speech (gTTS) to synthesize speech from the given text
        and saves the resulting audio to an MP3 file.

        Args:
            text (str): The input text to be converted into speech.
            language (str): The language code for the speech synthesis
                (e.g., "en" for English, "ja" for Japanese).
            base_dir (str, optional): Base directory of the application. Falls back
                to AINA_BASE_DIR env var if not provided.
        """

        speech = gTTS(text=text, lang=language, slow=False)

        if base_dir is None:
            base_dir = os.environ.get("AINA_BASE_DIR")
        if base_dir is None:
            raise ValueError("base_dir not provided and AINA_BASE_DIR env var not set")
        filename = os.path.join(base_dir, "temp", "output.mp3")
        os.makedirs(os.path.dirname(filename), exist_ok=True)

        speech.save(filename)
        return filename
