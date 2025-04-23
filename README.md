# ADABot - Gemini & Multi-API Powered Discord Bot

ADABot is an advanced Discord bot powered by Google's Gemini AI, offering a suite of features from conversational AI with selectable personalities to file/URL summarization, AI image generation, news updates, stock analysis, weather forecasts, translation, polls, and fun social interactions like reminders, roasts, compliments, and memes. Built with Python, discord.py, and SQLite for context-aware responses, ADABot brings powerful AI and utility capabilities directly into your Discord server.

---

## ✨ Key Features

-   **🤖 Conversational AI**:
    -   `!chat <prompt>`: Engage with Gemini AI, using recent chat history for context.
    -   `!tone`: Select a distinct personality for the AI (User-Friendly, Sarcastic, Depressed, Kid, Tutor, BrainRot).
-   **📄 Summarization**:
    -   `!summarize` (with file attachment): Summarize text from `.txt`, `.pdf`, `.docx`, or even text within images (`.png`, `.jpg`, etc.).
    -   `!summarize <url>`: Summarize the content of a given webpage.
-   **🎨 AI Image Generation**:
    -   `!generate <prompt>`: Create unique images based on your text descriptions using Gemini's image generation capabilities.
-   **📰 News & Information**:
    -   `!news <topic>`: Fetch recent headlines and interactively get AI-generated summaries.
    -   `!stock <symbol>`: Retrieve real-time and historical stock data, with an option for detailed AI-driven analysis.
    -   `!weather <city>`: Get current weather conditions using Open-Meteo.
    -   `!zodiac <sign>`: Receive daily horoscopes.
    -   `!thisday`: Discover an interesting historical fact relevant to today's date using Gemini and Google Search.
-   **🌐 Translation**:
    -   `!translate <start/stop>`: Automatically translate non-English messages sent in the chat into English.
-   **📊 Polls**:
    -   `!poll "Question" "Option 1" "Option 2" ...`: Create interactive polls with multiple choices.
-   **🎉 Fun & Social**:
    -   `!meme`: Generate contextual memes using Imgflip templates and AI captioning via OpenRouter.
    -   `!roast @user`: Playfully roast a member using context from recent chat history.
    -   `!compliment @user`: Generate a thoughtful compliment for a member based on chat context.
    -   `!remindme <time> <message>`: Set personal reminders (e.g., `!remindme 1d2h30m Check email`). Supports `d`, `h`, `m`, `s`.
-   **🧠 Contextual Memory**:
    -   Maintains recent conversation history (up to 20 messages by default) and user join data via an SQLite database (`DataBase.db`) for richer, context-aware AI interactions (chat, roast, compliment).

---

## ✅ Requirements

-   **Python**: 3.10 or higher recommended
-   **Dependencies**: Install necessary libraries using pip.

    ```bash
    pip install discord.py google-genai Pillow requests beautifulsoup4 PyPDF2 python-docx nest_asyncio python-dateutil newsapi-python yfinance pycryptodome
    ```

    Or use the `requirements.txt` file:
    ```bash
    pip install -r requirements.txt
    ```

---

## ⚙️ Setup & Configuration

1.  **Clone the Repository** (if applicable) or save the script:
    ```bash
    # Example if using Git
    git clone https://github.com/ValehK08/ADABot.git
    cd ADABot
    ```

