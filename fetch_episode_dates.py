"""
Fetch episode publish dates from the lennys-podcast-claire-vo GitHub repo.
Maps speaker names to publish dates for episode recency sorting.

Reads: output/*_quotes.json (to get speaker names)
Fetches: GitHub raw transcript frontmatter for each speaker
Output: episode_dates.json
"""

import json
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path

OUTPUT_DIR = "output"
DATES_FILE = "episode_dates.json"
BASE_RAW_URL = "https://raw.githubusercontent.com/swathidbhat/lennys-podcast-claire-vo/main/episodes"


def speaker_to_slug(speaker_name: str) -> str:
    """Convert speaker name to GitHub folder slug."""
    # Handle special cases
    slug = speaker_name.lower().strip()
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return slug


def fetch_publish_date(slug: str) -> str | None:
    """Fetch the publish_date from a transcript's YAML frontmatter."""
    url = f"{BASE_RAW_URL}/{slug}/transcript.md"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            # Read just the first 500 bytes - enough for frontmatter
            content = resp.read(500).decode("utf-8", errors="replace")
            match = re.search(r'publish_date:\s*(\d{4}-\d{2}-\d{2})', content)
            if match:
                return match.group(1)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"  HTTP {e.code} for {slug}")
    except Exception as e:
        print(f"  Error for {slug}: {e}")
    return None


def main():
    # Get all speaker names from output files
    files = sorted(Path(OUTPUT_DIR).glob("*_quotes.json"))
    print(f"Found {len(files)} speaker files")

    # Load existing dates to allow resume
    existing = {}
    if os.path.exists(DATES_FILE):
        with open(DATES_FILE, "r", encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Loaded {len(existing)} existing date entries")

    dates = dict(existing)
    fetched = 0
    not_found = []

    for filepath in files:
        # Extract speaker name from filename
        stem = filepath.stem.replace("_quotes", "")
        speaker_name = stem.replace("_", " ")

        # Skip if already fetched
        if speaker_name in dates:
            continue

        slug = speaker_to_slug(speaker_name)

        # Try the slug directly
        date = fetch_publish_date(slug)

        # Try alternate slugs for "2.0" episodes
        if date is None and "2.0" in stem:
            alt_slug = slug.replace("-20", "-20")  # already correct
            # Also try with underscore variant
            alt_slug2 = slug.replace("-2-0", "-20")
            if alt_slug2 != slug:
                date = fetch_publish_date(alt_slug2)

        # Try removing trailing underscores/numbers
        if date is None and slug.endswith("-"):
            date = fetch_publish_date(slug.rstrip("-"))

        if date:
            dates[speaker_name] = date
            fetched += 1
            print(f"  [{fetched}] {speaker_name}: {date}")
        else:
            not_found.append((speaker_name, slug))

        # Save checkpoint every 20 fetches
        if fetched > 0 and fetched % 20 == 0:
            with open(DATES_FILE, "w", encoding="utf-8") as f:
                json.dump(dates, f, indent=2, ensure_ascii=False)

        # Rate limit: small delay between requests
        time.sleep(0.2)

    # Final save
    with open(DATES_FILE, "w", encoding="utf-8") as f:
        json.dump(dates, f, indent=2, ensure_ascii=False)

    print(f"\n{'=' * 60}")
    print(f"Total speakers with dates: {len(dates)}")
    print(f"Newly fetched: {fetched}")
    print(f"Not found: {len(not_found)}")

    if not_found:
        print(f"\nMissing speakers (tried slug):")
        for name, slug in not_found:
            print(f"  {name} -> {slug}")


if __name__ == "__main__":
    main()
