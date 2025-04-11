import discord
from discord.ext import commands
import requests
import json
import sqlite3
from datetime import datetime
import random

DISCORD_TOKEN = 'MTM2MDIyODkwMzcyOTM2OTI3OA.GnKQOK.Div-zDG_VfBLmNxyC_ZhyZFDGoP4bj1_DXPveA'
OPENROUTER_API_KEY = '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'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

conn = sqlite3.connect("botdata.db")
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp TEXT)''')
cursor.execute('''CREATE TABLE IF NOT EXISTS members (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, join_date TEXT)''')
conn.commit()

AI_TONE = "You're a friendly assistant named ADABot. Keep it casual and short. Just answer the prompt directly and don't add additional stuff."

tone_options = {
    "user-friendly": "You're a friendly assistant named ADABot. Keep it casual and short. Just answer the prompt directly and don't add additional stuff.",
    "kid": "You're a cheerful, energetic kid named ADABot. Keep your responses simple, fun, and full of enthusiasm. Just answer the prompt directly and don't add additional stuff.",
    "rude": "You're a blunt and slightly rude assistant named ADABot. Keep your responses short and cutting. Just answer the prompt directly and don't add additional stuff.",
    "sarcastic": "You're a sarcastic assistant with a dry wit named ADABot. Keep your responses brief and witty. Just answer the prompt directly and don't add additional stuff."
}

def ask_openrouter(prompt, tone=AI_TONE):
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "messages": [
            {"role": "system", "content": tone},
            {"role": "user", "content": prompt}
        ]
    }
    response = requests.post("https://openrouter.ai/api/v1/chat/completions",
                             headers=headers,
                             data=json.dumps(data))
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        return f"Error: {response.status_code}"

@bot.event
async def on_ready():
    print(f"Bot is online as {bot.user}")
    for member in bot.get_all_members():
        if not member.bot:
            cursor.execute("SELECT * FROM members WHERE name = ?", (member.name,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO members (name, join_date) VALUES (?, ?)",
                               (member.name, member.joined_at.strftime("%Y-%m-%d")))
    conn.commit()
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

@bot.command()
async def chat(ctx, *, message):
    user_tag = ctx.author.mention
    await ctx.send("Thinking... 🤖")
    reply = ask_openrouter(message, tone=AI_TONE)
    cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)",
                   (ctx.author.name, message, datetime.now().isoformat()))
    conn.commit()
    await ctx.send(f"{user_tag} {reply[:2000]}")

@bot.command()
async def quote(ctx):
    prompt = "Give me a short, inspiring motivational quote. Don't write anything else. It needs to be in this format: *quote* ~ person who said"
    result = ask_openrouter(prompt, tone=AI_TONE)
    await ctx.send(f"💬 {result}")

@bot.command()
async def weather(ctx, *, city):
    url = f"http://wttr.in/{city}?format=3"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            await ctx.send(f"☀️ Weather in {city.capitalize()}: {response.text}")
        else:
            await ctx.send("⚠️ Couldn't fetch weather data.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def joke(ctx):
    url = "https://official-joke-api.appspot.com/random_joke"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            joke_text = f"{data['setup']} ... {data['punchline']}"
            await ctx.send(f"😂 {joke_text}")
        else:
            await ctx.send("⚠️ Couldn't fetch a joke.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def search(ctx, *, query):
    await ctx.send("🔎 Searching Wikipedia...")

    try:
        formatted_query = query.replace(" ", "_")
        wiki_url = f"https://en.wikipedia.org/wiki/{formatted_query}"

        response = requests.get(wiki_url)
        if response.status_code != 200:
            return await ctx.send("❌ Could not find a Wikipedia article for that.")

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.select("p")
        text = " ".join(p.get_text() for p in paragraphs[:5]).strip()

        if not text:
            return await ctx.send("❌ Couldn't extract any readable content.")

        prompt = f"Summarize this Wikipedia content in simple terms:\n\n{text}"
        summary = ask_openrouter(prompt)

        await ctx.send(f"📚 **Summary for '{query}'**:\n{summary}\n🔗 {wiki_url}")

    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")


@bot.command()
async def movie(ctx):
    movies = [
        "Inception (2010)", "The Matrix (1999)", "Interstellar (2014)",
        "Parasite (2019)", "The Godfather (1972)", "Pulp Fiction (1994)",
        "The Shawshank Redemption (1994)", "Forrest Gump (1994)",
        "The Dark Knight (2008)", "Fight Club (1999)"
    ]
    await ctx.send(f"🎬 How about watching: {random.choice(movies)}")

@bot.command()
async def zodiac(ctx, sign: str):
    sign = sign.lower()
    url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign}&day=TODAY"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            horoscope = data.get('data', {}).get('horoscope_data', 'No horoscope available.')
            date = data.get('data', {}).get('date', 'Unknown date')
            msg = f"🔮 **Daily Horoscope for {sign.capitalize()}** ({date})\n**Horoscope:** {horoscope}"
            await ctx.send(msg)
        else:
            await ctx.send("⚠️ Failed to get horoscope. Check the zodiac sign.")
    except Exception as e:
        await ctx.send(f"Error: {str(e)}")

@bot.command()
async def define(ctx, *, word):
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()[0]
            meanings = data['meanings']
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
