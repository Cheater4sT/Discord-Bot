token = "INSERT TOKEN HERE"

ytdl_format_options = {
    'format': 'bestaudio/best',
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192'
    }],
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'socket_timeout': 5,
    'retries': 1,
    'extract_flat': True, 
    'extractaudio': False,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': False,
    'no_warnings': True,
    'nocache': True,
    'writeinfojson': False,
    'writethumbnail': False,
    'embedthumbnail': False,
    'writeallthumbnails': False,
    'subtitleslangs': [],
    'subtitles': False,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0'
}

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn -bufsize 64k'
}
