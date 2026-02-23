"""
Regenerate Translations for Trimmed Quotes

Regenerates translations (text_ko, text_zh, text_es) for quotes where
`text_trimmed: true`. The current translations were generated from the
longer `original_text`, not the trimmed `text`.

Uses OpenAI API (gpt-5-mini) for all translations.

Estimated cost: ~$2-5 for ~1,529 quotes
Uses checkpoint pattern for resumability.
"""

import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load API keys
load_dotenv('.env.local')

OUTPUT_DIR = "output"
CHECKPOINT_FILE = "regenerate_translations_checkpoint.json"

# Model configuration
OPENAI_MODEL = "gpt-5-mini"

# Translation prompts
PROMPTS = {
    "ko": """Translate this English business quote into natural, conversational Korean that Korean professionals actually use. Use -요/-해요 ending. For technical terms/jargon, add English in parentheses like '호기심 루프(curiosity loop)'. Avoid stiff literal translation. Be natural and conversational. Return ONLY the Korean translation.

Quote to translate:
{text}""",

    "zh": """Translate this English business quote into natural, conversational Simplified Chinese that Chinese business professionals actually use.

CRITICAL RULES:
- Use natural spoken Chinese (口语化), not stiff/formal written Chinese
- Avoid literal word-for-word translation (避免翻译腔)
- For English jargon or technical terms, keep the English in parentheses after Chinese. Example: "好奇心循环(curiosity loop)"
- Use natural Chinese expressions and idioms
- Think: How would a Chinese person naturally say this in a business conversation?

Examples of natural style:
- 'it's bad because' → '问题在于' (NOT '这是不好的因为')
- 'well-intentioned' → '不是故意的' or '出发点是好的' (NOT '善意的')
- 'contextual' → '缺乏具体情境' (NOT '上下文相关的')
- 'sit tight and grind' → '坚持下去' or '熬过去' (natural Chinese phrase)

Quote to translate:
{text}

Return ONLY the Chinese translation, nothing else.""",

    "es": """Translate this English business quote into natural, conversational Spanish that Spanish-speaking business professionals actually use.

CRITICAL RULES:
- Use natural spoken Spanish, not stiff/formal written Spanish
- Use a professional but approachable tone (tú/usted as appropriate for business)
- Avoid literal word-for-word translation
- For English jargon or technical terms, keep the English in parentheses after Spanish. Example: "bucle de curiosidad (curiosity loop)"
- Use natural Spanish expressions and idioms
- Think: How would a Spanish speaker naturally say this in a business conversation?

Examples of natural style:
- 'it's bad because' → 'el problema es que' (NOT 'es malo porque')
- 'well-intentioned' → 'con buenas intenciones' or 'no es mala fe' (natural phrasing)
- 'contextual' → 'depende del contexto' or 'sin contexto' (NOT 'contextual')
- 'sit tight and grind' → 'aguantar y seguir adelante' (natural Spanish phrase)

Quote to translate:
{text}

Return ONLY the Spanish translation, nothing else."""
}


def load_checkpoint() -> dict:
    """Load checkpoint with processed quotes."""
    if Path(CHECKPOINT_FILE).exists():
        with open(CHECKPOINT_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "processed_quotes": {},  # {filename: [indices]}
        "stats": {"total_regenerated": 0}
    }


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w", encoding="utf-8") as f:
        json.dump(checkpoint, f, indent=2)


def translate_with_openai(client: OpenAI, text: str, lang_code: str) -> str:
    """Translate text using OpenAI API."""
    prompt_template = PROMPTS.get(lang_code)
    if not prompt_template:
        raise ValueError(f"Unknown language code: {lang_code}")

    prompt = prompt_template.format(text=text)

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_completion_tokens=2000
    )

    return response.choices[0].message.content.strip()


def find_trimmed_quotes() -> list[tuple[Path, int, dict]]:
    """
    Find all quotes with text_trimmed=True.
    Returns list of (filepath, quote_index, quote) tuples.
    """
    trimmed_quotes = []
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            quotes = json.load(f)

        for idx, quote in enumerate(quotes):
            if quote.get("text_trimmed"):
                trimmed_quotes.append((filepath, idx, quote))

    return trimmed_quotes


def main():
    checkpoint = load_checkpoint()
    processed_quotes = checkpoint.get("processed_quotes", {})
    stats = checkpoint.get("stats", {"total_regenerated": 0})

    # Initialize API client
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    print("=" * 60)
    print("Regenerate Translations for Trimmed Quotes")
    print("=" * 60)
    print(f"Using: OpenAI {OPENAI_MODEL} for all languages (ko, zh, es)")
    print()

    # Find all trimmed quotes
    trimmed_quotes = find_trimmed_quotes()
    total_trimmed = len(trimmed_quotes)
    print(f"Found {total_trimmed} quotes with text_trimmed=True")

    # Filter out already processed
    quotes_to_process = []
    for filepath, idx, quote in trimmed_quotes:
        filename = filepath.name
        processed_indices = set(processed_quotes.get(filename, []))
        if idx not in processed_indices:
            quotes_to_process.append((filepath, idx, quote))

    already_done = total_trimmed - len(quotes_to_process)
    print(f"Already processed: {already_done}")
    print(f"Remaining: {len(quotes_to_process)}")
    print()

    if not quotes_to_process:
        print("All trimmed quotes already processed!")
        return

    # Group by file for efficient saving
    quotes_by_file = {}
    for filepath, idx, quote in quotes_to_process:
        if filepath not in quotes_by_file:
            quotes_by_file[filepath] = []
        quotes_by_file[filepath].append((idx, quote))

    # Process each file
    regenerated_this_run = 0

    for filepath, quote_list in quotes_by_file.items():
        filename = filepath.name
        speaker = filename.replace("_quotes.json", "").replace("_", " ")

        # Load full file
        with open(filepath, "r", encoding="utf-8") as f:
            all_quotes = json.load(f)

        print(f"\n{speaker} ({len(quote_list)} quotes to regenerate)")

        for idx, quote in quote_list:
            text = quote.get("text", "")
            print(f"  [{idx+1}] Translating...", end=" ", flush=True)

            try:
                # Regenerate all three translations using OpenAI
                text_ko = translate_with_openai(openai_client, text, "ko")
                time.sleep(0.3)

                text_zh = translate_with_openai(openai_client, text, "zh")
                time.sleep(0.3)

                text_es = translate_with_openai(openai_client, text, "es")
                time.sleep(0.3)

                # Update quote in full list
                all_quotes[idx]["text_ko"] = text_ko
                all_quotes[idx]["text_zh"] = text_zh
                all_quotes[idx]["text_es"] = text_es
                all_quotes[idx]["translations_regenerated"] = True

                # Track in checkpoint
                if filename not in processed_quotes:
                    processed_quotes[filename] = []
                processed_quotes[filename].append(idx)

                stats["total_regenerated"] += 1
                regenerated_this_run += 1

                print("done")

                # Save file and checkpoint after each quote
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(all_quotes, f, indent=2, ensure_ascii=False)

                checkpoint["processed_quotes"] = processed_quotes
                checkpoint["stats"] = stats
                save_checkpoint(checkpoint)

            except Exception as e:
                print(f"ERROR: {e}")
                # Continue to next quote

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Translations regenerated this run: {regenerated_this_run}")
    print(f"Total regenerated (all runs):      {stats['total_regenerated']}")
    print()
    print("Next step: Run export_for_react.py")


if __name__ == "__main__":
    main()
