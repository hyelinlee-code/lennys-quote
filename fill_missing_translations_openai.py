"""
Fill missing translations in quote files using OpenAI GPT-4o-mini
"""

import os
import json
import glob
import time
from datetime import datetime
from dotenv import load_dotenv

from openai import OpenAI

# Load environment variables
load_dotenv('.env.local')

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Model configuration
MODEL = "gpt-4o-mini"
TEMPERATURE = 0.3
MAX_TOKENS = 500

# File paths
OUTPUT_DIR = "output"

# Rate limit delay (seconds)
RATE_LIMIT_DELAY = 1

# Cost per 1M tokens for GPT-4o-mini
COST_PER_1M_INPUT_TOKENS = 0.15
COST_PER_1M_OUTPUT_TOKENS = 0.60

# Translation prompts
PROMPTS = {
    "text_ko": """Translate this English business quote into natural, conversational Korean that Korean professionals actually use. Use -요/-해요 ending. For technical terms/jargon, add English in parentheses like '호기심 루프(curiosity loop)'. Avoid stiff literal translation. Be natural and conversational. Return ONLY the Korean translation.""",
    
    "text_zh": """Translate this English business quote into natural, professional Simplified Chinese that Chinese business professionals actually use. For technical terms/jargon, add English in parentheses. Avoid overly literal translation. Return ONLY the Chinese translation.""",
    
    "text_es": """Translate this English business quote into natural, professional Spanish that Latin American business professionals actually use. For technical terms/jargon, add English in parentheses. Avoid overly literal translation. Return ONLY the Spanish translation."""
}

LANGUAGE_NAMES = {
    "text_ko": "Korean",
    "text_zh": "Chinese",
    "text_es": "Spanish"
}


def is_missing_translation(quote, field):
    """Check if a translation field is missing or empty."""
    if field not in quote:
        return True
    value = quote[field]
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def translate_text(english_text, language_field):
    """Translate text using OpenAI GPT-4o-mini."""
    prompt = PROMPTS[language_field]
    
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": prompt
            },
            {
                "role": "user",
                "content": english_text
            }
        ],
        temperature=TEMPERATURE,
        max_tokens=MAX_TOKENS
    )
    
    translation = response.choices[0].message.content.strip()
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    
    return translation, input_tokens, output_tokens


def process_quote_file(filepath):
    """Process a single quote file and fill missing translations."""
    # Load quotes
    with open(filepath, 'r', encoding='utf-8') as f:
        quotes = json.load(f)
    
    # Track statistics
    stats = {
        "quotes_checked": len(quotes),
        "text_ko_added": 0,
        "text_zh_added": 0,
        "text_es_added": 0,
        "api_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "translations_needed": 0
    }
    
    # Count missing translations first
    missing_counts = {"text_ko": 0, "text_zh": 0, "text_es": 0}
    for quote in quotes:
        for field in ["text_ko", "text_zh", "text_es"]:
            if is_missing_translation(quote, field):
                missing_counts[field] += 1
                stats["translations_needed"] += 1
    
    # Process each quote
    for quote_idx, quote in enumerate(quotes):
        english_text = quote.get("text", "")
        
        if not english_text:
            continue
        
        for field in ["text_ko", "text_zh", "text_es"]:
            if is_missing_translation(quote, field):
                try:
                    # Translate
                    translation, input_tokens, output_tokens = translate_text(english_text, field)
                    
                    # Update quote
                    quote[field] = translation
                    
                    # Update stats
                    stats[f"{field}_added"] += 1
                    stats["api_calls"] += 1
                    stats["input_tokens"] += input_tokens
                    stats["output_tokens"] += output_tokens
                    
                    # Rate limit delay
                    time.sleep(RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    print(f"    Error translating to {LANGUAGE_NAMES[field]}: {e}")
    
    # Save updated quotes
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    
    return stats, missing_counts


def get_quote_files():
    """Get all quote JSON files from output directory."""
    pattern = os.path.join(OUTPUT_DIR, "*_quotes.json")
    return sorted(glob.glob(pattern))


def main():
    """Main function to fill missing translations."""
    print("=" * 70)
    print("Filling Missing Translations with GPT-4o-mini")
    print("=" * 70)
    
    # Get all quote files
    quote_files = get_quote_files()
    print(f"\nFound {len(quote_files)} quote files in {OUTPUT_DIR}/\n")
    
    # Statistics
    start_time = datetime.now()
    total_stats = {
        "files_processed": 0,
        "quotes_checked": 0,
        "text_ko_added": 0,
        "text_zh_added": 0,
        "text_es_added": 0,
        "api_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0
    }
    
    files_with_missing = []
    
    # First pass: count missing translations
    print("Scanning for missing translations...\n")
    for filepath in quote_files:
        filename = os.path.basename(filepath)
        
        with open(filepath, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        
        missing = 0
        for quote in quotes:
            for field in ["text_ko", "text_zh", "text_es"]:
                if is_missing_translation(quote, field):
                    missing += 1
        
        if missing > 0:
            files_with_missing.append((filepath, filename, len(quotes), missing))
    
    if not files_with_missing:
        print("All translations are complete! Nothing to do.")
        return
    
    print(f"Found {len(files_with_missing)} files with missing translations\n")
    print("-" * 70)
    
    # Process files with missing translations
    for filepath, filename, quote_count, missing_count in files_with_missing:
        print(f"\n{filename}: {missing_count // 3 if missing_count % 3 == 0 else missing_count}/{quote_count} quotes need translations ({missing_count} total)")
        
        try:
            stats, missing_counts = process_quote_file(filepath)
            
            # Update totals
            total_stats["files_processed"] += 1
            total_stats["quotes_checked"] += stats["quotes_checked"]
            total_stats["text_ko_added"] += stats["text_ko_added"]
            total_stats["text_zh_added"] += stats["text_zh_added"]
            total_stats["text_es_added"] += stats["text_es_added"]
            total_stats["api_calls"] += stats["api_calls"]
            total_stats["input_tokens"] += stats["input_tokens"]
            total_stats["output_tokens"] += stats["output_tokens"]
            
            # Show what was added
            added = []
            if stats["text_ko_added"] > 0:
                added.append(f"KO:{stats['text_ko_added']}")
            if stats["text_zh_added"] > 0:
                added.append(f"ZH:{stats['text_zh_added']}")
            if stats["text_es_added"] > 0:
                added.append(f"ES:{stats['text_es_added']}")
            
            if added:
                print(f"  ✓ Added: {', '.join(added)}")
            else:
                print(f"  ✓ Complete")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split('.')[0]
    
    # Calculate cost
    input_cost = (total_stats["input_tokens"] / 1_000_000) * COST_PER_1M_INPUT_TOKENS
    output_cost = (total_stats["output_tokens"] / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
    total_cost = input_cost + output_cost
    
    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Files processed:          {total_stats['files_processed']}")
    print(f"Quotes checked:           {total_stats['quotes_checked']}")
    print(f"Korean translations:      {total_stats['text_ko_added']}")
    print(f"Chinese translations:     {total_stats['text_zh_added']}")
    print(f"Spanish translations:     {total_stats['text_es_added']}")
    print(f"Total API calls:          {total_stats['api_calls']}")
    print(f"Input tokens:             {total_stats['input_tokens']:,}")
    print(f"Output tokens:            {total_stats['output_tokens']:,}")
    print(f"Approximate cost:         ${total_cost:.4f}")
    print(f"Time elapsed:             {elapsed_str}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
