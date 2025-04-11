
# ADABot
ADABot is a Discord bot developed for the ADA AI Competition. It leverages an external AI API to process user prompts and provide dynamic, engaging responses. The bot features customizable response tones and various commands to interact with users in multiple ways.

---

## ✅ Requirements

- **Python 3.10+**
- `discord.py`
- `requests`
- `sqlite3` (built-in with Python)

> **Note:** Include your API keys directly in the code for testing as per competition rules.

---

## 🚀 How to Run It

1. **Clone the Repo**

   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```

2. **Configure API Keys**

   Open the main file (e.g., `bot.py`) and edit these variables:

   ```python
   DISCORD_TOKEN = 'your_discord_bot_token'
   OPENROUTER_API_KEY = 'your_openrouter_api_key'
   ```

3. **Add the Bot to Your Discord Server**

   Use this invite link to add ADABot with full permissions:

   [Add ADABot to Your Server](https://discord.com/oauth2/authorize?client_id=1360228903729369278&permissions=8&integration_type=0&scope=bot)

4. **Run the Bot**

   Run the bot using:

   ```bash
   python bot.py
   ```

---

## 🧠 Features & Commands

| Command       | Description                                                                 |
|---------------|-----------------------------------------------------------------------------|
| `!chat`       | Talk with the AI. Returns intelligent responses using OpenRouter.           |
| `!tone`       | Change AI response tone: `user-friendly` (default), `kid`, `rude`, `sarcastic` |
| `!quote`      | Sends a motivational quote in the format: *"quote" ~ person*                |
| `!weather`    | Get current weather of any city (e.g., `!weather Paris`)                    |
| `!joke`       | Get a random joke                                                           |
| `!search`     | Returns a summary + link for a search term (e.g., `!search Python`)         |
| `!movie`      | Suggests a random movie                                                     |
| `!zodiac`     | Shows daily horoscope for a zodiac sign (e.g., `!zodiac Leo`)               |
| `!define`     | Get definitions of a word (e.g., `!define ephemeral`)                       |
| `!info`       | Shows member list and count for your server                                 |

---

## 📦 APIs Used

- **OpenRouter API** – for AI responses and quotes
- **wttr.in** – plain text weather data
- **Official Joke API** – for random jokes
- **DuckDuckGo API** – for search results
- **Horoscope App API** – daily horoscope
- **Dictionary API** – definitions and meanings

---

## 🗃️ Data Handling

ADABot uses SQLite for lightweight local data storage:

- `messages` table – saves chat messages and timestamps
- `members` table – stores server members and join dates

The database (`botdata.db`) is automatically created on first run.

---
