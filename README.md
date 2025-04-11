# ADABot
# Discord AI Chatbot 🤖

A multi-functional Discord bot powered by OpenRouter and several public APIs. It supports AI chat, dictionary lookups, jokes, horoscopes, weather reports, search functionality, and more — all with a customizable tone.

> ✅ The bot is already hosted and running. You just need to add it to your server!

---

## 🚀 Add the Bot to Your Server

Click below to invite the bot with admin permissions:

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

- **OpenRouter API** – for AI chat and quote generation  
- **wttr.in** – weather lookup via plain-text URL  
- **Official Joke API** – jokes in JSON format  
- **DuckDuckGo Instant Answer API** – search summaries  
- **Horoscope App API** – zodiac horoscopes  
- **Free Dictionary API** – word definitions  

---

## 🗃️ Data Storage

- The bot uses **SQLite** (`botdata.db`) to store:
  - AI chat messages (user + timestamp)
  - Server members (name + join date)

---

## 🔧 Optional: Run Locally

> Skip this section if you're only using the hosted bot.

1. **Clone the repository**

    ```bash
    git clone https://github.com/yourusername/discord-bot.git
    cd discord-bot
    ```

2. **Set up a virtual environment & install dependencies**

    ```bash
    python -m venv venv
    source venv/bin/activate  # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

3. **Add your API keys (if hosting yourself)**  
    Edit `bot.py` and replace:
    - `DISCORD_TOKEN`
    - `OPENROUTER_API_KEY`

4. **Run the bot**

    ```bash
    python bot.py
    ```

---

## 📝 License

This project is closed-source and all rights are reserved. You are allowed to use the hosted version via the invite link above. For development or distribution rights, please contact the author.

---

Enjoy chatting, searching, joking, and more — all through one bot. 🎉  
