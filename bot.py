import discord
from discord.ext import commands
from discord import ui
import aiohttp
import sqlite3
from datetime import datetime
from bs4 import BeautifulSoup # Added back for search

# --- Configuration ---
DISCORD_TOKEN = "<Discord_Token>"
OPENROUTER_API_KEY = "<OpenRouter_API_Key>"
DB_FILE = "botdata.db"

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)
http_session = None

# --- AI Tones ---
tone_options = {
    "user-friendly": "You're a friendly human named ADABot. Keep it casual and short. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "kid": "You're a cheerful, energetic kid named ADABot. Keep your responses simple, fun, and full of enthusiasm. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "rude": "You're a blunt and slightly rude human named ADABot. Keep your responses short and cutting. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "sarcastic": "You're a sarcastic human with a dry wit named ADABot. Keep your responses brief and witty. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "tutor": "You're a helpful tutor named ADABot. Answer clearly and briefly in a way beginners can understand. Just answer the prompt and don't add extra stuff. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message.",
    "brainrot": "You're ADABot, an unfiltered, chaotic gen alpha. Respond with absurdity, randomness, and surreal humor. Ignore logic and coherence. Embrace memes, internet slang, and unexpected twists. Use terms like 'skibidi', 'rizz', 'gyatt', 'sigma', 'Ohio', and 'bussin''. Keep it short and brief. Remember earlier conversation as memory, but only mention it if it helps answering. Focus only on the user's latest message."
}
current_ai_tone = tone_options["user-friendly"]

