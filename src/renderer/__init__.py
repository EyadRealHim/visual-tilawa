from typing import Any, Dict

from pydantic import BaseModel
from PIL import Image, ImageDraw


from .utilities import load_font, verse_word2terms, verse_words_load_fonts, terms2lines
from ..verse import verse_info, VerseKey
from .types import TextRenderer
from .config import OPEN_SANS


class Renderer(BaseModel):
    height: int
    width: int

    fps: int

    # FreeTypeFont
    english_font: Any
    # font_url, FreeTypeFont
    font_cache: Dict[str, Any]



if __name__ == "__main__":
    verse = verse_info(VerseKey(chapter_id=2, verse_id=255))

    renderer = Renderer(
        english_font=load_font(OPEN_SANS, size=20),
        font_cache={},
        height=1080, width=540, fps=60, 
    )
    max_width = int(renderer.width * 0.8)
    
    verse_words_load_fonts(verse.content, 35, renderer.font_cache)

    terms = verse_word2terms(verse.content, renderer.font_cache)
    texts = [TextRenderer(list(reversed(term))) for term in terms2lines(terms, max_width)]


    canvas = Image.new("RGB", (renderer.width, renderer.height), 0)
    draw = ImageDraw.Draw(canvas, "RGB")

    y = 0
    for text in texts:
        text.render(draw, renderer.width / 2, renderer.height / 2 + y, fill=(255, 255, 255))
        y += 35 + 5
    
    canvas.save("out.png")

