"""
Full Vocabulary Enrichment

Populates all vocabulary insight fields using OpenAI API.
Processes vocabulary_highlights and creates structured vocabulary objects.

Fields Generated (for each vocabulary item):
- word: The vocabulary term
- definition: English definition
- businessContext: Business usage explanation
- nuance: Subtle meaning and connotations
- synonyms: Array of 2 alternatives
- antonyms: Array of 2 opposites

Uses checkpoint pattern for resumability.
Batches 5-6 words per API call for efficiency.
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "enrich_vocab_insights_checkpoint.json"
BATCH_SIZE = 5  # Words per API call

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> dict:
    """Load checkpoint with processed files."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_files": [], "total_vocab_enriched": 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def enrich_vocabulary_batch(words: list[str], quote_text: str) -> list[dict]:
    """
    Generate full vocabulary enrichment for a batch of words using GPT.
    """
    words_list = "\n".join(f"- {w}" for w in words)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert business English vocabulary instructor.
Generate comprehensive vocabulary definitions for advanced English learners.
Your definitions should be clear, professional, and suitable for university-level learners.
Return ONLY valid JSON."""
                },
                {
                    "role": "user",
                    "content": f"""For each word/phrase below, generate a comprehensive vocabulary object.

Words/Phrases:
{words_list}

Context from quote: "{quote_text[:300]}"

For EACH word, provide:
1. word: the original word/phrase (exactly as given)
2. definition: Clear, concise English definition (1-2 sentences)
3. businessContext: How this is specifically used in business/tech/startup settings (1-2 sentences)
4. nuance: Subtle meaning, connotations, or when to use vs. not use (1 sentence)
5. synonyms: Array of exactly 2 alternative words/phrases
6. antonyms: Array of exactly 2 opposite words/phrases (use ["N/A", "N/A"] if not applicable)

Return a JSON object with key "vocabulary" containing an array of these objects."""
                }
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Extract vocabulary array
        if isinstance(result, dict):
            vocab_list = result.get("vocabulary", result.get("words", result.get("items", [])))
            if not isinstance(vocab_list, list):
                for v in result.values():
                    if isinstance(v, list):
                        vocab_list = v
                        break
                else:
                    vocab_list = []
        elif isinstance(result, list):
            vocab_list = result
        else:
            vocab_list = []

        # Validate and structure each item
        enriched = []
        for item in vocab_list:
            if isinstance(item, dict) and "word" in item:
                vocab_obj = {
                    "word": item.get("word", ""),
                    "definition": item.get("definition", ""),
                    "businessContext": item.get("businessContext", ""),
                    "nuance": item.get("nuance", ""),
                    "synonyms": item.get("synonyms", [])[:2] if isinstance(item.get("synonyms"), list) else [],
                    "antonyms": item.get("antonyms", [])[:2] if isinstance(item.get("antonyms"), list) else []
                }
                enriched.append(vocab_obj)

        return enriched

    except Exception as e:
        print(f"    API error: {e}")
        # Return basic stubs on failure
        return [{
            "word": w,
            "definition": "",
            "businessContext": "",
            "nuance": "",
            "synonyms": [],
            "antonyms": []
        } for w in words]


def process_file(filepath: str) -> tuple[int, int]:
    """
    Process a single quote JSON file, enriching its vocabulary.
    Returns (total_quotes, total_vocab_enriched).
    """
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    total_quotes = len(quotes)
    total_vocab = 0
    modified = False

    for quote in quotes:
        vocab_highlights = quote.get("vocabulary_highlights", [])

        if not vocab_highlights:
            quote["vocabulary"] = []
            continue

        # Check if vocab_highlights is already structured (dict objects)
        if isinstance(vocab_highlights[0], dict):
            # Already enriched, check if it has all fields
            first = vocab_highlights[0]
            if all(k in first for k in ["definition", "nuance", "synonyms"]):
                # Already fully enriched
                quote["vocabulary"] = vocab_highlights
                continue

        # Get string list of words
        if isinstance(vocab_highlights[0], str):
            words = vocab_highlights
        else:
            words = [v.get("word", str(v)) for v in vocab_highlights]

        # Process in batches
        all_enriched = []
        quote_text = quote.get("text", "")

        for batch_start in range(0, len(words), BATCH_SIZE):
            batch = words[batch_start:batch_start + BATCH_SIZE]
            enriched = enrich_vocabulary_batch(batch, quote_text)
            all_enriched.extend(enriched)
            time.sleep(0.3)  # Rate limiting

        # Store enriched vocabulary
        quote["vocabulary"] = all_enriched
        total_vocab += len(all_enriched)
        modified = True

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return total_quotes, total_vocab


def main():
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_files", []))
    total_vocab = checkpoint.get("total_vocab_enriched", 0)

    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total_files = len(files)

    print("Enriching vocabulary with full insights...")
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

            print(f"enriched {vocab_count} vocabulary items")

            processed.add(filename)
            checkpoint["processed_files"] = list(processed)
            checkpoint["total_vocab_enriched"] = total_vocab
            save_checkpoint(checkpoint)

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Vocabulary enrichment complete.")
    print(f"  Files processed this run:  {files_processed_this_run}")
    print(f"  Vocab enriched this run:   {vocab_this_run}")
    print(f"  Total vocab enriched:      {total_vocab}")
    print(f"\nNext step: Run audit_key_sentences.py to fix keySentence mismatches")


if __name__ == "__main__":
    main()
