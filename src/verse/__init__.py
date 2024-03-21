from typing import List, Set

from pydub import AudioSegment, silence

from .types import VerseInformation, ClipInformation, VerseWord, VerseKey
from ..utilities import GET, virtual_io
from .config import RECITER_ID, SILENCE_THRESHOLD, CODE_VERSION


def verse_info(key: VerseKey):
    url = f"https://api.quran.com//api/v4/verses/by_key/{key}"
    url += "?" + f"language=en&words=true&audio={RECITER_ID}"
    url += "&word_fields=" + f"code_v{CODE_VERSION},v{CODE_VERSION}_page"

    raw = GET(url=url).json()

    if not isinstance(raw, dict) or raw.get("error") is not None:
        raise RuntimeError("Error fetching verse raw information.")

    verse_data = raw["verse"]
    audio_data = verse_data["audio"]
    audio_segments = audio_data["segments"]

    SEG_BEGIN, SEG_END = 2, 3

    content: List[VerseWord] = []
    for raw_word in verse_data["words"]:
        position = raw_word["position"] - 1
        segment = (
            audio_segments[-1]
            if position >= len(audio_segments)
            else audio_segments[position]
        )

        # FIXME: I DONT WANT TO DO THIS!
        if raw_word["char_type_name"] != "word":
            continue  # Ignore non-words (e.g. AyahNumber)

        content.append(
            VerseWord(
                translation=raw_word["translation"]["text"],
                code_page=raw_word[f"v{CODE_VERSION}_page"],
                content=raw_word[f"code_v{CODE_VERSION}"],
                spell_audio_path=raw_word["audio_url"],
                begin=segment[SEG_BEGIN],
                end=segment[SEG_END],
            )
        )

    return VerseInformation(
        audio_path=audio_data["url"], verse_key=key, content=content
    )


def extract_clips(verse: VerseInformation):
    audio: AudioSegment = AudioSegment.from_file(virtual_io(verse.audio_url))
    silence_periods = silence.detect_silence(
        audio_segment=audio,
        min_silence_len=350,
        silence_thresh=audio.dBFS - SILENCE_THRESHOLD,
    )

    silence_periods = [(a + b) // 2 for a, b in silence_periods]
    silence_periods = [
        (prev, curr) for prev, curr in zip([0] + silence_periods, silence_periods)
    ]
    if not silence_periods:
        silence_periods = [(0, round(audio.duration_seconds * 1000))]

    clips: List[ClipInformation] = []
    words = set(verse.content)

    for index, (begin, end) in enumerate(silence_periods):
        collection: Set[VerseWord] = set()
        for word in words:
            if end >= word.timestamps >= begin:
                collection.add(word)

        words = words - collection

        collection = list(collection)
        collection = sorted(collection, key=lambda x: x.timestamps)

        clips.append(
            ClipInformation(
                verse_key=verse.verse_key,
                clip_index=index,
                content=collection,
                audio_url=verse.audio_url,
                begin=begin,
                end=end,
            )
        )

    if words:
        raise RuntimeError(
            f"Failed to group verse words into clips. {len(words)} words left unorganized."
        )

    return clips, audio


if __name__ == "__main__":
    verse = verse_info(VerseKey(chapter_id=1, verse_id=1))

    print(extract_clips(verse)[0][0].model_dump())
