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

    # Human-readable language names used in the profile transition note.
    LANGUAGE_NAMES = {"en-US": "English", "ja": "Japanese"}

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

        The history starts with the system prompt only, so the user is the one
        who starts the conversation.

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

        self.history = [
            {"role": "system", "content": self._load_prompt(prompt_path)},
        ]

        self.set_provider(provider_config)

    @staticmethod
    def _load_prompt(prompt_path: str) -> str:
        """
        Reads the system prompt from disk.

        Args:
            prompt_path (str): Path to the prompt file.

        Returns:
            str: The prompt text.
        """

        with open(prompt_path, "r", encoding="utf-8") as file:
            return file.read()

    @property
    def has_conversation(self) -> bool:
        """
        Whether at least one message was exchanged after the system prompt.
        """

        return len(self.history) > 1

    def set_profile(
        self, language: str, language_level: str, prompt_path: str
    ) -> None:
        """
        Replaces the system prompt with a new language/level profile.

        The Chat Completions API is stateless, so swapping the system prompt
        mid-conversation is safe. If a conversation is already in progress, a
        transition note is appended to the system prompt so the model knows the
        earlier messages used a different profile. The prompt is rebuilt from
        disk each time, so notes never stack up.

        Args:
            language (str): The new language code, e.g., 'en-US' or 'ja'.
            language_level (str): The new proficiency level, e.g., 'Basic'.
            prompt_path (str): Path to the prompt file of the new profile.
        """

        content = self._load_prompt(prompt_path)

        if self.has_conversation:
            old_name = self.LANGUAGE_NAMES.get(self.language, self.language)
            new_name = self.LANGUAGE_NAMES.get(language, language)
            content += (
                f"\n\nNote: earlier messages in this conversation were in "
                f"{old_name} ({self.language_level}). From now on, continue the "
                f"conversation in {new_name} at the {language_level} level, "
                f"following the instructions above."
            )

        self.history[0] = {"role": "system", "content": content}
        self.language = language
        self.language_level = language_level

    def set_provider(self, provider_config: dict | None) -> None:
        """
        (Re)creates the API client and model name from a provider configuration.

        The conversation history is left untouched, so the provider can be
        switched mid-conversation.

        Args:
            provider_config (dict, optional): Provider settings containing base_url, api_key, and model.
        """

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
