from PIL import Image, ImageDraw
import numpy as np
import cv2


from .utilities import *
from ..verse import verse_info, VerseKey, ClipInformation, extract_clips
from .types import TextRenderer, Renderer
from .config import OPEN_SANS

TEXT_MAX_WIDTH_RATIO = 0.8
VERTICAL_PADDING = 5

def clip2frames(renderer: Renderer, clip: ClipInformation):
    translation_font_size = renderer.translation_font_size
    quran_font_size = renderer.quran_font_size


    max_width = int(renderer.width * TEXT_MAX_WIDTH_RATIO)
    frame_count = time_step2frame_index(clip.duration, renderer.fps)

    verse_words_load_fonts(clip.content, quran_font_size, renderer.font_cache)

    translation_terms = [x.translation.split(" ") for x in clip.content]
    translation_terms = sum(translation_terms, [])
    translation_terms = " ".join(translation_terms)
    translation_terms = text2terms(translation_terms, renderer.translation_font)
    translation_lines = [TextRenderer(term) for term in terms2lines(translation_terms, max_width)]

    terms = verse_word2terms(clip.content, renderer.font_cache)
    lines = [TextRenderer(list(reversed(terms))) for terms in terms2lines(terms, max_width)]

    canvas = Image.new("RGB", renderer.frame_size, 0)
    draw = ImageDraw.Draw(canvas, "RGB")

    y = 0
    for line in lines:
        line.render(draw, renderer.width / 2, renderer.height / 2 + y, fill=(255, 255, 255))
        y += quran_font_size + VERTICAL_PADDING
    y += translation_font_size + VERTICAL_PADDING
    for line in translation_lines:
        line.render(draw, renderer.width / 2, renderer.height / 2 + y, fill=(255, 255, 255))
        y += translation_font_size + VERTICAL_PADDING
    
    static_image = np.array(canvas)
    black_canvas = np.zeros_like(static_image)

    transition_duration = int(min(clip.duration * (1/6), 500))
    transition_duration = time_step2frame_index(transition_duration, renderer.fps)

    transition_begin = transition_duration - 0
    transition_end = frame_count - transition_begin

    for index in range(frame_count+1):
        darkness = 0
        if transition_begin >= index:
            darkness = (transition_begin - index) / transition_duration
        elif index >= transition_end:
            darkness = (index - transition_end) / transition_duration


        if darkness != 0:
            yield cv2.addWeighted(static_image, 1 - darkness, black_canvas, 1, 0)
        else:
            yield static_image



if __name__ == "__main__":
    renderer = Renderer(
        translation_font=load_font(OPEN_SANS, size=20),
        height=1080, width=540, fps=20,
        quran_font_size=40,
    )

    clips, audio = extract_clips(verse_info(VerseKey(chapter_id=1, verse_id=1)))

    for clip in clips:
        out = renderer.video_writer(f"dist/{clip.filename()}.mp4")
        for frame in clip2frames(renderer, clip):
            out.write(frame)
        out.release()