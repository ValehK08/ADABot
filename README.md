## ADABot - Gemini & Multi-API Powered Discord Bot

ADABot is an advanced Discord bot powered by Google's Gemini AI, offering a suite of features from conversational AI to file summarization, AI image generation, news updates, stock analysis, and fun social interactions. Built with Python and SQLite for context-aware responses, ADABot brings powerful AI capabilities directly into your Discord server.

---

## ✨ Key Features

- **🤖 Conversational AI**: Engage with Gemini AI using `!chat <prompt>`, and personalize responses by selecting different personalities with `!tone`.
- **📄 File Summarization**: Summarize text from `.txt`, `.pdf`, `.docx`, or even text within images using `!summarize` (attach your file or image).
- **🎨 AI Image Generation**: Generate custom images from text prompts with `!generate <prompt>`.
- **📰 News & Information**:
  - `!news <topic>`: Fetch and summarize the latest headlines on any topic.
  - `!stock <symbol>`: Retrieve real-time and historical stock data, with optional AI-driven financial analysis.
  - `!weather <city>`: Get current weather conditions and forecasts.
  - `!zodiac <sign>`: Receive daily horoscopes for all zodiac signs.
  - `!thisday`: Discover historical facts relevant to today's date.
- **🎉 Fun & Social**:
  - `!meme`: Generate AI-powered memes.
  - `!roast @user` / `!compliment @user`: Playfully roast or compliment members using context from recent chats.
  - `!remindme <time> <message>`: Set personal reminders (supports d/h/m/s notation, e.g., `2h30m`).
- **🧠 Contextual Memory**: Maintains recent conversation history and user join data via SQLite for richer, context-aware interactions.

---

## ✅ Requirements

- **Python**: 3.10 or higher
- **Dependencies** (install via `pip`):
  ```bash
  pip install discord.py google-generativeai requests Pillow PyPDF2 python-docx nest_asyncio python-dateutil newsapi-python beautifulsoup4 yfinance
  OR
  pip install -r requirements.txt
  ```

---

## ⚙️ Setup & Configuration

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ValehK08/ADABot.git
   cd ADABot
   ```
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API Keys**:
   - Open `adabot.py` (or your script file).
   - Replace placeholders with the actual keys:
     ```python
     discord_token = "YOUR_DISCORD_BOT_TOKEN"
     gemini_api_key = "YOUR_GEMINI_API_KEY"
     news_api_key = "YOUR_NEWS_API_KEY"
     openrouter_api_key = "YOUR_OPENROUTER_API_KEY"
     ```

---

## ▶️ Running ADABot

Start the bot with:
```bash
python bot.py  # or your script filename
```
On successful launch, the console will display a login confirmation.

---

---

## 📚 Command Reference
### 🧠 Chat & AI
| Command                | Description                                           |
|------------------------|-------------------------------------------------------|
| `!chat <prompt>`       | Chat with Gemini AI using recent message history.     |
| `!tone`                | Choose an AI personality/tone for `!chat`.            |

### 📝 Summarization
| Command                         | Description                                                       |
|----------------------------------|-------------------------------------------------------------------|
| `!summarize` (+ attachment)     | Summarize `.txt`, `.pdf`, `.docx` files or text from images.     |

### 🎨 Image Generation
| Command                | Description                                           |
|------------------------|-------------------------------------------------------|
| `!generate <prompt>`   | Create AI-generated images based on your prompt.      |

### 🗞️ News & Info
| Command                | Description                                           |
|------------------------|-------------------------------------------------------|
| `!news <topic>`        | Fetch top 5 headlines and AI summarize your choice.   |
| `!stock <symbol>`      | Get current/historical stock data with AI analysis.   |
| `!weather <city>`      | Display current weather conditions.                   |
| `!thisday`             | Fun historical fact for today’s date.                 |
| `!zodiac <sign>`       | Daily horoscope for any zodiac sign.                  |

### 😄 Fun & Social
| Command                        | Description                                           |
|--------------------------------|-------------------------------------------------------|
| `!meme`                        | Generate a random AI-driven meme.                     |
| `!roast @user`                 | Generate a playful roast for a user.                  |
| `!compliment @user`            | Generate a thoughtful compliment for a user.          |
| `!remindme <time> <message>`   | Schedule a personal reminder (d/h/m/s format).        |

### 🛠️ Utility
| Command        | Description                   |
|----------------|-------------------------------|
| `!info`        | Display this help message.     |

---
---

## 📦 APIs & Integrations

- **Discord API** (`discord.py`)
- **Google Gemini AI** (`google-generativeai`)
- **NewsAPI** (`newsapi-python`)
- **OpenRouter** (for meme caption generation)
- **Imgflip** (meme templates & generation)
- **Open-Meteo** (weather data)
- **Horoscope API** (daily horoscopes)
- **Yahoo Finance** (`yfinance`)

---

## 🗃️ Data Handling & Storage

ADABot uses an SQLite database (`DataBase.db`) to persist user and message data:

- **`users` table**: Tracks `user_id`, `username`, and `join_date`.
- **`messages` table**: Logs `username`, `message`, and `timestamp` for context in AI interactions.

Database is auto-created on first run if not present.

---
