"""
Phase 1A: Enrich Speaker Profiles with Role & Company

Reads speaker_profiles.json and transcript files to extract each speaker's
job title (role) and company. Uses regex parsing first, then falls back to
OpenAI API for ambiguous cases.

Output: speaker_profiles_enriched.json
"""

import json
import os
import re
import time
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

SPEAKER_PROFILES_PATH = "speaker_profiles.json"
TRANSCRIPTS_DIR = "transcripts"
OUTPUT_PATH = "speaker_profiles_enriched.json"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_role_company_from_transcript(transcript_text: str, speaker_name: str) -> dict:
    """
    Try to extract role and company from Lenny's introduction in the transcript.
    Lenny typically introduces guests with their title and company.
    """
    # Look for Lenny's introduction section (usually within first 2000 chars)
    intro_section = transcript_text[:3000]

    # Common patterns in Lenny's intros:
    # "Today my guest is [Name]. [Name] is [role] at [company]"
    # "[Name] is the [role] at [company]"
    # "[Name], [role] at [company]"
    # "who is [role] at [company]"

    first_name = speaker_name.split()[0]
    last_name = speaker_name.split()[-1] if len(speaker_name.split()) > 1 else ""

    patterns = [
        # "[Name] is [a/an/the] [role] at [company]"
        rf"(?:{re.escape(speaker_name)}|{re.escape(first_name)})\s+is\s+(?:a|an|the\s+)?(.+?)\s+at\s+([A-Z][^\.,]+)",
        # "[Name] is [a/an/the] [role] of [company]"
        rf"(?:{re.escape(speaker_name)}|{re.escape(first_name)})\s+is\s+(?:a|an|the\s+)?(.+?)\s+of\s+([A-Z][^\.,]+)",
        # "was [role] at [company]"
        rf"(?:{re.escape(speaker_name)}|{re.escape(first_name)})\s+was\s+(?:a|an|the\s+)?(.+?)\s+at\s+([A-Z][^\.,]+)",
        # "[Name], [role] at [company]"
        rf"(?:{re.escape(speaker_name)}|{re.escape(first_name)}),\s+(.+?)\s+at\s+([A-Z][^\.,]+)",
        # "who is [role] at [company]"
        rf"who\s+is\s+(?:a|an|the\s+)?(.+?)\s+at\s+([A-Z][^\.,]+)",
        # "[Name] is [role] and [something] at [company]"
        rf"(?:{re.escape(speaker_name)}|{re.escape(first_name)})\s+is\s+(.+?)\s+at\s+([A-Z][^\.,]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, intro_section, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            company = match.group(2).strip()
            # Clean up role - remove trailing articles/prepositions
            role = re.sub(r'\s+(and|or|the|a|an)\s*$', '', role).strip()
            # Clean up company - remove trailing punctuation
            company = re.sub(r'[,.\s]+$', '', company).strip()
            if len(role) > 3 and len(company) > 1 and len(role) < 100:
                return {"role": role, "company": company}

    return None


def extract_role_company_with_api(transcript_text: str, speaker_name: str) -> dict:
    """Use OpenAI API to extract role and company when regex fails."""
    intro_section = transcript_text[:3000]

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You extract speaker information from podcast transcripts. Return ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": f"""From this transcript introduction, extract the job title/role and company for "{speaker_name}".

Transcript excerpt:
{intro_section}

Return JSON in this exact format:
{{"role": "their job title", "company": "their company name"}}

If you cannot determine the role, use "Guest". If you cannot determine the company, use ""."""
                }
            ],
            temperature=0,
            max_tokens=100,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return {
            "role": result.get("role", "Guest"),
            "company": result.get("company", "")
        }
    except Exception as e:
        print(f"  API error for {speaker_name}: {e}")
        return None


def main():
    # Load existing profiles
    with open(SPEAKER_PROFILES_PATH, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    enriched = {}
    total = len(profiles)
    regex_success = 0
    api_success = 0
    fallback_count = 0

    print(f"Enriching {total} speaker profiles...")
    print("=" * 60)

    for i, (speaker, profile) in enumerate(profiles.items(), 1):
        print(f"[{i}/{total}] {speaker}...", end=" ")

        # Find transcript file
        transcript_filename = speaker.replace(" ", "_") + ".txt"
        transcript_path = os.path.join(TRANSCRIPTS_DIR, transcript_filename)

        role_company = None

        if os.path.exists(transcript_path):
            with open(transcript_path, "r", encoding="utf-8") as f:
                transcript_text = f.read()

            # Try regex first
            role_company = extract_role_company_from_transcript(transcript_text, speaker)

            if role_company:
                regex_success += 1
                print(f"[regex] {role_company['role']} @ {role_company['company']}")
            else:
                # Fall back to API
                role_company = extract_role_company_with_api(transcript_text, speaker)
                if role_company and role_company.get("role") != "Guest":
                    api_success += 1
                    print(f"[api] {role_company['role']} @ {role_company['company']}")
                else:
                    fallback_count += 1
                    print(f"[fallback] Using function: {profile.get('function', 'Unknown')}")

                # Rate limit for API calls
                time.sleep(0.5)
        else:
            fallback_count += 1
            print(f"[no transcript] Using function: {profile.get('function', 'Unknown')}")

        # Build enriched profile
        enriched[speaker] = {
            "function": profile.get("function", "Unknown"),
            "expertise": profile.get("expertise", []),
            "role": role_company["role"] if role_company and role_company.get("role") else profile.get("function", "Guest"),
            "company": role_company["company"] if role_company and role_company.get("company") else ""
        }

    # Save enriched profiles
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(enriched, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Done! Enriched profiles saved to {OUTPUT_PATH}")
    print(f"  Regex extractions: {regex_success}")
    print(f"  API extractions:   {api_success}")
    print(f"  Fallbacks:         {fallback_count}")
    print(f"  Total:             {total}")


if __name__ == "__main__":
    main()
