import discord
import asyncio
from music.utils.ytdl import YTDLSource

async def download_audio(url, requester, ytdl, ffmpeg_options):
    loop = asyncio.get_event_loop()
    try:
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        filename = data.get('url')
        if not filename:
            raise Exception("Не удалось получить URL для воспроизведения.")
        return YTDLSource(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data, requester=requester)
    except Exception as e:
        print(f"Ошибка при загрузке трека: {e}")
        return None

async def play_next(bot, ctx_or_interaction, *, music_info, ytdl, ffmpeg_options):
    if isinstance(ctx_or_interaction, discord.Interaction):
        voice_client = discord.utils.get(bot.voice_clients, guild=ctx_or_interaction.guild)
    else:
        voice_client = ctx_or_interaction.voice_client

    if voice_client is not None and voice_client.is_connected():
        if isinstance(ctx_or_interaction, discord.Interaction):
            author = [ctx_or_interaction.user.display_name, ctx_or_interaction.user.name]
        else:
            author = [ctx_or_interaction.author.display_name, ctx_or_interaction.author.name]
        if music_info.loop:
            track = await download_audio(music_info.current_track.webpage_url, requester=author, ytdl=ytdl, ffmpeg_options=ffmpeg_options)
        else:
            queue=music_info.queue
            if queue:
                track = queue.pop(0)
                if not isinstance(track, YTDLSource):
                    if track['not_ffmpeg']:
                        url = track['url']
                        deleted_title = track['title']
                        track = await download_audio(url, requester=author, ytdl=ytdl, ffmpeg_options=ffmpeg_options)
                        if track is not None:
                            deleted_title=None

                if music_info.repeat:
                    if not isinstance(track, YTDLSource):
                        queue.append({'url': music_info.current_track['url'], 'not_ffmpeg': True, 'duration': music_info.current_track['duration'], 'requester': music_info.current_track['requester'], 'title': music_info.current_track['title']})
                    else:
                        queue.append({'url': music_info.current_track.webpage_url, 'not_ffmpeg': True, 'duration': music_info.current_track.duration, 'requester': music_info.current_track.requester, 'title': music_info.current_track.title})

                music_info.current_track = track
            else:
                embed = discord.Embed(colour=discord.Colour.dark_blue(),description="Очереди нет")
                music_info.current_track=None
                if isinstance(ctx_or_interaction, discord.Interaction):
                    await ctx_or_interaction.followup.send(embed=embed)
                else:
                    await ctx_or_interaction.send(embed=embed)
                return

        if track is None:
            embed=discord.Embed(colour=discord.Colour.dark_red(),description=f"{deleted_title} столкнулся с проблемой")
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.followup.send(embed=embed)
            else:
                await ctx_or_interaction.send(embed=embed)
            await play_next(bot, ctx_or_interaction, music_info=music_info, ytdl=ytdl, ffmpeg_options=ffmpeg_options)
            return
        print(len(music_info.queue))
        voice_client.play(track, after=lambda e: asyncio.run_coroutine_threadsafe(play_next(bot, ctx_or_interaction, music_info=music_info, ytdl=ytdl, ffmpeg_options=ffmpeg_options), bot.loop))
        if not music_info.loop:
            embed = discord.Embed(colour=discord.Colour.dark_teal())
            embed.add_field(name="ИГРАЕТ",
                            value=f"[{track.title}]({track.webpage_url if track.webpage_url else track.url})")
            embed.add_field(name="ДЛИТЕЛЬНОСТЬ", value=f"{track.duration}")
            embed.set_footer(text=f'ДОБАВИЛ: {track.requester[0]} ({track.requester[1]})')
            if isinstance(ctx_or_interaction, discord.Interaction):
                await ctx_or_interaction.followup.send(embed=embed)
            else:
                await ctx_or_interaction.send(embed=embed)
