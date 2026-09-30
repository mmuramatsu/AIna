from PySide6.QtWidgets import QMessageBox


class ErrorHandler:
    """
    Utility class for handling and displaying error messages to the user.

    Uses QMessageBox to show predefined user-friendly error messages based
    on the error code, followed by any additional exception information.
    """

    @staticmethod
    def handle_exception(message: dict, error_status: int) -> None:
        """
        Displays an error message using QMessageBox based on the given status
        code and exception details.

        Args:
            message (dict): The original exception data or message payload.
            error_status (int): The numeric code identifying the type of error.
        """

        error_message = {
            1: (
                "An error occurred while communicating with the GPT model. This"
                " may be due to network issues or model unavailability. Try "
                'reinitializing the model.\n\nDetails: "'
            ),
            2: (
                "Failed to generate audio from text. This could be due to an "
                "issue with the text-to-speech engine or an unsupported format."
                '\n\nDetails: "'
            ),
            3: (
                "An error occurred while playing the generated audio. Ensure "
                "that the audio file exists and your system's audio output is "
                'working properly.\n\nDetails: "'
            ),
            4: (
                "Could not transcribe the audio. The audio file may be "
                "corrupted, or the speech recognition service encountered an "
                'issue.\n\nDetails: "'
            ),
            5: (
                "Profile initialization failed. This may be due to missing "
                "dependencies, incorrect API credentials, or a configuration "
                'issue. Please check the settings and try again.\n\nDetails: "'
            ),
        }

        err = message.get("error")
        err_str = str(err) if err is not None else ""

        # Provide actionable context for common LLM provider connection failures
        extra_hint = ""
        if error_status == 1:
            if any(term in err_str for term in ("Connection refused", "Failed to connect", "ConnectError")):
                extra_hint = "\n\nTip: If you are using a local provider (LM Studio or Ollama), verify that the local server is running."
            elif any(term in err_str for term in ("401", "Incorrect API key", "AuthenticationError")):
                extra_hint = "\n\nTip: Authentication failed. Please verify your API key in Settings -> LLM Providers."
            elif any(term in err_str for term in ("404", "NotFoundError")):
                extra_hint = "\n\nTip: The specified model was not found. Please verify the model name in Settings -> LLM Providers."
            elif any(term in err_str for term in ("429", "RateLimitError")):
                extra_hint = "\n\nTip: Provider quota or rate limit exceeded."

        base_msg = error_message.get(error_status, 'An unexpected error occurred.\n\nDetails: "')
        dialog_text = base_msg + err_str + '"' + extra_hint

        # Displays an error message in a popup dialog.
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error code " + str(hex(error_status)))
        msg_box.setText(dialog_text)
        msg_box.exec()
