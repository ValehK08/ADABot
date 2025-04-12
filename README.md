
# ADABot
ADABot is a Discord bot created for the ADA AI Competition. It offers customizable response tones, interactive commands, and a unique memory feature that stores previous conversations and user data in a .db file.

---

## ✅ Requirements

- **Python 3.10+**
- `discord`
- `requests`
- `sqlite3`
- `aiohttp`
- `json`, `random`, `datetime`(built-in Python)
---

## 🚀 How to Run It

1. **Clone the Repo**

   ```bash
   git clone https://github.com/ValehK08/ADABot.git
   cd ADABot
   ```

2. **Set Discord Token and The API Keys**

   Open `bot.py` and replace the placeholder variables with my actual credentials:

   ```python
   DISCORD_TOKEN = '<Discord_Token>'
   OPENROUTER_API_KEY = '<OpenRouter_API_Key>'
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
| `!chat <prompt>`       | Talk with the AI. Returns intelligent responses using OpenRouter.           |
| `!tone`       | Change AI response tone: `user-friendly` (default), `kid`, `rude`, `sarcastic` |
| `!quote`      | Sends a motivational quote in the format: *"quote" ~ person*                |
| `!weather <city>`    | Get current weather of any city                   |
| `!joke`       | Get a random joke                                                           |
| `!search <topic>`     | Returns a summary of wikipedia article + link for a search term         |
| `!movie`      | Suggests a random movie                                                     |
| `!zodiac <sign>`     | Shows daily horoscope for a zodiac sign              |
| `!define <word>`     | Get definitions of a word                         |
| `!info`     | Get informed about commands and their format                        |

---

## 📦 APIs Used

- **OpenRouter API** – for AI responses and quotes
- **Open-Meteo** – plain text weather data
- **Official Joke API** – for random jokes
- **Horoscope App API** – daily horoscope
- **Dictionary API** – definitions and meanings

---

## 🗃️ Data Handling

ADABot uses SQLite for local data storage:

- `messages` table – saves chat messages and timestamps
- `members` table – stores server members and join dates

The database (`botdata.db`) is automatically created on first run.

---
