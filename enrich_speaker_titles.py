"""
Enrich Speaker Titles via Web Research

Replaces generic `speaker_function` (e.g., "Product") with actual job titles
(e.g., "ex-CEO, SurveyMonkey") using web search and GPT extraction.

Approach:
- Use `duckduckgo-search` library to search: "Lenny's Podcast" "[Speaker Name]"
- Pass search results to GPT-4o-mini to extract structured title/company
- Update speaker_profiles.json with new `job_title` field

Output adds job_title field:
{
  "Adam Fishman": {
    "function": "Product",
    "job_title": "ex-VP Growth, Patreon",
    "expertise": [...]
  }
}

Uses checkpoint pattern for resumability.
"""

import json
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(".env.local")

SPEAKER_PROFILES = "speaker_profiles.json"
OUTPUT_PROFILES = "speaker_profiles.json"  # Update in place
CHECKPOINT_FILE = "speaker_titles_checkpoint.json"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Try to import duckduckgo_search, provide helpful message if missing
try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False
    print("Warning: duckduckgo-search not installed.")
    print("Install with: pip install duckduckgo-search")
    print("Falling back to GPT-only inference (less accurate).\n")


def load_checkpoint() -> dict:
    """Load checkpoint with processed speakers."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, "r") as f:
            return json.load(f)
    return {"processed_speakers": [], "enriched_count": 0}


def save_checkpoint(checkpoint: dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump(checkpoint, f, indent=2)


def search_speaker(speaker_name: str) -> str:
    """
    Search for speaker info using DuckDuckGo.
    Returns concatenated search result snippets.
    """
    if not HAS_DDGS:
        return ""

    try:
        with DDGS() as ddgs:
            query = f'"Lenny\'s Podcast" "{speaker_name}"'
            results = list(ddgs.text(query, max_results=5))

            if not results:
                # Try broader search
                query = f'"{speaker_name}" CEO founder VP'
                results = list(ddgs.text(query, max_results=5))

            # Concatenate snippets
            snippets = []
            for r in results:
                title = r.get("title", "")
                body = r.get("body", "")
                snippets.append(f"{title}: {body}")

            return "\n".join(snippets)[:2000]  # Limit context size

    except Exception as e:
        print(f"    Search error: {e}")
        return ""


def extract_job_title(speaker_name: str, search_results: str, current_function: str) -> str:
    """
    Use GPT to extract job title from search results.
    Returns a formatted job title string.
    """
    try:
        context = search_results if search_results else f"Speaker is known for {current_function} expertise in tech/startups."

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert at extracting professional titles from text.
Extract the most relevant/impressive job title for a podcast guest.

Format guidelines:
- Include company if known: "VP Product, Airbnb" or "CEO, Stripe"
- Use "ex-" for former roles: "ex-VP Growth, Facebook"
- Keep it concise: max 6 words
- For consultants/coaches: "Executive Coach" or "Leadership Coach"
- For authors/advisors: "Author & Advisor" or "Growth Advisor"
- For founders: "Founder, CompanyName" or "Co-founder, CompanyName"

If you cannot determine a specific title, return "Guest" as fallback."""
                },
                {
                    "role": "user",
                    "content": f"""Extract the job title for this Lenny's Podcast guest.

Speaker: {speaker_name}
Current category: {current_function}

Search results / context:
{context}

Return ONLY the job title (e.g., "ex-VP Growth, Patreon" or "CEO, Replit"):"""
                }
            ],
            temperature=0.2,
            max_tokens=50
        )

        title = response.choices[0].message.content.strip()
        # Clean up any quotes
        title = title.strip('"\'')

        # Validate it's reasonable
        if len(title) > 60 or len(title) < 3:
            return "Guest"

        return title

    except Exception as e:
        print(f"    GPT error: {e}")
        return "Guest"


def main():
    # Check if speaker profiles exist
    if not os.path.exists(SPEAKER_PROFILES):
        print(f"Error: {SPEAKER_PROFILES} not found.")
        return

    # Load profiles
    with open(SPEAKER_PROFILES, "r", encoding="utf-8") as f:
        profiles = json.load(f)

    # Load checkpoint
    checkpoint = load_checkpoint()
    processed = set(checkpoint.get("processed_speakers", []))
    enriched_count = checkpoint.get("enriched_count", 0)

    speakers = list(profiles.keys())
    total = len(speakers)

    print("Enriching speaker profiles with job titles...")
    if HAS_DDGS:
        print("Using DuckDuckGo search + GPT extraction")
    else:
        print("Using GPT-only inference (install duckduckgo-search for better results)")
    print(f"Already processed: {len(processed)} speakers")
    print("=" * 60)

    processed_this_run = 0
    enriched_this_run = 0

    for i, speaker in enumerate(speakers, 1):
        if speaker in processed:
            continue

        profile = profiles[speaker]

        # Skip if already has job_title
        if profile.get("job_title"):
            processed.add(speaker)
            continue

        current_function = profile.get("function", "Unknown")
        print(f"[{i}/{total}] {speaker}...", end=" ")

        # Search for speaker info
        search_results = search_speaker(speaker)
        time.sleep(1.0)  # Rate limiting for search

        # Extract job title
        job_title = extract_job_title(speaker, search_results, current_function)

        # Update profile
        profile["job_title"] = job_title
        profiles[speaker] = profile

        print(f"{job_title}")

        processed_this_run += 1
        if job_title != "Guest":
            enriched_count += 1
            enriched_this_run += 1

        # Save progress
        processed.add(speaker)
        checkpoint["processed_speakers"] = list(processed)
        checkpoint["enriched_count"] = enriched_count
        save_checkpoint(checkpoint)

        # Save profiles periodically
        if processed_this_run % 10 == 0:
            with open(OUTPUT_PROFILES, "w", encoding="utf-8") as f:
                json.dump(profiles, f, indent=2, ensure_ascii=False)

        time.sleep(0.5)  # Rate limiting for GPT

    # Final save
    with open(OUTPUT_PROFILES, "w", encoding="utf-8") as f:
        json.dump(profiles, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 60)
    print(f"Done! Speaker titles enrichment complete.")
    print(f"  Processed this run:  {processed_this_run}")
    print(f"  Enriched this run:   {enriched_this_run}")
    print(f"  Total enriched:      {enriched_count}")
    print(f"  Output: {OUTPUT_PROFILES}")
    print(f"\nNext step: Run export_for_react.py to generate final quotes.json")


if __name__ == "__main__":
    main()
