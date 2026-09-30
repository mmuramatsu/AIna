from openai import OpenAI


class AIna:
    """
    Represents a GPT model instance for managing prompts, history, and API communication.

    This class handles the preparation of prompts, maintains message history,
    and manages the client responsible for sending and receiving messages
    through the GPT API.
    """

    # Maximum number of conversation messages to keep (excluding system prompt).
    # This prevents unbounded history growth that would hit token limits.
    MAX_HISTORY_MESSAGES = 50

    def __init__(
        self,
        language: str = "en-US",
        language_level: str = "Basic",
        prompt_path: str = None,
        provider_config: dict | None = None,
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
            provider_config (dict, optional): Provider settings containing base_url, api_key, and model.
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

        # Configure provider credentials and model
        config = provider_config or {}
        base_url = config.get("base_url") or "http://localhost:1234/v1"
        api_key = config.get("api_key") or "none"
        self.model_name = config.get("model") or "model-identifier"

        self.client = OpenAI(
            base_url=base_url if base_url else None,
            api_key=api_key if api_key else "none",
        )

    def trim_history(self) -> None:
        """
        Trims conversation history to prevent unbounded growth.

        Keeps the system prompt (first message) and the most recent messages
        up to MAX_HISTORY_MESSAGES. This prevents hitting token limits on
        long conversations.
        """

        # +1 accounts for the system prompt at index 0
        if len(self.history) > self.MAX_HISTORY_MESSAGES + 1:
            system_prompt = self.history[0]
            self.history = [system_prompt] + self.history[-(self.MAX_HISTORY_MESSAGES):]
