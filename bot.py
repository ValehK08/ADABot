import discord
from discord.ext import commands
import os
import asyncio
import config
import traceback

# --- Bot Setup ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.reactions = True

# Bot instance
bot = commands.Bot(command_prefix='!', intents=intents)

# --- Bot Events ---

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!info for commands"))

@bot.event
async def on_command_error(ctx, error):
    """Global error handler as a fallback."""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Command not found. Use `!info` to see available commands.")
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏳ Woah there! This command is on cooldown. Try again in {error.retry_after:.1f} seconds.", delete_after=10)
    elif isinstance(error, commands.UserInputError):
         await ctx.send(f"🤔 Invalid input. Please check the command usage. Use `!info` for help.\nError: {error}")
    else:
        print(f'Ignoring exception in command {ctx.command}:')
        await ctx.send("⚠️ An unexpected error occurred while running that command. The developers have been notified (probably).")


# --- Load Cogs ---
async def load_extensions():
    cogs_to_load = ['cogs.database','cogs.uis','cogs.main_commands', 'cogs.extra_commands','cogs.utility']
    for extension in cogs_to_load:
        try:
            await bot.load_extension(extension)
            print(f'Successfully loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}.')
            traceback.print_exception(type(e), e, e.__traceback__)


# --- Main Execution ---
async def main():
    async with bot:
        await load_extensions()
        await bot.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    # Apply nest_asyncio if running in an environment like Jupyter/Spyder that needs it
    # import nest_asyncio
    # nest_asyncio.apply()
    if not config.DISCORD_TOKEN or config.DISCORD_TOKEN == "YOUR_DISCORD_TOKEN":
        print("ERROR: Discord token is missing or placeholder in config.py / .env")
    else:
        try:
            asyncio.run(main())
        except Exception as e:
             print(f"An error occurred during bot startup or runtime: {e}")
             traceback.print_exc()
