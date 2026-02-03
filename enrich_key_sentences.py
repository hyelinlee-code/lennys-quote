"""
Enrich Key Sentences

For each quote, extracts a short, impactful sentence from the quote text
that contains at least one vocabulary highlight word. Uses OpenAI API
for quality extraction.

Writes `key_sentence` field into each quote in output/*.json files.
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
CHECKPOINT_FILE = "key_sentences_checkpoint.json"
BATCH_SIZE = 10  # Quotes per API call

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint() -> set:
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_checkpoint(processed: set):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(list(processed), f)


def extract_key_sentence_local(text: str, vocab_words: list[str]) -> str:
    """
    Local fallback: split text into sentences and pick the shortest one
    containing a vocabulary word.
    """
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

    matches = []
    for sentence in sentences:
        lower = sentence.lower()
        for word in vocab_words:
            if word.lower() in lower:
                matches.append(sentence)
                break

    if matches:
        return min(matches, key=len)
    return sentences[0] if sentences else text[:150]


def extract_key_sentences_batch(quotes_batch: list[dict]) -> list[str]:
    """
    Use OpenAI to extract the best key sentence from each quote in a batch.
    """
    items = []
    for i, q in enumerate(quotes_batch):
        vocab = q.get("vocabulary_highlights", [])
        if isinstance(vocab, list) and vocab and isinstance(vocab[0], dict):
            vocab = [v.get("word", "") for v in vocab]
        items.append(
            f"Quote {i+1}:\n"
            f"Text: \"{q['text']}\"\n"
            f"Vocabulary words: {vocab}\n"
        )

    prompt = "\n".join(items)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You distill quotes into short key sentences for preview cards. "
                        "Rules:\n"
                        "1. Output must be UNDER 15 WORDS.\n"
                        "2. Must contain at least one of the given vocabulary words.\n"
                        "3. Must capture the core message of the full quote.\n"
                        "4. Remove filler words that start sentences (Well, And, So, "
                        "You know, I think, I mean, Like, Basically, Actually, Right). "
                        "Clean the beginning so the sentence starts strong.\n"
                        "5. It should be a complete, grammatical sentence — not a fragment.\n"
                        "6. You may lightly edit for brevity (trim clauses, remove hedging) "
                        "but keep the speaker's original phrasing for the key idea.\n\n"
                        "Example:\n"
                        "Full quote: \"And it's not bad because it's not well-intentioned, "
                        "but it's bad because it's not contextual. So when someone tells "
                        "you to quit your job...\"\n"
                        "Vocabulary: [\"well-intentioned\", \"contextual\"]\n"
                        "Key sentence: \"It's not bad because it's not well-intentioned, "
                        "but because it's not contextual.\"\n\n"
                        "Return ONLY valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"For each of the {len(quotes_batch)} quotes below, produce "
                        f"a refined key sentence (under 15 words, no filler words, "
                        f"contains a vocabulary word, captures the core message).\n\n"
                        f"{prompt}\n\n"
                        f'Return JSON: {{"sentences": ["sentence1", "sentence2", ...]}}'
                    ),
                },
            ],
            temperature=0,
            max_tokens=3000,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        sentences = result.get("sentences", [])

        # Pad if API returned fewer items than expected
        while len(sentences) < len(quotes_batch):
            idx = len(sentences)
            vocab = quotes_batch[idx].get("vocabulary_highlights", [])
            if isinstance(vocab, list) and vocab and isinstance(vocab[0], dict):
                vocab = [v.get("word", "") for v in vocab]
            sentences.append(
                extract_key_sentence_local(quotes_batch[idx]["text"], vocab)
            )

        return sentences

    except Exception as e:
        print(f"    API error: {e}, using local fallback")
        results = []
        for q in quotes_batch:
            vocab = q.get("vocabulary_highlights", [])
            if isinstance(vocab, list) and vocab and isinstance(vocab[0], dict):
                vocab = [v.get("word", "") for v in vocab]
            results.append(extract_key_sentence_local(q["text"], vocab))
        return results


def process_file(filepath: str) -> bool:
    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    # Skip if already enriched
    if quotes and "key_sentence" in quotes[0]:
        return False

    # Process in batches
    for batch_start in range(0, len(quotes), BATCH_SIZE):
        batch = quotes[batch_start : batch_start + BATCH_SIZE]
        sentences = extract_key_sentences_batch(batch)

        for q, sentence in zip(batch, sentences):
            q["key_sentence"] = sentence

        time.sleep(0.3)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)

    return True


def main():
    processed = load_checkpoint()
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    total = len(files)
    enriched = 0
    skipped = 0

    print(f"Extracting key sentences for {total} files...")
    print(f"Already processed: {len(processed)}")
    print("=" * 60)

    for i, filepath in enumerate(files, 1):
        filename = filepath.name
        if filename in processed:
            skipped += 1
            continue

        speaker = filename.replace("_quotes.json", "").replace("_", " ")
        print(f"[{i}/{total}] {speaker}...", end=" ")

        try:
            modified = process_file(str(filepath))
            if modified:
                enriched += 1
                print("done")
            else:
                print("already has key_sentence")

            processed.add(filename)
            save_checkpoint(processed)

        except Exception as e:
            print(f"ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Done! Key sentences: {enriched} enriched, {skipped} skipped")


if __name__ == "__main__":
    main()
