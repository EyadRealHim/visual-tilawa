from verse import VerseKey, extract_clips, verse_info



if __name__ == "__main__":
    verse = verse_info(VerseKey(chapter_id=1, verse_id=1))

    print(
        extract_clips(verse)
    )