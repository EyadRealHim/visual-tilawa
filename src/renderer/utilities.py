from typing import List, Dict

from PIL.ImageFont import FreeTypeFont

from .types import Term
from ..utilities import virtual_io
from ..verse.types import VerseWord

FontCache = Dict[str, FreeTypeFont]


def load_font(url: str, **kwargs):
    return FreeTypeFont(virtual_io(url), **kwargs)


def terms2lines(terms: List[Term], max_width: int):
    temp: List[Term] = []

    width = 0
    for term in terms:
        term_width = term.width

        if width + term_width > max_width:
            yield temp
            temp = []
            width = 0

        temp.append(term)
        width += term_width

    if temp:
        yield temp

def text2terms(text: str, font: FreeTypeFont):
    terms = [[Term(w, font), Term(" ", font)] for w in text.split(" ")]
    terms = sum(terms, [])

    return terms

def verse_word2terms(verse_words: List[VerseWord], font_cache: FontCache):
    return[Term(vw.content, font_cache[vw.font_url]) for vw in verse_words]

def verse_words_load_fonts(
   verse_words: List[VerseWord], font_size: int, font_cache: FontCache = {}
):
    for w in verse_words:
        f = w.font_url
        font_cache.setdefault(f, font_cache.get(f) or load_font(f, size=font_size))

    return font_cache

