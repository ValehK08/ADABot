Okay, here is a formatted README.md file based on the provided Python code and your notes.

# ADABot - Gemini & Multi-API Powered Discord Bot

ADABot is an advanced Discord bot integrating Google's Gemini AI for diverse functionalities. It features customizable AI response tones, file summarization (text, PDF, DOCX, images), AI image generation, news fetching & summarization, stock analysis, weather updates, horoscopes, meme generation, reminders, and social commands like roasting and complimenting. It utilizes a local SQLite database (`DataBase.db`) to store user information and message history for context-aware interactions.

---

## ✨ Features

*   **🤖 Conversational AI:** Chat with Gemini AI (`!chat`), choosing from various personalities (`!tone`).
*   **📄 File Summarization:** Summarize text from `.txt`, `.pdf`, `.docx` files, or text within images (`!summarize` with attachment).
*   **🎨 Image Generation:** Create images based on prompts using Gemini (`!generate`).
*   **📰 News & Information:** Get latest news headlines and AI summaries (`!news`), stock market data with AI analysis (`!stock`), weather forecasts (`!weather`), daily horoscopes (`!zodiac`), and historical facts (`!thisday`).
*   **🎉 Fun & Social:** Generate AI-powered memes (`!meme`), roast (`!roast`) or compliment (`!compliment`) users, and set reminders (`!remindme`).
*   **🧠 Contextual Memory:** Remembers recent conversation history from the channel (via SQLite DB) to provide more relevant responses in `!chat`, `!roast`, and `!compliment`.
*   **⚙️ Database Integration:** Logs messages and user join dates to a local SQLite database.

---

## ✅ Requirements

*   **Python 3.10+**
*   Required Python libraries:
    *   `discord.py`
    *   `google-generativeai`
    *   `requests`
    *   `sqlite3` (usually built-in)
    *   `Pillow` (PIL)
    *   `PyPDF2`
    *   `python-docx`
    *   `nest_asyncio`
    *   `python-dateutil`
    *   `newsapi-python`
    *   `beautifulsoup4`
    *   `yfinance`
    *   `asyncio` (built-in)
    *   `json` (built-in)
    *   `random` (built-in)

You can install most dependencies using pip:
```bash
pip install discord.py google-generativeai requests Pillow PyPDF2 python-docx nest_asyncio python-dateutil newsapi-python beautifulsoup4 yfinance

🚀 Setup & Configuration

Clone the Repository:

git clone <your-repo-url>
cd <your-repo-directory>
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Install Dependencies:

pip install -r requirements.txt # Make sure you have the requirements listed above in a file named requirements.txt
# Or install manually as shown in the Requirements section
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

Configure API Keys:
Open the Python script (e.g., adabot.py) and replace the placeholder strings with your actual API keys/tokens:

discord_token = "YOUR_DISCORD_BOT_TOKEN"
gemini = "YOUR_GEMINI_API_KEY"
news_api = "YOUR_NEWS_API_KEY"
openrouter = "YOUR_OPENROUTER_API_KEY" # Used for the !meme command's text generation
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Python
IGNORE_WHEN_COPYING_END

⚠️ Security Note: For production or shared bots, it is highly recommended to use environment variables or a configuration file (.env) to store sensitive keys instead of hardcoding them directly in the script.

Discord Bot Permissions:
Ensure your Discord bot has the necessary Intents enabled in the Discord Developer Portal (especially Server Members Intent and Message Content Intent). It also needs appropriate permissions (like Read Messages, Send Messages, Attach Files, Embed Links, etc.) when you invite it to your server.

▶️ How to Run

Execute the Python script:

python your_script_name.py # Replace 'your_script_name.py' with the actual filename
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

The bot should log in and print a confirmation message to your console.

⚙️ Commands

Here's a breakdown of the available commands:

Command	Description	Example Usage
🤖 Chat & AI		
!chat <prompt>	Chat with the Gemini AI. Uses recent message history for context.	!chat What's the weather like?
!tone	Opens a selection menu to change the AI's personality/tone for !chat.	!tone
!summarize (+ attachment)	Summarizes text from attached .txt, .pdf, .docx files, or describes/summarizes attached images.	!summarize (with file attached)
!generate <prompt>	Generates an image using AI based on the provided text prompt.	!generate A cat riding a bike
📰 News & Info		
!news <topic>	Fetches 5 recent news headlines on a topic and lets you choose one for an AI-generated summary.	!news technology
!stock <symbol>	Provides current and historical stock data for a symbol, with a button for AI financial analysis.	!stock AAPL
!weather <city>	Fetches and displays the current weather conditions for the specified city.	!weather London
!thisday	Shares an interesting historical fact related to the current date.	!thisday
!zodiac <sign>	Retrieves and displays the daily horoscope for the specified zodiac sign.	!zodiac Aries
🎉 Fun & Social		
!meme	Generates a random meme using a template and AI-generated captions (via OpenRouter & Imgflip).	!meme
!roast @user	Generates a creative roast for the mentioned user, using message history/username for context.	!roast @SomeUser
!compliment @user	Generates a thoughtful compliment for the mentioned user, using message history/username for context.	!compliment @AnotherUser
!remindme <time> <message>	Sets a reminder. Time format uses d/h/m/s (e.g., 1h30m).	!remindme 2h Check email
ℹ️ Utility		
!info	Displays this help message listing all available commands and their descriptions.	!info
📦 APIs Used

Discord API (via discord.py)

Google Gemini API (via google-generativeai) - For chat, summarization, image generation, analysis, etc.

NewsAPI (via newsapi-python & requests) - For fetching news headlines.

OpenRouter API (via requests) - For AI model access (!meme caption generation).

Imgflip API (via requests) - For meme template fetching and generation.

Open-Meteo APIs (via requests) - For geocoding and weather data.

Horoscope API (horoscope-app-api.vercel.app via requests) - For daily horoscopes.

Yahoo Finance API (via yfinance) - For stock market data.

🗃️ Data Handling

ADABot uses a local SQLite database file named DataBase.db to persist data:

users table: Stores basic information about server members (user_id, username, join_date). Populated when a member joins.

messages table: Logs messages sent in channels the bot can read (username, message, timestamp). This history is used to provide context for the !chat, !roast, and !compliment commands.

The database file is created automatically in the same directory as the script if it doesn't exist.

IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
IGNORE_WHEN_COPYING_END
