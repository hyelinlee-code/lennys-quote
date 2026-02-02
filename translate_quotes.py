import os
import json
import time
from pathlib import Path
from anthropic import Anthropic


LANGUAGES = {
    "ko": "Korean",
    "zh": "Chinese Simplified",
    "es": "Spanish"
}

BATCH_SIZE = 5


TRANSLATION_PROMPTS = {
    "ko": """Translate this English business quote into natural, conversational Korean that Korean business professionals actually use.

CRITICAL RULES:
- Use natural spoken Korean (구어체), not stiff/formal written Korean
- Use -요/-해요 ending for casual professional tone
- Avoid literal word-for-word translation (번역투 금지)
- For English jargon or technical terms, keep the English in parentheses after Korean. Example: "호기심 루프(curiosity loop)"
- Use natural Korean expressions and idioms
- Think: How would a Korean person naturally say this in a business conversation?

Examples of natural style:
- 'it's bad because' → '나쁜 이유는' (NOT '이것이 나쁜 이유는')
- 'well-intentioned' → '악의가 있어서가 아니라' (NOT '선의가 없어서가 아니라')
- 'contextual' → '맥락이 없어서' (NOT '맥락적이지 않기 때문에')
- 'sit tight and grind' → '버티면서' (natural Korean phrase)

Quote to translate:
{text}

Return ONLY the Korean translation, nothing else.""",

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


def get_translation_prompt(text: str, language_code: str) -> str:
    """Generate translation prompt for a single text based on language."""
    prompt_template = TRANSLATION_PROMPTS.get(language_code)
    if prompt_template:
        return prompt_template.format(text=text)
    else:
        # Fallback for unknown languages
        return f"Translate this to {language_code}: {text}"


def translate_batch(client: Anthropic, texts: list[str], language_code: str) -> list[str]:
    """Translate a batch of texts to a single language."""
    translations = []
    
    for text in texts:
        prompt = get_translation_prompt(text, language_code)
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        translation = message.content[0].text.strip()
        translations.append(translation)
    
    return translations


def translate_quotes_in_file(client: Anthropic, quotes: list, filename: str) -> tuple[list, int]:
    """Translate all quotes in a file to all languages."""
    total_quotes = len(quotes)
    translated_count = 0
    
    # Process in batches
    for batch_start in range(0, total_quotes, BATCH_SIZE):
        batch_end = min(batch_start + BATCH_SIZE, total_quotes)
        batch_quotes = quotes[batch_start:batch_end]
        
        # Get texts to translate from this batch
        texts_to_translate = [q["text"] for q in batch_quotes]
        
        # Translate to each language
        for lang_code in LANGUAGES.keys():
            field_name = f"text_{lang_code}"
            
            # Translate batch
            translations = translate_batch(client, texts_to_translate, lang_code)
            
            # Add translations to quotes
            for i, translation in enumerate(translations):
                quotes[batch_start + i][field_name] = translation
            
            # Delay between language API calls
            time.sleep(2)
        
        translated_count += len(batch_quotes)
        print(f"  Translating {filename}: {translated_count}/{total_quotes} quotes")
    
    return quotes, translated_count


def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    
    # Initialize Anthropic client
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Get all *_quotes.json files
    quote_files = sorted(output_dir.glob("*_quotes.json"))
    
    if not quote_files:
        print("No *_quotes.json files found in output/ folder.")
        return
    
    print(f"Found {len(quote_files)} quote file(s) to translate.\n")
    
    # Track statistics
    total_quotes_translated = 0
    errors = []
    
    # Process each file
    for file_path in quote_files:
        filename = file_path.name
        print(f"\nProcessing {filename}...")
        
        try:
            # Load quotes
            with open(file_path, "r", encoding="utf-8") as f:
                quotes = json.load(f)
            
            # Translate quotes
            quotes, count = translate_quotes_in_file(client, quotes, filename)
            total_quotes_translated += count
            
            # Save updated quotes back to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(quotes, f, indent=2, ensure_ascii=False)
            
            print(f"  -> Saved translations to {filename}")
            
        except Exception as e:
            error_msg = f"{filename}: {str(e)}"
            errors.append(error_msg)
            print(f"  -> ERROR: {str(e)}")
    
    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total quotes translated: {total_quotes_translated}")
    print(f"Total languages: {len(LANGUAGES)} (ko, zh, es)")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nNo errors encountered!")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
