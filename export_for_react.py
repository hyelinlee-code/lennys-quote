"""
Phase 1D: Export to React-ready JSON

Merges all enriched data into a single quotes_enriched.json file ready
for the React app. Handles both current data format (string vocab arrays)
and enriched data format (structured vocab objects).

Reads:
  - output/*.json (quote files)
  - speaker_profiles_enriched.json (or speaker_profiles.json as fallback)

Output:
  - fluent-stakeholder/public/data/quotes.json
"""

import json
import os
import re
from pathlib import Path

OUTPUT_DIR = "output"
ENRICHED_PROFILES = "speaker_profiles_enriched.json"
FALLBACK_PROFILES = "speaker_profiles.json"
REACT_OUTPUT_DIR = "fluent-stakeholder/public/data"
REACT_OUTPUT_FILE = os.path.join(REACT_OUTPUT_DIR, "quotes.json")


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text


def load_speaker_profiles() -> dict:
    """Load enriched profiles, falling back to base profiles."""
    if os.path.exists(ENRICHED_PROFILES):
        print(f"Using enriched profiles: {ENRICHED_PROFILES}")
        with open(ENRICHED_PROFILES, "r", encoding="utf-8") as f:
            return json.load(f)

    print(f"Enriched profiles not found, using fallback: {FALLBACK_PROFILES}")
    with open(FALLBACK_PROFILES, "r", encoding="utf-8") as f:
        base = json.load(f)

    # Convert base format to enriched format
    enriched = {}
    for speaker, data in base.items():
        enriched[speaker] = {
            "function": data.get("function", "Unknown"),
            "expertise": data.get("expertise", []),
            "role": data.get("function", "Guest"),
            "company": ""
        }
    return enriched


def normalize_vocabulary(vocab_highlights, vocab_enriched=None):
    """
    Normalize vocabulary into structured format.
    Handles: string arrays, already-structured objects, or enriched objects.
    """
    # If enriched vocabulary exists (from Phase 1B), use it
    if vocab_enriched and isinstance(vocab_enriched, list) and len(vocab_enriched) > 0:
        if isinstance(vocab_enriched[0], dict):
            result = []
            for v in vocab_enriched:
                item = {
                    "word": v.get("word", ""),
                    "definition": v.get("definition", ""),
                    "businessContext": v.get("businessContext", ""),
                    "exampleUsage": v.get("exampleUsage", ""),
                }
                # Include insight if present (from Phase 1C)
                if "insight" in v:
                    item["insight"] = {
                        "nuance": v["insight"].get("nuance", ""),
                        "synonyms": v["insight"].get("synonyms", []),
                        "antonyms": v["insight"].get("antonyms", [])
                    }
                result.append(item)
            return result

    # Fall back to converting string arrays to basic objects
    if vocab_highlights and isinstance(vocab_highlights, list):
        result = []
        for v in vocab_highlights:
            if isinstance(v, str):
                result.append({
                    "word": v,
                    "definition": "",
                    "businessContext": "",
                    "exampleUsage": ""
                })
            elif isinstance(v, dict):
                result.append({
                    "word": v.get("word", ""),
                    "definition": v.get("definition", ""),
                    "businessContext": v.get("businessContext", ""),
                    "exampleUsage": v.get("exampleUsage", ""),
                })
        return result

    return []


def main():
    profiles = load_speaker_profiles()
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))

    all_quotes = []
    topics_set = set()
    speakers_count = 0
    quote_count = 0

    print(f"Exporting {len(files)} speaker files to React-ready JSON...")
    print("=" * 60)

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            quotes = json.load(f)

        if not quotes:
            continue

        speakers_count += 1
        speaker_name = quotes[0].get("speaker", filepath.stem.replace("_", " "))
        profile = profiles.get(speaker_name, {})

        for qi, quote in enumerate(quotes):
            quote_count += 1

            # Generate unique ID
            quote_id = f"{slugify(speaker_name)}-{qi + 1}"

            # Get topics
            topics = quote.get("topics", [])
            primary_topic = topics[0] if topics else "General"
            for t in topics:
                topics_set.add(t)

            # Normalize vocabulary
            vocabulary = normalize_vocabulary(
                quote.get("vocabulary_highlights", []),
                quote.get("vocabulary", None)
            )

            # Build the React-ready quote object
            react_quote = {
                "id": quote_id,
                "speaker": speaker_name,
                "role": profile.get("role", quote.get("speaker_function", "Guest")),
                "company": profile.get("company", ""),
                "speaker_function": quote.get("speaker_function", profile.get("function", "Unknown")),
                "speaker_expertise": quote.get("speaker_expertise", profile.get("expertise", [])),
                "topic": primary_topic,
                "topics": topics,
                "text": quote.get("text", ""),
                "text_ko": quote.get("text_ko", ""),
                "text_zh": quote.get("text_zh", ""),
                "text_es": quote.get("text_es", ""),
                "fullContext": quote.get("context", ""),
                "vocabulary": vocabulary,
                "difficulty_level": quote.get("difficulty_level", "Intermediate"),
                "timestamp": quote.get("timestamp", "")
            }

            all_quotes.append(react_quote)

    # Sort by speaker name then by ID for consistency
    all_quotes.sort(key=lambda q: (q["speaker"], q["id"]))

    # Ensure output directory exists
    os.makedirs(REACT_OUTPUT_DIR, exist_ok=True)

    # Write the combined JSON
    with open(REACT_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_quotes, f, indent=2, ensure_ascii=False)

    # Print summary
    functions = set(q["speaker_function"] for q in all_quotes)
    difficulties = set(q["difficulty_level"] for q in all_quotes)
    vocab_count = sum(len(q["vocabulary"]) for q in all_quotes)
    has_translations = sum(1 for q in all_quotes if q["text_ko"])
    has_enriched_vocab = sum(1 for q in all_quotes if any(v.get("definition") for v in q["vocabulary"]))
    has_insights = sum(1 for q in all_quotes if any(v.get("insight") for v in q["vocabulary"]))

    print("\n" + "=" * 60)
    print(f"Export complete! {REACT_OUTPUT_FILE}")
    print(f"  Speakers:           {speakers_count}")
    print(f"  Quotes:             {quote_count}")
    print(f"  Vocabulary terms:   {vocab_count}")
    print(f"  Topics:             {len(topics_set)}")
    print(f"  Functions:          {', '.join(sorted(functions))}")
    print(f"  Difficulties:       {', '.join(sorted(difficulties))}")
    print(f"  With translations:  {has_translations}")
    print(f"  With enriched vocab:{has_enriched_vocab}")
    print(f"  With AI insights:   {has_insights}")
    print(f"\nTopics: {', '.join(sorted(topics_set))}")


if __name__ == "__main__":
    main()
