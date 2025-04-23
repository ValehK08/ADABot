import discord
from discord.ext import commands
import requests
import re
from datetime import datetime, timedelta
import asyncio
from dateutil.relativedelta import relativedelta
from newsapi import NewsApiClient
import config
import traceback
from google import genai
from google.genai import types
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch

# --- Utility Commands Cog ---
class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.newsapi = NewsApiClient(api_key=config.NEWS_API_KEY)
        self.zodiac_url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily?"
        self.gemini_client = None
    
    async def _ensure_client(self):
        if not self.gemini_client:
            main_cog = self.bot.get_cog('MainCommands')
            if main_cog and main_cog.gemini_client:
                self.gemini_client = main_cog.gemini_client
            else:
                try:
                    self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                except Exception as e:
                    print(f"Failed to initialize Gemini client in Utility: {e}")
                    return False
        return bool(self.gemini_client)

    @commands.Cog.listener()
    async def on_ready(self):
        """Ensure Gemini client is available after bot is ready."""
        await self._ensure_client()
        print(f"Utility Cog loaded. Gemini Client {'Available' if self.gemini_client else 'Not Available'}.")


    @commands.command(aliases=['manual'])
    async def info(self, ctx):
        """Shows the list of available commands."""
        embed = discord.Embed(
            title="📜 ADABot Commands Guide",
            description="Here's what I can do! (Powered by Gemini AI 💡)",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="🤖 Chat & AI",
            value="• `!chat <prompt>` - Chat with AI\n"
                  "• `!tone` - Change bot's personality (friendly, sarcastic, etc.)\n"
                  "• `!summarize` - Summarize attached files (.txt, .pdf, .docx, images)\n"
                  "• `!summarize <url>` - Summarize a webpage\n"
                  "• `!generate <prompt>` - Generate AI images\n"
                  "• `!translate <start/stop>` - Toggle auto-translation of non-English messages.",
            inline=False
        )

        embed.add_field(
            name="📰 News & Info",
            value="• `!news <topic>` - Get recent news summaries\n"
                  "• `!stock <symbol>` - Get stock market data & analysis\n"
                  "• `!weather <city>` - Current weather forecast\n"
                  "• `!thisday` - Historical fact for today\n"
                  "• `!zodiac <sign>` - Daily horoscope (e.g., `!zodiac Aries`)",
            inline=False
        )

        embed.add_field(
            name="🎉 Fun & Utilities",
            value="• `!meme` - Generate a random AI-captioned meme\n"
                  "• `!roast @user` - Lightheartedly roast someone\n"
                  "• `!compliment @user` - Compliment someone\n"
                  """• `!poll "Question" "Opt 1" "Opt 2"...` - Create a poll\n"""
                  "• `!remindme <time> <message>` - Set a reminder (e.g., `!remindme 1h30m Check oven`)",
            inline=False
        )

        embed.set_footer(text="Example: !chat Write a poem about a robot cat")
        await ctx.send(embed=embed)

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user) # Cooldown: 1 use per 5 sec
    async def zodiac(self, ctx, *, sign: str = None):
        """Gets the daily horoscope for a zodiac sign."""
        if not sign:
            await ctx.send("❓ Please provide a zodiac sign (e.g., `!zodiac Leo`).")
            return
        # Getting zodiac sign
        sign = sign.strip().capitalize()
        valid_signs = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
        if sign not in valid_signs:
             await ctx.send(f"❌ Invalid sign: '{sign}'. Please use one of: {', '.join(valid_signs)}.")
             return

        full_url = self.zodiac_url + f"sign={sign}&day=TODAY"
        await ctx.typing()

        try:
            response = requests.get(full_url, timeout=10)
            response.raise_for_status() # Raise HTTPError for bad responses
            data = response.json()

            if "data" in data and "horoscope_data" in data["data"]:
                horoscope_data = data["data"]
                date = horoscope_data.get("date", "Today")
                horoscope = horoscope_data.get("horoscope_data", "No horoscope data found.")

                embed = discord.Embed(
                    title=f"✨ Horoscope for {sign} ✨",
                    description=horoscope,
                    color=discord.Color.random()
                )
                embed.set_footer(text=f"Date: {date}")
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"❌ Couldn't parse horoscope data for **{sign}** from the API.")
                print(f"Zodiac API Response (raw): {data}")

        except requests.exceptions.Timeout:
             await ctx.send(f"❌ Request timed out while fetching horoscope for **{sign}**.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Couldn't fetch horoscope for **{sign}**: {e}")
        except Exception as e:
             await ctx.send(f"❌ An unexpected error occurred fetching the horoscope: {e}")
             traceback.print_exc()

    @zodiac.error
    async def zodiac_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Horoscope cooldown! Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
             await ctx.send("❓ Please provide a zodiac sign. Usage: `!zodiac <sign>`")
        else:
             await ctx.send(f"⚠️ An error occurred with the zodiac command: {error}")
             traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user) # 1 use per 10 sec
    async def news(self, ctx, *, topic: str = None):
        """Gets recent news headlines for a topic and summarizes selected articles."""
        if not config.NEWS_API_KEY:
            await ctx.send("⚠️ News API key is not configured. This command is unavailable.")
            return

        if not topic:
            await ctx.send("❓ What topic are you interested in? Usage: `!news <topic>`")
            return

        if not await self._ensure_client():
            await ctx.send("⚠️ AI service for summarization is unavailable. Headlines will be shown without summary option.")
        await ctx.typing()

        try:
            # Get news from the last 7 days based on relevancy
            from_date = (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d')
            articles = self.newsapi.get_everything(
                q=topic,
                from_param=from_date,
                language='en',
                sort_by='relevancy',
                page_size=5
            )

            if not articles or articles.get('status') != 'ok' or not articles.get('articles'):
                await ctx.send(f"😔 No relevant news found for '{topic}' in the last 7 days. Try a broader topic?")
                return

            article_list = articles['articles']
            titles = [f"{i+1}. {article['title']}" for i, article in enumerate(article_list)]
            msg = "\n".join(titles)

            from cogs.uis import News_View 

            embed = discord.Embed(
                title=f"📰 Top 5 News Headlines for '{topic.capitalize()}'",
                description=msg,
                color=discord.Color.orange()
            )
            embed.set_footer(text="Click a number button below to get a summary.")

            view = News_View(articles, len(titles), self.gemini_client)
            await ctx.send(embed=embed, view=view)

        except Exception as e:
            await ctx.send(f"⚠️ Error fetching news for '{topic}': {e}")
            traceback.print_exc()

    @news.error
    async def news_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ News cooldown! Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Please provide a topic to search for news. Usage: `!news <topic>`")
        else:
            await ctx.send(f"⚠️ An error occurred with the news command: {error}")
            traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user) # Cooldown: 1 use per 5 sec
    async def weather(self, ctx, *, city: str = None):
        """Gets the current weather for a specified city."""
        if not city:
            await ctx.send("❓ Please specify a city. Usage: `!weather <city>`")
            return

        await ctx.typing()
        try:
            # 1. Geocode city to get coordinates
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
            geo_resp = requests.get(geo_url, timeout=10)
            geo_resp.raise_for_status()
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                await ctx.send(f"⚠️ Couldn't find location data for '{city}'. Please be more specific or check the spelling.")
                return

            loc = geo_data["results"][0]
            lat = loc.get("latitude")
            lon = loc.get("longitude")
            display_name_parts = [loc.get("name", city)]
            if loc.get("admin1"): display_name_parts.append(loc["admin1"])
            if loc.get("country_code"): display_name_parts.append(loc["country_code"])
            display_name = ", ".join(filter(None, display_name_parts))


            # 2. Get weather data using coordinates
            weather_url = (
                f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                f"&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
                f"&temperature_unit=celsius&wind_speed_unit=kmh&precipitation_unit=mm"
                f"&timezone=auto"
            )
            weather_resp = requests.get(weather_url, timeout=10)
            weather_resp.raise_for_status()
            weather_data = weather_resp.json()

            current_hour = datetime.now().hour
            temp = weather_data['hourly']['temperature_2m'][current_hour]
            apparent_temp = weather_data['hourly']['apparent_temperature'][current_hour]
            humidity = weather_data['hourly']['relative_humidity_2m'][current_hour]
            precip = weather_data['hourly']['precipitation'][current_hour]
            wind_speed = weather_data['hourly']['wind_speed_10m'][current_hour]
            wind_dir = weather_data['hourly']['wind_direction_10m'][current_hour]
            wmo_code = weather_data['hourly']['weather_code'][current_hour]
            is_day = weather_data['hourly']['is_day'][current_hour]

            # --- Emojis based on Weather Code ---
            weather_icon = "❓"
            if wmo_code == 0: weather_icon = "☀️" if is_day else "🌙" # Clear sky
            elif wmo_code == 1: weather_icon = "☀️" if is_day else "🌙" # Mainly clear
            elif wmo_code == 2: weather_icon = "⛅" if is_day else "☁️" # Partly cloudy
            elif wmo_code == 3: weather_icon = "☁️" # Overcast
            elif wmo_code in [45, 48]: weather_icon = "🌫️" # Fog
            elif wmo_code in [51, 53, 55, 56, 57]: weather_icon = "🌦️" # Drizzle
            elif wmo_code in [61, 63, 65, 66, 67]: weather_icon = "🌧️" # Rain
            elif wmo_code in [71, 73, 75, 77, 85, 86]: weather_icon = "🌨️" # Snow
            elif wmo_code in [80, 81, 82]: weather_icon = "🌧️" # Rain showers
            elif wmo_code in [95, 96, 99]: weather_icon = "⛈️" # Thunderstorm

            degrees = wind_dir
            if degrees is not None and degrees != 'N/A':
                if 337.5 <= degrees or degrees < 22.5: direction_arrow = "⬆️ N"
                elif 22.5 <= degrees < 67.5: direction_arrow = "↗️ NE"
                elif 67.5 <= degrees < 112.5: direction_arrow = "➡️ E"
                elif 112.5 <= degrees < 157.5: direction_arrow = "↘️ SE"
                elif 157.5 <= degrees < 202.5: direction_arrow = "⬇️ S"
                elif 202.5 <= degrees < 247.5: direction_arrow = "↙️ SW"
                elif 247.5 <= degrees < 292.5: direction_arrow = "⬅️ W"
                elif 292.5 <= degrees < 337.5: direction_arrow = "↖️ NW"
                else: direction_arrow = f"{degrees}°"
            else: direction_arrow = "N/A"
        
            embed = discord.Embed(
                title=f"{weather_icon} Weather in {display_name}",
                color=discord.Color.og_blurple()
            )
            embed.add_field(name="Temperature", value=f"{temp}°C", inline=True)
            embed.add_field(name="Feels Like", value=f"{apparent_temp}°C", inline=True)
            embed.add_field(name="Humidity", value=f"{humidity}%", inline=True)
            embed.add_field(name="Wind", value=f"{wind_speed} km/h ({direction_arrow})", inline=True)
            embed.add_field(name="Precipitation", value=f"{precip} mm", inline=True)
        
            # Add timestamp
            embed.timestamp = datetime.now()
        
            await ctx.send(embed=embed)

        except requests.exceptions.Timeout:
             await ctx.send(f"❌ Request timed out while fetching weather for **{city}**.")
        except requests.exceptions.RequestException as e:
            await ctx.send(f"❌ Network error fetching weather for **{city}**: {e}")
        except Exception as e:
            await ctx.send(f"❌ An unexpected error occurred fetching weather: {e}")
            traceback.print_exc()

    @weather.error
    async def weather_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Weather cooldown! Try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
             await ctx.send("❓ Please specify a city. Usage: `!weather <city>`")
        else:
            await ctx.send(f"⚠️ An error occurred with the weather command: {error}")
            traceback.print_exc()


    @commands.command()
    async def remindme(self, ctx, time_str: str = None, *, reminder: str = None):
        """Sets a reminder. Time format: 1d, 2h, 3m, 4s or combined like 1h30m."""
        if not time_str or not reminder:
            await ctx.send("❓ Incorrect format. Use: `!remindme <time> <message>`\n"
                           "Example: `!remindme 1h30m Check the oven`\n"
                           "Units: `d` (days), `h` (hours), `m` (minutes), `s` (seconds)")
            return

        total_seconds = 0
        pattern = re.compile(r'(\d+)([dhms])')
        matches = pattern.findall(time_str.lower())

        if not matches:
            await ctx.send("❌ Invalid time format. Use numbers followed by d, h, m, or s (e.g., `2h30m`).")
            return

        try:
            for value, unit in matches:
                value = int(value)
                if unit == 'd':
                    total_seconds += value * 86400
                elif unit == 'h':
                    total_seconds += value * 3600
                elif unit == 'm':
                    total_seconds += value * 60
                elif unit == 's':
                    total_seconds += value
        except ValueError:
            await ctx.send("❌ Invalid number in time format.")
            return

        if total_seconds <= 0:
            await ctx.send("❌ Reminder time must be in the future.")
            return
        if total_seconds > 60 * 60 * 24 * 30: # Limit to 30 days
            await ctx.send("❌ Maximum reminder time is 30 days.")
            return

        remind_at = datetime.now() + timedelta(seconds=total_seconds)
        remind_timestamp = discord.utils.format_dt(remind_at, style='F') # Full date and time
        relative_timestamp = discord.utils.format_dt(remind_at, style='R') # Relative time

        await ctx.send(f"{ctx.author.mention} Okay! I will remind you to '{reminder}' on {remind_timestamp} ({relative_timestamp}).")

        # Set the reminder
        await asyncio.sleep(total_seconds)

        # Send the reminder
        try:
            await ctx.send(f"⏰ Hey {ctx.author.mention}! Reminder: **{reminder}**", allowed_mentions=discord.AllowedMentions(users=[ctx.author]))
        except discord.HTTPException as e:
             print(f"Failed to send reminder to {ctx.author} (ID: {ctx.author.id}): {e}")


    @remindme.error
    async def remindme_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Incorrect format. Use: `!remindme <time> <message>`\n"
                           "Example: `!remindme 1h30m Check the oven`")
        else:
            await ctx.send(f"⚠️ An error occurred with the remindme command: {error}")
            traceback.print_exc()

    @commands.command()
    async def poll(self, ctx, *, args: str = None):
        """Creates a poll with multiple options. Format: !poll "Question" "Option 1" "Option 2" ..."""
        if not args:
            await ctx.send('❓ Please provide a question and at least two options in quotes.\n'
                           'Format: `!poll "Question" "Option 1" "Option 2" ...`')
            return

        # Regex to find all quoted strings
        matches = re.findall(r'"(.*?)"', args)

        if len(matches) < 3:
            await ctx.send('❌ You need a question and at least **two** options in quotes.\n'
                           'Format: `!poll "Question" "Option 1" "Option 2" ...`')
            return

        if len(matches) > 26: # Discord select menu limit
             await ctx.send("❌ Maximum number of options is 25.")
             return

        question = matches[0]
        options = matches[1:]

        # Check for duplicate options
        if len(options) != len(set(options)):
             await ctx.send("❌ Poll options must be unique.")
             return

        from cogs.uis import PollView

        embed = discord.Embed(
            title=f"📊 Poll by {ctx.author.display_name}",
            description=f"**{question}**\n\nSelect an option below to cast your vote.",
            color=discord.Color.random()
        )
        embed.set_footer(text="Votes are anonymous until you reveal them.")
        view = PollView(options, question)
        await ctx.send(embed=embed, view=view)

    @poll.error
    async def poll_error(self, ctx, error):
         if isinstance(error, commands.MissingRequiredArgument):
             await ctx.send('❓ Please provide arguments. Format: `!poll "Question" "Option 1" "Option 2"...`')
         else:
             await ctx.send(f"⚠️ An error occurred with the poll command: {error}")
             traceback.print_exc()


async def setup(bot):
    await bot.add_cog(Utility(bot))
