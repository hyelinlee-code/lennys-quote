"""
Fix timestamps by mechanically extracting correct timestamps from transcripts

PRECISE ALGORITHM:
1. Find quote text position in transcript → quote_start_pos
2. Define search window (BEFORE quote only!):
   search_start = max(0, quote_start_pos - 200)
   search_end = quote_start_pos  # NOT quote_start_pos + anything!
3. Find ALL timestamps in search window
4. Choose the LAST one (closest to quote, but still before it)
5. If none found, expand to 500/1000 chars and retry

CRITICAL: Never search beyond quote_start_pos!
"""

import os
import json
import glob
import re


# File paths
OUTPUT_DIR = "output"
TRANSCRIPTS_DIR = "transcripts"


def normalize_timestamp(ts):
    """Normalize timestamp to HH:MM:SS format."""
    parts = ts.split(':')
    if len(parts) == 2:
        # MM:SS -> 00:MM:SS
        return f"00:{parts[0].zfill(2)}:{parts[1]}"
    elif len(parts) == 3:
        # HH:MM:SS
        return f"{parts[0].zfill(2)}:{parts[1]}:{parts[2]}"
    return ts


def find_transcript_file(speaker_name, quote_filename):
    """Find the transcript file for a given speaker or quote file."""
    # First try to derive from quote filename
    # Ada_Chen_Rekhi_quotes.json -> Ada_Chen_Rekhi.txt
    base_name = quote_filename.replace("_quotes.json", "")
    filepath = os.path.join(TRANSCRIPTS_DIR, f"{base_name}.txt")
    if os.path.exists(filepath):
        return filepath
    
    # Try speaker name
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
    
    return None


def clean_text_for_search(text):
    """Clean text for fuzzy matching."""
    # Remove extra whitespace, normalize quotes
    text = re.sub(r'\s+', ' ', text)
    text = text.replace('"', '"').replace('"', '"')
    text = text.replace("'", "'").replace("'", "'")
    text = text.strip()
    return text


def find_quote_position(transcript, quote_text):
    """Find the position of a quote in the transcript."""
    # Clean both texts
    clean_quote = clean_text_for_search(quote_text)
    clean_transcript = clean_text_for_search(transcript)
    
    # Try exact match first
    pos = clean_transcript.find(clean_quote)
    if pos != -1:
        return pos
    
    # Try first 100 characters
    if len(clean_quote) > 100:
        first_part = clean_quote[:100]
        pos = clean_transcript.find(first_part)
        if pos != -1:
            return pos
    
    # Try first 50 characters
    if len(clean_quote) > 50:
        first_part = clean_quote[:50]
        pos = clean_transcript.find(first_part)
        if pos != -1:
            return pos
    
    # Try first 30 characters (more lenient)
    if len(clean_quote) > 30:
        first_part = clean_quote[:30]
        pos = clean_transcript.find(first_part)
        if pos != -1:
            return pos
    
    # Try case-insensitive match
    pos = clean_transcript.lower().find(clean_quote.lower()[:50])
    if pos != -1:
        return pos
    
    return -1


def find_timestamp_before_position(transcript, quote_start_pos):
    """
    Find the closest timestamp that appears IMMEDIATELY BEFORE the quote.
    
    CRITICAL: Only searches BEFORE quote_start_pos, never after!
    
    Algorithm:
    1. Define search window: [quote_start_pos - 200, quote_start_pos]
    2. Find ALL timestamps in this window
    3. Choose the LAST one (closest to quote, but still before it)
    4. If none found, expand to 500 chars and retry
    """
    # Timestamp pattern: matches (HH:MM:SS), (MM:SS), or standalone
    timestamp_pattern = re.compile(r'\((\d{1,2}:\d{2}:\d{2})\)')
    
    def search_in_window(window_size):
        """Search for timestamps in a window before the quote."""
        # Define search window (BEFORE quote only!)
        search_start = max(0, quote_start_pos - window_size)
        search_end = quote_start_pos  # NOT quote_start_pos + anything!
        
        # Extract search text
        search_text = transcript[search_start:search_end]
        
        # Find ALL timestamps in this search_text
        timestamps = []
        for match in timestamp_pattern.finditer(search_text):
            ts = match.group(1)
            ts_pos = match.start()  # Position relative to search_start
            timestamps.append((ts_pos, ts))
        
        if timestamps:
            # Sort by position (ascending)
            timestamps.sort(key=lambda x: x[0])
            # Choose the LAST one (closest to quote, but still before it)
            return timestamps[-1][1]
        
        return None
    
    # First try: search in 200 chars before quote
    result = search_in_window(200)
    if result:
        return normalize_timestamp(result)
    
    # Second try: expand to 500 chars
    result = search_in_window(500)
    if result:
        return normalize_timestamp(result)
    
    # Third try: expand to 1000 chars (for quotes far from timestamp)
    result = search_in_window(1000)
    if result:
        return normalize_timestamp(result)
    
    # Last try: search entire text before quote
    result = search_in_window(quote_start_pos)
    if result:
        return normalize_timestamp(result)
    
    return None


