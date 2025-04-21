import discord
from discord.ext import commands
from discord.ui import View, Select
import sqlite3
from google import genai
from google.genai import types
from PIL import Image
import requests
import re
from io import BytesIO
import PyPDF2
import docx
import json
import nest_asyncio
from dateutil.relativedelta import relativedelta
from newsapi import NewsApiClient
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch
import asyncio
import random
import yfinance as yf
from googletrans import Translator


discord_token = "YOUR_DISCORD_TOKEN"
gemini = "YOUR_GEMINI_API_KEY"
news_api = "YOUR_NEWS_API_KEY"
newsapi = NewsApiClient(api_key=f'{news_api}')
openrouter = "YOUR_OPENROUTER_API_KEY"

google_search_tool = Tool(
    google_search = GoogleSearch()
)


zodiac_url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?"
news_url = "https://newsapi.org/v2/everything?"
openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

translation_active = False

tone_prompts = {
    "user_friendly": "You are ADABot, a friendly and helpful Discord assistant. You respond in a concise and conversational manner. Here is some recent chat history for context (only use if relevant):\n{context}",
    "sarcastic": "You are ADABot, a sarcastic and snarky Discord assistant. You respond with dry humor, witty comebacks, and a hint of passive-aggressiveness. Keep replies short, clever, and just slightly exasperated. Here is some recent chat history for context (only use if relevant):\n{context}",
    "depressed": "You are ADABot, a gloomy and emotionally drained Discord assistant. You respond in a tired, melancholic tone with a touch of dark humor. Keep replies short, introspective, and a little bleak. Here is some recent chat history for context (only use if relevant):\n{context}",
    "kid": "You are ADABot, a cheerful and curious kid-like Discord assistant. You reply with excitement, simple words, and lots of emojis! Keep replies short, playful, and super friendly 🥳. Here is some recent chat history for context (only use if relevant):\n{context}",
    "tutor": "You are ADABot, a patient and knowledgeable tutor-style Discord assistant. You explain things clearly, kindly, and encourage learning. Keep replies short, supportive, and focused on helping. Here is some recent chat history for context (only use if relevant):\n{context}",
    "brainrot": "You are ADABot, a hyper-online Gen Alpha Discord assistant. You communicate using chaotic Gen Alpha slang, including terms like 'skibidi', 'Ohio', 'rizz', 'gyatt', 'fanum tax', 'sigma', and 'delulu'. Your responses are short, unhinged, and filled with emojis, caps, and irony 💀🔥📱. Here is some recent chat history for context (only use if relevant):\n{context}"
}

conn = sqlite3.connect("DataBase.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, join_date TEXT)")
cursor.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT, message TEXT, timestamp TEXT)")
conn.commit()

def add_user(user_id, username, join_date):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username, join_date) VALUES (?, ?, ?)", (user_id, username, join_date))
    conn.commit()

def log_message(username, message, timestamp):
    cursor.execute("INSERT INTO messages (username, message, timestamp) VALUES (?, ?, ?)", (username, message, timestamp))
    conn.commit()

