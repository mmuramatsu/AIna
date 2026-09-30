from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QMessageBox
from src.aina.ErrorHandler import ErrorHandler


def test_format_error_message_codes():
    for code in (1, 2, 3, 4, 5):
        msg = ErrorHandler._format_error_message({"error": "test error"}, code)
        assert "Details: \"test error\"" in msg


def test_connection_refused_diagnostic_tip():
    msg = ErrorHandler._format_error_message(
        {"error": "Connection refused to http://localhost:11434"}, 1
    )
    assert "Tip: If you are using a local provider" in msg


def test_auth_error_diagnostic_tip():
    msg = ErrorHandler._format_error_message(
        {"error": "Error 401: Incorrect API key provided"}, 1
    )
    assert "Tip: Authentication failed. Please verify your API key" in msg


def test_model_not_found_diagnostic_tip():
    msg = ErrorHandler._format_error_message(
        {"error": "NotFoundError: 404 model not found"}, 1
    )
    assert "Tip: The specified model was not found" in msg


def test_rate_limit_diagnostic_tip():
    msg = ErrorHandler._format_error_message(
        {"error": "RateLimitError: 429 quota exceeded"}, 1
    )
    assert "Tip: Provider quota or rate limit exceeded" in msg


def test_handle_retryable_exception_retry():
    with patch("src.aina.ErrorHandler.QMessageBox") as MockMsgBox:
        mock_instance = MockMsgBox.return_value
        mock_retry_btn = MagicMock()
        # First addButton call adds "Retry", second adds Cancel
        mock_instance.addButton.side_effect = [mock_retry_btn, MagicMock()]
        mock_instance.clickedButton.return_value = mock_retry_btn

        result = ErrorHandler.handle_retryable_exception(
            {"error": "Network timeout"}, 1
        )
        assert result is True


def test_handle_retryable_exception_cancel():
    with patch("src.aina.ErrorHandler.QMessageBox") as MockMsgBox:
        mock_instance = MockMsgBox.return_value
        mock_retry_btn = MagicMock()
        mock_cancel_btn = MagicMock()
        mock_instance.addButton.side_effect = [mock_retry_btn, mock_cancel_btn]
        # User clicked Cancel
        mock_instance.clickedButton.return_value = mock_cancel_btn

        result = ErrorHandler.handle_retryable_exception(
            {"error": "Network timeout"}, 1
        )
        assert result is False
