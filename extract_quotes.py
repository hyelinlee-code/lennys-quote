import os
import json
import time
from pathlib import Path
from anthropic import Anthropic


def load_file(file_path: str) -> str:
    """Load and return contents of a text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def extract_quotes(transcript: str, prompt: str) -> list:
    """Call Anthropic API to extract quotes from transcript."""
    client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": f"{prompt}\n\nHere is the podcast transcript to analyze:\n\n{transcript}"
            }
        ]
    )

    response_text = message.content[0].text
    quotes = json.loads(response_text)
    return quotes


def enrich_quotes_with_speaker_info(quotes: list, speaker_profiles: dict) -> list:
    """Add speaker_function and speaker_expertise to each quote."""
    for quote in quotes:
        speaker_name = quote.get("speaker", "")
        
        if speaker_name in speaker_profiles:
            profile = speaker_profiles[speaker_name]
            quote["speaker_function"] = profile.get("function", "Leadership")
            quote["speaker_expertise"] = profile.get("expertise", [])
        else:
            # Default values for unknown speakers
            quote["speaker_function"] = "Leadership"
            quote["speaker_expertise"] = []
    
    return quotes


def main():
    base_dir = Path(__file__).parent
    transcripts_dir = base_dir / "transcripts"
    prompt_path = base_dir / "extraction_prompt.txt"
    speaker_profiles_path = base_dir / "speaker_profiles.json"
    output_dir = base_dir / "output"

    output_dir.mkdir(exist_ok=True)

    # Load speaker profiles
    print("Loading speaker profiles...")
    with open(speaker_profiles_path, "r", encoding="utf-8") as f:
        speaker_profiles = json.load(f)

    # Get all .txt files in transcripts folder
    transcript_files = sorted(transcripts_dir.glob("*.txt"))
    total_files = len(transcript_files)

    if total_files == 0:
        print("No .txt files found in transcripts/ folder.")
        return

    print(f"Found {total_files} transcript(s) to process.\n")

    # Load extraction prompt once
    print("Loading extraction prompt...")
    prompt = load_file(prompt_path)

    # Track statistics
    total_quotes = 0
    errors = []

    # Process each transcript
    for index, transcript_path in enumerate(transcript_files, start=1):
        filename = transcript_path.name
        print(f"Processing {index}/{total_files}: {filename}")

        try:
            # Load transcript
            transcript = load_file(transcript_path)

            # Extract quotes via API
            quotes = extract_quotes(transcript, prompt)
            
            # Enrich quotes with speaker profile info
            quotes = enrich_quotes_with_speaker_info(quotes, speaker_profiles)
            
            num_quotes = len(quotes)
            total_quotes += num_quotes

            # Save to output file
            output_filename = transcript_path.stem + "_quotes.json"
            output_path = output_dir / output_filename

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(quotes, f, indent=2, ensure_ascii=False)

            print(f"  -> Extracted {num_quotes} quotes, saved to {output_filename}")

        except Exception as e:
            error_msg = f"{filename}: {str(e)}"
            errors.append(error_msg)
            print(f"  -> ERROR: {str(e)}")

        # Add delay between API calls (except after the last file)
        if index < total_files:
            print("  -> Waiting 2 seconds before next file...")
            time.sleep(2)

    # Print summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print(f"Total files processed: {total_files}")
    print(f"Total quotes extracted: {total_quotes}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for error in errors:
            print(f"  - {error}")
    else:
        print("\nNo errors encountered!")

    print("=" * 50)


if __name__ == "__main__":
    main()