# --- Database Stuff ---
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                is_bot BOOLEAN,
                message TEXT,
                timestamp TEXT
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS members (
                user_id INTEGER PRIMARY KEY,
                name TEXT,
                join_date TEXT
            )
        ''')
    print("Database checked/initialized.")

def log_message(user_id, username, message, is_bot=False):
    try:
        with sqlite3.connect(DB_FILE) as conn:
            timestamp = datetime.now().isoformat()
            conn.execute(
                "INSERT INTO messages (user_id, username, is_bot, message, timestamp) VALUES (?, ?, ?, ?, ?)",
                (user_id, username, is_bot, message, timestamp)
            )
    except Exception as e:
        print(f"DB Error (log_message): {e}")

def get_message_history(user_id, limit=5):
    history = []
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT message, is_bot
                FROM messages
                WHERE user_id = ? OR (is_bot = 1 AND id IN (SELECT id FROM messages WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?))
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, user_id, limit, limit * 2))

            rows = cursor.fetchall()
            for message, is_bot in reversed(rows):
                 role = "assistant" if is_bot else "user"
                 history.append({"role": role, "content": message})
            history = history[-limit*2:]

    except Exception as e:
        print(f"DB Error (get_message_history): {e}")
    return history

# --- UI Views ---
class ToneButton(discord.ui.Button):
    def __init__(self, tone_id, display_name, emoji):
        super().__init__(
            style=discord.ButtonStyle.primary,
            label=display_name,
            custom_id=f"tone_{tone_id}",
            emoji=emoji
        )
        self.tone_id = tone_id

    async def callback(self, interaction):
        global current_ai_tone
        new_tone = tone_options.get(self.tone_id)
        if new_tone:
            current_ai_tone = new_tone
            await interaction.response.send_message(
                f"✅ Switched tone to **{self.tone_id}**!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("⚠️ Couldn't find that tone.", ephemeral=True)

class ToneButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)
        emoji_map = {
            "user-friendly": "😊", "kid": "🧒", "rude": "😠",
            "sarcastic": "🙄", "tutor": "📚", "brainrot": "💀"
        }
        for tone_id in tone_options:
            display_name = tone_id.replace('-', ' ').title()
            emoji = emoji_map.get(tone_id, "🤖")
            self.add_item(ToneButton(tone_id, display_name, emoji))

class MovieGenreButton(discord.ui.Button):
    def __init__(self, genre):
        super().__init__(label=genre, style=discord.ButtonStyle.primary, custom_id=f"genre_{genre.lower()}")
        self.genre = genre

    async def callback(self, interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            reply = await ask_openrouter(
                f"Recommend a {self.genre} movie. Just the title and a one-sentence reason.",
                session=http_session
            )
            await interaction.followup.send(f"🎬 **{self.genre}:** {reply}", ephemeral=True)
        except Exception as e:
            print(f"Error getting movie recommendation: {e}")
            await interaction.followup.send(f"❌ Whoops, couldn't get a {self.genre} movie suggestion.", ephemeral=True)

class MovieGenreView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)
        genres = ["Sci-fi", "Romance", "Mystery", "Comedy", "Horror", "Fantasy", "Action", "Drama"]
        for genre in genres:
            self.add_item(MovieGenreButton(genre))

# --- API Call ---
async def ask_openrouter(prompt, session, tone=None, history=None):
    if tone is None:
        tone = current_ai_tone

    messages = [{"role": "system", "content": tone}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": prompt})

    data = {
        "model": "google/gemini-flash-1.5:free",
        "messages": messages,
        "max_tokens": 1000 # Increased back for define/search
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}

    try:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers, json=data, timeout=45 # Increased back
        ) as response:
            if response.status == 200:
                res_json = await response.json()
                return res_json.get("choices", [{}])[0].get("message", {}).get("content", "AI gave a weird answer.").strip()
            else:
                print(f"OpenRouter API error {response.status}")
                return f"❌ AI API Error ({response.status})."
    except Exception as e:
        print(f"OpenRouter Error: {e}")
        return f"❌ Couldn't reach the AI ({type(e).__name__})."

# --- Bot Events ---
@bot.event
async def on_ready():
    global http_session
    init_db()
    http_session = aiohttp.ClientSession()
    print(f'Bot online as {bot.user.name}')

@bot.event
async def on_close():
    if http_session:
        await http_session.close()
    print("Bot shutting down.")

@bot.event
async def on_member_join(member):
    if not member.bot:
        try:
            with sqlite3.connect(DB_FILE) as conn:
                join_dt = member.joined_at or datetime.now()
                join_date_str = join_dt.strftime("%Y-%m-%d %H:%M:%S")
                conn.execute(
                    "INSERT OR IGNORE INTO members (user_id, name, join_date) VALUES (?, ?, ?)",
                    (member.id, member.name, join_date_str)
                )
                print(f"Member joined and recorded: {member.name}")
        except Exception as e:
            print(f"DB Error (on_member_join): {e}")

# --- Bot Commands ---
@bot.command()
async def info(ctx):
    help_message = """
🤖 **ADABot Help Menu**

Available commands:
• !chat [message] – Talk to the AI. It remembers your conversation!
• !tone – Change the AI's personality.
• !quote – Get a motivational quote.
• !weather [city] – Check current weather.
• !joke – Get a random joke.
• !search [topic] – Get a Wikipedia summary.
• !movie – Get a movie suggestion by genre.
• !zodiac [sign] – Get a daily horoscope.
• !define [word] – Look up a word definition.
• !info – Shows this help menu.
"""
    await ctx.send(help_message)

@bot.command()
async def tone(ctx):
    current_tone_name = next((name for name, text in tone_options.items() if text == current_ai_tone), "unknown")
    await ctx.send(
        f"Current tone: **{current_tone_name.replace('-', ' ').title()}**\nChoose a new one:",
        view=ToneButtonsView()
    )

@bot.command()
async def chat(ctx, *, message: str):
    user = ctx.author
    log_message(user.id, user.name, message, is_bot=False)

    async with ctx.typing():
        history = get_message_history(user.id)
        reply = await ask_openrouter(message, http_session, history=history)

        if not reply.startswith("❌"):
             log_message(bot.user.id, bot.user.name, reply, is_bot=True)

        if len(reply) > 1950:
            reply = reply[:1950] + "..."

    await ctx.send(f"{user.mention} {reply}")

@bot.command()
async def quote(ctx):
    async with ctx.typing():
        prompt = "Give me a short, inspiring motivational quote. Format: \"Quote text.\" - Author"
        result = await ask_openrouter(prompt, http_session, tone="You provide quotes.")
        await ctx.send(f"💬 {result}")

@bot.command()
async def weather(ctx, *, city: str):
    async with ctx.typing():
        try:
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json"
            async with http_session.get(geo_url) as geo_resp:
                if geo_resp.status != 200:
                    await ctx.send(f"⚠️ Couldn't geocode '{city}'.")
                    return
                geo_data = await geo_resp.json()
                if not geo_data.get("results"):
                    await ctx.send(f"⚠️ Couldn't find location for '{city}'.")
                    return
                loc = geo_data["results"][0]
                lat, lon = loc.get("latitude"), loc.get("longitude")
                display_name = loc.get("name", city)

            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}¤t=temperature_2m,wind_speed_10m,wind_direction_10m&temperature_unit=celsius&wind_speed_unit=kmh"
            async with http_session.get(weather_url) as weather_resp:
                if weather_resp.status != 200:
                     await ctx.send("⚠️ Weather data unavailable.")
                     return
                weather_data = await weather_resp.json()
                current = weather_data.get("current")
                if not current:
                    await ctx.send("⚠️ Could not parse weather data.")
                    return

                temp = current.get('temperature_2m', 'N/A')
                wind = current.get('wind_speed_10m', 'N/A')
                wind_dir = current.get('wind_direction_10m', 'N/A')

                await ctx.send(
                    f"☀️ **Weather in {display_name.title()}**:\n"
                    f"- Temp: {temp}°C\n"
                    f"- Wind: {wind} km/h at {wind_dir}°"
                 )

        except Exception as e:
            print(f"Weather Error: {e}")
            await ctx.send(f"❌ Error getting weather.")

@bot.command()
async def joke(ctx):
    async with ctx.typing():
        try:
            async with http_session.get("https://official-joke-api.appspot.com/random_joke", timeout=10) as response:
                if response.status != 200:
                    await ctx.send("⚠️ Couldn't reach the joke factory.")
                    return
                data = await response.json()
                await ctx.send(f"😂 {data['setup']} ... {data['punchline']}")
        except Exception as e:
            print(f"Joke Error: {e}")
            await ctx.send("❌ Failed to get joke.")

@bot.command()
async def search(ctx, *, query: str):
    formatted_query = query.replace(" ", "_")
    wiki_url = f"https://en.wikipedia.org/wiki/{formatted_query}"

    async with ctx.typing():
        try:
            async with http_session.get(wiki_url, timeout=15) as response:
                if response.status != 200:
                    await ctx.send(f"❌ Could not find a Wikipedia page for '{query}'.")
                    return
                html = await response.text()

            soup = BeautifulSoup(html, "html.parser")
            content_div = soup.find(id="mw-content-text")
            if not content_div:
                await ctx.send("❌ Couldn't identify the main content of the page.")
                return

            paragraphs = content_div.find_all("p", limit=6)
            text = " ".join(p.get_text() for p in paragraphs if p.get_text().strip()).strip()

            if not text:
                await ctx.send("❌ Found the page, but couldn't extract readable text.")
                return

            text = text[:2500] + "..." if len(text) > 2500 else text

            summary_prompt = f"Briefly summarize this Wikipedia text about '{query}':\n\n{text}"
            summary = await ask_openrouter(summary_prompt, http_session,
                                      tone="You are a helpful assistant summarizing text accurately and concisely.")

            if len(summary) > 1800:
                summary = summary[:1800] + "..."

            await ctx.send(f"📚 **Summary for '{query}'**:\n{summary}\n\n🔗 Link: <{wiki_url}>")

        except Exception as e:
            print(f"Search Error: {e}")
            await ctx.send(f"❌ Error searching for '{query}'.")

@bot.command()
async def movie(ctx):
    await ctx.send("🎥 What genre are you in the mood for?", view=MovieGenreView())

@bot.command()
async def zodiac(ctx, sign: str):
    sign = sign.lower()
    valid_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra",
                  "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    if sign not in valid_signs:
        await ctx.send(f"⚠️ '{sign}' is not a valid zodiac sign. Please use one of: {', '.join(valid_signs)}.")
        return

    async with ctx.typing():
        try:
            url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?sign={sign}&day=TODAY"
            async with http_session.get(url, timeout=15) as response:
                if response.status != 200:
                    await ctx.send(f"⚠️ Failed to get horoscope for {sign.capitalize()}.")
                    return
                data = await response.json()
                horoscope = data.get('data', {}).get('horoscope_data', 'Not available.')
                await ctx.send(f"🔮 **{sign.capitalize()} Today:**\n{horoscope}")
        except Exception as e:
            print(f"Zodiac Error: {e}")
            await ctx.send(f"❌ Error getting horoscope.")

@bot.command()
async def define(ctx, *, word: str):
    word = word.strip().split()[0] if word.strip() else ""
    if not word:
        await ctx.send("Please provide a word to define!")
        return

    async with ctx.typing():
        try:
            url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
            async with http_session.get(url, timeout=15) as response:
                if response.status == 404:
                    await ctx.send(f"❌ Couldn't find the word '{word}' in the dictionary.")
                    return
                elif response.status != 200:
                    await ctx.send(f"⚠️ Dictionary API error ({response.status}).")
                    return

                data = await response.json()
                if not isinstance(data, list) or not data:
                    await ctx.send(f"❌ Couldn't find a definition for '{word}'.")
                    return

                entry = data[0]
                meanings = entry.get('meanings', [])
                if not meanings:
                    await ctx.send(f"❌ Found the word '{word}', but no meanings were listed.")
                    return

                message_text = f"📖 **{entry.get('word', word).capitalize()}**:\n"
                definition_count = 0

                for i, meaning in enumerate(meanings[:3]):
                    part_of_speech = meaning.get('partOfSpeech', 'N/A')
                    definitions = meaning.get('definitions', [])
                    if definitions:
                        definition = definitions[0].get('definition', 'No definition found.')
                        definition_count += 1
                        message_text += f"\n{definition_count}. **({part_of_speech})**: {definition}"

                        example = definitions[0].get('example')
                        if example:
                            message_text += f"\n   *Example: {example}*"

                if definition_count == 0:
                    await ctx.send(f"❌ Found the word '{word}', but couldn't extract definitions.")
                else:
                    if len(message_text) > 1950:
                        message_text = message_text[:1950] + "..."
                    await ctx.send(message_text)

        except Exception as e:
            print(f"Define Error: {e}")
            await ctx.send(f"❌ Error looking up '{word}'.")


# --- Start Bot ---
print("Starting bot...")
bot.run(DISCORD_TOKEN)
