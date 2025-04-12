import discord
from discord.ext import commands
import aiohttp
import json
import sqlite3
from datetime import datetime
import random

# Token and API keys
DISCORD_TOKEN = '<Discord_Token>'
OPENROUTER_API_KEY = '<OpenRouter_API_Key>'

# Default Discord Bot Setting
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Database
conn = sqlite3.connect("botdata.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, join_date TEXT)''')
conn.commit()

# Customizable AI Tone
AI_TONE = "You're a friendly human named ADABot. Keep it casual and short. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message."

tone_options = {
    "user-friendly": "You're a friendly human named ADABot. Keep it casual and short. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "kid": "You're a cheerful, energetic kid named ADABot. Keep your responses simple, fun, and full of enthusiasm. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "rude": "You're a blunt and slightly rude human named ADABot. Keep your responses short and cutting. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "sarcastic": "You're a sarcastic human with a dry wit named ADABot. Keep your responses brief and witty. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "tutor": "You're a helpful tutor named ADABot. Answer clearly and briefly in a way beginners can understand. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message."
}

# Function for AI API usage(OpenRouter)
async def ask_openrouter(prompt, tone=AI_TONE, history=[]):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    messages = [{"role": "system", "content": tone}]
    for entry in history:
        messages.append({"role": "user", "content": entry["user"]})
        messages.append({"role": "assistant", "content": entry["bot"]})
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "messages": messages
    }

    async with aiohttp.ClientSession() as session:
        async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data) as response:
            if response.status == 200:
                try:
                    res_json = await response.json()
                    if 'choices' in res_json:
                        return res_json['choices'][0]['message']['content']
                    else:
                        return "⚠️ Unexpected response from AI. Please try again."
                except Exception as e:
                    return f"⚠️ Failed to parse AI response: {e}"
            else:
                try:
                    error_detail = await response.text()
                    return f"❌ API error {response.status}: {error_detail}"
                except:
                    return f"❌ API error {response.status}"

# Bot Status Notifier
@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    for member in bot.get_all_members():
        if not member.bot:
            cursor.execute("SELECT * FROM members WHERE name = ?", (member.name,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO members (name, join_date) VALUES (?, ?)", (member.name, member.joined_at.strftime("%Y-%m-%d")))
    conn.commit()

# | !info | command for ADABot Help Menu
@bot.command()
async def info(ctx):
    help_message = """
🤖 **ADABot Help Menu**

Here are the available commands:

- `!chat [message]` – Talk to the AI in your chosen tone.
- `!tone [style]` – Change AI tone. Options: user-friendly, kid, rude, sarcastic.
- `!quote` – Get a short motivational quote.
- `!weather [city]` – Check weather for a city.
- `!joke` – Hear a random joke.
- `!search [topic]` – Summarize a Wikipedia article on the topic.
- `!movie` – Get a random movie suggestion.
- `!zodiac [sign]` – Daily horoscope by zodiac sign (e.g. `!zodiac aries`)
- `!define [word]` – Show dictionary definition of a word.
"""
    await ctx.send(help_message)

# | !tone <user-friendly/rude/kid/sarcastic/tutor> | command for Customizable Tone Setting
@bot.command()
async def tone(ctx, *, new_tone: str = None):
    global AI_TONE
    if new_tone is None:
        await ctx.send(f"The current tone is: **{AI_TONE}**")
        return

    new_tone = new_tone.lower()
    if new_tone in tone_options:
        AI_TONE = tone_options[new_tone]
        await ctx.send(f"Tone updated to **{new_tone}**.")
    else:
        available = ", ".join(tone_options.keys())
        await ctx.send(f"Unknown tone. Available tones are: {available}.")

# | !chat <prompt> | command for Chatting With AI
@bot.command()
async def chat(ctx, *, message):
    user_tag = ctx.author.mention
    await ctx.send("Thinking... 🤖")
    now = datetime.now().isoformat()

    cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)", (ctx.author.name, message, now))
    conn.commit()

    cursor.execute("""
        SELECT username, message FROM messages 
        WHERE username = ? OR username = 'ADABot'
        ORDER BY id DESC LIMIT 6
    """, (ctx.author.name,))
    rows = cursor.fetchall()[::-1]

    history = []
    i = 0
    while i < len(rows) - 1:
        if rows[i][0] == ctx.author.name and rows[i + 1][0] == "ADABot":
            history.append({"user": rows[i][1], "bot": rows[i + 1][1]})
            i += 2
        else:
            i += 1

    reply = await ask_openrouter(message, tone=AI_TONE, history=history)

    cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)", ("ADABot", reply[:2000], now))
    conn.commit()

    await ctx.send(f"{user_tag} {reply[:2000]}")

