import logging
from concurrent.futures import ProcessPoolExecutor

from youtube_dl import YoutubeDL

from .log import applog as log

AUDIO = 'audio'
VIDEO = 'video'


bob = ProcessPoolExecutor(max_workers=1)  # bob who does all the job


ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': './downloads/audio/%(title)s.%(ext)s',
    'noplaylist': True,
    'noprogress': True,
    'ignoreerrors': True,
    'postprocessors': [
        {
            'key': 'MetadataFromTitle',
        },
        {
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }
    ]
}


async def worker(q, loop):
    while True:
        future, (url, work_unit) = await q.get()
        log.info('GOT task %s (%s)', url, work_unit)
        return_code = await loop.run_in_executor(bob, get_audio, url)
        future.set_result(return_code)

    log.info('Worker done')


def _get_audio(url):
    with YoutubeDL(yds_opts) as ydl:
        return ydl.download([url])
