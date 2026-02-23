"""
Filter Vocabulary to Match Text

Filters vocabulary items to only include words/phrases that appear in the
current `text` field. This fixes the mismatch where vocabulary was extracted
from `context` or `original_text` but doesn't appear in the trimmed `text`.

FREE operation - no API calls needed.
Uses checkpoint pattern for resumability.
"""

import json
import re
from pathlib import Path

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "filter_vocab_checkpoint.json"


def load_checkpoint() -> dict:
    """Load checkpoint with processed files."""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed_files": [], "stats": {"quotes_modified": 0, "items_removed": 0}}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def word_in_text(word: str, text: str) -> bool:
    """
    Check if a word or phrase appears in text (case-insensitive).
    Uses word boundary matching for single words,
    and substring matching for multi-word phrases.
    """
    word_lower = word.lower()
    text_lower = text.lower()

    # For multi-word phrases, use simple substring match
    if " " in word_lower:
        return word_lower in text_lower

    # For single words, use word boundary matching
    # This handles punctuation like "growth." matching "growth"
    pattern = r'\b' + re.escape(word_lower) + r'\b'
    return bool(re.search(pattern, text_lower))


def filter_quote_vocabulary(quote: dict) -> tuple[bool, int]:
    """
    Filter vocabulary to only include words that appear in text.
    Returns (was_modified, items_removed_count).
    """
    text = quote.get("text", "")
    if not text:
        return False, 0

    items_removed = 0
    modified = False

    # Filter vocabulary_highlights
    highlights = quote.get("vocabulary_highlights", [])
    if highlights:
        filtered_highlights = [h for h in highlights if word_in_text(h, text)]
        removed_count = len(highlights) - len(filtered_highlights)
        if removed_count > 0:
            quote["vocabulary_highlights"] = filtered_highlights
            items_removed += removed_count
            modified = True

    # Filter vocabulary (enriched vocabulary items)
    vocabulary = quote.get("vocabulary", [])
    if vocabulary:
        filtered_vocab = [v for v in vocabulary if word_in_text(v.get("word", ""), text)]
        removed_count = len(vocabulary) - len(filtered_vocab)
        if removed_count > 0:
            quote["vocabulary"] = filtered_vocab
            items_removed += removed_count
            modified = True

    # Mark as filtered if any items were removed
    if modified:
        quote["vocabulary_filtered"] = True

    return modified, items_removed


def process_file(filepath: Path) -> tuple[int, int, int]:
    """
    Process a single quote file.
    Returns (total_quotes, quotes_modified, items_removed).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    total_quotes = len(quotes)
    quotes_modified = 0
    items_removed = 0

    for quote in quotes:
        modified, removed = filter_quote_vocabulary(quote)
        if modified:
            quotes_modified += 1
            items_removed += removed

    # Save if any modifications were made
    if quotes_modified > 0:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return total_quotes, quotes_modified, items_removed


def main():
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_files", []))
    stats = checkpoint.get("stats", {"quotes_modified": 0, "items_removed": 0})

    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total_files = len(files)

    print("=" * 60)
    print("Filter Vocabulary to Match Text")
    print("=" * 60)
    print(f"Already processed: {len(processed)} files")
    print()

    files_processed_this_run = 0

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total_files}] {speaker}...", end=" ")

        try:
            total_quotes, quotes_modified, items_removed = process_file(filepath)
            files_processed_this_run += 1

            stats["quotes_modified"] += quotes_modified
            stats["items_removed"] += items_removed

            if quotes_modified > 0:
                print(f"{quotes_modified} quotes modified, {items_removed} items removed")
            else:
                print("no changes")

            processed.add(filename)
            checkpoint["processed_files"] = list(processed)
            checkpoint["stats"] = stats
            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"ERROR: {e}")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Files processed this run: {files_processed_this_run}")
    print(f"Total quotes modified:    {stats['quotes_modified']}")
    print(f"Total items removed:      {stats['items_removed']}")
    print()
    print("Next step: Run regenerate_trimmed_translations.py")


if __name__ == "__main__":
    main()
