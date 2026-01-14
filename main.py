import discord
from discord.ext import commands
from config.config import *

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


async def load_extensions():
    extensions=['music.commands.commands', 'music.commands.another_commands']
    for extension in extensions:
        await bot.load_extension(extension)


@bot.event
async def on_ready():
    await load_extensions()
    try:
        synced = await bot.tree.sync()
        print(f"Синхронизированные команды: {synced}")
    except Exception as e:
        print(f"Ошибка синхронизации: {e}")


bot.run(token)
