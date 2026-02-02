"""
Reprocess failed transcript files using Google Gemini Flash 2.0
"""

import os
import json
import time
import re
from datetime import datetime
from dotenv import load_dotenv

import google.generativeai as genai

# Load environment variables
load_dotenv('.env.local')

# Configure Gemini API
genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

# Initialize model
model = genai.GenerativeModel('gemini-2.0-flash-exp')

# List of failed files to reprocess
FAILED_FILES = [
    "Brian_Balfour.txt",
    "Brian_Chesky.txt",
    "Brian_Tolkin.txt",
    "Cam_Adams.txt",
    "Camille_Fournier.txt",
    "Camille_Hearst.txt",
    "Camille_Ricketts.txt",
    "Carilu_Dietrich.txt",
    "Chris_Hutchins.txt",
    "Christian_Idiodi.txt",
    "Christina_Wodtke.txt",
    "Christine_Itwaru.txt",
    "Christopher_Lochhead.txt",
    "Christopher_Miller.txt",
    "Claire_Butler.txt",
    "Claire_Hughes_Johnson.txt",
]

# Paths
TRANSCRIPTS_DIR = "transcripts"
OUTPUT_DIR = "output"
PROMPT_FILE = "extraction_prompt.txt"

# Rate limit delay (seconds)
RATE_LIMIT_DELAY = 2

# Approximate cost per 1M tokens for Gemini Flash 2.0
# Input: $0.075/1M tokens, Output: $0.30/1M tokens (approximate)
COST_PER_1M_INPUT_TOKENS = 0.075
COST_PER_1M_OUTPUT_TOKENS = 0.30


def load_extraction_prompt():
    """Load the extraction prompt from file."""
    with open(PROMPT_FILE, 'r', encoding='utf-8') as f:
        return f.read()


def load_transcript(filename):
    """Load a transcript file."""
    filepath = os.path.join(TRANSCRIPTS_DIR, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()


def extract_json_from_response(response_text):
    """Extract JSON array from response text, handling markdown code blocks."""
    text = response_text.strip()
    
    # Remove markdown code blocks if present
    if text.startswith("```"):
        # Remove opening code block (```json or ```)
        text = re.sub(r'^```(?:json)?\s*\n?', '', text)
        # Remove closing code block
        text = re.sub(r'\n?```\s*$', '', text)
    
    # Find JSON array in the text
    start_idx = text.find('[')
    end_idx = text.rfind(']')
    
    if start_idx != -1 and end_idx != -1:
        json_str = text[start_idx:end_idx + 1]
        return json.loads(json_str)
    
    # Try parsing the whole text as JSON
    return json.loads(text)


def process_transcript(filename, extraction_prompt):
    """Process a single transcript file with Gemini."""
    # Load transcript
    transcript_text = load_transcript(filename)
    
    # Call Gemini API
    response = model.generate_content([
        extraction_prompt,
        transcript_text
    ])
    
    # Parse response
    response_text = response.text
    quotes = extract_json_from_response(response_text)
    
    # Get token usage if available
    input_tokens = 0
    output_tokens = 0
    if hasattr(response, 'usage_metadata'):
        input_tokens = getattr(response.usage_metadata, 'prompt_token_count', 0)
        output_tokens = getattr(response.usage_metadata, 'candidates_token_count', 0)
    
    return quotes, input_tokens, output_tokens


def save_quotes(filename, quotes):
    """Save extracted quotes to output file."""
    # Generate output filename
    base_name = os.path.splitext(filename)[0]
    output_filename = f"{base_name}_quotes.json"
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    # Save to file
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(quotes, f, indent=2, ensure_ascii=False)
    
    return output_path


def main():
    """Main function to reprocess failed files."""
    print("=" * 60)
    print("Reprocessing Failed Files with Gemini Flash 2.0")
    print("=" * 60)
    
    # Load extraction prompt
    extraction_prompt = load_extraction_prompt()
    print(f"\nLoaded extraction prompt ({len(extraction_prompt)} chars)")
    
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Statistics
    start_time = datetime.now()
    total_files = len(FAILED_FILES)
    processed_files = 0
    failed_files = []
    total_quotes = 0
    total_input_tokens = 0
    total_output_tokens = 0
    
    print(f"\nProcessing {total_files} files...\n")
    
    for idx, filename in enumerate(FAILED_FILES, 1):
        print(f"Processing {filename} ({idx}/{total_files})...", end=" ", flush=True)
        
        try:
            # Process transcript
            quotes, input_tokens, output_tokens = process_transcript(filename, extraction_prompt)
            
            # Save quotes
            output_path = save_quotes(filename, quotes)
            
            # Update statistics
            processed_files += 1
            total_quotes += len(quotes)
            total_input_tokens += input_tokens
            total_output_tokens += output_tokens
            
            print(f"OK - {len(quotes)} quotes extracted")
            
        except json.JSONDecodeError as e:
            print(f"FAILED - JSON parsing error: {e}")
            failed_files.append((filename, f"JSON parsing error: {e}"))
            
        except Exception as e:
            print(f"FAILED - {e}")
            failed_files.append((filename, str(e)))
        
        # Rate limit delay (skip for last file)
        if idx < total_files:
            time.sleep(RATE_LIMIT_DELAY)
    
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
    
    # Calculate approximate cost
    input_cost = (total_input_tokens / 1_000_000) * COST_PER_1M_INPUT_TOKENS
    output_cost = (total_output_tokens / 1_000_000) * COST_PER_1M_OUTPUT_TOKENS
    total_cost = input_cost + output_cost
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Files processed:    {processed_files}/{total_files}")
    print(f"Total quotes:       {total_quotes}")
    print(f"Time elapsed:       {elapsed_str}")
    print(f"Input tokens:       {total_input_tokens:,}")
    print(f"Output tokens:      {total_output_tokens:,}")
    print(f"Approximate cost:   ${total_cost:.4f}")
    
    if failed_files:
        print(f"\nFailed files ({len(failed_files)}):")
        for filename, error in failed_files:
            print(f"  - {filename}: {error}")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