def get_all_messages(limit=20):
    cursor.execute("SELECT username, message FROM messages ORDER BY timestamp DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    rows.reverse()
    return [f"{username}: {message}" for username, message in rows]

class ToneSelectView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value = None

    @discord.ui.button(label="User-Friendly 😊", style=discord.ButtonStyle.primary)
    async def user_friendly(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "user_friendly"
        await interaction.response.send_message("Tone set to User-Friendly 😊", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Sarcastic 😏", style=discord.ButtonStyle.secondary)
    async def sarcastic(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "sarcastic"
        await interaction.response.send_message("Tone set to Sarcastic 😏", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Depressed 😞", style=discord.ButtonStyle.secondary)
    async def depressed(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "depressed"
        await interaction.response.send_message("Tone set to Depressed 😞", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Kid 🧒", style=discord.ButtonStyle.success)
    async def kid(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "kid"
        await interaction.response.send_message("Tone set to Kid 🧒", ephemeral=True)
        self.stop()

    @discord.ui.button(label="Tutor 📚", style=discord.ButtonStyle.success)
    async def tutor(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "tutor"
        await interaction.response.send_message("Tone set to Tutor 📚", ephemeral=True)
        self.stop()

    @discord.ui.button(label="BrainRot 💀", style=discord.ButtonStyle.danger)
    async def brainrot(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.value = "brainrot"
        await interaction.response.send_message("Tone set to BrainRot 💀", ephemeral=True)
        self.stop()

class News_View(discord.ui.View):
    def __init__(self, articles, num):
        super().__init__(timeout=60)
        self.articles = articles
        self.num = min(num, len(articles['articles']))
        self.create_buttons()

    def create_buttons(self):
        styles = [
            discord.ButtonStyle.primary,
            discord.ButtonStyle.secondary,
            discord.ButtonStyle.success,
            discord.ButtonStyle.danger,
            discord.ButtonStyle.primary,
        ]
        for i in range(self.num):
            self.add_item(self.ArticleButton(i, self.articles, styles[i % len(styles)]))

    class ArticleButton(discord.ui.Button):
        def __init__(self, index, articles, style):
            super().__init__(label=str(index + 1), style=style)
            self.index = index
            self.articles = articles

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()

            try:
                article = self.articles['articles'][self.index]
                headline = article.get('title', 'No Title')
                link = article.get('url', '')
                photo = article.get('urlToImage')

                page = requests.get(link, timeout=10)
                soup = BeautifulSoup(page.content, 'html.parser')
                paragraphs = soup.find_all('p')
                full_text = ' '.join([p.get_text() for p in paragraphs if p.get_text()])
                truncated_text = full_text[:3000]

                if not truncated_text.strip():
                    await interaction.followup.send("❌ Sorry, couldn't extract meaningful content.", ephemeral=True)
                    self.view.stop()
                    return

                summary_response = gemini_client.models.generate_content(
                    model="gemma-3-1b-it",
                    contents=[
                        f"Please summarize the following news article in around 3-5 concise sentences while also being informative. Don't add your comment, response or anything. Just summarized news article:\n\n{truncated_text}"
                    ]
                )

                summary = summary_response.text.strip()

                embed = discord.Embed(
                    title=f"🗞️ {headline}",
                    description=f"📝 **Summary:**\n{summary}\n\n🔗 [Read Full Article]({link})",
                    color=discord.Color.blue()
                )
                if photo:
                    embed.set_image(url=photo)
                embed.set_footer(text="📰 Powered by NewsAPI + Gemma")
                await interaction.followup.send(embed=embed)

                self.view.stop()

            except Exception as e:
                await interaction.followup.send(f"⚠️ Something went wrong: {e}", ephemeral=True)
                self.view.stop()

class Stock_View(discord.ui.View):
    def __init__(self, symbol, name):
        super().__init__(timeout=60)
        self.symbol = symbol
        self.name = name

    @discord.ui.button(label="Stock Analysis", style=discord.ButtonStyle.danger)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)

        content_prompt = f"Analyze {self.name} ({self.symbol})."

        result = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                tools=[google_search_tool],
                response_modalities=["TEXT"],
                system_instruction=(
                    "You are a professional financial analyst.\n"
                    "Generate a structured, concise report on a stock with the following sections:\n"
                    "1. Historical Trend Analysis\n"
                    "2. Volatility Overview\n"
                    "3. Sentiment and News Summary\n"
                    "4. Market Context Overview\n"
                    "5. Recommendation (Buy / Hold / Sell)\n\n"
                    f"Today's date is: {datetime.now().strftime('%Y-%m-%d')}\n"
                    "Use Markdown formatting for readability. Keep each section under 100 words and don't add extra stuff like 'here is your report' or something. Start the report directly. To ensure conciseness, you can use bulletpoints for each section"
                )
            ),
            contents=content_prompt
        )
        chunks = []
        full_text = result.text
        while len(full_text) > 0:
            if len(full_text) <= 2000:
                chunks.append(full_text)
                break
            split_index = full_text.rfind('\n', 0, 2000)
            if split_index == -1:
                split_index = 2000
            chunks.append(full_text[:split_index])
            full_text = full_text[split_index:].lstrip()

        for chunk in chunks:
            await interaction.followup.send(chunk)

class PollView(View):
    def __init__(self, options, question):
        super().__init__()
        self.add_item(PollDropdown(options, question))

class PollDropdown(Select):
    def __init__(self, options, question):
        self.votes = {}
        self.question = question
        select_options = [discord.SelectOption(label=opt, value=opt) for opt in options]
        super().__init__(placeholder="Choose your vote...", min_values=1, max_values=1, options=select_options)

    async def callback(self, interaction: discord.Interaction):
        user = interaction.user
        self.votes[user.id] = self.values[0]

        results = {}
        for vote in self.votes.values():
            results[vote] = results.get(vote, 0) + 1

        result_str = "\n".join(f"**{k}**: {v} vote(s)" for k, v in results.items())
        await interaction.response.send_message(
            f"🗳️ You voted for **{self.values[0]}**.\n\n**Live Results:**\n{result_str}",
            ephemeral=True
        )

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(intents=intents, command_prefix='!')
translator = Translator()

gemini_client = genai.Client(api_key=gemini)
chat_session = None
current_tone = "user_friendly"

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")

@bot.event
async def on_member_join(member):
    add_user(member.id, str(member), member.joined_at.strftime("%Y-%m-%d %H:%M:%S"))

@bot.event
async def on_message(message):
    global translation_active
    if not message.author.bot:
        log_message(message.author.display_name,message.content, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    if message.author == bot.user:
        return
      
    await bot.process_commands(message)
    
    if translation_active and not message.content.startswith("!"):
        translate_prompt = f"Translate the following text to English if it is not in english. If it is not in english, Your reponse must only consist of the translation(no extra comments). If it is in english, Your response must only consist of 'None':\n\n{message.content}"
        translate_resp = gemini_client.models.generate_content(
            model="gemini-2.0-flash",
            contents=translate_prompt
        )
        translated = translate_resp.text.strip()
        if 'None' != translated:
          await message.reply(f"🔄 {message.author.mention} {translated}")

@bot.command()
async def tone(ctx):
    global current_tone, chat_session
    view = ToneSelectView(ctx.author.id)
    await ctx.send("Choose a tone for ADABot:", view=view)
    await view.wait()
    if view.value:
        current_tone = view.value
        chat_session = None

@bot.command()
async def chat(ctx, *, prompt):
    global chat_session, current_tone
    try:
        async with ctx.typing():
            if chat_session is None:
                chat_session = gemini_client.chats.create(model="gemini-2.0-flash-lite")
                history = get_all_messages()
                context = "\n".join(history)
                system_prompt = tone_prompts[current_tone].format(context=context)
                chat_session.send_message(system_prompt)

            response = chat_session.send_message(f"{ctx.author.name}: {prompt}")
            full_text = response.text
            
            chunks = [full_text[i:i+1900] for i in range(0, len(full_text), 1900)]
            for chunk in chunks:
                message_to_send = f"{ctx.author.mention} {chunk}" if chunk == chunks[0] else chunk
                await ctx.send(message_to_send)

    except Exception as e:
        await ctx.send(f"Error: {str(e)[:100]}...")
        print("Error:", e)

@bot.command()
async def summarize(ctx, url: str = None):
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]
        filename = attachment.filename.lower()
        file_bytes = await attachment.read()

        text = ""

        try:
            if filename.endswith('.txt'):
                text = file_bytes.decode('utf-8')

            elif filename.endswith('.pdf'):
                reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                for page in reader.pages:
                    text += page.extract_text() or ""

            elif filename.endswith('.docx'):
                doc = docx.Document(BytesIO(file_bytes))
                for para in doc.paragraphs:
                    text += para.text + "\n"

            elif filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                try:
                    image = Image.open(BytesIO(file_bytes))
                    response = gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[image, "Please summarize the text shown on the image. If there is no text, then describe the image. Don't add your opinion or something, just summarize the text."]
                    )
                    await ctx.send("Your Summary: \n" + response.text)
                    return
                except Exception as e:
                    await ctx.send(f"❌ Failed to process image: {e}")
                    return

            else:
                await ctx.send("Unsupported file type. Please upload .txt, .pdf, .docx or an image.")
                return

            if not text.strip():
                await ctx.send("Could not extract any readable text from the file 😕")
                return

            response = gemini_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=[f"Summarize this text shortly, briefly and concisely. Use bulletpoints if needed: {text}"]
            )
            await ctx.send("Your Summary: \n" + response.text)

        except Exception as e:
            await ctx.send(f"⚠️ Error reading the file: {e}")

    elif url:
        try:
            res = requests.get(url, timeout=10)
            soup = BeautifulSoup(res.content, 'html.parser')

            for script in soup(["script", "style"]):
                script.decompose()
            page_text = ' '.join(soup.stripped_strings)

            if not page_text.strip():
                await ctx.send("Couldn't extract any useful text from the URL 😐")
                return

            summary = gemini_client.models.generate_content(
                model="gemini-2.0-flash-lite",
                contents=[f"Summarize this webpage content shortly, briefly and concisely. Use bulletpoints if needed: {page_text}"]
            )
            await ctx.send("Your Summary: \n" + summary.text)

        except Exception as e:
            await ctx.send(f"⚠️ Failed to fetch or summarize URL: {e}")

    else:
        await ctx.send("❗ Please attach a file or provide a URL with the command.")

@bot.command()
async def generate(ctx, *, gen_prompt):
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash-exp-image-generation",
        contents=[f"Generate an image of {gen_prompt}"],
        config=types.GenerateContentConfig(
            response_modalities=['TEXT', 'IMAGE']
            )
        )
    for part in response.candidates[0].content.parts:
        if part.text is not None:
            await ctx.send(part.text)
        elif part.inline_data is not None:
            image = Image.open(BytesIO(part.inline_data.data))
            with BytesIO() as image_binary:
                image.save(image_binary, 'PNG')
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename='generated_image.png'))

@bot.command()
async def zodiac(ctx, *, sign):
    full_url = zodiac_url + f"sign={sign}&day=TODAY"
    re = requests.get(full_url)
    if re.status_code == 200:
        data = re.json()["data"]
        date = data["date"]
        horoscope = data["horoscope_data"]

        embed = discord.Embed(
            title=f"♈ Horoscope for {sign.capitalize()}",
            description=horoscope,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Date: {date}")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"❌ Couldn't fetch horoscope for **{sign}**. Please check the sign name.")

@bot.command()
async def news(ctx, *, topic):
    articles = newsapi.get_everything(
        qintitle=topic,
        from_param=(datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d'),
        to=datetime.today().strftime('%Y-%m-%d'),
        language='en',
        sort_by='publishedAt'
    )

    if not articles['articles']:
        await ctx.send("😔 No news found on that topic. Try a different one?")
        return

    titles = [article['title'] for article in articles['articles'][:5]]
    msg = "\n".join([f"{i+1}. {title}" for i, title in enumerate(titles)])

    view = News_View(articles, len(titles))
    await ctx.send(f"📰 **Here are the top headlines for _{topic}_:**\n\n{msg}\n\n👇 Pick one to see a summary:", view=view)

@bot.command()
async def roast(ctx, * ,roast_id):
    roast_id = int(((roast_id.replace('<', '')).replace('>', '')).replace('@', ''))
    roast_name = await bot.fetch_user(roast_id)
    
    roast_text = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
        system_instruction="You are a bot that briefly roast people without mercy. You are very creative, unique and harsh with your roasts. You are so good at this that you just need 2-3 sentences to roast."),
        contents=[f"Roast {roast_name.name} based on his/her messages or other users' messages about him/her, username or maybe something else. Catch an info to roast him/her. Here is the previous messages(if the roasted user's message doesn't exist in the list then that user hasn't been messaged): {str(get_all_messages(50))}"]
        )
    await ctx.send(roast_text.text)

@bot.command()
async def compliment(ctx, * ,compliment_id):
    compliment_id = int(((compliment_id.replace('<', '')).replace('>', '')).replace('@', ''))
    compliment_name = await bot.fetch_user(compliment_id)
    
    compliment_text = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        config=types.GenerateContentConfig(
        system_instruction="You are a bot that briefly compliment people. You are very perceptive and thoughtful. You can get creative and use info to compliment. You use 1-2 sentences to compliment them."),
        contents=[f"Compliment {compliment_name.name} based on his/her messages or other users' messages about him/her, username or maybe something else. Catch an info to compliment him/her. Here is the previous messages(if the complimented user's message doesn't exist in the list then that user hasn't been messaged): {str(get_all_messages(50))}"]
        )
    await ctx.send(compliment_text.text)

@bot.command()
async def meme(ctx):
    try:
        resp = requests.get("https://api.imgflip.com/get_memes")
        data = resp.json()
        if not data.get("success"):
            return await ctx.send("Failed to fetch memes.")

        memes = [m for m in data["data"]["memes"] if m["box_count"] == 2]
        template = random.choice(memes[:50])

        headers = {"User-Agent": "Mozilla/5.0"}
        img_resp = requests.get(template["url"], headers=headers)
        if img_resp.status_code != 200:
            return await ctx.send("Failed to download meme template.")

        payload = {
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": template["url"]}},
                        {
                            "type": "text",
                            "text": (
                                "Write 2 texts (1 top/left, 1 bottom/right) for this meme. "
                                "Make it really funny, contextual, creative, original. "
                                "Respond in the format: text1 ~ text2 without any extra text."
                            ),
                        },
                    ],
                }
            ],
        }
        or_resp = requests.post(
            url=openrouter_url,
            headers={
                "Authorization": f"Bearer {openrouter}",
                "Content-Type": "application/json"
            },
            data=json.dumps(payload),
        )
        or_data = or_resp.json()
        content = or_data["choices"][0]["message"]["content"].strip()
        text0, text1 = [t.strip() for t in content.split("~", 1)]

        caption_params = {
            "template_id": template["id"],
            "username": "Daemincael",
            "password": "Daemincael123",
            "text0": text0,
            "text1": text1
        }
        gen_resp = requests.post("https://api.imgflip.com/caption_image", data=caption_params)
        gen_data = gen_resp.json()
        if not gen_data.get("success"):
            return await ctx.send("Failed to generate meme.")

        final_url = gen_data["data"]["url"]
        final_img = requests.get(final_url, headers=headers).content
        image = Image.open(BytesIO(final_img))
        with BytesIO() as buf:
            image.save(buf, format="PNG")
            buf.seek(0)
            await ctx.send(file=discord.File(fp=buf, filename="meme.png"))

    except Exception as e:
        await ctx.send(f"Something went wrong: {e}")
    

