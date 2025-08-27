from typing import List
import os

import click
from tqdm import tqdm

from .renderer import Renderer, load_font, OPEN_SANS, clip2frames
from .verse import verse_info_by_key, extract_clips, get_reciter_config
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


class VerseKeyRange:
    def __init__(self, start: VerseKey, end: VerseKey):
        self.start = start
        self.end = end

    def __str__(self) -> str:
        return f"{self.start}..{self.end}"


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
                ranges = part.split("..")

                out = []
                for part in ranges:
                    chapter_id, verse_id = map(int, part.split(":"))
                    k = VerseKey(chapter_id=chapter_id, verse_id=verse_id)
                    if k.chapter_id <= 0 or k.verse_id <= 0:
                        raise click.BadArgumentUsage(
                            f"chapter_id and verse_id must be positive integers. '{k}'"
                        )
                    out.append(k)

                if len(out) == 1:
                    results.extend(out)
                elif len(out) == 2:
                    r = VerseKeyRange(start=out[0], end=out[1])

                    if r.start.chapter_id != r.end.chapter_id:
                        raise click.BadArgumentUsage(f"chapter_id mismatch '{r}'")
                    if r.start.verse_id >= r.end.verse_id:
                        raise click.BadArgumentUsage(
                            f"range must be in ascending order: '{r}'"
                        )
                    results.append(r)
                else:
                    raise click.BadArgumentUsage(f"Invalid range format. '{part}'")
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
@click.option(
    "-y", "--yes",
    is_flag=True,
    default=False,
    help="Automatically confirm and proceed without prompting."
)
def App(
    ctx: click.Context,
    verse_key: List[VerseKey],
    dist: str,
    fps: int,
    resolution: VideoResolution,
    verbose: bool,
    yes: bool
):
    """generate clips by verse"""
    line_text = "-" * 10

    click.echo("")
    click.echo(f"{line_text}Summary{line_text}")
    click.echo(f"key: {'|'.join([str(v) for v in verse_key])}\tdist: {dist}")
    click.echo(f"resolution: {resolution}\tfps: {fps}")
    click.echo("")

    if not yes and not click.confirm("Do you want to proceed?", default=True):
        return


    click.echo("Generating...")
    reciter = get_reciter_config("Mahmoud Khalil Al-Husary")
    renderer = Renderer(
        height=resolution.height,
        width=resolution.width,
        translation_font=load_font(OPEN_SANS, size=20),
        fps=fps,
    )

    TEMP_FILENAME = f"{dist}/TEMP-DO-NOT-TOUCH"
    videos: List[str] = []

    generation_keys = []
    for k in verse_key:
        if isinstance(k, VerseKeyRange):
            for i in range(k.start.verse_id, k.end.verse_id + 1):
                generation_keys.append(
                    VerseKey(chapter_id=k.start.chapter_id, verse_id=i)
                )
        else:
            generation_keys.append(k)

    for key in generation_keys:
        filename = f"{dist}/{key.chapter_id}-{key.verse_id}.mp4"

        verbose_echo(verbose, f"loading verse[{key}] information...")
        verse_info = None
        try:
            verse_info = verse_info_by_key(key=key, reciter=reciter)
        except Exception:
            click.echo(f"[ERROR] key '{key}' not found")
            if click.confirm(f"ignore '{key}' and continue?", default=False):
                continue
            else:
                click.echo("exiting...")
                return
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
    os.system(
        f"ffmpeg -f concat -i {fname} -c copy -loglevel error -y {output_filename}"
    )
    os.remove(fname)


if __name__ == "__main__":
    App()
