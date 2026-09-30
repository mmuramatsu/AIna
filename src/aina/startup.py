import json
import os
from pathlib import Path
import platform


DEFAULT_CONFIG = {
    "theme": "light",
    "language": "English",
    "language_level": "Basic",
    "auto_send": False,
    "active_provider": "LM Studio (Local)",
    "providers": {
        "LM Studio (Local)": {
            "base_url": "http://localhost:1234/v1",
            "api_key": "lm-studio",
            "model": "model-identifier",
            "requires_api_key": False,
        },
        "Ollama (Local)": {
            "base_url": "http://localhost:11434/v1",
            "api_key": "ollama",
            "model": "llama3.2",
            "requires_api_key": False,
        },
        "OpenAI (Cloud)": {
            "base_url": "https://api.openai.com/v1",
            "api_key": "",
            "model": "gpt-4o-mini",
            "requires_api_key": True,
        },
        "Google Gemini (Cloud)": {
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
            "api_key": "",
            "model": "gemini-1.5-flash",
            "requires_api_key": True,
        },
        "Custom (OpenAI-Compatible)": {
            "base_url": "",
            "api_key": "",
            "model": "",
            "requires_api_key": False,
        },
    },
}


def _deep_merge(defaults: dict, overrides: dict) -> dict:
    """
    Recursively merges overrides into a copy of defaults dictionary.

    Args:
        defaults (dict): The base default configuration.
        overrides (dict): User-supplied configuration values.

    Returns:
        dict: A new dictionary with overrides merged into defaults.
    """
    result = {}
    for key, value in defaults.items():
        if key in overrides:
            if isinstance(value, dict) and isinstance(overrides[key], dict):
                result[key] = _deep_merge(value, overrides[key])
            else:
                result[key] = overrides[key]
        else:
            if isinstance(value, dict):
                result[key] = _deep_merge(value, {})
            else:
                result[key] = value

    for key, value in overrides.items():
        if key not in result:
            result[key] = value

    return result


def get_config_path(app_name: str) -> Path:
    """
    Returns the path to the configuration file based on the OS.

    Creates the appropriate configuration directory depending on the operating
    system (Windows, macOS, or Linux) and ensures it exists.

    Args:
        app_name (str): The name of the application.

    Returns:
        Path: The full path to the configuration file (config.json).
    """

    if platform.system() == "Windows":
        config_dir = Path(os.getenv("APPDATA")) / app_name
    elif platform.system() == "Darwin":  # macOS
        config_dir = Path.home() / "Library" / "Application Support" / app_name
    else:  # Linux and other Unix-like systems
        config_dir = Path.home() / ".config" / app_name

    config_dir.mkdir(parents=True, exist_ok=True)

    return config_dir / "config.json"


# Writing the configuration
def save_config(config: dict, config_path: Path) -> None:
    """
    Saves the given configuration dictionary to a JSON file.

    Args:
        config (dict): The configuration data to be saved.
        config_path (Path): The path to the config file.
    """

    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)


def load_config(config_path: Path) -> dict:
    """
    Loads the configuration from a JSON file and merges it with default values.

    If the file exists and contains valid JSON, it loads the settings.
    Otherwise, it uses an empty dictionary. Default values are recursively merged in.

    Args:
        config_path (Path): The path to the config file.

    Returns:
        dict: The merged configuration dictionary.
    """

    if config_path.exists():
        with open(config_path, "r") as file:
            try:
                config = json.load(file)
            except json.JSONDecodeError:
                config = {}
    else:
        config = {}

    return _deep_merge(DEFAULT_CONFIG, config)