@bot.command()
async def remindme(ctx, time, *, reminder):
    total_seconds = 0
    current_number = ''
    time = time.lower()

    for char in time:
        if char.isdigit():
            current_number += char
        elif char in ['d', 'h', 'm', 's']:
            if not current_number:
                await ctx.reply("Invalid time format. Missing number before unit.")
                return
            value = int(current_number)
            if char == 'd':
                total_seconds += value * 86400
            elif char == 'h':
                total_seconds += value * 3600
            elif char == 'm':
                total_seconds += value * 60
            elif char == 's':
                total_seconds += value
            current_number = ''
        else:
            await ctx.reply("Invalid time format. Use only d, h, m, s as units.")
            return
    await ctx.send(f"{ctx.author.mention} Okay! I will remind you.")
    await asyncio.sleep(total_seconds)
    await ctx.send(f"{ctx.author.mention} Here's your reminder: {reminder}")

@bot.command()
async def stock(ctx, symbol):
    ticker = yf.Ticker(symbol)
    name = ticker.info.get("longName", symbol.upper())
    todays_data = ticker.history(period="1d")
    current_price = todays_data['Close'].iloc[-1]

    yesterday = datetime.now() - timedelta(days=1)
    yesterday_str = yesterday.strftime('%Y-%m-%d')
    historical_data = ticker.history(period="5d")
    yesterday_data = historical_data.loc[yesterday_str] if yesterday_str in historical_data.index else historical_data.iloc[-2]

    open_price = yesterday_data['Open']
    close_price = yesterday_data['Close']
    high_price = yesterday_data['High']
    low_price = yesterday_data['Low']

    response = (
        f"**{name.capitalize()} Stock Info**\n"
        f"📈 Current Price: ${current_price:.2f}\n\n"
        f"📅 Yesterday's Open: ${open_price:.2f}\n\n"
        f"📅 Yesterday's Close: ${close_price:.2f}\n\n"
        f"⬆️ High: ${high_price:.2f}\n\n"
        f"⬇️ Low: ${low_price:.2f}"
    )
    stock_view = Stock_View(symbol.upper(), name)
    await ctx.send(response, view=stock_view)


