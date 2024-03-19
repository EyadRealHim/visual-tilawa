from typing import List

from pydantic import BaseModel

from .utilities import path2url
from .config import CODE_VERSION


class VerseKey(BaseModel):
    chapter_id: int
    verse_id: int

    def __str__(self) -> str:
        return f"{self.chapter_id}:{self.verse_id}"

class VerseWord(BaseModel):
    spell_audio_path: str
    translation: str

    code_page: int
    content: str

    # in milliseconds
    begin: int
    # in milliseconds
    end: int

    @property
    def timestamps(self):
        return (self.begin + self.end) // 2

    @property
    def font_url(self) -> str:
        return f"https://quran.com/fonts/quran/hafs/v{CODE_VERSION}/ttf/p{self.code_page}.ttf"

    @property
    def spell_audio_url(self) -> str:
        return path2url(self.spell_audio_path, "https://audio.qurancdn.com/")

    def __hash__(self) -> int:
        return hash(self.content) + hash(self.translation) + self.timestamps

class VerseInformation(BaseModel):
    audio_path: str
    verse_key: VerseKey

    content: List[VerseWord]

    @property
    def audio_url(self) -> str:
        return path2url(self.audio_path, "https://verses.quran.com/")
    
class ClipInformation(BaseModel):
    verse_key: VerseKey
    clip_index: int

    content: List[VerseWord]
    audio_url: str

    # in milliseconds
    begin: int
    # in milliseconds
    end: int

    # in milliseconds
    @property
    def duration(self):
        return self.end - self.begin

    def filename(self):
        return f"{self.verse_key}:{self.clip_index}".replace(":", "-")