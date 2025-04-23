import discord
from discord.ui import View, Select
from discord import ButtonStyle
import requests
from bs4 import BeautifulSoup
from io import BytesIO
import asyncio
from datetime import datetime
from google import genai
from google.genai import types
import config
from discord.ext import commands

class ToneSelectView(discord.ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=60)  # 60 second timeout
        self.author_id = author_id
        self.value = None

        # Tone Keys
        tones = [
            ("User‑Friendly 😊", "user_friendly", ButtonStyle.primary),
            ("Sarcastic 😏", "sarcastic", ButtonStyle.secondary),
            ("Depressed 😞", "depressed", ButtonStyle.secondary),
            ("Kid 🧒", "kid", ButtonStyle.success),
            ("Tutor 📚", "tutor", ButtonStyle.success),
            ("BrainRot 💀", "brainrot", ButtonStyle.danger)
        ]

        # Creating button for each tone in loop
        for label, val, style in tones:
            btn = discord.ui.Button(label=label, style=style, custom_id=val)
            btn.callback = self._make_callback(label, val)
            self.add_item(btn)

    # Callback Function for tones
    def _make_callback(self, label, val):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.author_id:
                await interaction.response.send_message("This tone selection is not for you!", ephemeral=True)
                return
                
            self.value = val
            await interaction.response.send_message(f"Tone set to {label}", ephemeral=True)
            self.stop()
        return callback

class News_View(discord.ui.View):
    def __init__(self, articles, num, gemini_client):
        super().__init__(timeout=60)  # 60 second timeout
        self.articles = articles
        self.num = min(num, len(articles['articles']))  # For Safety
        self.gemini_client = gemini_client
        self.create_buttons()

    def create_buttons(self):
        # Button Styles
        styles = [
            ButtonStyle.primary,
            ButtonStyle.secondary,
            ButtonStyle.success,
            ButtonStyle.danger,
            ButtonStyle.primary,
        ]
        for i in range(self.num):
            self.add_item(self.ArticleButton(i, self.articles, styles[i], self.gemini_client))

    # Class for Buttons
    class ArticleButton(discord.ui.Button):
        def __init__(self, index, articles, style, gemini_client):
            super().__init__(label=str(index + 1), style=style)  # Label = {1,2,3,4,5}, style= styles[i]
            self.index = index
            self.articles = articles
            self.gemini_client = gemini_client

        async def callback(self, interaction: discord.Interaction):
            await interaction.response.defer()  # Notifying Discord to avoid 3 second interaction timeout

            try:
                article = self.articles['articles'][self.index]
                headline = article.get('title')
                link = article.get('url', '')
                photo = article.get('urlToImage')

                try:
                    page = requests.get(link, timeout=10)
                    soup = BeautifulSoup(page.content, 'html.parser')
                    paragraphs = soup.find_all('p')
                    full_text = ' '.join([p.get_text() for p in paragraphs if p.get_text()])
                    if not full_text:
                        full_text = article.get('description', 'No content available')
                    shorter_text = full_text[:3000]  # Not to exceed context window
                except Exception as e:
                    print(f"Error fetching article: {e}")
                    shorter_text = article.get('description', 'No content available')

                if not shorter_text.strip():
                    await interaction.followup.send("❌ Sorry, couldn't extract meaningful content.", ephemeral=True)
                    self.view.stop()
                    return

                # AI response
                try:
                    summary_response = self.gemini_client.models.generate_content(
                        model="gemma-3-27b-it",
                        contents=[
                            f"Please summarize the following news article in around 3-5 concise sentences while also being informative. Don't add your comment, response or anything. Just summarized news article:\n\n{shorter_text}"
                        ]
                    )
                    summary = summary_response.text.strip()
                except Exception as e:
                    print(f"Error generating summary: {e}")
                    summary = "Unable to generate summary at this time."

                # Using Embeds for better UI
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
    def __init__(self, symbol, name, gemini_client):
        super().__init__(timeout=60)  # 60 second timeout
        self.symbol = symbol
        self.name = name
        self.gemini_client = gemini_client

    # Stock Analysis Button
    @discord.ui.button(label="Stock Analysis", style=ButtonStyle.danger)
    async def report(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True)  # Notifying Discord to avoid 3 second interaction timeout

        try:
            content_prompt = f"Analyze {self.name} ({self.symbol})."
            
            # Google search tool
            google_search_tool = types.Tool(
                google_search=types.GoogleSearch()
            )

            # Gemini 2.0 flash with google search
            result = self.gemini_client.models.generate_content(
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

            # Splitting the Text into Chunks to avoid 2000 character limit of Discord
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
                
        except Exception as e:
            await interaction.followup.send(f"⚠️ Error generating stock analysis: {e}")

class PollView(View):
    def __init__(self, options, question):
        super().__init__(timeout=300)  # Timeout after 5 minutes
        self.add_item(PollDropdown(options, question))

class PollDropdown(Select):
    def __init__(self, options, question):
        self.votes = {}
        self.question = question
        select_options = [discord.SelectOption(label=opt, value=opt) for opt in options]  # DropDown Selection for each option
        super().__init__(placeholder="Choose your vote...", min_values=1, max_values=1, options=select_options)

    async def callback(self, interaction: discord.Interaction):
        try:
            user = interaction.user
            self.votes[user.id] = self.values[0]

            results = {}  # To Store Voters and Votes
            for vote in self.votes.values():
                results[vote] = results.get(vote, 0) + 1

            result_str = "\n".join(f"**{k}**: {v} vote(s)" for k, v in results.items())  # k- voter, v- votes
            await interaction.response.send_message(
                f"🗳️ You voted for **{self.values[0]}**.\n\n**Live Results:**\n{result_str}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error with your vote: {e}", ephemeral=True)

class UIs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"UI components loaded for {self.bot.user.name}")

async def setup(bot):
    await bot.add_cog(UIs(bot))
