from io import BytesIO
import os

from requests import get


def GET(url: str, **kwargs):
    response = get(url, **kwargs)
    response.raise_for_status()

    return response


def virtual_io(url: str, **kwargs):
    return BytesIO(GET(url=url, **kwargs).content)


def merge_audio_and_video(out_filename: str, audio_filename: str, video_filename: str):
    os.system(
        "ffmpeg -i %s -i %s -c:v libx264 -c:a aac -y -loglevel quiet %s"
        % (audio_filename, video_filename, out_filename)
    )
