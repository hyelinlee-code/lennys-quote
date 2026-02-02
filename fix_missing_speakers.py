"""
Fix missing speakers: generate profiles and update quote files
"""

import os
import json
import glob
import time
import re
from datetime import datetime
from dotenv import load_dotenv

from openai import OpenAI

# Load environment variables
load_dotenv('.env.local')

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Model configuration
MODEL = "gpt-4o-mini"

# File paths
PROFILES_FILE = "speaker_profiles.json"
TRANSCRIPTS_DIR = "transcripts"
OUTPUT_DIR = "output"

# Rate limit delay (seconds)
RATE_LIMIT_DELAY = 1

# How many characters to read from transcript
TRANSCRIPT_CHARS = 3000

# List of missing speakers
MISSING_SPEAKERS = [
    "Aarthi Ramamurthy",
    "Aishwarya Naresh Reganti",
    "Alex Hardiman",
    "Andrew 'Boz' Bosworth",
    "Cameron Adams",
    "Chris Miller",
    "Crystal Widjaja",
    "Eeke De Miliano",
    "Georgiana Laudi",
    "Gergely Orosz",
    "Greg Isenberg",
    "Gustaf Alströmer",
    "Inbal Shani",
    "Jason Lemkin",
    "Jessica Lachs",
    "Jiaona Zhang (JZ)",
    "Julie Zhou",
    "Meltem Kuran Berkowitz",
    "Sahil Bloom",
    "Shweta Shrivastava",
    "Sriram Krishnan",
    "Tobi Lütke",
    "Vijay Iyengar",
    "Yuhki Yamashita"
]

# Manual mapping for speakers with non-standard transcript filenames
TRANSCRIPT_MAPPING = {
    "Aarthi Ramamurthy": "Sriram_and_Aarthi.txt",
    "Aishwarya Naresh Reganti": "Aishwarya_Naresh_Reganti_+_Kiriti_Badam.txt",
    "Alex Hardiman": "Alex_Hardimen.txt",
    "Andrew 'Boz' Bosworth": "Boz.txt",
    "Cameron Adams": "Cam_Adams.txt",
    "Chris Miller": "Christopher_Miller.txt",
    "Crystal Widjaja": "Crystal_W.txt",
    "Eeke De Miliano": "Eeke_de_Milliano.txt",
    "Georgiana Laudi": "Gia_Laudi.txt",
    "Gergely Orosz": "Gergely.txt",
    "Gustaf Alströmer": "Gustaf_Alstromer.txt",
    "Inbal Shani": "Inbal_S.txt",
    "Jason Lemkin": "Jason_M_Lemkin.txt",
    "Jessica Lachs": "Jess_Lachs.txt",
    "Jiaona Zhang (JZ)": "Jiaona_Zhang.txt",
    "Julie Zhou": "Julie_Zhuo.txt",
    "Meltem Kuran Berkowitz": "Meltem_Kuran.txt",
    "Shweta Shrivastava": "Shweta_Shriva.txt",
    "Sriram Krishnan": "Sriram_and_Aarthi.txt",
    "Tobi Lütke": "Tobi_Lutke.txt",
    "Vijay Iyengar": "Vijay.txt",
    "Yuhki Yamashita": "Yuhki_Yamashata.txt",
}

# Analysis prompt (same as generate_speaker_profiles.py)
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

Guidelines for expertise (use standard terms):
- Product Strategy, Product Management, Product Design
- Growth Strategy, Marketing Strategy, Go-to-Market, Sales Strategy
- Engineering Leadership, User Experience, Data Analytics
- AI/ML Products, B2B SaaS, Consumer Products, Marketplace
- Executive Coaching, Leadership Development, Team Building
- Company Building, Fundraising, Venture Capital
- Community Building, Monetization, Operations, Career Development

