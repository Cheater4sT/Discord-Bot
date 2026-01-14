import discord
from discord.ext import commands
from discord import app_commands
import yt_dlp as youtube_dl
import asyncio
import random
import logging
from config.config import *
from music.utils.audio_utils import *
from music.utils.ytdl import YTDLSource

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')

class MusicInfo:
    def __init__(self):
        self.queue = []
        self.loop = False
        self.repeat = False
        self.current_track = None
        self.last_message = None
        self.last_ctx = None
        self.last_interaction = None

guild_music_info = {}
ALLOWED_USER_IDS = {431806348359893003, 356834587801944067, 837037134564687942, 431805993974759434, 436553224862826506}

class TextCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_music_info = guild_music_info

    @staticmethod
    def has_role_or_is_owner():
        async def predicate(ctx):
            if await ctx.bot.is_owner(ctx.author):
                return True
            role = discord.utils.get(ctx.author.roles, name="DJ")
            if role is not None:
                return True
            if ctx.author.id in ALLOWED_USER_IDS:
                return True
            return False
        return commands.check(predicate)

    def get_music_info(self, guild_id):
        if guild_id not in self.guild_music_info:
            self.guild_music_info[guild_id] = MusicInfo()
        return self.guild_music_info[guild_id]

    async def play_next(self, ctx):
        guild_id = ctx.guild.id
        await play_next(self.bot, ctx, music_info=self.guild_music_info[guild_id], ytdl=ytdl, ffmpeg_options=ffmpeg_options)

    async def download_audio(self, url, requester):
        return await download_audio(url, requester, ytdl, ffmpeg_options)

    @commands.command(name="play", aliases=["p", "з", "здай", 'Z', 'z', 'P', 'З', 'П', 'п'], help='> Использовать для добавления трека в очередь и запуска треков', description='* !play `название трека/url`')
    @has_role_or_is_owner()
    async def play_command(self, ctx, *, query):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        music_info.last_ctx = ctx
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            embed = discord.Embed(colour=discord.Colour.dark_red(), description="Вы не находитесь в голосовом канале!")
            await ctx.send(embed=embed)
            return
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        music_info.queue = await YTDLSource.from_url(query, music_info.queue, music_info.last_ctx, ytdl, loop=self.bot.loop, requester=[ctx.author.display_name, ctx.author.name], add_to_front=False)
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command(name='playnext', aliases=['здфнтуче', 'туче'], help='> Использовать для добавления трека в НАЧАЛО очереди', description='* !playnext `название трека/url`')
    @has_role_or_is_owner()
    async def play_next_command(self, ctx, *, query):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        music_info.last_ctx = ctx
        if ctx.author.voice is None or ctx.author.voice.channel is None:
            embed = discord.Embed(colour=discord.Colour.dark_red(), description="Вы не находитесь в голосовом канале!")
            await ctx.send(embed=embed)
            return
        voice_channel = ctx.author.voice.channel
        voice_client = ctx.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        music_info.queue = await YTDLSource.from_url(query, music_info.queue, music_info.last_ctx, ytdl, loop=self.bot.loop, requester=[ctx.author.display_name, ctx.author.name], add_to_front=True)
        if not ctx.voice_client.is_playing():
            await self.play_next(ctx)

    @commands.command(name='choose', aliases=['срщщыу', 'срщщіу'], help='> Выбор трека из очереди для того чтобы он играл следующим (после этого трека)', description='* !choose `index(номер) трека в очереди`')
    @has_role_or_is_owner()
    async def choose(self, ctx, index):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        if not music_info.queue:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Очередь пуста"))
            return
        try:
            index = int(index)
        except ValueError:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Введите число!"))
            return
        if index < 1 or index > len(music_info.queue):
            await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Число трека неверно, есть числа только от 1 до " + str(len(music_info.queue))))
            return
        track = music_info.queue.pop(index - 1)
        music_info.queue.insert(0, track)
        await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_teal(), description=f"{track['title']} перемещен в начало очереди"))

    @commands.command(name='skip', aliases=['s', 'ы', 'ылшз', 'і', 'ілшз'], help='> Пропустить текущий трек', description='* !skip')
    @has_role_or_is_owner()
    async def skip(self, ctx):
        if ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    @commands.command(name='queue', aliases=['q','й','йгугу'], help='Показывает очередь', description='* !queue')
    @has_role_or_is_owner()
    async def show_queue(self, ctx):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        view = QueueView(music_info.queue, author_id=ctx.author.id)
        embed = view.get_queue_embed()
        await ctx.send(embed=embed, view=view)

    @commands.command(name='leave', aliases=['l', 'д', 'дефму'], help='Отключается из голосового канала', description='* !leave')
    @has_role_or_is_owner()
    async def leave(self, ctx):
        guild_id = ctx.guild.id
        if ctx.voice_client:
            if guild_id in self.guild_music_info:
                del self.guild_music_info[guild_id]
            await ctx.voice_client.disconnect()

    @commands.command(name='current', aliases=['c', 'с', 'сгккуте'], help='Показывает трек, который играет в данный момент', description='* !current')
    @has_role_or_is_owner()
    async def current(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            track = ctx.voice_client.source
            embed = discord.Embed(
                colour=discord.Colour.dark_teal(),
                title="ИГРАЕТ",
                description=f"[{track.title}]({track.webpage_url})\n"
                            f"ДОБАВИЛ: {track.requester[0]} ({track.requester[1]})\n"
                            f"ДЛИТЕЛЬНОСТЬ: {track.duration}"
            )
        else:
            embed = discord.Embed(
                colour=discord.Colour.dark_red(),
                description="В данный момент ничего не играет!"
            )
        await ctx.send(embed=embed)

    @commands.command(name='clear', aliases=['сдуфк'], help='Очищает очередь', description='* !clear')
    @has_role_or_is_owner()
    async def clear_queue(self, ctx):
        guild_id = ctx.guild.id
        self.guild_music_info[guild_id].queue.clear()
        embed = discord.Embed(colour=discord.Colour.green(), description="Очищено.")
        await ctx.send(embed=embed)

    @commands.command(name='shuffle', aliases=['ыргааду', 'іргааду'], help='Перемешивает очередь', description='* !shuffle')
    @has_role_or_is_owner()
    async def shuffle_queue(self, ctx):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.queue:
            random.shuffle(music_info.queue)
            embed = discord.Embed(colour=discord.Colour.teal(), description='Очередь перемешана.')
        else:
            embed = discord.Embed(colour=discord.Colour.dark_red(), description='Очередь пуста.')
        await ctx.send(embed=embed)

    @commands.command(name="loop", aliases=['дщщз'], help='Зацикливает текущий трек', description='* !loop')
    @has_role_or_is_owner()
    async def loop_command(self, ctx):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.current_track is not None:
            music_info.loop = not music_info.loop
            if music_info.repeat:
                music_info.repeat = False
            if music_info.loop:
                await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_green(), description="Трек теперь играет постоянно."))
            else:
                await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_grey(), description="Трек более не зациклен."))
        else:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Ничего не играет"))

    @commands.command(name="repeat", aliases=['кузуфе'], help='Зацикливает очередь', description='* !repeat')
    @has_role_or_is_owner()
    async def repeat_command(self, ctx):
        guild_id = ctx.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.queue:
            music_info.repeat = not music_info.repeat
            if music_info.loop:
                music_info.loop = False
            if music_info.repeat:
                await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_green(), description="Очередь повторяется."))
            else:
                await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_grey(), description="Очередь более не повторяется"))
        else:
            await ctx.send(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Очередь пуста."))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
        guild_id = member.guild.id
        music_info = self.get_music_info(guild_id)
        if voice_client and member == self.bot.user:
            await asyncio.sleep(60)
            voice_client = discord.utils.get(self.bot.voice_clients, guild=member.guild)
            if voice_client is None:
                music_info.queue.clear()
                music_info.repeat = False
                music_info.loop = False
        if voice_client and voice_client.channel:
            if member == voice_client.guild.me:
                return
            if len(voice_client.channel.members) == 1:
                await asyncio.sleep(120)
                if len(voice_client.channel.members) == 1:
                    await voice_client.disconnect()
                    if guild_id in self.guild_music_info and self.guild_music_info[guild_id].last_ctx:
                        embed = discord.Embed(colour=discord.Colour.dark_red(), description="Меня оставили одного.")
                        await self.guild_music_info[guild_id].last_ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.errors.CommandNotFound):
            await ctx.send("Неизвестная команда.")
        elif isinstance(error, commands.errors.CheckFailure):
            await ctx.send(f"{ctx.author.mention}, Вам запрещено пользоваться командами.")
        else:
            logger.error(f"Произошла ошибка: {str(error)}")

class SlashCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.guild_music_info = guild_music_info

    @staticmethod
    def has_role_or_is_owner():
        async def predicate(interaction: discord.Interaction):
            if await interaction.client.is_owner(interaction.user):
                return True
            role = discord.utils.get(interaction.user.roles, name="DJ")
            if role is not None:
                return True
            if interaction.user.id in ALLOWED_USER_IDS:
                return True
            return False
        return app_commands.check(predicate)

    def get_music_info(self, guild_id):
        if guild_id not in self.guild_music_info:
            self.guild_music_info[guild_id] = MusicInfo()
        return self.guild_music_info[guild_id]

    async def play_next(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        await play_next(self.bot, interaction, music_info=self.guild_music_info[guild_id], ytdl=ytdl, ffmpeg_options=ffmpeg_options)

    @app_commands.command(name="play", description='Запускает треки, добавляет в очередь, раунд')
    @has_role_or_is_owner()
    async def slash_play_command(self, interaction: discord.Interaction, query: str):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        music_info.last_interaction = interaction
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(description="Вы не находитесь в голосовом канале!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        music_info.queue = await YTDLSource.from_url(query, music_info.queue, music_info.last_interaction, ytdl, loop=self.bot.loop, requester=[interaction.user.display_name, interaction.user.name], add_to_front=False)
        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    @app_commands.command(name='playnext', description='Добавляет трек в начало очереди')
    @has_role_or_is_owner()
    async def slash_play_next_command(self, interaction: discord.Interaction, query: str):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        music_info.last_interaction = interaction
        if not interaction.user.voice or not interaction.user.voice.channel:
            embed = discord.Embed(description="Вы не находитесь в голосовом канале!")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        voice_channel = interaction.user.voice.channel
        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        music_info.queue = await YTDLSource.from_url(query, music_info.queue, music_info.last_interaction, ytdl, loop=self.bot.loop, requester=[interaction.user.display_name, interaction.user.name], add_to_front=True)
        if not interaction.guild.voice_client.is_playing():
            await self.play_next(interaction)

    @app_commands.command(name='choose', description='Выбрать трек из очереди следующим')
    @has_role_or_is_owner()
    async def slash_choose(self, interaction: discord.Interaction, index: int):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        if not music_info.queue:
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Очередь пуста."), ephemeral=True)
            return
        if index < 1 or index > len(music_info.queue):
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Число трека неверно, есть числа только от 1 до " + str(len(music_info.queue))), ephemeral=True)
            return
        track = music_info.queue.pop(index - 1)
        music_info.queue.insert(0, track)
        await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_teal(), description=f"{track['title']} перемещен в начало очереди"))

    @app_commands.command(name='skip', description='Скипает трек')
    @has_role_or_is_owner()
    async def slash_skip(self, interaction: discord.Interaction):
        if interaction.guild.voice_client and interaction.guild.voice_client.is_playing():
            interaction.guild.voice_client.stop()
            await interaction.response.send_message("Трек пропущен.", ephemeral=True)
        else:
            await interaction.response.send_message("В данный момент ничего не играет.", ephemeral=True)

    @app_commands.command(name='queue', description='Показывает очередь')
    @has_role_or_is_owner()
    async def slash_show_queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        view = QueueView(music_info.queue, author_id=interaction.user.id)
        embed = view.get_queue_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name='leave', description='Выходит из голосового канала')
    @has_role_or_is_owner()
    async def slash_leave(self, interaction: discord.Interaction):
        if interaction.guild.voice_client:
            guild_id = interaction.guild.id
            if guild_id in self.guild_music_info:
                del self.guild_music_info[guild_id]
            await interaction.guild.voice_client.disconnect()
            await interaction.response.send_message("Канал покинут", ephemeral=True)

    @app_commands.command(name='current', description='Показывает текущий трек')
    @has_role_or_is_owner()
    async def slash_current(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_playing():
            track = voice_client.source
            embed = discord.Embed(
                colour=discord.Colour.dark_teal(),
                title="ИГРАЕТ",
                description=f"[{track.title}]({track.webpage_url})\n"
                            f"ДОБАВИЛ: {track.requester[0]} ({track.requester[1]})\n"
                            f"ДЛИТЕЛЬНОСТЬ: {track.duration}"
            )
        else:
            embed = discord.Embed(
                colour=discord.Colour.dark_red(),
                description="В данный момент ничего не играет."
            )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name='clear', description='Очищает очередь')
    @has_role_or_is_owner()
    async def slash_clear_queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        music_info.queue.clear()
        await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.green(), description="Очередь очищена."))

    @app_commands.command(name='shuffle', description='Перемешивает очередь')
    @has_role_or_is_owner()
    async def slash_shuffle_queue(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.queue:
            random.shuffle(music_info.queue)
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.teal(), description='Очередь перемешана.'))
        else:
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_red(), description='Очередь пуста!'), ephemeral=True)

    @app_commands.command(name="loop", description='Зацикливает текущий трек')
    @has_role_or_is_owner()
    async def slash_loop_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.current_track is not None:
            music_info.loop = not music_info.loop
            if music_info.repeat:
                music_info.repeat = False
            status = "Трек повторяется" if music_info.loop else "Трек перестал повторяться"
            colour = discord.Colour.dark_green() if music_info.loop else discord.Colour.dark_grey()
            await interaction.response.send_message(embed=discord.Embed(colour=colour, description=status))
        else:
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_red(), description="В данный момент ничего не играет."), ephemeral=True)

    @app_commands.command(name="repeat", description='Зацикливает очередь')
    @has_role_or_is_owner()
    async def slash_repeat_command(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        music_info = self.get_music_info(guild_id)
        if music_info.queue:
            music_info.repeat = not music_info.repeat
            if music_info.loop:
                music_info.loop = False
            status = "Очередь повторяется." if music_info.repeat else "Очередь перестала повторяться."
            colour = discord.Colour.dark_green() if music_info.repeat else discord.Colour.dark_grey()
            await interaction.response.send_message(embed=discord.Embed(colour=colour, description=status))
        else:
            await interaction.response.send_message(embed=discord.Embed(colour=discord.Colour.dark_red(), description="Очередь пуста!"), ephemeral=True)

class QueueView(discord.ui.View):
    tracks_per_page = 10

    def __init__(self, queue, author_id, page=0):
        super().__init__(timeout=300)
        self.queue = queue
        self.page = page
        self.author_id = author_id
        self.update_buttons()

    def get_queue_embed(self):
        start_index = self.page * self.tracks_per_page
        end_index = start_index + self.tracks_per_page
        tracks = self.queue[start_index:end_index]
        if not tracks:
            description = 'Треков нет'
        else:
            description = ""
            for i, track in enumerate(tracks, start=start_index + 1):
                if isinstance(track, dict):
                    title = track['title']
                    duration = track.get('duration', 'Неизвестно')
                    webpage_url = track.get('webpage_url') or track.get('url', '')
                    requester = track['requester']
                else:  # YTDLSource instance
                    title = track.title
                    duration = track.duration
                    webpage_url = track.webpage_url
                    requester = track.requester
                description += f"{i}. [{title}]({webpage_url})\n" \
                               f"Длительность: {duration}\n" \
                               f"Добавил: {requester[0]} ({requester[1]})\n\n"
        embed = discord.Embed(
            title=f"Очередь (страница {self.page + 1})",
            colour=discord.Colour.dark_magenta(),
            description=description or "Очередь пуста"
        )
        embed.set_footer(text=f"Всего треков: {len(self.queue)}")
        return embed

    def update_buttons(self):
        self.previous.disabled = self.page == 0
        max_page = (len(self.queue) - 1) // self.tracks_per_page
        self.next.disabled = self.page >= max_page
        self.refresh.disabled = False

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.primary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Не вы вызывали команду", ephemeral=True)
            return
        if self.page > 0:
            self.page -= 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_queue_embed(), view=self)
        else:
            await interaction.response.send_message("Дальше страниц нет.", ephemeral=True)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.primary)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Не вы вызывали команду.", ephemeral=True)
            return
        max_page = (len(self.queue) - 1) // self.tracks_per_page
        if self.page < max_page:
            self.page += 1
            self.update_buttons()
            await interaction.response.edit_message(embed=self.get_queue_embed(), view=self)
        else:
            await interaction.response.send_message("Дальше страниц нет", ephemeral=True)

    @discord.ui.button(label="🔃", style=discord.ButtonStyle.green)
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("Не вы вызывали команду", ephemeral=True)
            return
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_queue_embed(), view=self)

async def setup(bot):
    await bot.add_cog(TextCommands(bot))
    await bot.add_cog(SlashCommands(bot))