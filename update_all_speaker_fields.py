"""
Update all quote files with speaker_function and speaker_expertise from speaker_profiles.json
"""

import os
import json
import glob

# File paths
PROFILES_FILE = "speaker_profiles.json"
OUTPUT_DIR = "output"


def load_speaker_profiles():
    """Load speaker profiles from JSON file."""
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_quote_files():
    """Get all quote JSON files from output directory."""
    pattern = os.path.join(OUTPUT_DIR, "*_quotes.json")
    return sorted(glob.glob(pattern))


def update_quote_file(filepath, profiles):
    """Update a single quote file with speaker information."""
    # Load quotes
    with open(filepath, 'r', encoding='utf-8') as f:
        quotes = json.load(f)
    
    # Track statistics
    quotes_updated = 0
    function_updated = 0
    expertise_updated = 0
    speakers_not_found = set()
    
    # Update each quote
    for quote in quotes:
        speaker = quote.get('speaker', '')
        
        if speaker in profiles:
            profile = profiles[speaker]
            
            # Update speaker_function
            old_function = quote.get('speaker_function')
            new_function = profile.get('function', '')
            if old_function != new_function:
                function_updated += 1
            quote['speaker_function'] = new_function
            
            # Update speaker_expertise
            old_expertise = quote.get('speaker_expertise')
            new_expertise = profile.get('expertise', [])
            if old_expertise != new_expertise:
                expertise_updated += 1
            quote['speaker_expertise'] = new_expertise
            
            quotes_updated += 1
        else:
            # Speaker not found in profiles
            speakers_not_found.add(speaker)
            
            # Set empty values
            if quote.get('speaker_function') != '':
                function_updated += 1
            quote['speaker_function'] = ''
            
            if quote.get('speaker_expertise') != []:
                expertise_updated += 1
            quote['speaker_expertise'] = []
            
            quotes_updated += 1
    
    # Save updated quotes
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    
    return {
        'quotes_updated': quotes_updated,
        'function_updated': function_updated,
        'expertise_updated': expertise_updated,
        'speakers_not_found': speakers_not_found
    }


def main():
    """Main function to update all quote files."""
    print("=" * 60)
    print("Updating Speaker Fields in Quote Files")
    print("=" * 60)
    
    # Load speaker profiles
    profiles = load_speaker_profiles()
    print(f"\nLoaded {len(profiles)} speaker profiles from {PROFILES_FILE}")
    
    # Get all quote files
    quote_files = get_quote_files()
    print(f"Found {len(quote_files)} quote files in {OUTPUT_DIR}/\n")
    
    # Statistics
    total_files = 0
    total_quotes = 0
    total_function_updated = 0
    total_expertise_updated = 0
    all_speakers_not_found = set()
    
    # Process each file
    for filepath in quote_files:
        filename = os.path.basename(filepath)
        
        try:
            result = update_quote_file(filepath, profiles)
            
            total_files += 1
            total_quotes += result['quotes_updated']
            total_function_updated += result['function_updated']
            total_expertise_updated += result['expertise_updated']
            all_speakers_not_found.update(result['speakers_not_found'])
            
            # Show progress
            check = "✓" if not result['speakers_not_found'] else "⚠"
            print(f"Updating {filename}... {check} {result['quotes_updated']} quotes")
            
        except Exception as e:
            print(f"Updating {filename}... ✗ Error: {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed:              {total_files}")
    print(f"Quotes updated:               {total_quotes}")
    print(f"speaker_function updated:     {total_function_updated}")
    print(f"speaker_expertise updated:    {total_expertise_updated}")
    print(f"Speakers not found:           {len(all_speakers_not_found)}")
    
    if all_speakers_not_found:
        print(f"\nSpeakers not found in profiles ({len(all_speakers_not_found)}):")
        for speaker in sorted(all_speakers_not_found):
            print(f"  - {speaker}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
