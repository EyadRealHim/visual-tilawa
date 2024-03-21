from typing import List, Any, Dict

from PIL.ImageFont import FreeTypeFont
from PIL.ImageDraw import ImageDraw
from pydantic import BaseModel

from cv2 import VideoWriter, VideoWriter_fourcc


fourcc = VideoWriter_fourcc(*"mp4v")


class Term:
    def __init__(self, content: str, font: FreeTypeFont) -> None:
        self.content = content
        self.font = font

        self.width = round(self.font.getlength(self.content))
    

class TextRenderer:
    def __init__(self, terms: List[Term]) -> None:
        self.terms = terms
        self.text_width = sum(map(lambda term: term.width, self.terms))


    def render(self, canvas: ImageDraw, x: float, y: float, fill, active_term: Term=None, active_fill=None):
        x -= self.text_width / 2

        for term in self.terms:
            canvas.text((x, y), term.content, font=term.font, fill=active_term if term is active_term else fill)
            x += term.width

class Renderer(BaseModel):
    height: int
    width: int

    fps: int

    # FreeTypeFont
    translation_font: Any
    # font_url, FreeTypeFont
    font_cache: Dict[str, Any]

    @property
    def frame_size(self):
        return (self.width, self.height)

    def video_writer(self, filename: str):
        return VideoWriter(
            filename=filename, fourcc=fourcc,
            fps=self.fps, frameSize=self.frame_size
        )
