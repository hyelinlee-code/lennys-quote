import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from anthropic import Anthropic

# Load API keys from .env.local file
load_dotenv('.env.local')

# Model configurations
OPENAI_MODEL = "gpt-5-mini"
ANTHROPIC_MODEL = "claude-sonnet-4-20250514"

# Language configurations
KOREAN_PROMPT = """Translate this English business quote into natural, conversational Korean that Korean professionals actually use. Use -요/-해요 ending. For technical terms/jargon, add English in parentheses like '호기심 루프(curiosity loop)'. Avoid stiff literal translation. Be natural and conversational. Return ONLY the Korean translation.

Quote to translate:
{text}"""

CLAUDE_PROMPTS = {
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


def translate_to_korean_openai(openai_client: OpenAI, text: str) -> str:
    """Translate text to Korean using OpenAI API."""
    prompt = KOREAN_PROMPT.format(text=text)
    
    response = openai_client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_completion_tokens=2000
    )
    
    return response.choices[0].message.content.strip()


def translate_with_claude(anthropic_client: Anthropic, text: str, lang_code: str) -> str:
    """Translate text to Chinese or Spanish using Claude API."""
    prompt_template = CLAUDE_PROMPTS.get(lang_code)
    if not prompt_template:
        raise ValueError(f"Unknown language code: {lang_code}")
    
    prompt = prompt_template.format(text=text)
    
    message = anthropic_client.messages.create(
        model=ANTHROPIC_MODEL,
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )
    
    return message.content[0].text.strip()


def translate_quotes_in_file(
    openai_client: OpenAI,
    anthropic_client: Anthropic,
    quotes: list,
    filename: str
) -> tuple[list, int]:
    """Translate all quotes in a file using hybrid approach."""
    total_quotes = len(quotes)
    
    for idx, quote in enumerate(quotes, start=1):
        text = quote["text"]
        
        # Translate to Korean using OpenAI
        quote["text_ko"] = translate_to_korean_openai(openai_client, text)
        time.sleep(2)
        
        # Translate to Chinese using Claude
        quote["text_zh"] = translate_with_claude(anthropic_client, text, "zh")
        time.sleep(2)
        
        # Translate to Spanish using Claude
        quote["text_es"] = translate_with_claude(anthropic_client, text, "es")
        time.sleep(2)
        
        print(f"  Translating {filename}: {idx}/{total_quotes} quotes")
    
    return quotes, total_quotes


def main():
    base_dir = Path(__file__).parent
    output_dir = base_dir / "output"
    
    # Initialize API clients
    openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    anthropic_client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Get all *_quotes.json files
    quote_files = sorted(output_dir.glob("*_quotes.json"))
    
    if not quote_files:
        print("No *_quotes.json files found in output/ folder.")
        return
    
    print(f"Found {len(quote_files)} quote file(s) to translate.")
    print(f"Using: Korean (OpenAI {OPENAI_MODEL}), Chinese/Spanish (Claude {ANTHROPIC_MODEL})\n")
    
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
            quotes, count = translate_quotes_in_file(
                openai_client, anthropic_client, quotes, filename
            )
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
    print(f"Languages: ko (OpenAI), zh (Claude), es (Claude)")
    
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nNo errors encountered!")
    
    print("=" * 50)


if __name__ == "__main__":
    main()
