# ADABot

A multi-functional Discord bot powered by OpenRouter and other public APIs. It supports AI chat, dictionary lookups, jokes, horoscopes, weather reports, web searches, and more — all in one sleek package.

> ✅ The bot is already hosted and running. You just need to add it to your server!

---

## 🚀 Add the Bot to Your Server

Click below to invite the bot to your server with admin permissions:

👉 [Add to Discord](https://discord.com/oauth2/authorize?client_id=1360228903729369278&permissions=8&integration_type=0&scope=bot)

---

## 🧠 Features

| Command      | Description                                                                 |
|--------------|-----------------------------------------------------------------------------|
| `!chat`      | AI chat powered by OpenRouter. Remembers your tone preference.              |
| `!tone`      | Changes AI chat tone. Options: `user-friendly` (default), `kid`, `rude`, `sarcastic` |
| `!quote`     | Generates an inspirational quote in a neat format.                          |
| `!weather`   | Shows current weather for a city using wttr.in.                             |
| `!joke`      | Sends a random joke.                                                        |
| `!search`    | Provides a quick search summary and source link using DuckDuckGo.           |
| `!movie`     | Recommends a random movie.                                                  |
| `!zodiac`    | Daily horoscope for any zodiac sign using Horoscope API.                    |
| `!define`    | Provides full dictionary definitions with parts of speech.                  |
| `!info`      | Displays server member count and list of saved members.                     |

---

## 🧩 APIs Used

- **OpenRouter API** – AI chat and quote generation  
- **wttr.in** – Weather lookup via plain-text URL  
- **Official Joke API** – Random jokes  
- **DuckDuckGo Instant Answer API** – Quick web search summaries  
- **Horoscope App API** – Daily zodiac readings  
- **Free Dictionary API** – English word definitions  

---

## 🗃️ Data Storage

This bot uses an SQLite database (`botdata.db`) to store:

- AI chat messages with timestamps
- Server member names and join dates

---

## 🔧 Run the Bot Locally (For Developers)

> You do **not** need to create your own Discord bot. This code is configured to use the official hosted ADABot. Use this only if you want to run your own version with your own API keys.

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/ADABot.git
    cd ADABot
    ```

2. **Set up a virtual environment & install dependencies**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Insert your credentials**

    Open `bot.py` and replace:
    - `DISCORD_TOKEN` (optional if not self-hosting)
    - `OPENROUTER_API_KEY` (needed for chat/quote)

4. **Run the bot**

    ```bash
    python bot.py
    ```

---

## 📝 License

This project is **closed-source** and all rights are reserved. You are free to use the hosted version via the invite link. For commercial use, forking, or deployment under a different name, please contact the author.

---

Enjoy chatting, searching, joking, and more — all through **ADABot**. 🧠✨
