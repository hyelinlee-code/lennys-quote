"""
Validate Data Quality

Runs quality checks on all quote data after enrichment:
1. All quotes have `text` ≤45 words
2. All vocabulary items have non-empty definitions
3. key_sentence appears in text (or has high word overlap)
4. All speakers have job_title in profiles

Outputs a summary report with issues found.
"""

import json
import os
import re
from pathlib import Path

OUTPUT_DIR = "output"
SPEAKER_PROFILES = "speaker_profiles.json"
MAX_WORDS = 45
OVERLAP_THRESHOLD = 0.6


def count_words(text: str) -> int:
    """Count words in text."""
    return len(text.split())


def normalize_text(text: str) -> set[str]:
    """Normalize text to set of lowercase words."""
    text = re.sub(r'[^\w\s]', '', text.lower())
    return set(text.split())


def calculate_overlap(key_sentence: str, full_text: str) -> float:
    """Calculate word overlap ratio."""
    key_words = normalize_text(key_sentence)
    text_words = normalize_text(full_text)
    if not key_words:
        return 0.0
    overlap = key_words.intersection(text_words)
    return len(overlap) / len(key_words)


def check_verbatim(key_sentence: str, full_text: str) -> bool:
    """Check if key_sentence is verbatim in text."""
    key_norm = re.sub(r'\s+', ' ', key_sentence.lower().strip())
    text_norm = re.sub(r'\s+', ' ', full_text.lower().strip())
    key_no_punct = re.sub(r'[^\w\s]', '', key_norm)
    text_no_punct = re.sub(r'[^\w\s]', '', text_norm)
    return key_no_punct in text_no_punct


def validate_quotes():
    """Validate all quote files."""
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))

    issues = {
        "text_too_long": [],
        "missing_vocab_definition": [],
        "key_sentence_mismatch": [],
        "missing_key_sentence": [],
    }

    total_quotes = 0
    total_vocab = 0

    for filepath in files:
        with open(filepath, "r", encoding="utf-8") as f:
            quotes = json.load(f)

        speaker = filepath.stem.replace("_quotes", "").replace("_", " ")

        for qi, quote in enumerate(quotes):
            total_quotes += 1
            quote_id = f"{speaker}[{qi}]"
            text = quote.get("text", "")

            # Check 1: Text length
            word_count = count_words(text)
            if word_count > MAX_WORDS:
                issues["text_too_long"].append({
                    "quote": quote_id,
                    "words": word_count,
                    "text": text[:100] + "..."
                })

            # Check 2: Vocabulary definitions
            vocabulary = quote.get("vocabulary", [])
            for v in vocabulary:
                total_vocab += 1
                if isinstance(v, dict):
                    if not v.get("definition"):
                        issues["missing_vocab_definition"].append({
                            "quote": quote_id,
                            "word": v.get("word", "unknown")
                        })

            # Check 3: Key sentence
            key_sentence = quote.get("key_sentence", "")
            if not key_sentence:
                issues["missing_key_sentence"].append({
                    "quote": quote_id
                })
            elif text:
                is_verbatim = check_verbatim(key_sentence, text)
                if not is_verbatim:
                    overlap = calculate_overlap(key_sentence, text)
                    if overlap < OVERLAP_THRESHOLD:
                        issues["key_sentence_mismatch"].append({
                            "quote": quote_id,
                            "overlap": f"{overlap:.0%}",
                            "key": key_sentence[:50] + "..."
                        })

    return issues, total_quotes, total_vocab


