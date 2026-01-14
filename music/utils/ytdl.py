import discord
import asyncio
from config.config import ytdl_format_options, ffmpeg_options
import re
def duration_formatted(duration):
    if duration is None:
        return "Неизвестно"
    hours, remain = divmod(int(duration), 3600)
    minutes, seconds = divmod(remain, 60)
    if hours > 0:
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    else:
        return f"{int(minutes):02}:{int(seconds):02}"

async def add_playlist_to_queue(data, last_ctx_or_interaction, queue, requester, add_to_front):
    playlist_duration = 0
    deleted_tracks=0
    for entry in data['entries']:
        if entry.get('title') is None or entry.get('duration') is None:
            deleted_tracks+=1
            continue

        duration = entry['duration'] if entry['duration'] is not None else 0
        track_info={'url': entry['url'],
                      'not_ffmpeg': True,
                      'duration': duration_formatted(duration),
                      'requester': requester,
                      'title': entry['title']}
        if add_to_front:
            queue.insert(0, track_info)
        else:
            queue.append(track_info)
        playlist_duration += entry['duration']
    embed = discord.Embed(colour=discord.Colour.dark_grey(), title="ДОБАВЛЕН ПЛЕЙЛИСТ",
                          description=f"[{data['title']}]({data['webpage_url']})\n"f"ДЛИТЕЛЬНОСТЬ: {duration_formatted(playlist_duration)}\n")
    embed.set_footer(text=f"ДОБАВИЛ: {requester[0]} ({requester[1]}) КОЛИЧЕСТВО УДАЛЁННЫХ ТРЕКОВ: {deleted_tracks}")
    if isinstance(last_ctx_or_interaction, discord.Interaction):
        await last_ctx_or_interaction.response.send_message(embed=embed)
    else:
        await last_ctx_or_interaction.send(embed=embed)

async def add_song_to_queue(entry, last_ctx_or_interaction, queue, requester, add_to_front):
    if entry.get('title') is None or entry.get('duration') is None:
        return None
    embed = discord.Embed(colour=discord.Colour.dark_grey(), title="ДОБАВЛЕН ТРЕК",
                          description=f"[{entry['title']}]({entry['webpage_url']})\n"f"ДЛИТЕЛЬНОСТЬ: {duration_formatted(entry['duration'])}\n")
    embed.set_footer(text=f"ДОБАВИЛ: {requester[0]} ({requester[1]})")
    if isinstance(last_ctx_or_interaction, discord.Interaction):
        await last_ctx_or_interaction.response.send_message(embed=embed)
    else:
        await last_ctx_or_interaction.send(embed=embed)
    filename = entry['url']
    track_info = YTDLSource(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=entry, requester=requester)
    if add_to_front:
        queue.insert(0, track_info)
    else:
        queue.append(track_info)


async def add_search_to_queue(entries, last_ctx_or_interaction, queue, requester, add_to_front):
    view = TrackSelectionView(entries, requester, last_ctx_or_interaction)
    track = await view.wait_for_selection()
    track_info = {'url': track['url'], 'not_ffmpeg': True, 'duration': duration_formatted(track['duration']),
                  'requester': requester, 'title': track['title']}
    if add_to_front:
        queue.insert(0, track_info)
    else:
        queue.append(track_info)
    embed = discord.Embed(colour=discord.Colour.dark_grey(), title="ДОБАВЛЕН ТРЕК",
                          description=f"[{track['title']}]({track['url']})\n"f"ДЛИТЕЛЬНОСТЬ: {duration_formatted(track['duration'])}\n")
    if isinstance(last_ctx_or_interaction, discord.Interaction):
        await last_ctx_or_interaction.followup.send(embed=embed)
    else:
        await last_ctx_or_interaction.send(embed=embed)


YOUTUBE_URL_PATTERN = re.compile(r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/')
SOUNDCLOUD_URL_PATTERN = re.compile(r'(https?://)?(www\.)?(soundcloud)\.com/')
SPOTIFY_URL_PATTERN = re.compile(r'(https?://)?(www\.)?(open\.)?spotify\.com/')

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.webpage_url=data.get('webpage_url')
        self.durat=data.get('duration')
        self.duration = duration_formatted(self.durat)
        self.requester = requester

    @classmethod
    async def from_url(cls, url, queue, last_ctx_or_interaction, ytdl, *, loop=None, requester=None, add_to_front):
        loop = loop or asyncio.get_event_loop()
        if YOUTUBE_URL_PATTERN.match(url) or SOUNDCLOUD_URL_PATTERN.match(url) or SPOTIFY_URL_PATTERN.match(url):
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            if 'entries' in data:
                await add_playlist_to_queue(data, last_ctx_or_interaction, queue, requester, add_to_front)
            else:
                await add_song_to_queue(data, last_ctx_or_interaction, queue, requester, add_to_front)
            return queue
        else:
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(f"ytsearch5:{url}", download=False))
            entries = data['entries'][:5]
            await add_search_to_queue(entries, last_ctx_or_interaction, queue, requester, add_to_front)
            return queue


class TrackSelectionView(discord.ui.View):
    def __init__(self, entries, requester, ctx):
        super().__init__(timeout=120)
        self.entries = entries
        self.requester = requester
        self.last_ctx_or_interaction = ctx
        self.selected_track = None

        for i in range(5):
            button = discord.ui.Button(label=str(i+1), style=discord.ButtonStyle.primary)
            button.callback = self.create_button_callback(i)
            self.add_item(button)

    def create_button_callback(self, index):
        async def callback(interaction: discord.Interaction):
            self.selected_track = self.entries[index]
            await interaction.response.send_message(f"ТРЕК: {self.entries[index]['title']}", delete_after=120)
            self.stop()  # Закрываем выбор после нажатия
        return callback

    async def wait_for_selection(self):
        embed = discord.Embed(title="ЧТО ВКЛЮЧАТЬ?", description="ВЫБЕРИ ЦИФЕРКУ (1-5):")

        for i, entry in enumerate(self.entries[:5]):
            embed.add_field(name=f"{i+1}. {entry['title']}",
                            value=f"ДЛИТЕЛЬНОСТЬ: {duration_formatted(entry['duration'])}\nАВТОР: [{entry['channel']}]({entry['channel_url']})", inline=False)

        if isinstance(self.last_ctx_or_interaction, discord.Interaction):
            await self.last_ctx_or_interaction.response.send_message(embed=embed, view=self, delete_after=120)
        else:
            await self.last_ctx_or_interaction.send(embed=embed, view=self, delete_after=120)
        await self.wait()

        if self.selected_track:
            return self.selected_track
        else:
            if isinstance(self.last_ctx_or_interaction, discord.Interaction):
                await self.last_ctx_or_interaction.response.send_message(embed=discord.Embed(description="ДОСТУП ЗАПРЕЩЕН"), view=self, delete_after=120)
            else:
                await self.last_ctx_or_interaction.send(embed=discord.Embed(description="ДОСТУП ЗАПРЕЩЕН"), view=self, delete_after=120)
            return