def process_quote_file(filepath):
    """Process a single quote file and fix timestamps."""
    filename = os.path.basename(filepath)
    
    # Load quotes
    with open(filepath, 'r', encoding='utf-8') as f:
        quotes = json.load(f)
    
    if not quotes:
        return {
            'quotes_checked': 0,
            'timestamps_updated': 0,
            'timestamps_unchanged': 0,
            'warnings': []
        }
    
    # Find transcript file
    first_speaker = quotes[0].get('speaker', '') if quotes else ''
    transcript_path = find_transcript_file(first_speaker, filename)
    
    if not transcript_path:
        return {
            'quotes_checked': len(quotes),
            'timestamps_updated': 0,
            'timestamps_unchanged': 0,
            'warnings': [f"Transcript not found for {filename}"]
        }
    
    # Load transcript
    with open(transcript_path, 'r', encoding='utf-8') as f:
        transcript = f.read()
    
    # Also create a cleaned version for searching
    clean_transcript = clean_text_for_search(transcript)
    
    # Statistics
    stats = {
        'quotes_checked': len(quotes),
        'timestamps_updated': 0,
        'timestamps_unchanged': 0,
        'warnings': []
    }
    
    # Process each quote
    for quote in quotes:
        quote_text = quote.get('text', '')
        old_timestamp = quote.get('timestamp', '')
        
        if not quote_text:
            continue
        
        # Find quote position in transcript
        pos = find_quote_position(transcript, quote_text)
        
        if pos == -1:
            # Quote text not found
            stats['warnings'].append(f"Text not found: {quote_text[:40]}...")
            stats['timestamps_unchanged'] += 1
            continue
        
        # Find timestamp before this position
        new_timestamp = find_timestamp_before_position(transcript, pos)
        
        if new_timestamp is None:
            # No timestamp found
            stats['warnings'].append(f"No timestamp found for: {quote_text[:40]}...")
            if old_timestamp:
                stats['timestamps_unchanged'] += 1
            else:
                quote['timestamp'] = "00:00:00"
                stats['timestamps_updated'] += 1
            continue
        
        # Update timestamp if different
        if old_timestamp != new_timestamp:
            quote['timestamp'] = new_timestamp
            stats['timestamps_updated'] += 1
        else:
            stats['timestamps_unchanged'] += 1
    
    # Save updated quotes
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    
    return stats


def get_quote_files():
    """Get all quote JSON files from output directory."""
    pattern = os.path.join(OUTPUT_DIR, "*_quotes.json")
    return sorted(glob.glob(pattern))


def main():
    """Main function to fix timestamps."""
    print("=" * 60)
    print("Fixing Timestamps from Transcripts")
    print("=" * 60)
    
    # Get all quote files
    quote_files = get_quote_files()
    print(f"\nFound {len(quote_files)} quote files in {OUTPUT_DIR}/\n")
    
    # Statistics
    total_stats = {
        'files_processed': 0,
        'quotes_checked': 0,
        'timestamps_updated': 0,
        'timestamps_unchanged': 0,
        'warnings': 0
    }
    
    all_warnings = []
    
    # Process each file
    for filepath in quote_files:
        filename = os.path.basename(filepath)
        
        try:
            stats = process_quote_file(filepath)
            
            total_stats['files_processed'] += 1
            total_stats['quotes_checked'] += stats['quotes_checked']
            total_stats['timestamps_updated'] += stats['timestamps_updated']
            total_stats['timestamps_unchanged'] += stats['timestamps_unchanged']
            total_stats['warnings'] += len(stats['warnings'])
            
            # Show progress
            if stats['warnings']:
                all_warnings.extend([(filename, w) for w in stats['warnings']])
                print(f"Processing {filename}: {stats['timestamps_updated']}/{stats['quotes_checked']} timestamps fixed (⚠ {len(stats['warnings'])} warnings)")
            else:
                print(f"Processing {filename}: {stats['timestamps_updated']}/{stats['quotes_checked']} timestamps fixed")
                
        except Exception as e:
            print(f"Processing {filename}: ERROR - {e}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed:              {total_stats['files_processed']}")
    print(f"Quotes checked:               {total_stats['quotes_checked']}")
    print(f"Timestamps updated:           {total_stats['timestamps_updated']}")
    print(f"Timestamps unchanged:         {total_stats['timestamps_unchanged']}")
    print(f"Warnings (text not found):    {total_stats['warnings']}")
    
    if all_warnings and len(all_warnings) <= 20:
        print(f"\nWarnings:")
        for filename, warning in all_warnings:
            print(f"  [{filename}] {warning}")
    elif all_warnings:
        print(f"\nFirst 20 warnings (of {len(all_warnings)}):")
        for filename, warning in all_warnings[:20]:
            print(f"  [{filename}] {warning}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
