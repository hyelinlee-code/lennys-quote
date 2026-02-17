"""
Re-extract Professional Vocabulary

Replaces existing vocabulary_highlights with professional/university-level words
using OpenAI API. Focuses on high-quality vocabulary for language learners.

Selection Criteria:
- Single professional words (e.g., "relentless", "friction", "leverage", "nuanced")
- Business idioms (e.g., "move the needle", "table stakes")
- Phrasal verbs with professional meaning (e.g., "double down on")

Exclusions:
- Common phrases that aren't vocabulary (e.g., "fairly middle class")
- Basic words any English speaker knows
- Long phrases (5+ words)

Uses checkpoint pattern for resumability.
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "reparse_vocab_checkpoint.json"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> dict:
    """Load checkpoint with processed files."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_files": [], "total_vocab_extracted": 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def extract_vocabulary(text: str, context: str) -> list[str]:
    """
    Extract professional vocabulary from a quote using GPT.
    Returns a list of 2-4 vocabulary items.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an English vocabulary instructor helping intermediate learners improve their professional English.
Your task is to identify useful vocabulary from business podcast quotes that learners should study.

ALWAYS extract 2-4 items from each quote. Look for:

1. PROFESSIONAL/ACADEMIC WORDS - words common in business but less common in casual speech:
   Examples: leverage, iterate, prioritize, optimize, validate, articulate, compelling, sustainable, scalable, friction, traction, alignment, bandwidth, stakeholder, initiative, metrics, trajectory, nuanced, deliberate, intentional, pivotal, crucial, fundamental

2. BUSINESS IDIOMS & EXPRESSIONS:
   Examples: move the needle, table stakes, double down, skin in the game, low-hanging fruit, at the end of the day, the bottom line, get buy-in, push back, circle back, take ownership, raise the bar, set the bar, north star, game changer

3. PHRASAL VERBS used in business:
   Examples: ramp up, scale up, phase out, roll out, sign off on, buy into, lean into, tap into, hone in on, zero in on, carve out, build out, flesh out

4. DESCRIPTIVE WORDS that add nuance:
   Examples: relentless, deliberate, intentional, incremental, exponential, counterintuitive, overwhelming, sustainable, viable, tangible

DO NOT include:
- Very basic words (good, bad, big, small, think, want, need)
- Incomplete phrases or sentence fragments
- Proper nouns (company/people names)

You MUST return 2-4 vocabulary items. Always find something useful for learners."""
                },
                {
                    "role": "user",
                    "content": f"""Extract 2-4 vocabulary items from this business quote that would be useful for English learners.

Quote: "{text}"

Context: {context[:200] if context else "Business podcast discussion"}

Return a JSON object with key "vocabulary" containing an array of 2-4 strings:"""
                }
            ],
            temperature=0.4,
            max_tokens=200,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Handle different response formats
        if isinstance(result, list):
            vocab = result
        elif isinstance(result, dict):
            # Try common keys
            vocab = result.get("vocabulary", result.get("words", result.get("items", [])))
            if not isinstance(vocab, list):
                for v in result.values():
                    if isinstance(v, list):
                        vocab = v
                        break
                else:
                    vocab = []
        else:
            vocab = []

        # Filter and validate
        valid_vocab = []
        for item in vocab:
            if isinstance(item, str):
                item = item.strip()
                word_count = len(item.split())
                # Keep only items 1-4 words
                if 1 <= word_count <= 4 and len(item) >= 3:
                    valid_vocab.append(item)

        # Return 2-4 items
        return valid_vocab[:4]

    except Exception as e:
        print(f"    API error: {e}")
        return []


def process_file(filepath: str) -> tuple[int, int]:
    """
    Process a single quote JSON file, re-extracting vocabulary.
    Returns (total_quotes, total_vocab_items).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    total_quotes = len(quotes)
    total_vocab = 0
    modified = False

    for quote in quotes:
        text = quote.get("text", "")
        context = quote.get("context", "")

        if not text:
            continue

        # Extract new vocabulary
        new_vocab = extract_vocabulary(text, context)

        # Update quote - replace old vocabulary_highlights
        old_vocab = quote.get("vocabulary_highlights", [])
        quote["vocabulary_highlights"] = new_vocab

        # Clear any previously enriched vocabulary to force re-enrichment
        if "vocabulary" in quote:
            del quote["vocabulary"]

        # Flag for vocabulary enrichment
        quote["vocab_reparsed"] = True

        total_vocab += len(new_vocab)
        modified = True

        time.sleep(0.3)  # Rate limiting

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return total_quotes, total_vocab


def main():
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_files", []))
    total_vocab = checkpoint.get("total_vocab_extracted", 0)

    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total_files = len(files)

    print("Re-extracting professional vocabulary...")
    print(f"Already processed: {len(processed)} files")
    print("=" * 60)

    files_processed_this_run = 0
    vocab_this_run = 0

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total_files}] {speaker}...", end=" ")

        try:
            quotes_count, vocab_count = process_file(str(filepath))
            files_processed_this_run += 1
            vocab_this_run += vocab_count
            total_vocab += vocab_count

            avg_per_quote = vocab_count / quotes_count if quotes_count > 0 else 0
            print(f"{vocab_count} vocab items ({avg_per_quote:.1f}/quote)")

            processed.add(filename)
            checkpoint["processed_files"] = list(processed)
            checkpoint["total_vocab_extracted"] = total_vocab
            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Vocabulary re-extraction complete.")
    print(f"  Files processed this run:  {files_processed_this_run}")
    print(f"  Vocab extracted this run:  {vocab_this_run}")
    print(f"  Total vocab extracted:     {total_vocab}")
    print(f"\nNext step: Run enrich_vocabulary_insights.py to add definitions")


if __name__ == "__main__":
    main()
