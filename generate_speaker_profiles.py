"""
Generate speaker profiles from transcripts using GPT-4o-mini
"""

import os
import json
import time
import re
import glob
from datetime import datetime
from dotenv import load_dotenv

from openai import OpenAI

# Load environment variables
load_dotenv('.env.local')

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Model configuration
MODEL = "gpt-4o-mini"

# Paths
OUTPUT_DIR = "output"
TRANSCRIPTS_DIR = "transcripts"
EXISTING_PROFILES_FILE = "speaker_profiles.json"
GENERATED_PROFILES_FILE = "speaker_profiles_generated.json"

# Rate limit delay (seconds)
RATE_LIMIT_DELAY = 1

# How many characters to read from transcript
TRANSCRIPT_CHARS = 3000

# Analysis prompt
ANALYSIS_PROMPT = """Analyze this podcast transcript excerpt and identify the guest speaker's professional background.

Based on the content, determine:
1. Their primary function/role category
2. Their areas of expertise (3 items max)

Return ONLY a JSON object in this exact format:
{
  "function": "<one of: Product|Engineering|Design|Marketing|Sales|Growth|Operations|Leadership|Finance|Data|HR|Legal|Consulting>",
  "expertise": ["expertise1", "expertise2", "expertise3"]
}

Guidelines for function:
- Product: Product managers, product leaders
- Engineering: Software engineers, CTOs, technical leaders
- Design: UX/UI designers, design leaders
- Marketing: Marketing, brand, communications
- Sales: Sales leaders, account executives
- Growth: Growth marketers, growth product managers
- Operations: COOs, operations leaders
- Leadership: CEOs, founders, general executives
- Finance: CFOs, investors, VCs
- Data: Data scientists, analysts
- HR: People ops, talent, HR leaders
- Consulting: Coaches, consultants, advisors

Guidelines for expertise:
- Be specific (e.g., "B2B SaaS Growth" not just "Growth")
- Include industry focus if clear (e.g., "Marketplace Strategy")
- Include frameworks/methods they're known for

Return ONLY the JSON object, no other text."""


def load_existing_profiles():
    """Load existing speaker profiles."""
    if os.path.exists(EXISTING_PROFILES_FILE):
        with open(EXISTING_PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def get_speakers_from_quotes():
    """Extract all unique speaker names from quote files."""
    speakers = set()
    quote_files = glob.glob(os.path.join(OUTPUT_DIR, "*_quotes.json"))
    
    for filepath in quote_files:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                quotes = json.load(f)
                for quote in quotes:
                    if 'speaker' in quote:
                        speakers.add(quote['speaker'])
        except Exception as e:
            print(f"Warning: Could not read {filepath}: {e}")
    
    return speakers


def find_transcript_file(speaker_name):
    """Find the transcript file for a given speaker name."""
    # Convert speaker name to potential filename
    # "Brian Balfour" -> "Brian_Balfour.txt"
    filename = speaker_name.replace(" ", "_") + ".txt"
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # Try variations
    # Handle special characters
    clean_name = re.sub(r'[^\w\s]', '', speaker_name)
    filename = clean_name.replace(" ", "_") + ".txt"
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    
    if os.path.exists(filepath):
        return filepath
    
    # Search for partial matches
    search_pattern = speaker_name.split()[0] + "_" + speaker_name.split()[-1]
    for file in os.listdir(TRANSCRIPTS_DIR):
        if search_pattern.lower() in file.lower():
            return os.path.join(TRANSCRIPTS_DIR, file)
    
    return None


def read_transcript_excerpt(filepath, max_chars=TRANSCRIPT_CHARS):
    """Read the first N characters of a transcript."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read(max_chars)


def analyze_speaker(speaker_name, transcript_excerpt):
    """Use GPT-4o-mini to analyze speaker profile."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": ANALYSIS_PROMPT
            },
            {
                "role": "user",
                "content": f"Speaker: {speaker_name}\n\nTranscript excerpt:\n{transcript_excerpt}"
            }
        ],
        temperature=0.3,
        max_tokens=256
    )
    
    response_text = response.choices[0].message.content.strip()
    
    # Extract JSON from response
    if response_text.startswith("```"):
        response_text = re.sub(r'^```(?:json)?\s*\n?', '', response_text)
        response_text = re.sub(r'\n?```\s*$', '', response_text)
    
    # Find JSON object
    start_idx = response_text.find('{')
    end_idx = response_text.rfind('}')
    
    if start_idx != -1 and end_idx != -1:
        json_str = response_text[start_idx:end_idx + 1]
        return json.loads(json_str)
    
    return json.loads(response_text)