Return ONLY the JSON object, no other text."""


def load_speaker_profiles():
    """Load existing speaker profiles."""
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_speaker_profiles(profiles):
    """Save speaker profiles to file."""
    with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)


def find_transcript_file(speaker_name):
    """Find the transcript file for a given speaker name."""
    # Check manual mapping first
    if speaker_name in TRANSCRIPT_MAPPING:
        filename = TRANSCRIPT_MAPPING[speaker_name]
        filepath = os.path.join(TRANSCRIPTS_DIR, filename)
        if os.path.exists(filepath):
            return filepath
    
    # Try standard conversion: "Speaker Name" -> "Speaker_Name.txt"
    filename = speaker_name.replace(" ", "_") + ".txt"
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    
    # Try without special characters
    clean_name = re.sub(r"['\"\(\)]", "", speaker_name)
    filename = clean_name.replace(" ", "_") + ".txt"
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    
    # Try with special character normalization (ö -> o, ü -> u, etc.)
    normalized_name = speaker_name
    for old, new in [("ö", "o"), ("ü", "u"), ("ä", "a"), ("é", "e"), ("'", "")]:
        normalized_name = normalized_name.replace(old, new)
    filename = normalized_name.replace(" ", "_") + ".txt"
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    
    # Try fuzzy matching: search by first and last name parts
    name_parts = speaker_name.replace("'", "").split()
    if len(name_parts) >= 2:
        first_name = name_parts[0]
        last_name = name_parts[-1].rstrip(")")
        
        for file in os.listdir(TRANSCRIPTS_DIR):
            file_lower = file.lower()
            if first_name.lower() in file_lower and last_name.lower()[:4] in file_lower:
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


def update_quote_files(profiles):
    """Update all quote files with speaker function and expertise."""
    quote_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*_quotes.json")))
    
    files_updated = 0
    quotes_updated = 0
    
    for filepath in quote_files:
        with open(filepath, 'r', encoding='utf-8') as f:
            quotes = json.load(f)
        
        modified = False
        for quote in quotes:
            speaker = quote.get('speaker', '')
            if speaker in profiles:
                profile = profiles[speaker]
                new_function = profile.get('function', '')
                new_expertise = profile.get('expertise', [])
                
                if quote.get('speaker_function') != new_function or quote.get('speaker_expertise') != new_expertise:
                    quote['speaker_function'] = new_function
                    quote['speaker_expertise'] = new_expertise
                    quotes_updated += 1
                    modified = True
        
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(quotes, f, indent=2, ensure_ascii=False)
            files_updated += 1
    
    return files_updated, quotes_updated


def main():
    """Main function to fix missing speakers."""
    print("=" * 60)
    print("Fixing Missing Speaker Profiles")
    print("=" * 60)
    
    # Load existing profiles
    profiles = load_speaker_profiles()
    print(f"\nExisting profiles: {len(profiles)}")
    print(f"Missing speakers to process: {len(MISSING_SPEAKERS)}")
    
    # Statistics
    start_time = datetime.now()
    transcripts_found = 0
    profiles_generated = 0
    not_found = []
    already_exists = []
    
    print("\n" + "-" * 60)
    print("STEP 1: Generating profiles for missing speakers")
    print("-" * 60 + "\n")
    
    for speaker in MISSING_SPEAKERS:
        print(f"Processing: {speaker}...", end=" ", flush=True)
        
        # Check if profile already exists
        if speaker in profiles:
            print("SKIPPED - Profile already exists")
            already_exists.append(speaker)
            continue
        
        # Find transcript file
        transcript_path = find_transcript_file(speaker)
        
        if not transcript_path:
            print("NOT FOUND - No transcript file")
            not_found.append(speaker)
            continue
        
        transcripts_found += 1
        
        try:
            # Read transcript excerpt
            excerpt = read_transcript_excerpt(transcript_path)
            
            # Analyze with GPT
            profile = analyze_speaker(speaker, excerpt)
            
            # Add to profiles
            if 'function' in profile and 'expertise' in profile:
                profiles[speaker] = profile
                profiles_generated += 1
                print(f"OK - {profile['function']}")
            else:
                print("FAILED - Invalid response format")
            
            # Rate limit delay
            time.sleep(RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"FAILED - {e}")
    
    # Save updated profiles
    save_speaker_profiles(profiles)
    print(f"\n✓ Saved {len(profiles)} profiles to {PROFILES_FILE}")
    
    print("\n" + "-" * 60)
    print("STEP 2: Updating quote files with new profiles")
    print("-" * 60 + "\n")
    
    # Update quote files
    files_updated, quotes_updated = update_quote_files(profiles)
    print(f"✓ Updated {files_updated} files, {quotes_updated} quotes")
    
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split('.')[0]
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Speakers to process:      {len(MISSING_SPEAKERS)}")
    print(f"Already had profiles:     {len(already_exists)}")
    print(f"Transcripts found:        {transcripts_found}")
    print(f"Profiles generated:       {profiles_generated}")
    print(f"Transcripts not found:    {len(not_found)}")
    print(f"speaker_profiles.json:    {len(profiles)} total profiles")
    print(f"Quote files updated:      {files_updated} files, {quotes_updated} quotes")
    print(f"Time elapsed:             {elapsed_str}")
    
    if not_found:
        print(f"\nSpeakers without transcripts ({len(not_found)}):")
        for speaker in not_found:
            print(f"  - {speaker}")
    
    if already_exists:
        print(f"\nSpeakers already in profiles ({len(already_exists)}):")
        for speaker in already_exists:
            print(f"  - {speaker}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