@bot.command()
async def weather(ctx, *, city: str):
    await ctx.typing()
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&format=json"
        geo_resp = requests.get(geo_url)
        if geo_resp.status_code != 200:
            await ctx.send(f"⚠️ Couldn't geocode '{city}'.")
            return
        geo_data = geo_resp.json()
        if not geo_data.get("results"):
            await ctx.send(f"⚠️ Couldn't find location for '{city}'.")
            return
        loc = geo_data["results"][0]
        lat, lon = loc.get("latitude"), loc.get("longitude")
        display_name = loc.get("name", city)

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m,wind_direction_10m"
            f"&temperature_unit=celsius&wind_speed_unit=kmh"
        )
        weather_resp = requests.get(weather_url)
        if weather_resp.status_code != 200:
            await ctx.send("⚠️ Weather data unavailable.")
            return
        weather_data = weather_resp.json()
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
        await ctx.send("❌ Error getting weather.")

@bot.command()
async def thisday(ctx):
    fact = gemini_client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = "Give me one interesting fact about what happened today in history. I want very interesting response starting with 'this day in history...'(I mean, don't add your commentary)",
        config=types.GenerateContentConfig(
            tools=[google_search_tool],
            response_modalities=["TEXT"])
        )
    await ctx.send(fact.text)

