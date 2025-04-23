import discord
from discord.ext import commands
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import config
import asyncio
import json
import traceback

class MainCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gemini_client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.chat_session = None
        self.current_tone = "user_friendly"
        
    @commands.command()
    async def tone(self, ctx):
        """Choose a tone for ADABot's responses."""
        from cogs.uis import ToneSelectView
        
        try:
            view = ToneSelectView(ctx.author.id)
            await ctx.send("Choose a tone for ADABot:", view=view)
            timeout = await view.wait()
            
            if timeout:
                await ctx.send("Tone selection timed out.", ephemeral=True)
                return
                
            if view.value:
                self.current_tone = view.value
                self.chat_session = None  # Reset chat session when tone changes
                
        except Exception as e:
            await ctx.send(f"Error setting tone: {str(e)[:100]}...")
            traceback.print_exc()
            
    @commands.command()
    async def chat(self, ctx, *, prompt):
        """Chat with ADABot using various tones."""
        try:
            # Get the database cog to access message history
            db_cog = self.bot.get_cog('Database')
            if not db_cog:
                await ctx.send("⚠️ Database not available, chat functionality limited.")
                return
                
            async with ctx.typing():
                if self.chat_session is None:
                    self.chat_session = self.gemini_client.chats.create(model="gemini-2.0-flash-lite")
                    history = db_cog.get_all_messages()
                    context = "\n".join(history)
                    system_prompt = config.TONE_PROMPTS[self.current_tone].format(context=context)
                    self.chat_session.send_message(system_prompt)

                response = self.chat_session.send_message(f"{ctx.author.name}: {prompt}")
                full_text = response.text
                
                # Manage response chunking for large responses
                if len(full_text) > 1900:
                    chunks = [full_text[i:i+1900] for i in range(0, len(full_text), 1900)]
                    for i, chunk in enumerate(chunks):
                        message_to_send = f"{ctx.author.mention} {chunk}" if i == 0 else chunk
                        await ctx.send(message_to_send)
                else:
                    await ctx.send(f"{ctx.author.mention} {full_text}")

        except Exception as e:
            await ctx.send(f"⚠️ Chat error: {str(e)[:100]}...")
            traceback.print_exc()

    @chat.error
    async def chat_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Please provide a message to chat with me. Example: `!chat Hello there!`")
        else:
            await ctx.send(f"⚠️ Error: {str(error)[:100]}...")
            traceback.print_exc()

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)  # Rate limit: 1 use per 10 seconds per user
    async def generate(self, ctx, *, gen_prompt):
        """Generate an AI image based on a prompt."""
        try:
            await ctx.send("🎨 Generating image, please wait...")
            
            response = self.gemini_client.models.generate_content(
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
            
        except Exception as e:
            await ctx.send(f"⚠️ Image generation failed: {str(e)[:100]}...")
            traceback.print_exc()

    @generate.error
    async def generate_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send("❓ Please provide a prompt for image generation. Example: `!generate a serene sunset over mountains`")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏱️ Please wait {error.retry_after:.1f} seconds before generating another image.")
        else:
            await ctx.send(f"⚠️ Error: {str(error)[:100]}...")
            traceback.print_exc()

async def setup(bot):
    await bot.add_cog(MainCommands(bot))
