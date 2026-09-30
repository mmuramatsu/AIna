import os

from gtts import gTTS


class SpeechProcessor:
    """
    Utility class for processing text and audio files.

    Provides methods to convert text into audio using gTTS and transcribe audio
    into text locally and offline using faster-whisper.
    """

    _whisper_model = None

    @classmethod
    def get_whisper_model(cls, model_size: str = "base"):
        """
        Lazily loads and caches the faster-whisper model singleton.

        Args:
            model_size (str): Whisper model size ('tiny', 'base', etc.). Defaults to 'base'.

        Returns:
            WhisperModel: The loaded model instance.
        """
        if cls._whisper_model is None:
            from faster_whisper import WhisperModel

            cls._whisper_model = WhisperModel(
                model_size, device="cpu", compute_type="int8"
            )
        return cls._whisper_model

    @classmethod
    def speech_to_text(
        cls, language: str = "en-US", base_dir: str = None
    ) -> str:
        """
        Transcribes spoken audio into text locally using faster-whisper.

        Loads the recorded WAV audio file and runs offline speech recognition.

        Args:
            language (str, optional): The language code for speech recognition
                (e.g., "en-US" for English, "ja" for Japanese). Defaults to "en-US".
            base_dir (str, optional): Base directory of the application. Falls back
                to AINA_BASE_DIR env var if not provided.

        Returns:
            str: The transcribed text.
        """
        if base_dir is None:
            base_dir = os.environ.get("AINA_BASE_DIR")
        if base_dir is None:
            raise ValueError(
                "base_dir not provided and AINA_BASE_DIR env var not set"
            )
        filename = os.path.join(base_dir, "temp", "input.wav")

        model = cls.get_whisper_model()
        lang_code = language.split("-")[0] if language else None

        segments, _ = model.transcribe(filename, language=lang_code, beam_size=5)
        text = " ".join(segment.text.strip() for segment in segments).strip()
        return text

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
