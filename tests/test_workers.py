from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from src.aina.SpeechProcessor import SpeechProcessor
from src.aina.SpeechThread import SpeechThread
from src.aina.GPTClient import GPTClient
from src.aina.SpeakerThread import SpeakerThread
from tests.conftest import make_mock_streaming_chunks


def test_speech_processor_text_to_speech(tmp_path: Path):
    with patch("src.aina.SpeechProcessor.gTTS") as mock_gtts_cls:
        mock_instance = mock_gtts_cls.return_value
        mock_instance.save.side_effect = lambda path: Path(path).write_bytes(b"dummy_mp3")

        output_path = SpeechProcessor.text_to_speech(
            "Hello world", "en", base_dir=str(tmp_path)
        )
        assert Path(output_path).exists()
        mock_gtts_cls.assert_called_once_with(
            text="Hello world", lang="en", slow=False
        )


def test_speech_processor_speech_to_text(tmp_path: Path):
    # Create a dummy wav file
    audio_dir = tmp_path / "temp"
    audio_dir.mkdir(parents=True, exist_ok=True)
    wav_file = audio_dir / "input.wav"
    wav_file.write_bytes(b"dummy_wav_data")

    mock_segment = MagicMock()
    mock_segment.text = "transcribed voice"

    mock_model = MagicMock()
    mock_model.transcribe.return_value = ([mock_segment], None)

    with patch.object(SpeechProcessor, "get_whisper_model", return_value=mock_model):
        result = SpeechProcessor.speech_to_text("en-US", base_dir=str(tmp_path))
        assert result == "transcribed voice"
        mock_model.transcribe.assert_called_once()


def test_speech_thread_success(qtbot, tmp_path: Path):
    with patch("src.aina.SpeechThread.SpeechProcessor.speech_to_text", return_value="recognized audio"):
        thread = SpeechThread(language="en-US", base_dir=str(tmp_path))
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 0
        assert msg["message"] == "recognized audio"


def test_speech_thread_error(qtbot, tmp_path: Path):
    with patch("src.aina.SpeechThread.SpeechProcessor.speech_to_text", side_effect=RuntimeError("Mic failure")):
        thread = SpeechThread(language="en-US", base_dir=str(tmp_path))
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 4
        assert "Mic failure" in str(msg["error"])


def test_gpt_client_streaming_success(qtbot):
    mock_aina = MagicMock()
    mock_aina.language = "en-US"
    mock_aina.history = [{"role": "user", "content": "hi"}]
    mock_aina.model_name = "test-model"

    chunks = make_mock_streaming_chunks(["Hello", " there", "!"])
    mock_aina.client.chat.completions.create.return_value = chunks

    with patch("src.aina.GPTClient.SpeechProcessor.text_to_speech", return_value="path/to/audio.mp3"):
        thread = GPTClient(AIna=mock_aina)
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 0
        assert msg["role"] == "assistant"
        assert msg["content"] == "Hello there!"


def test_gpt_client_stop_cancellation(qtbot):
    mock_aina = MagicMock()
    mock_aina.language = "en-US"
    mock_aina.history = [{"role": "user", "content": "hi"}]

    def slow_chunks():
        for word in ["Chunk1", "Chunk2"]:
            yield from make_mock_streaming_chunks([word])

    mock_aina.client.chat.completions.create.return_value = slow_chunks()

    thread = GPTClient(AIna=mock_aina)
    # Stop before/during iteration
    thread.stop()

    with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
        thread.start()

    msg, code = blocker.args
    assert code == -1


def test_gpt_client_api_error(qtbot):
    mock_aina = MagicMock()
    mock_aina.history = []
    mock_aina.client.chat.completions.create.side_effect = ConnectionError("LM Studio not running")

    thread = GPTClient(AIna=mock_aina)
    with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
        thread.start()

    msg, code = blocker.args
    assert code == 1
    assert "LM Studio not running" in str(msg["error"])


def test_gpt_client_tts_error(qtbot):
    mock_aina = MagicMock()
    mock_aina.language = "en-US"
    mock_aina.history = []
    chunks = make_mock_streaming_chunks(["Response"])
    mock_aina.client.chat.completions.create.return_value = chunks

    with patch("src.aina.GPTClient.SpeechProcessor.text_to_speech", side_effect=ValueError("TTS network timeout")):
        thread = GPTClient(AIna=mock_aina)
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 2
        assert "TTS network timeout" in str(msg["error"])


def test_speaker_thread_success(qtbot, tmp_path: Path):
    audio_dir = tmp_path / "temp"
    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "output.mp3").write_bytes(b"dummy")

    mock_sound = MagicMock()
    mock_sound.is_alive.return_value = False  # Sound finishes immediately

    with patch("src.aina.SpeakerThread.playsound", return_value=mock_sound):
        thread = SpeakerThread(base_dir=str(tmp_path))
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 0


def test_speaker_thread_stop(qtbot, tmp_path: Path):
    audio_dir = tmp_path / "temp"
    audio_dir.mkdir(parents=True, exist_ok=True)
    (audio_dir / "output.mp3").write_bytes(b"dummy")

    mock_sound = MagicMock()
    # Stay alive until stopped
    mock_sound.is_alive.return_value = True

    with patch("src.aina.SpeakerThread.playsound", return_value=mock_sound):
        thread = SpeakerThread(base_dir=str(tmp_path))
        thread.stop()
        with qtbot.waitSignal(thread.finished_signal, timeout=2000) as blocker:
            thread.start()

        msg, code = blocker.args
        assert code == 0
        mock_sound.stop.assert_called_once()