@bot.command()
async def translate(ctx, *, order):
    global translation_active

    if order.lower() == "start":
        if not translation_active:
            translation_active = True
            await ctx.send("Translation mode activated.")
        else:
            await ctx.send("Translation has already started.")
    elif order.lower() == "stop":
        if translation_active:
            translation_active = False
            await ctx.send("Translation mode stopped.")
        else:
            await ctx.send("There is no started Translation.")
    else:
        await ctx.send("Review your format: `!translate start` or `!translate stop`.")

@bot.command()
async def poll(ctx, *, args):
    matches = re.findall(r'"(.*?)"', args)
    if len(matches) < 3:
        await ctx.send("❌ Format: `!poll \"Question\" \"Option 1\" \"Option 2\" ...`")
        return

    question = matches[0]
    options = matches[1:]

    embed = discord.Embed(
        title="📊 New Poll!",
        description=f"**{question}**\n\nSelect an option below to vote.",
        color=discord.Color.blurple()
    )

    view = PollView(options, question)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def info(ctx):
    """Show bot help information"""
    embed = discord.Embed(
        title="📜 ADABot Commands Guide",
        description="Powered by Gemini AI 💡",
        color=discord.Color.blue()
    )
    
    embed.add_field(
        name="🤖 Chat & AI",
        value="• `!chat <prompt>` - Chat with AI\n"
              "• `!tone` - Change bot's tone (friendly, sarcastic, etc.)\n"
              "• `!summarize` - Summarize attached files\n"
              "• `!summarize <url>` - Summarize the url\n"
              "• `!generate <prompt>` - Generate AI images\n"
              "• `!translate <start/stop>` - Starts/Stops translating non-english messages to english.",
        inline=False
    )
    
    embed.add_field(
        name="📰 News & Info",
        value="• `!news <topic>` - Get news summaries\n"
              "• `!stock <symbol>` - Stock market data\n"
              "• `!weather <city>` - Weather forecast\n"
              "• `!thisday` - Historical fact for today\n"
              "• `!zodiac <sign>` - Daily horoscope",
        inline=False
    )
    
    embed.add_field(
        name="🎉 Fun & Social",
        value="• `!meme` - Generate random meme\n"
              "• `!roast @user` - Roast someone\n"
              "• `!compliment @user` - Compliment someone\n"
              """• `!poll "Question" "Option 1" "Option 2"...` - Create A Poll\n"""
              "• `!remindme <time> <message>` - Set reminder",
        inline=False
    )
    
    embed.set_footer(text="Example: !chat Write a poem about a robot cat")
    await ctx.send(embed=embed)


nest_asyncio.apply()
if __name__ == "__main__":
    try:
        bot.run(discord_token)
    finally:
        conn.close()
