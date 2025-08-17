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
                "Model initialization failed. This may be due to missing "
                "dependencies incorrect API credentials, or a configuration "
                'issue. Please check the settings and try again.\n\nDetails: "'
            ),
        }

        message = error_message[error_status] + str(message["error"]) + '"'

        # Displays an error message in a popup dialog.
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle("Error code " + str(hex(error_status)))
        msg_box.setText(message)
        msg_box.exec()
