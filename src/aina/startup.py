import json
import os
from pathlib import Path
import platform


DEFAULT_CONFIG = {
    "theme": "light",
    "language": "English",
    "language_level": "Basic",
    "auto_send": False,
}


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
    Otherwise, it uses an empty dictionary. Default values are merged in.

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

    # Merge default settings with loaded config
    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config)
    return merged_config