2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt # If using requirements.txt
    # Or use the single pip install command from the Requirements section
    ```

3.  **Configure API Keys and Other Credentials**:
    -   Open the .env file.
    -   Replace the placeholder string with your actual token:
        ```python
        DISCORD_TOKEN = "YOUR_DISCORD_BOT_TOKEN"
        ```
4.  **⚠️ Warning: If you are running the bot in an environment...**:
    -   If you're running this project in an interactive environment such as **Jupyter Notebook** or **Spyder**, you may encounter issues with asynchronous functions (e.g., `... cannot be called from a running event loop`).
    -   To resolve this, you can apply a fix using the `nest_asyncio` library.
    -   Uncomment the lines below from the bottom lines of bot.py to fix that issue:
        ```
        # import nest_asyncio
        # nest_asyncio.apply()
        ```

---

## ▶️ Running ADABot

1.  Navigate to the directory containing the script in your terminal.
2.  Run the bot using Python:
    ```bash
    python bot.py
    ```
3.  On successful launch, the console will display a message like: `Logged in as ADABot (ID: ADABotID)`. The bot should now be online in your Discord server.

---

## 📚 Command Reference

*(Note: Default prefix is `!`)*

### 🧠 Chat & AI
| Command                       | Description                                                          |
| :---------------------------- | :------------------------------------------------------------------- |
| `!chat <prompt>`              | Chat with Gemini AI. Uses recent message history for context.        |
| `!tone`                       | Opens a selection menu to choose the AI's personality/tone.          |
| `!translate <start / stop>` | Starts or stops automatic translation of non-English messages.       |

### 📝 Summarization & Generation
| Command                       | Description                                                          |
| :---------------------------- | :------------------------------------------------------------------- |
| `!summarize` (+ attachment)   | Summarize `.txt`, `.pdf`, `.docx` files or text from images.         |
| `!summarize <url>`            | Summarize the textual content of a webpage URL.                      |
| `!generate <prompt>`          | Create an AI-generated image based on your prompt.                   |

### 🗞️ News & Info
| Command                       | Description                                                          |
| :---------------------------- | :------------------------------------------------------------------- |
| `!news <topic>`               | Fetch top headlines and interactively request AI summaries.          |
| `!stock <symbol>`             | Get current/historical stock data. Button for AI analysis report.    |
| `!weather <city>`             | Display current weather conditions for the specified city.           |
| `!thisday`                    | Get an interesting historical fact for today’s date.                 |
| `!zodiac <sign>`              | Fetch the daily horoscope for any zodiac sign.                       |

### 😄 Fun & Social
| Command                                   | Description                                                          |
| :---------------------------------------- | :------------------------------------------------------------------- |
| `!meme`                                   | Generate a random meme with AI-generated captions.                   |
| `!roast @user`                            | Generate a playful roast targeting the mentioned user.               |
| `!compliment @user`                       | Generate a thoughtful compliment for the mentioned user.             |
| `!remindme <time_duration> <message>`     | Set a personal reminder (e.g., `1d2h30m`, `5m`). Units: d, h, m, s. |
| `!poll "Question" "Opt1" "Opt2" ...`      | Create an interactive poll for users to vote on.                     |

### 🛠️ Utility
| Command        | Description                   |
| :------------- | :---------------------------- |
| `!info`        | Display the help message summarizing all commands. |

---

## 📦 APIs & Integrations

ADABot leverages several external APIs and libraries:

-   **Discord API** (`discord.py`): For all Discord bot interactions.
-   **Google Gemini AI** (`google-generativeai`): Powers chat, summarization, image generation, analysis (stock, roast, compliment), translation, and historical facts. Includes Google Search Tool integration.
-   **NewsAPI** (`newsapi-python`): Fetches news articles for the `!news` command.
-   **OpenRouter** (`requests`): Used indirectly via HTTP requests for advanced AI model access (Qwen for `!meme` captioning).
-   **Imgflip API** (`requests`): Provides meme templates and final meme generation for the `!meme` command.
-   **Open-Meteo API** (`requests`): Supplies geocoding and weather data for the `!weather` command.
-   **Horoscope API** (`requests` - via `zodiac_url`): Delivers daily horoscopes for the `!zodiac` command.
-   **Yahoo Finance** (`yfinance`): Retrieves stock market data for the `!stock` command.

---

## 🗃️ Data Handling & Storage

ADABot uses an SQLite database (`DataBase.db`) located in the same directory as the script to persist data:

-   **`users` table**: Stores `user_id` (Primary Key), `username`, and `join_date`. Used to track when users join.
-   **`messages` table**: Logs `id` (Auto-incrementing Primary Key), `username`, `message` content, and `timestamp`. This history provides context for the `!chat`, `!roast`, and `!compliment` commands.

The database file (`DataBase.db`) and tables are automatically created on the first run if they do not exist.
