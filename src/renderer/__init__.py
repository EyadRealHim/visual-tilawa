from PIL import Image, ImageDraw
import numpy as np
import cv2


from .utilities import *
from ..verse import verse_info, VerseKey, ClipInformation, extract_clips
from .types import TextRenderer, Renderer
from .config import OPEN_SANS

TEXT_MAX_WIDTH_RATIO = 0.8

def clip2frames(renderer: Renderer, clip: ClipInformation):
    VERTICAL_PADDING = 5
    TRANSLATION_FONT_SIZE = 20
    FONT_SIZE = 35

    max_width = int(renderer.width * TEXT_MAX_WIDTH_RATIO)
    frame_count = time_step2frame_index(clip.duration, renderer.fps)


    verse_words_load_fonts(clip.content, FONT_SIZE, renderer.font_cache)

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
        y += FONT_SIZE + VERTICAL_PADDING
    y += TRANSLATION_FONT_SIZE + VERTICAL_PADDING
    for line in translation_lines:
        line.render(draw, renderer.width / 2, renderer.height / 2 + y, fill=(255, 255, 255))
        y += TRANSLATION_FONT_SIZE + VERTICAL_PADDING
    
    static_image = np.array(canvas)
    black_canvas = np.zeros_like(static_image)

    TRANSITION_DURATION = int(min(clip.duration * (1/6), 500))
    TRANSITION_DURATION = time_step2frame_index(TRANSITION_DURATION, renderer.fps)

    TRANSITION_BEGIN = TRANSITION_DURATION - 0
    TRANSITION_END = frame_count - TRANSITION_BEGIN

    for index in range(frame_count+1):
        darkness = 0
        if TRANSITION_BEGIN >= index:
            darkness = (TRANSITION_BEGIN - index) / TRANSITION_DURATION
        elif index >= TRANSITION_END:
            darkness = (index - TRANSITION_END) / TRANSITION_DURATION


        if darkness != 0:
            yield cv2.addWeighted(static_image, 1 - darkness, black_canvas, 1, 0)
        else:
            yield static_image



if __name__ == "__main__":
    renderer = Renderer(
        translation_font=load_font(OPEN_SANS, size=20),
        font_cache={},
        height=1080, width=540, fps=20,
    )

    clips, audio = extract_clips(verse_info(VerseKey(chapter_id=2, verse_id=255)))

    for clip in clips:
        out = renderer.video_writer(f"dist/{clip.filename()}.mp4")
        for frame in clip2frames(renderer, clip):
            out.write(frame)
        out.release()
    exit()