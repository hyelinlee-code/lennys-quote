"""
Phase 1C: Pre-generate AI Vocabulary Insights

For each enriched vocabulary item in the quote files, generates an insight
object with: nuance, synonyms, and antonyms.

Uses OpenAI API with structured JSON output.
Batches by speaker file with checkpoint/resume capability.
Stores insights nested inside each vocabulary object.
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "insights_generation_checkpoint.json"

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


def generate_insights_batch(vocab_items: list[dict], quote_context: str) -> list[dict]:
    """
    Generate AI insights for a batch of vocabulary items.
    Returns list of insight objects with nuance, synonyms, antonyms.
    """
    words_desc = "\n".join(
        f"- \"{item['word']}\": {item.get('definition', 'N/A')}"
        for item in vocab_items
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert business English coach for non-native speakers.
Generate vocabulary insights that help learners understand the nuances of business language.
Return ONLY valid JSON."""
                },
                {
                    "role": "user",
                    "content": f"""For each word/phrase below, generate an insight object:

Words:
{words_desc}

Context from the quote:
"{quote_context[:500]}"

For each word, provide:
1. nuance: Why this specific word/phrase is used instead of simpler alternatives. What subtle meaning does it convey in a business setting? (2-3 sentences)
2. synonyms: 3 formal/professional synonyms or alternative phrases
3. antonyms: 3 antonyms or opposite concepts

Return a JSON object with key "insights" containing an array of objects, each with:
- word (string)
- nuance (string)
- synonyms (array of 3 strings)
- antonyms (array of 3 strings)"""
                }
            ],
            temperature=0.3,
            max_tokens=2000,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Handle various response formats
        insights_list = result.get("insights", [])
        if not isinstance(insights_list, list):
            for v in result.values():
                if isinstance(v, list):
                    insights_list = v
                    break

        # Build a lookup by word
        insights_map = {}
        for insight in insights_list:
            if isinstance(insight, dict) and "word" in insight:
                insights_map[insight["word"].lower()] = {
                    "nuance": insight.get("nuance", ""),
                    "synonyms": insight.get("synonyms", [])[:3],
                    "antonyms": insight.get("antonyms", [])[:3]
                }

        return insights_map

    except Exception as e:
        print(f"    API error: {e}")
        return {}


def process_file(filepath: str) -> bool:
    """Process a single quote file, adding insights to vocabulary items."""
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    modified = False

    for quote in quotes:
        vocab = quote.get("vocabulary", [])
        if not vocab or not isinstance(vocab, list):
            continue

        # Skip if first vocab item already has insights
        if isinstance(vocab[0], dict) and "insight" in vocab[0]:
            continue

        # Only process structured vocabulary (dicts, not strings)
        structured_vocab = [v for v in vocab if isinstance(v, dict)]
        if not structured_vocab:
            continue

        # Generate insights for all vocab in this quote
        context = quote.get("context", quote.get("text", ""))
        insights_map = generate_insights_batch(structured_vocab, context)

        if insights_map:
            for v_item in structured_vocab:
                word_lower = v_item["word"].lower()
                if word_lower in insights_map:
                    v_item["insight"] = insights_map[word_lower]
                else:
                    # Try partial match
                    matched = False
                    for key, val in insights_map.items():
                        if key in word_lower or word_lower in key:
                            v_item["insight"] = val
                            matched = True
                            break
                    if not matched:
                        v_item["insight"] = {
                            "nuance": "",
                            "synonyms": [],
                            "antonyms": []
                        }
            modified = True

        time.sleep(0.5)  # Rate limiting

    if modified:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(quotes, f, indent=2, ensure_ascii=False)

    return modified


def main():
    processed = load_checkpoint()
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total = len(files)
    enriched_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Generating AI insights for {total} quote files...")
    print(f"Already processed: {len(processed)} files")
    print("=" * 60)

    for i, filepath in enumerate(files, 1):
        filename = filepath.name

        if filename in processed:
            skipped_count += 1
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total}] {speaker}...", end=" ")

        try:
            modified = process_file(str(filepath))
            if modified:
                enriched_count += 1
                print("insights generated")
            else:
                print("skipped (already has insights or no structured vocab)")

            processed.add(filename)
            save_checkpoint(processed)

        except Exception as e:
            error_count += 1
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! AI insights generation complete.")
    print(f"  Generated:      {enriched_count}")
    print(f"  Skipped:        {skipped_count}")
    print(f"  Errors:         {error_count}")
    print(f"  Total files:    {total}")


if __name__ == "__main__":
    main()
