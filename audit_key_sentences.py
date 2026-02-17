"""
Audit and Fix keySentence Mismatches

Ensures `key_sentence` is a verbatim excerpt from `text`.
Identifies and fixes mismatches where keySentence doesn't appear in the original quote.

Algorithm:
1. For each quote, check if key_sentence words appear in text (fuzzy match)
2. Flag mismatches where <60% word overlap
3. For flagged quotes, re-generate key_sentence with strict verbatim requirement

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
CHECKPOINT_FILE = "audit_keysent_checkpoint.json"
OVERLAP_THRESHOLD = 0.6  # 60% word overlap required

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> dict:
    """Load checkpoint with processed files."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_files": [], "fixed_count": 0, "already_good_count": 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def normalize_text(text: str) -> set[str]:
    """Normalize text to set of lowercase words for comparison."""
    # Remove punctuation and convert to lowercase
    text = re.sub(r'[^\w\s]', '', text.lower())
    return set(text.split())


def calculate_overlap(key_sentence: str, full_text: str) -> float:
    """
    Calculate word overlap between key_sentence and full_text.
    Returns a ratio (0.0 to 1.0) of key_sentence words found in full_text.
    """
    key_words = normalize_text(key_sentence)
    text_words = normalize_text(full_text)

    if not key_words:
        return 0.0

    overlap = key_words.intersection(text_words)
    return len(overlap) / len(key_words)


def check_verbatim_substring(key_sentence: str, full_text: str) -> bool:
    """
    Check if key_sentence (or a close variant) appears as substring in full_text.
    More lenient check that handles minor punctuation/case differences.
    """
    # Normalize both for comparison
    key_norm = re.sub(r'\s+', ' ', key_sentence.lower().strip())
    text_norm = re.sub(r'\s+', ' ', full_text.lower().strip())

    # Check if key appears in text (exact substring)
    if key_norm in text_norm:
        return True

    # Check without punctuation
    key_no_punct = re.sub(r'[^\w\s]', '', key_norm)
    text_no_punct = re.sub(r'[^\w\s]', '', text_norm)

    return key_no_punct in text_no_punct


def regenerate_key_sentence(text: str, context: str) -> str:
    """
    Use GPT to select a verbatim key sentence from the text.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at identifying the most impactful BUSINESS INSIGHT in a quote.
Your task is to select a VERBATIM sentence or clause directly from the provided text.

CRITICAL RULES:
1. The output MUST be an EXACT copy of words from the input text
2. Do NOT paraphrase, summarize, or modify any words
3. Select the sentence/clause that best captures a BUSINESS-RELEVANT insight
4. The selection should be 10-25 words ideally
5. You may select a partial sentence if it contains the key insight

CONTENT FILTERING (mandatory):
- REJECT personal biography: family background, childhood, where they grew up
- REJECT anecdotes: "I was nine years old", "my parents", "when I was born"
- PREFER: actionable advice, frameworks, mental models, strategic insights
- PREFER: wisdom about product, leadership, growth, startups, technology
- If the quote is ONLY personal background, select the LEAST personal sentence

Return ONLY the verbatim excerpt, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"""Select the most impactful VERBATIM sentence or clause from this quote.

QUOTE:
"{text}"

CONTEXT: {context[:200] if context else "Business podcast discussion"}

Return ONLY the exact words from the quote (do not add or change any words):"""
                }
            ],
            temperature=0.1,
            max_tokens=150
        )

        key_sentence = response.choices[0].message.content.strip()
        # Remove any quotes GPT might have added
        key_sentence = key_sentence.strip('"\'')

        return key_sentence

    except Exception as e:
        print(f"    API error: {e}")
        return ""


def process_file(filepath: str) -> tuple[int, int, int]:
    """
    Process a single quote JSON file, auditing and fixing key sentences.
    Returns (total_quotes, fixed_count, already_good_count).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    total_quotes = len(quotes)
    fixed_count = 0
    good_count = 0
    modified = False

    for quote in quotes:
        text = quote.get("text", "")
        key_sentence = quote.get("key_sentence", "")

        if not text:
            continue

        # Check if key_sentence is valid
        if key_sentence:
            # First check if it's a verbatim substring
            is_verbatim = check_verbatim_substring(key_sentence, text)

            # If not verbatim, check word overlap
            if not is_verbatim:
                overlap = calculate_overlap(key_sentence, text)

                if overlap >= OVERLAP_THRESHOLD:
                    # Good enough overlap
                    good_count += 1
                    continue
                else:
                    # Need to regenerate
                    print(f"    Mismatch ({overlap:.0%} overlap): regenerating...", end=" ")
            else:
                good_count += 1
                continue
        else:
            # No key_sentence exists
            print(f"    Missing: generating...", end=" ")

        # Regenerate key_sentence
        new_key = regenerate_key_sentence(text, quote.get("context", ""))

        if new_key:
            # Verify the new key is actually verbatim
            if check_verbatim_substring(new_key, text):
                quote["key_sentence"] = new_key
                fixed_count += 1
                modified = True
                print("fixed")
            else:
                # GPT failed to give verbatim, try extracting first sentence
                sentences = re.split(r'(?<=[.!?])\s+', text.strip())
                if sentences:
                    quote["key_sentence"] = sentences[0]
                    fixed_count += 1
                    modified = True
                    print("used first sentence")
        else:
            # Fallback to first sentence
            sentences = re.split(r'(?<=[.!?])\s+', text.strip())
            if sentences:
                quote["key_sentence"] = sentences[0]
                fixed_count += 1
                modified = True
                print("fallback to first sentence")

        time.sleep(0.3)  # Rate limiting

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return total_quotes, fixed_count, good_count


def main():
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_files", []))
    total_fixed = checkpoint.get("fixed_count", 0)
    total_good = checkpoint.get("already_good_count", 0)

    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total_files = len(files)

    print("Auditing key_sentence for verbatim accuracy...")
    print(f"Overlap threshold: {OVERLAP_THRESHOLD:.0%}")
    print(f"Already processed: {len(processed)} files")
    print("=" * 60)

    files_processed_this_run = 0
    fixed_this_run = 0
    good_this_run = 0

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total_files}] {speaker}...")

        try:
            total_quotes, fixed, good = process_file(str(filepath))
            files_processed_this_run += 1
            fixed_this_run += fixed
            good_this_run += good
            total_fixed += fixed
            total_good += good

            if fixed == 0:
                print(f"    All {total_quotes} quotes OK")

            processed.add(filename)
            checkpoint["processed_files"] = list(processed)
            checkpoint["fixed_count"] = total_fixed
            checkpoint["already_good_count"] = total_good
            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Key sentence audit complete.")
    print(f"  Files processed this run:  {files_processed_this_run}")
    print(f"  Fixed this run:            {fixed_this_run}")
    print(f"  Already good this run:     {good_this_run}")
    print(f"  Total fixed:               {total_fixed}")
    print(f"  Total already good:        {total_good}")


if __name__ == "__main__":
    main()
