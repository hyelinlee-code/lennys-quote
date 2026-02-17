"""
Trim Long Quotes to 45 Words

Trims the `text` field to ≤45 words by removing complete sentences from the end.
If the first sentence alone exceeds 45 words, uses GPT to select the most impactful clause.

Algorithm:
1. Count words in `text` field
2. If >45 words, split into sentences
3. Keep sentences from start until word count exceeds 45
4. If first sentence alone is >45 words, use GPT to select most impactful clause
5. After trimming, flag quote for translation regeneration

Uses checkpoint pattern for resumability.
"""

import json
import os
import re
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "trim_quotes_checkpoint.json"
MAX_WORDS = 45

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> dict:
    """Load checkpoint with processed files and their stats."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_files": [], "trimmed_quotes": 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences, preserving punctuation."""
    # Match sentence boundaries (., !, ?) followed by space or end
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def trim_by_sentences(text: str) -> str:
    """
    Trim text to ≤45 words by removing complete sentences from the end.
    Returns the first sentence if even that exceeds 45 words.
    """
    sentences = split_into_sentences(text)

    if not sentences:
        return text

    # Try adding sentences until we exceed the limit
    result_sentences = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = count_words(sentence)
        if current_word_count + sentence_words <= MAX_WORDS:
            result_sentences.append(sentence)
            current_word_count += sentence_words
        else:
            break

    if result_sentences:
        return " ".join(result_sentences)

    # First sentence alone exceeds limit - return it for GPT processing
    return sentences[0]


def use_gpt_to_trim(text: str, context: str) -> str:
    """
    Use GPT to select the most impactful clause from a long sentence.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert editor. Extract the most impactful,
insightful portion of a quote that captures its core message. Keep it under 45 words.
Maintain the speaker's original words as much as possible - do not paraphrase.
Return ONLY the trimmed quote, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"""Extract the most impactful portion (under 45 words) from this quote.
Keep the speaker's original words - select a clause or combination of clauses, don't rewrite.

Quote: "{text}"

Context: {context[:300]}

Return ONLY the trimmed quote:"""
                }
            ],
            temperature=0.2,
            max_tokens=200
        )

        trimmed = response.choices[0].message.content.strip()
        # Remove any surrounding quotes added by GPT
        trimmed = trimmed.strip('"\'')

        # Verify it's actually shorter
        if count_words(trimmed) <= MAX_WORDS:
            return trimmed
        else:
            # GPT failed to trim properly, truncate manually
            words = trimmed.split()[:MAX_WORDS]
            return " ".join(words) + "..."

    except Exception as e:
        print(f"    GPT error: {e}")
        # Fallback: simple word truncation
        words = text.split()[:MAX_WORDS]
        return " ".join(words) + "..."


def process_file(filepath: str) -> tuple[int, int]:
    """
    Process a single quote JSON file, trimming long quotes.
    Returns (total_quotes, trimmed_count).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    total_quotes = len(quotes)
    trimmed_count = 0
    modified = False

    for quote in quotes:
        text = quote.get("text", "")
        word_count = count_words(text)

        if word_count <= MAX_WORDS:
            continue

        # Try trimming by sentences first
        trimmed = trim_by_sentences(text)

        # If first sentence is still too long, use GPT
        if count_words(trimmed) > MAX_WORDS:
            print(f"    Using GPT for {word_count}-word quote...", end=" ")
            trimmed = use_gpt_to_trim(text, quote.get("context", ""))
            print(f"trimmed to {count_words(trimmed)} words")
            time.sleep(0.5)  # Rate limiting

        # Update quote
        quote["text"] = trimmed
        quote["text_trimmed"] = True  # Flag for translation regeneration
        quote["original_text"] = text  # Keep original for reference
        trimmed_count += 1
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return total_quotes, trimmed_count


def main():
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_files", []))
    total_trimmed = checkpoint.get("trimmed_quotes", 0)

    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total_files = len(files)

    print(f"Trimming quotes to {MAX_WORDS} words max...")
    print(f"Already processed: {len(processed)} files")
    print("=" * 60)

    files_processed_this_run = 0
    trimmed_this_run = 0

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total_files}] {speaker}...", end=" ")

        try:
            total_quotes, trimmed = process_file(str(filepath))
            files_processed_this_run += 1
            trimmed_this_run += trimmed
            total_trimmed += trimmed

            if trimmed > 0:
                print(f"trimmed {trimmed}/{total_quotes} quotes")
            else:
                print("all quotes within limit")

            processed.add(filename)
            checkpoint["processed_files"] = list(processed)
            checkpoint["trimmed_quotes"] = total_trimmed
            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Quote trimming complete.")
    print(f"  Files processed this run: {files_processed_this_run}")
    print(f"  Quotes trimmed this run:  {trimmed_this_run}")
    print(f"  Total quotes trimmed:     {total_trimmed}")


if __name__ == "__main__":
    main()
