from typing import List
import os

import click
from tqdm import tqdm

from .renderer import Renderer, load_font, OPEN_SANS, clip2frames
from .verse import verse_info_by_key, extract_clips
from .verse.types import VerseKey
from .utilities import merge_audio_and_video


class VideoResolution:
    def __init__(self, width: int, height: int):
        self.height = height
        self.width = width

    def __str__(self) -> str:
        return f"{self.width}x{self.height}"


class SizeParam(click.ParamType):
    name = "Size"

    def convert(self, value: str, _a, _b):
        if isinstance(value, tuple) or isinstance(value, VideoResolution):
            return value

        width, height = 0, 0
        try:
            width, height = map(int, value.split("x"))
        except ValueError:
            raise click.BadParameter(
                "Size must be specified in the format 'WidthxHeight'."
            )

        if width <= 0 or height <= 0:
            raise click.BadArgumentUsage("Width and height must be positive integers.")
        return VideoResolution(width=width, height=height)


class VerseKeyParam(click.ParamType):
    name = "VerseKey"

    def convert(self, value: str, _a, _b):
        if (
            isinstance(value, tuple)
            or isinstance(value, VerseKey)
            or isinstance(value, list)
        ):
            return value

        results = []

        try:
            for part in value.split(","):
                chapter_id, verse_id = map(int, part.split(":"))
                if chapter_id <= 0 or verse_id <= 0:
                    raise click.BadArgumentUsage(
                        "chapter_id and verse_id must be positive integers."
                    )

                results.append((VerseKey(chapter_id=chapter_id, verse_id=verse_id)))
        except ValueError:
            raise click.BadParameter(
                "verse key must be specified in the format 'chapter_id:verse_id'."
            )

        if not results:
            raise click.BadArgumentUsage("no verse keys found")

        return results


def verbose_echo(print: bool, msg):
    if print:
        click.echo(f"[VERBOSE] {msg}")


@click.command()
@click.pass_context
@click.option(
    "--verse_key",
    default="1:1",
    help="which verse to render",
    prompt="Enter the verse key",
    type=VerseKeyParam(),
)
@click.option(
    "--dist",
    default="dist",
    help="where to store the videos",
    prompt="Enter the output directory",
    type=click.Path(exists=True),
)
@click.option(
    "--fps",
    default=30,
    help="Frames per second of a video.",
    prompt="Enter the frames per second",
    type=int,
)
@click.option(
    "--resolution",
    default="540x1080",
    help="video resolution",
    prompt="Enter the video resolution",
    type=SizeParam(),
)
@click.option(
    "-v/-q",
    "--verbose/--quiet",
    default=True,
    is_flag=True,
    help="verbose output",
)
def App(
    ctx: click.Context,
    verse_key: List[VerseKey],
    dist: str,
    fps: int,
    resolution: VideoResolution,
    verbose: bool,
):
    """generate clips by verse"""
    line_text = "-" * 10

    click.echo("")
    click.echo(f"{line_text}Summary{line_text}")
    click.echo(f"key: {'|'.join([str(v) for v in verse_key])}\tdist: {dist}")
    click.echo(f"resolution: {resolution}\tfps: {fps}")
    click.echo("")

    if not click.confirm("Do you want to proceed?", default=True):
        return

    click.echo("Generating...")
    renderer = Renderer(
        height=resolution.height,
        width=resolution.width,
        translation_font=load_font(OPEN_SANS, size=20),
        fps=fps,
    )

    TEMP_FILENAME = f"{dist}/TEMP-DO-NOT-TOUCH"
    videos: List[str] = []

    for key in verse_key:
        filename = f"{dist}/{key.chapter_id}-{key.verse_id}.mp4"

        verbose_echo(verbose, f"loading verse[{key}] information...")
        verse_info = verse_info_by_key(key=key)
        verbose_echo(verbose, "extracting clips...")
        clips, audio = extract_clips(verse_info)

        if not clips:
            raise ValueError(f"no clips found for verse {key}")

        out = renderer.video_writer(f"{TEMP_FILENAME}.mp4")

        for clip in tqdm(clips, "rendering"):
            for frame in clip2frames(renderer, clip):
                out.write(frame)

        verbose_echo(verbose, "saving...")
        audio.export(f"{TEMP_FILENAME}.mp3")
        out.release()

        merge_audio_and_video(filename, f"{TEMP_FILENAME}.mp3", f"{TEMP_FILENAME}.mp4")
        videos.append(filename)

        click.echo("\n")

    output_filename = click.prompt(
        "Enter output video path",
        default="release.mp4",
        type=click.Path(exists=False),
    )

    fname = "temp-vagerwdlt.txt"
    with open(fname, "w") as f:
        f.writelines([f"file '{f}'\n" for f in videos])
    os.system(f"ffmpeg -f concat -i {fname} -c copy -loglevel error {output_filename}")
    os.remove(fname)


if __name__ == "__main__":
    App()