def validate_speaker_profiles():
    """Validate speaker profiles."""
    if not os.path.exists(SPEAKER_PROFILES):
        return {"missing_job_title": ["File not found"]}, 0

    with open(SPEAKER_PROFILES, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    missing_titles = []
    for speaker, data in profiles.items():
        if not data.get("job_title"):
            missing_titles.append(speaker)

    return {"missing_job_title": missing_titles}, len(profiles)


def main():
    print("=" * 60)
    print("Data Quality Validation Report")
    print("=" * 60)

    # Validate quotes
    quote_issues, total_quotes, total_vocab = validate_quotes()

    print(f"\nQuotes Analyzed: {total_quotes}")
    print(f"Vocabulary Items: {total_vocab}")
    print("-" * 40)

    # Report issues
    print("\n1. TEXT LENGTH (>{} words):".format(MAX_WORDS))
    if quote_issues["text_too_long"]:
        print(f"   Issues: {len(quote_issues['text_too_long'])}")
        for issue in quote_issues["text_too_long"][:5]:
            print(f"   - {issue['quote']}: {issue['words']} words")
        if len(quote_issues["text_too_long"]) > 5:
            print(f"   ... and {len(quote_issues['text_too_long']) - 5} more")
    else:
        print("   All quotes within limit")

    print("\n2. MISSING VOCABULARY DEFINITIONS:")
    if quote_issues["missing_vocab_definition"]:
        print(f"   Issues: {len(quote_issues['missing_vocab_definition'])}")
        for issue in quote_issues["missing_vocab_definition"][:5]:
            print(f"   - {issue['quote']}: '{issue['word']}'")
        if len(quote_issues["missing_vocab_definition"]) > 5:
            print(f"   ... and {len(quote_issues['missing_vocab_definition']) - 5} more")
    else:
        print("   All vocabulary items have definitions")

    print("\n3. KEY SENTENCE MISMATCHES (<{}% overlap):".format(int(OVERLAP_THRESHOLD * 100)))
    if quote_issues["key_sentence_mismatch"]:
        print(f"   Issues: {len(quote_issues['key_sentence_mismatch'])}")
        for issue in quote_issues["key_sentence_mismatch"][:5]:
            print(f"   - {issue['quote']}: {issue['overlap']} overlap")
        if len(quote_issues["key_sentence_mismatch"]) > 5:
            print(f"   ... and {len(quote_issues['key_sentence_mismatch']) - 5} more")
    else:
        print("   All key sentences are verbatim or have sufficient overlap")

    print("\n4. MISSING KEY SENTENCES:")
    if quote_issues["missing_key_sentence"]:
        print(f"   Issues: {len(quote_issues['missing_key_sentence'])}")
        for issue in quote_issues["missing_key_sentence"][:5]:
            print(f"   - {issue['quote']}")
    else:
        print("   All quotes have key sentences")

    # Validate speaker profiles
    profile_issues, total_speakers = validate_speaker_profiles()

    print(f"\n5. SPEAKER JOB TITLES ({total_speakers} speakers):")
    if profile_issues["missing_job_title"]:
        print(f"   Missing: {len(profile_issues['missing_job_title'])}")
        for speaker in profile_issues["missing_job_title"][:10]:
            print(f"   - {speaker}")
        if len(profile_issues["missing_job_title"]) > 10:
            print(f"   ... and {len(profile_issues['missing_job_title']) - 10} more")
    else:
        print("   All speakers have job titles")

    # Summary
    print("\n" + "=" * 60)
    total_issues = (
        len(quote_issues["text_too_long"]) +
        len(quote_issues["missing_vocab_definition"]) +
        len(quote_issues["key_sentence_mismatch"]) +
        len(quote_issues["missing_key_sentence"]) +
        len(profile_issues["missing_job_title"])
    )

    if total_issues == 0:
        print("All checks passed! Data quality is good.")
    else:
        print(f"Total Issues Found: {total_issues}")
        print("\nRecommended Actions:")
        if quote_issues["text_too_long"]:
            print("  - Run trim_long_quotes.py to fix long quotes")
        if quote_issues["missing_vocab_definition"]:
            print("  - Run enrich_vocabulary_insights.py to add definitions")
        if quote_issues["key_sentence_mismatch"] or quote_issues["missing_key_sentence"]:
            print("  - Run audit_key_sentences.py to fix key sentences")
        if profile_issues["missing_job_title"]:
            print("  - Run enrich_speaker_titles.py to add job titles")


if __name__ == "__main__":
    main()
