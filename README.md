# AIna - Your Conversational AI Partner

![AIna](assets/images/aina.png)

AIna is an artificial conversationalist designed to bring joy, warmth, and depth to every interaction. This project aims to provide a desktop application for users to practice English and Japanese conversations with AIna. You can interact with AIna through both text and voice, making it a versatile tool for language learners.

## Key Features

*   **Dual Language Support:** Practice conversations in both English and Japanese.
*   **Adjustable Difficulty:** Choose between "Basic" and "Advanced" language levels to match your skill.
*   **Voice and Text Interaction:** Communicate with AIna using your voice or by typing.
*   **Auto-Send Option:** Automatically send your transcribed voice messages for a more fluid conversation.
*   **Customizable Interface:** Switch between light and dark themes.
*   **Local LLM Support:** Connects to a local Large Language Model (such as LM Studio), ensuring privacy and control over your data.
*   **Standalone Executable:** A pre-compiled version is available for users who don't want to run the source code.

## Getting Started

### Prerequisites

*   Python 3.x
*   A local Large Language Model (LLM) server, such as [LM Studio](https://lmstudio.ai/).

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/mmuramatsu/AIna.git
    cd AIna
    ```

2.  **Create a virtual environment and activate it:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

### Running the Application

1.  **Start your local LLM server.** Make sure it's running and accessible at `http://localhost:1234`.

2.  **Run the application:**

    ```bash
    python main.py
    ```

3.  **Configure AIna:** In the application, select your desired language and language level, and then click the "Initialize AIna" button.

4.  **Start chatting!** You can now start a conversation with AIna by typing or holding the microphone button to speak.

### Standalone Executable

For users who prefer not to work with the source code, a standalone `.exe` file is available for download in the [Releases](https://github.com/your-username/AIna/releases) section of this repository.

## Contributing

Contributions are welcome! If you have any ideas, suggestions, or bug reports, please open an issue or submit a pull request. For major changes, please open an issue first to discuss what you would like to change.

## Contact

If you have any questions, suggestions, or just want to connect, feel free to reach out:

*   **Webpage:** [mmuramatsu.com](https://mmuramatsu.com/)
*   **GitHub:** [@mmuramatsu](https://github.com/mmuramatsu)
*   **Email:** [junior_muramatsu@hotmail.com](mailto:junior_muramatsu@hotmail.com)
*   **LinkedIn:** [Mario Muramatsu Júnior](https://www.linkedin.com/in/mario-muramatsu-jr/)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.