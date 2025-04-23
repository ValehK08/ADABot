import discord
from discord.ext import commands
import requests
import json
import random
import PyPDF2
import docx
from io import BytesIO
from PIL import Image
from datetime import datetime, timedelta
import yfinance as yf
from bs4 import BeautifulSoup
import config
import traceback
from google import genai
from google.genai import types

class ExtraCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_client = None
        self.translation_active = False
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

    # Get gemini client
    async def _ensure_client(self):
        if not self.gemini_client:
            main_cog = self.bot.get_cog('MainCommands')
            if main_cog and main_cog.gemini_client:
                self.gemini_client = main_cog.gemini_client
            else:
                try:
                    self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
                except Exception as e:
                    print(f"Failed to initialize Gemini client in ExtraCommands: {e}")
                    return False
        return bool(self.gemini_client)

    @commands.Cog.listener()
    async def on_ready(self):
        """Ensure Gemini client is available after bot is ready."""
        await self._ensure_client()
        print(f"ExtraCommands Cog loaded. Gemini Client {'Available' if self.gemini_client else 'Not Available'}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Translate non-English messages if translation mode is active."""
        if message.author.bot or message.content.startswith('!'):
            return

        if self.translation_active:
            if not await self._ensure_client():
                print("Translation skipped: AI client not available.")
                return

            try:
                translate_prompt = f"Translate the following text to English if it is not in english. If it is not in english, Your reponse must only consist of the translation(no extra comments). If it is in english, Your response must only consist of 'None':\n\n{message.content}"
                translate_resp = self.gemini_client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=translate_prompt
                )
                translated = translate_resp.text.strip()
                if translated.lower() != 'none':
                    await message.reply(f"🔄 {message.author.mention} {translated}", allowed_mentions=discord.AllowedMentions(users=True))
            except genai.types.generation_types.StopCandidateException:
                 await message.reply("⚠️ Translation stopped due to content policy.", allowed_mentions=discord.AllowedMentions.none())
            except Exception as e:
                print(f"Translation error: {e}")

    @commands.command()
    @commands.cooldown(1, 15, commands.BucketType.user) # Cooldown: 1 use per 15 sec
    async def summarize(self, ctx, url: str = None):
        """Summarize text from an attached file or a URL."""
        if not await self._ensure_client():
            await ctx.send("⚠️ AI service is currently unavailable. Please try again later.")
            return

        if not ctx.message.attachments and not url:
            await ctx.send("❗ Please attach a file (.txt, .pdf, .docx, .png, .jpg, .jpeg, .webp) or provide a URL.")
            return

        processing_msg = await ctx.send("⏳ Processing your request...")
        summary = ""
        source_type = ""

        try:
            if ctx.message.attachments:
                attachment = ctx.message.attachments[0]
                filename = attachment.filename.lower()
                source_type = f"file '{attachment.filename}'"

                if not any(filename.endswith(ext) for ext in ['.txt', '.pdf', '.docx', '.png', '.jpg', '.jpeg', '.webp']):
                    await processing_msg.edit(content="Unsupported file type. Please upload .txt, .pdf, .docx or an image.")
                    return

                await processing_msg.edit(content=f"⏳ Reading {source_type}...")
                file_bytes = await attachment.read()
                text = ""

                if filename.endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    await processing_msg.edit(content=f"⏳ Analyzing image {source_type}...")
                    image = Image.open(BytesIO(file_bytes))
                    response = self.gemini_client.models.generate_content(
                        model="gemini-2.0-flash",
                        contents=[image, "Summarize the text shown in the image concisely. If no text, describe the image briefly. Focus on key information."]
                    )
                    summary = response.text
                else:
                    if filename.endswith('.txt'):
                        text = file_bytes.decode('utf-8')
                    elif filename.endswith('.pdf'):
                        try:
                            reader = PyPDF2.PdfReader(BytesIO(file_bytes))
                            for page in reader.pages:
                                text += (page.extract_text() or "") + "\n"
                        except PyPDF2.errors.PdfReadError:
                            await processing_msg.edit(content="❌ Error reading PDF. It might be encrypted or corrupted.")
                            return
                    elif filename.endswith('.docx'):
                        doc = docx.Document(BytesIO(file_bytes))
                        for para in doc.paragraphs:
                            text += para.text + "\n"

                    if not text.strip():
                        await processing_msg.edit(content=f"Could not extract any readable text from {source_type} 😕")
                        return

                    await processing_msg.edit(content=f"⏳ Summarizing text from {source_type}...")
                    response = self.gemini_client.models.generate_content(
                        model="gemini-2.0-flash-lite",
                        contents=[f"Summarize the following text concisely, using bullet points if helpful:\n\n{text[:15000]}"] # Limit input size
                    )
                    summary = response.text

            elif url:
                source_type = f"URL '{url}'"
                await processing_msg.edit(content=f"⏳ Fetching content from {source_type}...")
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    res = requests.get(url, timeout=15, headers=headers)
                    res.raise_for_status() # Raise HTTPError for bad responses

                    soup = BeautifulSoup(res.content, 'html.parser')
                    for script in soup(["script", "style", "nav", "footer", "aside"]):
                        script.decompose()
                    page_text = ' '.join(soup.stripped_strings)

                    if not page_text.strip():
                        await processing_msg.edit(content=f"Couldn't extract useful text from {source_type}. The page might be dynamic or heavily scripted. 😐")
                        return

                    await processing_msg.edit(content=f"⏳ Summarizing content from {source_type}...")
                    summary = self.gemini_client.models.generate_content(
                        model="gemini-2.0-flash-lite",
                        contents=[f"Summarize the following webpage content concisely, using bullet points if appropriate:\n\n{page_text[:15000]}"] # Limit input size
                    ).text

                except requests.exceptions.RequestException as e:
                    await processing_msg.edit(content=f"⚠️ Failed to fetch URL: {e}")
                    return
                except Exception as e:
                    await processing_msg.edit(content=f"⚠️ Error processing URL content: {e}")
                    return

            # Final Output
            if summary:
                await processing_msg.delete() # Remove processing message
                # Send summary in chunks
                chunks = [summary[i:i+1950] for i in range(0, len(summary), 1950)]
                first_chunk = f"📄 **Summary for {source_type}:**\n{chunks[0]}"
                await ctx.send(first_chunk)
                for chunk in chunks[1:]:
                    await ctx.send(chunk)

        except Exception as e:
            await processing_msg.edit(content=f"⚠️ An unexpected error occurred during summarization: {str(e)[:150]}")
            traceback.print_exc()

    @summarize.error
    async def summarize_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
             await ctx.send("❗ Please attach a file or provide a URL. Usage: `!summarize [url]` or attach a file.")
        else:
            await ctx.send(f"⚠️ An error occurred: {error}")
            traceback.print_exc()


    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user) # Cooldown: 1 use per 5 sec
    async def stock(self, ctx, symbol: str = None):
        """Get stock information and an optional AI analysis."""
        if not symbol:
            await ctx.send("❓ Please provide a stock symbol. Example: `!stock AAPL`")
            return

        if not await self._ensure_client():
            await ctx.send("⚠️ AI service for analysis is currently unavailable, but basic data will be shown.")

        processing_msg = await ctx.send(f"⏳ Fetching data for **{symbol.upper()}**...")

        try:
            from cogs.uis import Stock_View

            ticker = yf.Ticker(symbol)
            info = ticker.info
            name = info.get("longName", symbol.upper())
            currency = info.get("currency", "$") # Get currency symbol

            # Now get history
            hist = ticker.history(period="5d") # Fetch 5 days to ensure we get previous close

            if hist.empty:
                await processing_msg.edit(content=f"⚠️ No historical data found for symbol: **{symbol.upper()}**. Is the symbol correct?")
                return

            # Get the most recent closing price
            current_price = hist['Close'].iloc[-1]

            # Try to get the previous day's data
            if len(hist) >= 2:
                prev_day_data = hist.iloc[-2]
                prev_open = prev_day_data['Open']
                prev_close = prev_day_data['Close']
                prev_high = prev_day_data['High']
                prev_low = prev_day_data['Low']
                change = current_price - prev_close
                change_percent = (change / prev_close) * 100 if prev_close else 0
                change_sign = "📈" if change >= 0 else "📉"
                response = (
                    f"**{name} ({symbol.upper()}) Stock Info**\n"
                    f"{change_sign} Current Price: **{currency}{current_price:.2f}** ({change:+.2f} / {change_percent:+.2f}%)\n\n"
                    f"📊 Previous Close: {currency}{prev_close:.2f}\n"
                    f"📊 Previous Open: {currency}{prev_open:.2f}\n"
                    f"⬆️ Previous High: {currency}{prev_high:.2f}\n"
                    f"⬇️ Previous Low: {currency}{prev_low:.2f}"
                )
            else:
                # Fallback if only one day of data is available
                response = (
                    f"**{name} ({symbol.upper()}) Stock Info**\n"
                    f"📈 Current Price: **{currency}{current_price:.2f}**\n\n"
                    f"_(Insufficient data for previous day comparison)_"
                )

            await processing_msg.delete()
            stock_view = Stock_View(symbol.upper(), name, self.gemini_client) # Pass client
            await ctx.send(response, view=stock_view)

        except requests.exceptions.HTTPError as http_err:
             await processing_msg.edit(content=f"⚠️ HTTP Error fetching data for **{symbol.upper()}**: {http_err}. Check the symbol or try again later.")
        except Exception as e:
            await processing_msg.edit(content=f"⚠️ Error retrieving stock data for **{symbol.upper()}**: {str(e)[:150]}")
            traceback.print_exc()

    @stock.error
    async def stock_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
             await ctx.send("❓ Please provide a stock symbol. Example: `!stock AAPL`")
        else:
            await ctx.send(f"⚠️ An error occurred with the stock command: {error}")
            traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def thisday(self, ctx):
        """Get an interesting historical fact about today."""
        if not await self._ensure_client():
            await ctx.send("⚠️ AI service is currently unavailable. Please try again later.")
            return

        await ctx.typing()
        try:
            google_search_tool = Tool(google_search=GoogleSearch())

            fact = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                contents="Give me one interesting historical fact about today's date (no year needed unless crucial). Start the response *directly* with 'On this day in history...' and keep it concise (1-2 sentences).",
                config=types.GenerateContentConfig(
                    tools=[google_search_tool],
                    response_modalities=["TEXT"]
                )
            )
            await ctx.send(fact.text)
        except genai.types.generation_types.StopCandidateException:
             await ctx.send("⚠️ Fact generation stopped due to content policy.")
        except Exception as e:
            await ctx.send(f"⚠️ Could not fetch historical fact: {str(e)[:150]}")
            traceback.print_exc()

    @thisday.error
    async def thisday_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ This command is on cooldown. Please try again in {error.retry_after:.1f} seconds.")
        else:
            await ctx.send(f"⚠️ An error occurred with the thisday command: {error}")
            traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 20, commands.BucketType.user) # Cooldown: 1 use per 20 sec
    async def meme(self, ctx):
        """Generates a random meme with AI-generated captions."""
        if not config.OPENROUTER_API_KEY or not config.IMGFLIP_USERNAME or not config.IMGFLIP_PASSWORD:
             await ctx.send("⚠️ Meme generation requires OpenRouter and ImgFlip credentials to be configured.")
             return

        processing_msg = await ctx.send("🧠 Thinking of a meme...")
        try:
            # 1. Get meme templates from Imgflip
            await processing_msg.edit(content="🖼️ Fetching meme templates...")
            resp = requests.get("https://api.imgflip.com/get_memes")
            resp.raise_for_status()
            data = resp.json()
            if not data.get("success"):
                await processing_msg.edit(content="❌ Failed to fetch meme list from Imgflip.")
                return

            # 2. Choose for 2-panel memes and take a sample
            memes = [m for m in data["data"]["memes"] if m["box_count"] == 2]
            if not memes:
                 await processing_msg.edit(content="❌ Couldn't find suitable meme templates.")
                 return
            template = random.choice(memes[:100]) # Choose from top 100 popular 2-panel memes

            # 3. Generate captions using OpenRouter
            await processing_msg.edit(content=f"✍️ Generating captions for '{template['name']}'...")
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
                                    "Analyze this meme template. Write two short, funny, and original captions (text for the top/first box, text for the bottom/second box). "
                                    "Make it relevant to internet culture, gaming, or everyday relatable situations. Avoid anything offensive or harmful. "
                                    "Respond *only* in the format: Caption 1 ~ Caption 2"
                                ),
                            },
                        ],
                    }
                ],
            }
            headers = {
                "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            }
            or_resp = requests.post(self.openrouter_url, headers=headers, data=json.dumps(payload), timeout=30) # Increased timeout
            or_resp.raise_for_status()
            or_data = or_resp.json()

            if "choices" not in or_data or not or_data["choices"]:
                 await processing_msg.edit(content="❌ AI caption generation failed (No choices returned).")
                 print(f"OpenRouter Response: {or_data}")
                 return

            content = or_data["choices"][0]["message"]["content"].strip()
            if "~" not in content:
                 await processing_msg.edit(content="❌ AI caption generation failed (Incorrect format). Trying again...")
                 text0, text1 = "Top Text", "Bottom Text"
            else:
                parts = content.split("~", 1)
                text0 = parts[0].strip()
                text1 = parts[1].strip()

            # 4. Generate the meme image via Imgflip
            await processing_msg.edit(content="🎨 Creating the meme image...")
            caption_params = {
                "template_id": template["id"],
                "username": config.IMGFLIP_USERNAME,
                "password": config.IMGFLIP_PASSWORD,
                "text0": text0,
                "text1": text1,
                "font": "impact",
                "max_font_size": "50px"
            }
            gen_resp = requests.post("https://api.imgflip.com/caption_image", data=caption_params, timeout=15)
            gen_resp.raise_for_status()
            gen_data = gen_resp.json()

            if not gen_data.get("success"):
                error_msg = gen_data.get("error_message", "Unknown Imgflip error")
                await processing_msg.edit(content=f"❌ Failed to generate meme on Imgflip: {error_msg}")
                return

            final_url = gen_data["data"]["url"]

            # 4. Send the meme
            await processing_msg.delete()
            await ctx.send(f"😂 Here's your meme (Template: {template['name']}):\n{final_url}")
            
        except requests.exceptions.Timeout:
            await processing_msg.edit(content="❌ Meme generation timed out. One of the APIs might be slow.")
        except requests.exceptions.RequestException as e:
            await processing_msg.edit(content=f"❌ Network error during meme generation: {e}")
        except Exception as e:
            await processing_msg.edit(content=f"❌ An unexpected error occurred: {str(e)[:150]}")
            traceback.print_exc()

    @meme.error
    async def meme_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Easy there, meme lord! Try again in {error.retry_after:.1f} seconds.")
        else:
            await ctx.send(f"⚠️ An error occurred with the meme command: {error}")
            traceback.print_exc()

    # Helper function to get user mentions
    async def _parse_user(self, ctx, user_input):
        member = await commands.MemberConverter().convert(ctx, user_input)
        return member

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user) # Cooldown: 1 use per 10 sec
    async def roast(self, ctx, *, user_mention: str):
        """Roasts a mentioned user based on recent chat history."""
        if not await self._ensure_client():
            await ctx.send("⚠️ AI service is currently unavailable. Can't generate roasts.")
            return

        target_user = await self._parse_user(ctx, user_mention)
        if not target_user:
            await ctx.send(f"❌ Couldn't find user: {user_mention}. Please mention a valid user or provide their ID.")
            return

        if target_user == self.bot.user:
            await ctx.send("😂 Roasting myself? Nice try!")
            return
        if target_user == ctx.author:
             await ctx.send("🤔 Roasting yourself? Okay, if you insist...")

        await ctx.typing()
        try:
            # Get message history from Database cog
            db_cog = self.bot.get_cog('Database')
            if not db_cog:
                await ctx.send("⚠️ Database unavailable, cannot fetch context for roast.")
                return
            history = db_cog.get_all_messages(limit=40)
            context = "\n".join(history)

            roast_text = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    temperature=0.8,
                    system_instruction="You are a witty but harmless roast bot. Generate a short (2-3 sentences), creative, and funny roast based *only* on the provided chat history context or the username. Avoid actual insults, harassment, or sensitive topics. Keep it lighthearted and clever."
                ),
                contents=[f"Roast the user '{target_user.display_name}'. Context:\n{context}"]
            )
            # Send roast for the target user
            await ctx.send(f"{target_user.mention}, {roast_text.text}", allowed_mentions=discord.AllowedMentions(users=True))
        except genai.types.generation_types.StopCandidateException:
             await ctx.send(f"⚠️ Roast generation stopped for {target_user.mention} due to content policy.", allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            await ctx.send(f"⚠️ Error generating roast for {target_user.mention}: {str(e)[:150]}", allowed_mentions=discord.AllowedMentions.none())
            traceback.print_exc()

    @roast.error
    async def roast_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Chill out! Roasting cooldown: {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Who should I roast? Mention a user like `!roast @username` or `!roast UserID`.")
        else:
            await ctx.send(f"⚠️ An error occurred with the roast command: {error}")
            traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user) # Cooldown: 1 use per 10 sec
    async def compliment(self, ctx, *, user_mention: str):
        """Compliments a mentioned user based on recent chat history."""
        if not await self._ensure_client():
            await ctx.send("⚠️ AI service is currently unavailable. Can't generate compliments.")
            return

        target_user = await self._parse_user(ctx, user_mention)
        if not target_user:
            await ctx.send(f"❌ Couldn't find user: {user_mention}. Please mention a valid user or provide their ID.")
            return

        if target_user == self.bot.user:
            await ctx.send("😊 Aw, thanks for thinking of me!")
            return

        await ctx.typing()
        try:
            # Get message history from Database cog
            db_cog = self.bot.get_cog('Database')
            if not db_cog:
                await ctx.send("⚠️ Database unavailable, cannot fetch context for compliment.")
                return
            history = db_cog.get_all_messages(limit=30)
            context = "\n".join(history)

            compliment_text = self.gemini_client.models.generate_content(
                model="gemini-2.0-flash",
                config=types.GenerateContentConfig(
                    temperature=0.6,
                    system_instruction="You are a kind and thoughtful bot. Generate a short (1-2 sentences), genuine, and specific compliment for the user based *only* on the provided chat history context or their username. Focus on positive aspects observed. If no context is useful, provide a general nice compliment."
                ),
                contents=[f"Compliment the user '{target_user.display_name}'. Context:\n{context}"]
            )
            # Send compliment for the target user
            await ctx.send(f"{target_user.mention}, {compliment_text.text}", allowed_mentions=discord.AllowedMentions(users=True))

        except genai.types.generation_types.StopCandidateException:
             await ctx.send(f"⚠️ Compliment generation stopped for {target_user.mention} due to content policy.", allowed_mentions=discord.AllowedMentions.none())
        except Exception as e:
            await ctx.send(f"⚠️ Error generating compliment for {target_user.mention}: {str(e)[:150]}", allowed_mentions=discord.AllowedMentions.none())
            traceback.print_exc()

    @compliment.error
    async def compliment_error(self, ctx, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏳ Spreading the love too fast! Compliment cooldown: {error.retry_after:.1f} seconds.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Who deserves a compliment? Mention a user like `!compliment @username` or `!compliment UserID`.")
        else:
            await ctx.send(f"⚠️ An error occurred with the compliment command: {error}")
            traceback.print_exc()

    @commands.command()
    async def translate(self, ctx, *, mode: str):
        """Turn automatic message translation on or off (start/stop)."""
        mode = mode.lower()
        if mode == "start":
            if not self.translation_active:
                if not await self._ensure_client():
                     await ctx.send("⚠️ AI service is unavailable. Cannot start translation.")
                     return
                self.translation_active = True
                await ctx.send("✅ Automatic translation **enabled**. I will now attempt to translate non-English messages to English.")
            else:
                await ctx.send("ℹ️ Automatic translation is already **enabled**.")
        elif mode == "stop":
            if self.translation_active:
                self.translation_active = False
                await ctx.send("☑️ Automatic translation **disabled**.")
            else:
                await ctx.send("ℹ️ Automatic translation is already **disabled**.")
        else:
            await ctx.send("❓ Invalid mode. Use `!translate start` or `!translate stop`.")

    @translate.error
    async def translate_error(self, ctx, error):
         if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Please specify 'start' or 'stop'. Usage: `!translate start` or `!translate stop`.")
         else:
            await ctx.send(f"⚠️ An error occurred with the translate command: {error}")
            traceback.print_exc()


async def setup(bot):
    await bot.add_cog(ExtraCommands(bot))
