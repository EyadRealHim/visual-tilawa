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
        if isinstance(value, tuple) or isinstance(value, VerseKey):
            return value

        chapter_id, verse_id = 0, 0

        try:
            chapter_id, verse_id = map(int, value.split(":"))
        except ValueError:
            raise click.BadParameter(
                "verse key must be specified in the format 'chapter_id:verse_id'."
            )

        if chapter_id <= 0 or verse_id <= 0:
            raise click.BadArgumentUsage(
                "chapter_id and verse_id must be positive integers."
            )

        return VerseKey(chapter_id=chapter_id, verse_id=verse_id)


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
    type=str,
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
    verse_key: VerseKey,
    dist: str,
    fps: int,
    resolution: VideoResolution,
    verbose: bool,
):
    """generate clips by verse"""
    line_text = "-" * 10

    click.echo("")
    click.echo(f"{line_text}Summary{line_text}")
    click.echo(f"key: {verse_key}\tdist: {dist}")
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

    verbose_echo(verbose, f"loading verse[{verse_key}] information...")
    verse_info = verse_info_by_key(key=verse_key)
    verbose_echo(verbose, "extracting clips...")
    clips, audio = extract_clips(verse_info)

    TEMP_FILENAME = f"{dist}/TEMP-DO-NOT-TOUCH"
    out = renderer.video_writer(f"{TEMP_FILENAME}.mp4")
    audio.export(f"{TEMP_FILENAME}.mp3")

    for clip in tqdm(clips, "rendering"):
        for frame in clip2frames(renderer, clip):
            out.write(frame)

    out.release()

    output_filename = click.prompt(
        "Enter output video path",
        default="release.mp4",
        type=click.Path(exists=False),
    )

    merge_audio_and_video(
        output_filename, f"{TEMP_FILENAME}.mp3", f"{TEMP_FILENAME}.mp4"
    )


if __name__ == "__main__":
    App()