def main():
    """Main function to generate speaker profiles."""
    print("=" * 60)
    print("Generating Speaker Profiles with GPT-4o-mini")
    print("=" * 60)
    
    # Load existing profiles
    existing_profiles = load_existing_profiles()
    print(f"\nExisting profiles: {len(existing_profiles)}")
    
    # Get all speakers from quote files
    all_speakers = get_speakers_from_quotes()
    print(f"Total speakers in quotes: {len(all_speakers)}")
    
    # Find speakers without profiles
    new_speakers = [s for s in all_speakers if s not in existing_profiles]
    print(f"New speakers to analyze: {len(new_speakers)}")
    
    if not new_speakers:
        print("\nNo new speakers to analyze. Done!")
        return
    
    # Statistics
    start_time = datetime.now()
    generated_profiles = {}
    processed = 0
    skipped = []
    failed = []
    
    print(f"\nProcessing {len(new_speakers)} speakers...\n")
    
    for idx, speaker in enumerate(sorted(new_speakers), 1):
        print(f"[{idx}/{len(new_speakers)}] {speaker}...", end=" ", flush=True)
        
        # Find transcript file
        transcript_path = find_transcript_file(speaker)
        
        if not transcript_path:
            print("SKIPPED - No transcript found")
            skipped.append(speaker)
            continue
        
        try:
            # Read transcript excerpt
            excerpt = read_transcript_excerpt(transcript_path)
            
            # Analyze with GPT
            profile = analyze_speaker(speaker, excerpt)
            
            # Validate profile
            if 'function' in profile and 'expertise' in profile:
                generated_profiles[speaker] = profile
                processed += 1
                print(f"OK - {profile['function']}")
            else:
                print("FAILED - Invalid response format")
                failed.append((speaker, "Invalid response format"))
                
        except json.JSONDecodeError as e:
            print(f"FAILED - JSON error: {e}")
            failed.append((speaker, f"JSON error: {e}"))
            
        except Exception as e:
            print(f"FAILED - {e}")
            failed.append((speaker, str(e)))
        
        # Rate limit delay
        if idx < len(new_speakers):
            time.sleep(RATE_LIMIT_DELAY)
    
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split('.')[0]
    
    # Merge with existing profiles for output
    all_profiles = {**existing_profiles, **generated_profiles}
    
    # Save generated profiles
    with open(GENERATED_PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_profiles, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Speakers processed:  {processed}")
    print(f"Speakers skipped:    {len(skipped)} (no transcript)")
    print(f"Speakers failed:     {len(failed)}")
    print(f"Total profiles:      {len(all_profiles)}")
    print(f"Time elapsed:        {elapsed_str}")
    print(f"Output file:         {GENERATED_PROFILES_FILE}")
    
    if skipped:
        print(f"\nSkipped speakers (no transcript found):")
        for speaker in skipped[:10]:
            print(f"  - {speaker}")
        if len(skipped) > 10:
            print(f"  ... and {len(skipped) - 10} more")
    
    if failed:
        print(f"\nFailed speakers:")
        for speaker, error in failed[:10]:
            print(f"  - {speaker}: {error}")
        if len(failed) > 10:
            print(f"  ... and {len(failed) - 10} more")
    
    # Show function distribution
    if generated_profiles:
        print("\nFunction distribution (new profiles):")
        functions = {}
        for profile in generated_profiles.values():
            func = profile.get('function', 'Unknown')
            functions[func] = functions.get(func, 0) + 1
        for func, count in sorted(functions.items(), key=lambda x: -x[1]):
            print(f"  {func}: {count}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
