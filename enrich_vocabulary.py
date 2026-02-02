"""
Phase 1B: Enrich Vocabulary with Definitions

Reads all quote JSON files from output/ and enriches each quote's
vocabulary_highlights (string array) into structured vocabulary objects
with definition, businessContext, and exampleUsage.

Uses OpenAI API with batching (5-10 words per call) for efficiency.
Writes enriched vocabulary back into each quote JSON file.
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "vocab_enrichment_checkpoint.json"
BATCH_SIZE = 6  # Words per API call

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> set:
    """Load set of already-processed files."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_checkpoint(processed: set):
    """Save checkpoint of processed files."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(list(processed), f)


def enrich_vocabulary_batch(words: list[str], quote_text: str, context: str) -> list[dict]:
    """
    Generate structured vocabulary objects for a batch of words using OpenAI.
    """
    words_list = "\n".join(f"- {w}" for w in words)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a business English vocabulary expert. Generate structured vocabulary definitions
for words/phrases used in business podcast contexts. Return ONLY valid JSON."""
                },
                {
                    "role": "user",
                    "content": f"""For each word/phrase below, generate a vocabulary object with:
- word: the original word/phrase
- definition: clear, concise definition (1-2 sentences)
- businessContext: how this is specifically used in business/tech/startup settings (1-2 sentences)
- exampleUsage: a natural example sentence using this word in a business meeting or email

Words/Phrases:
{words_list}

Original quote for context:
"{quote_text}"

Surrounding context:
"{context[:500]}"

Return a JSON array of objects with keys: word, definition, businessContext, exampleUsage"""
                }
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Handle both {vocabulary: [...]} and [...] formats
        if isinstance(result, dict):
            vocab_list = result.get("vocabulary", result.get("words", result.get("items", [])))
            if not isinstance(vocab_list, list):
                # Try to find any list value in the dict
                for v in result.values():
                    if isinstance(v, list):
                        vocab_list = v
                        break
        elif isinstance(result, list):
            vocab_list = result
        else:
            vocab_list = []

        # Validate and clean each item
        enriched = []
        for item in vocab_list:
            if isinstance(item, dict) and "word" in item:
                enriched.append({
                    "word": item["word"],
                    "definition": item.get("definition", ""),
                    "businessContext": item.get("businessContext", ""),
                    "exampleUsage": item.get("exampleUsage", "")
                })

        return enriched

    except Exception as e:
        print(f"    API error: {e}")
        # Return basic stubs on failure
        return [{"word": w, "definition": "", "businessContext": "", "exampleUsage": ""} for w in words]


def process_file(filepath: str) -> bool:
    """Process a single quote JSON file, enriching its vocabulary."""
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    modified = False

    for qi, quote in enumerate(quotes):
        vocab_highlights = quote.get("vocabulary_highlights", [])

        # Skip if already enriched (check if vocab is already structured)
        if vocab_highlights and isinstance(vocab_highlights[0], dict):
            continue

        if not vocab_highlights:
            quote["vocabulary"] = []
            continue

        # Process in batches
        all_enriched = []
        for batch_start in range(0, len(vocab_highlights), BATCH_SIZE):
            batch = vocab_highlights[batch_start:batch_start + BATCH_SIZE]
            enriched = enrich_vocabulary_batch(
                batch,
                quote.get("text", ""),
                quote.get("context", "")
            )
            all_enriched.extend(enriched)
            time.sleep(0.5)  # Rate limiting

        # Store enriched vocabulary in new field
        quote["vocabulary"] = all_enriched
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return modified


def main():
    processed = load_checkpoint()
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total = len(files)
    already_done = 0
    enriched_count = 0
    error_count = 0

    print(f"Enriching vocabulary for {total} quote files...")
    print(f"Already processed: {len(processed)} files")
    print("=" * 60)

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            already_done += 1
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total}] {speaker}...", end=" ")

        try:
            modified = process_file(str(filepath))
            if modified:
                enriched_count += 1
                print("enriched")
            else:
                print("already structured")

            processed.add(filename)
            save_checkpoint(processed)

        except Exception as e:
            error_count += 1
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Vocabulary enrichment complete.")
    print(f"  Enriched:       {enriched_count}")
    print(f"  Already done:   {already_done}")
    print(f"  Errors:         {error_count}")
    print(f"  Total files:    {total}")


if __name__ == "__main__":
    main()