# | !quote | command for Random Quote Generator
@bot.command()
async def quote(ctx):
    prompt = "Give me a short, inspiring motivational quote. Don't write anything else. Format it like: *quote* ~ person who said"
    result = await ask_openrouter(prompt, tone=AI_TONE)
    await ctx.send(f"💬 {result}")

@bot.command()
async def weather(ctx, *, city):
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(geocode_url) as geo_resp:
                if geo_resp.status != 200:
                    await ctx.send("⚠️ Couldn't fetch geocode data.")
                    return
                geo_data = await geo_resp.json()
                if "results" not in geo_data or not geo_data["results"]:
                    await ctx.send("⚠️ City not found.")
                    return

                result = geo_data["results"][0]
                lat = result["latitude"]
                lon = result["longitude"]

                weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
                async with session.get(weather_url) as weather_resp:
                    if weather_resp.status != 200:
                        await ctx.send("⚠️ Couldn't fetch weather data.")
                        return
                    weather_data = await weather_resp.json()
                    if "current_weather" in weather_data:
                        current = weather_data["current_weather"]
                        temperature = current.get("temperature", "N/A")
                        windspeed = current.get("windspeed", "N/A")
                        winddirection = current.get("winddirection", "N/A")
                        weather_message = (
                            f"☀️ Weather in {city.title()}:\n"
                            f"Temperature: {temperature}°C\n"
                            f"Wind Speed: {windspeed} km/h\n"
                            f"Wind Direction: {winddirection}°"
                        )
                        await ctx.send(weather_message)
                    else:
                        await ctx.send("⚠️ Weather data unavailable.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# | !joke | command for Random Joke Generator
@bot.command()
async def joke(ctx):
    url = "https://official-joke-api.appspot.com/random_joke"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    joke_text = f"{data['setup']} ... {data['punchline']}"
                    await ctx.send(f"😂 {joke_text}")
                else:
                    await ctx.send("⚠️ Couldn't fetch a joke.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# | !search <Topic> | command for Direct Wikipedia Search(Summarized by AI)
@bot.command()
async def search(ctx, *, query):
    await ctx.send("🔎 Searching Wikipedia...")
    try:
        formatted_query = query.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{formatted_query}"

        async with aiohttp.ClientSession() as session:
            async with session.get(wiki_url) as response:
                if response.status != 200:
                    return await ctx.send("❌ Could not find a Wikipedia article for that.")
                html = await response.text()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                paragraphs = soup.select("p")
                text = " ".join(p.get_text() for p in paragraphs[:5]).strip()

        if not text:
            return await ctx.send("❌ Couldn't extract any readable content.")

        prompt = f"Summarize this Wikipedia content in simple terms:\n\n{text}"
        summary = await ask_openrouter(prompt)

        await ctx.send(f"📚 **Summary for '{query}'**:\n{summary}\n🔗 {wiki_url}")
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")

# | !movie | command for Random Movie Recommender
@bot.command()
async def movie(ctx):
    movies = [
        "Inception (2010)", "The Matrix (1999)", "Interstellar (2014)",
        "Parasite (2019)", "The Godfather (1972)", "Pulp Fiction (1994)",
        "The Shawshank Redemption (1994)", "Forrest Gump (1994)",
        "The Dark Knight (2008)", "Fight Club (1999)"
    ]
    await ctx.send(f"🎮 How about watching: {random.choice(movies)}")

# | !zodiac <sign> | command for Daily Horoscope
@bot.command()
async def zodiac(ctx, sign: str):
    sign = sign.lower()
    url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign}&day=TODAY"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    horoscope = data.get('data', {}).get('horoscope_data', 'No horoscope available.')
                    date = data.get('data', {}).get('date', 'Unknown date')
                    msg = f"🔮 **Daily Horoscope for {sign.capitalize()}** ({date})\n**Horoscope:** {horoscope}"
                    await ctx.send(msg)
                else:
                    await ctx.send("⚠️ Failed to get horoscope. Check the zodiac sign.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

# | !define <word> | command for Dictionary Word Definition
@bot.command()
async def define(ctx, *, word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    meanings = data[0]['meanings']
                    message_text = f"📖 **{word.capitalize()}**:\n"
                    for idx, meaning in enumerate(meanings, 1):
                        definition = meaning['definitions'][0]['definition']
                        message_text += f"\n{idx}. **{meaning['partOfSpeech']}**: {definition}"
                    await ctx.send(message_text)
                else:
                    await ctx.send("❌ Couldn't find that word.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

bot.run(DISCORD_TOKEN)
