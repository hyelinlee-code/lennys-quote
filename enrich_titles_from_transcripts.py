"""
Extract speaker titles from Lenny's podcast introduction in transcripts.
More reliable than web search - Lenny provides precise descriptions.
"""

import json
import os
import re
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

TRANSCRIPTS_DIR = "transcripts"
SPEAKER_PROFILES = "speaker_profiles.json"
CHECKPOINT_FILE = "transcript_titles_checkpoint.json"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def load_checkpoint():
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_speakers": []}


def save_checkpoint(data):
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def extract_intro_section(transcript_path: str, speaker_name: str) -> str:
    """Extract Lenny's introduction section containing speaker description."""
    with open(transcript_path, "r", encoding="utf-8") as f:
        content = f.read()

    first_name = speaker_name.split()[0]

    # Look for "Today, my guest is [Name]" pattern
    patterns = [
        rf"Today,? my guests? (?:is|are) {re.escape(first_name)}[^.]*\.(.*?)(?:With that|This episode is brought|If you enjoy)",
        rf"my guests? (?:is|are) {re.escape(first_name)}[^.]*\.(.*?)(?:With that|This episode is brought|If you enjoy)",
    ]

    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(0)[:1500]

    # Fallback: find Lenny's paragraph with speaker name in first 5000 chars
    first_section = content[:5000]
    paragraphs = first_section.split('\n\n')
    for i, para in enumerate(paragraphs):
        if 'Lenny' in para and first_name in para:
            return '\n'.join(paragraphs[i:i+2])[:1500]

    return ""


def extract_title_with_gpt(speaker_name: str, intro_text: str) -> str:
    """Use GPT to extract job title from intro text."""
    if not intro_text:
        return "Guest"

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """Extract the speaker's professional title from a podcast introduction.

Format: "Role, Company" (max 6 words)
Examples:
- "CPO, Faire"
- "ex-VP Product, Facebook"
- "CEO, Replit"
- "Author & Executive Coach"

For multiple roles, pick the most notable/recognizable.
If founder: "Founder, Company"
If former role is more notable: use "ex-" prefix

Return ONLY the title string, nothing else."""
                },
                {
                    "role": "user",
                    "content": f"Extract job title for {speaker_name} from:\n\n{intro_text}"
                }
            ],
            temperature=0.1,
            max_tokens=50
        )
        return response.choices[0].message.content.strip().strip('"')
    except Exception as e:
        print(f"    GPT error: {e}")
        return "Guest"


def main():
    with open(SPEAKER_PROFILES, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_speakers", []))

    # Build transcript -> speaker mapping
    transcript_files = list(Path(TRANSCRIPTS_DIR).glob("*.txt"))

    print("Enriching speaker titles from transcripts...")
    print(f"Found {len(transcript_files)} transcripts")
    print(f"Already processed: {len(processed)} speakers")
    print("=" * 60)

    updated = 0

    for tf in transcript_files:
        # Convert filename to speaker name
        stem = re.sub(r'_\d+\.\d+$', '', tf.stem)  # Remove "_2.0" suffix
        possible_name = stem.replace('_', ' ')

        # Find matching speaker
        speaker_name = None
        for name in profiles.keys():
            if name.lower() == possible_name.lower() or possible_name.lower() in name.lower():
                speaker_name = name
                break

        if not speaker_name or speaker_name in processed:
            continue

        # Skip if already has non-Guest title
        current = profiles[speaker_name].get("job_title", "Guest")
        if current != "Guest":
            processed.add(speaker_name)
            continue

        print(f"[{len(processed)+1}] {speaker_name}...", end=" ")

        intro = extract_intro_section(str(tf), speaker_name)
        if not intro:
            print("no intro found")
            processed.add(speaker_name)
            continue

        title = extract_title_with_gpt(speaker_name, intro)
        profiles[speaker_name]["job_title"] = title
        print(title)

        updated += 1
        processed.add(speaker_name)
        save_checkpoint({"processed_speakers": list(processed)})

    with open(SPEAKER_PROFILES, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print(f"\nDone! Updated {updated} speaker titles from transcripts.")


if __name__ == "__main__":
    main()
