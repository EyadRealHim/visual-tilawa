from typing import List

from PIL.ImageFont import FreeTypeFont
from PIL.ImageDraw import ImageDraw


class Term:
    def __init__(self, content: str, font: FreeTypeFont) -> None:
        self.content = content
        self.font = font

        self.width = round(self.font.getlength(self.content))
    

class TextRenderer:
    def __init__(self, terms: List[Term]) -> None:
        self.terms = terms
        self.text_width = sum(map(lambda term: term.width, self.terms))


    def render(self, canvas: ImageDraw, x: float, y: float, **kwargs):
        x -= self.text_width / 2

        for term in self.terms:
            canvas.text((x, y), term.content, font=term.font, **kwargs)
            x += term.width