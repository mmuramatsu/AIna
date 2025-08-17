import os

from gtts import gTTS
import speech_recognition as sr


class SpeechProcessor:
    """
    Utility class for processing text and audio files.

    This class has methods specialized in turn text into audio files and audio file to text.
    """

    @staticmethod
    def speech_to_text(language: str = "en-US") -> None:
        """
        Converts spoken audio into text using the SpeechRecognition library.

        Load an audio file and transcribes it into text using a speech recognition
        engine (e.g., Google Speech Recognition).

        Args:
            language (str, optional): The language code for the speech recognition
                (e.g., "en-US" for English, "ja" for Japanese). Defaults to "en-US".
        """

        BASE_DIR = os.environ.get("AINA_BASE_DIR")
        filename = os.path.join(BASE_DIR, "temp", "input.wav")

        r = sr.Recognizer()

        input_file = sr.AudioFile(filename)
        with input_file as source:
            audio = r.record(source)

        s = r.recognize_google(audio, language=language)

        return s

    @staticmethod
    def text_to_speech(text: str, language: str) -> None:
        """
        Converts text into spoken audio using the gTTS library and saves it as an MP3 file.

        Uses Google Text-to-Speech (gTTS) to synthesize speech from the given text
        and saves the resulting audio to an MP3 file.

        Args:
            text (str): The input text to be converted into speech.
            language (str): The language code for the speech synthesis
                (e.g., "en" for English, "ja" for Japanese).
        """

        speech = gTTS(text=text, lang=language, slow=False)

        BASE_DIR = os.environ.get("AINA_BASE_DIR")
        filename = os.path.join(BASE_DIR, "temp", "output.mp3")

        speech.save(filename)
