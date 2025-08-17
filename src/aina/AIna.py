from openai import OpenAI


class AIna:
    """
    Represents a GPT model instance for managing prompts, history, and API communication.

    This class handles the preparation of prompts, maintains message history,
    and manages the client responsible for sending and receiving messages
    through the GPT API.
    """

    def __init__(
        self,
        language: str = "en-US",
        language_level: str = "Basic",
        prompt_path: str = None,
    ) -> None:
        """
        Initializes the GPT model by loading the prompt, setting up conversation history,
        and creating the API client for communication.

        Args:
            language (str, optional): The language used for communication with the model,
                                   e.g., 'en-US' or 'ja'. Defaults to 'en-US'.
            language_level (str, optional): The desired proficiency level for responses
                                            (e.g., 'Basic', 'Advanced').
                                            Defaults to 'Basic'.
            prompt_path (str, optional): Path to a custom prompt file. If None, a default prompt is used.
        """

        self.language = language
        self.language_level = language_level

        filename = prompt_path

        # Loading prompt
        with open(filename, "r", encoding="utf-8") as file:
            text = file.read()

        self.init_messages = {
            "en-US": [text, "Greet your new speaker and start a conversation."],
            "ja": [
                text,
                "あなたの新しいスピーカーに挨拶して、会話を始めましょう。",
            ],
        }

        self.history = [
            {"role": "system", "content": self.init_messages[language][0]},
            {"role": "user", "content": self.init_messages[language][1]},
        ]

        # Point to the local server
        self.client = OpenAI(
            base_url="http://localhost:1234/v1", api_key="lm-studio"
        )
