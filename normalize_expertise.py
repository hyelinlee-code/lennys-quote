"""
Normalize expertise values in speaker profiles to a standard list
"""

import os
import json
import time
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
INPUT_FILE = "speaker_profiles_generated.json"
OUTPUT_FILE = "speaker_profiles.json"

# Rate limit delay for GPT calls
RATE_LIMIT_DELAY = 0.5

# Standard expertise list (24 items)
STANDARD_EXPERTISE = [
    "Product Strategy",
    "Product Management",
    "Product Design",
    "Growth Strategy",
    "Marketing Strategy",
    "Go-to-Market",
    "Sales Strategy",
    "Engineering Leadership",
    "User Experience",
    "Data Analytics",
    "AI/ML Products",
    "B2B SaaS",
    "Consumer Products",
    "Marketplace",
    "Executive Coaching",
    "Leadership Development",
    "Team Building",
    "Company Building",
    "Fundraising",
    "Venture Capital",
    "Community Building",
    "Monetization",
    "Operations",
    "Career Development",
]

# Mapping rules: original expertise -> standard expertise
EXPERTISE_MAPPING = {
    # Product related
    "Product Development": "Product Management",
    "Product Leadership": "Product Strategy",
    "Product Innovation": "Product Strategy",
    "Product Marketing": "Marketing Strategy",
    "Product Roadmapping": "Product Management",
    "Product-Led Growth": "Growth Strategy",
    "Product Growth Strategy": "Growth Strategy",
    "Product Prioritization": "Product Management",
    "Product Experimentation": "Product Management",
    "Product Vision": "Product Strategy",
    "Product Thinking": "Product Strategy",
    "Product Operations": "Product Management",
    "Product Discovery": "Product Management",
    "Product Analytics": "Data Analytics",
    "Algorithmic Product Management": "Product Management",
    "Product Management in AI": "AI/ML Products",
    "AI Integration in Product Development": "AI/ML Products",
    "AI-powered software development": "AI/ML Products",
    "Product management implications of AI": "AI/ML Products",
    "AI Product Development": "AI/ML Products",
    "AI Product Strategy": "AI/ML Products",
    "AI Product Management": "AI/ML Products",
    "AI Strategy": "AI/ML Products",
    "AI Coding Agents": "AI/ML Products",
    "AI Automation": "AI/ML Products",
    "AI in Product Development": "AI/ML Products",
    "AI-driven Products": "AI/ML Products",
    "Machine Learning": "AI/ML Products",
    "LLM Applications": "AI/ML Products",
    "Generative AI": "AI/ML Products",
    
    # Growth related
    "Growth": "Growth Strategy",
    "Growth Marketing": "Growth Strategy",
    "Startup Growth Strategy": "Growth Strategy",
    "User Growth Strategy": "Growth Strategy",
    "B2B SaaS Growth": "Growth Strategy",
    "Consumer Subscription Growth": "Growth Strategy",
    "User Retention Strategies": "Growth Strategy",
    "User Acquisition Growth": "Growth Strategy",
    "User Acquisition": "Growth Strategy",
    "Retention Strategies": "Growth Strategy",
    "Activation Strategies": "Growth Strategy",
    "Growth Loops": "Growth Strategy",
    "Viral Growth": "Growth Strategy",
    "Organic Growth": "Growth Strategy",
    "PLG": "Growth Strategy",
    "Product-led Growth": "Growth Strategy",
    "Growth Experimentation": "Growth Strategy",
    "Growth Hacking": "Growth Strategy",
    "Experimentation": "Growth Strategy",
    "Experimentation Frameworks": "Growth Strategy",
    "A/B Testing": "Growth Strategy",
    
    # Marketing related
    "Marketing": "Marketing Strategy",
    "B2B SaaS Marketing": "Marketing Strategy",
    "B2B Marketing": "Marketing Strategy",
    "Content Marketing": "Marketing Strategy",
    "Brand Marketing": "Marketing Strategy",
    "Brand Strategy": "Marketing Strategy",
    "Brand Building": "Marketing Strategy",
    "Brand Positioning": "Marketing Strategy",
    "Positioning": "Marketing Strategy",
    "Messaging": "Marketing Strategy",
    "Storytelling": "Marketing Strategy",
    "Strategic Messaging": "Marketing Strategy",
    "Strategic Storytelling": "Marketing Strategy",
    "Strategic Narrative": "Marketing Strategy",
    "Narrative Strategy": "Marketing Strategy",
    "Category Design": "Marketing Strategy",
    "Category Creation": "Marketing Strategy",
    "Demand Generation": "Marketing Strategy",
    "Performance Marketing": "Marketing Strategy",
    "SEO": "Marketing Strategy",
    "SEO Strategy": "Marketing Strategy",
    "Podcast Marketing": "Marketing Strategy",
    "Influencer Marketing": "Marketing Strategy",
    
    # Go-to-Market
    "Go-to-Market Strategy": "Go-to-Market",
    "GTM Strategy": "Go-to-Market",
    "GTM": "Go-to-Market",
    "Launch Strategy": "Go-to-Market",
    "Market Entry": "Go-to-Market",
    "Market Expansion": "Go-to-Market",
    "International Expansion": "Go-to-Market",
    
    # Sales related
    "Sales": "Sales Strategy",
    "Sales Leadership": "Sales Strategy",
    "Enterprise Sales": "Sales Strategy",
    "B2B Sales": "Sales Strategy",
    "Sales Enablement": "Sales Strategy",
    "Sales Operations": "Sales Strategy",
    "Revenue Operations": "Sales Strategy",
    "Revenue Growth": "Sales Strategy",
    "Customer Success": "Sales Strategy",
    "Account Management": "Sales Strategy",
    
    # Engineering related
    "Engineering": "Engineering Leadership",
    "Engineering Management": "Engineering Leadership",
    "Software Development": "Engineering Leadership",
    "Software Development Acceleration": "Engineering Leadership",
    "Technical Leadership": "Engineering Leadership",
    "Tech Strategy": "Engineering Leadership",
    "Platform Engineering": "Engineering Leadership",
    "Developer Experience": "Engineering Leadership",
    "Developer Tools": "Engineering Leadership",
    "Developer community building": "Community Building",
    "Infrastructure": "Engineering Leadership",
    "System Design": "Engineering Leadership",
    "Architecture": "Engineering Leadership",
    
    # Design/UX related
    "Design": "Product Design",
    "UX Design": "User Experience",
    "UI Design": "User Experience",
    "UX/UI Design": "User Experience",
    "User Experience Design": "User Experience",
    "Design Leadership": "Product Design",
    "Design Strategy": "Product Design",
    "Design Thinking": "Product Design",
    "Visual Design": "Product Design",
    "Interaction Design": "User Experience",
    "Research": "User Experience",
    "User Research": "User Experience",
    "Customer Research": "User Experience",
    "Jobs-to-be-Done": "User Experience",
    
    # Data/Analytics related
    "Analytics": "Data Analytics",
    "Data Science": "Data Analytics",
    "Data Strategy": "Data Analytics",
    "Business Intelligence": "Data Analytics",
    "Metrics": "Data Analytics",
    "KPIs": "Data Analytics",
    "OKRs": "Data Analytics",
    "Measurement": "Data Analytics",
    
    # B2B SaaS
    "B2B SaaS": "B2B SaaS",
    "SaaS": "B2B SaaS",
    "SaaS Strategy": "B2B SaaS",
    "Enterprise Software": "B2B SaaS",
    "Enterprise Strategy": "B2B SaaS",
    
    # Consumer
    "Consumer Products": "Consumer Products",
    "Consumer Tech": "Consumer Products",
    "Consumer Apps": "Consumer Products",
    "Mobile Apps": "Consumer Products",
    "Social Products": "Consumer Products",
    "Media": "Consumer Products",
    "Entertainment": "Consumer Products",
    "Gaming": "Consumer Products",
    "Subscription Products": "Consumer Products",
    "Subscription Business": "Consumer Products",
    
    # Marketplace
    "Marketplace": "Marketplace",
    "Marketplace Strategy": "Marketplace",
    "B2B Marketplace Strategy": "Marketplace",
    "Two-sided Marketplaces": "Marketplace",
    "Platform Strategy": "Marketplace",
    "Network Effects": "Marketplace",
    
    # Coaching/Leadership Development
    "Executive Coaching": "Executive Coaching",
    "Coaching": "Executive Coaching",
    "Performance Coaching": "Executive Coaching",
    "Career Coaching": "Executive Coaching",
    "Leadership Coaching": "Executive Coaching",
    "Leadership Development": "Leadership Development",
    "Management Development": "Leadership Development",
    "Manager Development": "Leadership Development",
    "Leadership": "Leadership Development",
    "Leadership Skills": "Leadership Development",
    "Leadership Transitions": "Leadership Development",
    "Personal Development": "Leadership Development",
    "Self-improvement": "Leadership Development",
    "Performance Management": "Leadership Development",
    "Feedback": "Leadership Development",
    "Communication": "Leadership Development",
    "Communication Skills": "Leadership Development",
    "Presentation Skills": "Leadership Development",
    "Public Speaking": "Leadership Development",
    "Negotiation": "Leadership Development",
    "Influence": "Leadership Development",
    "Decision Making": "Leadership Development",
    "Strategic Thinking": "Leadership Development",
    "Mental Health Advocacy": "Leadership Development",
    "Burnout Prevention": "Leadership Development",
    "Work-Life Balance": "Leadership Development",
    "Mindfulness": "Leadership Development",
    "Emotional Intelligence": "Leadership Development",
    
    # Team Building
    "Team Building": "Team Building",
    "Team Management": "Team Building",
    "Team Leadership": "Team Building",
    "Team Culture": "Team Building",
    "Team Dynamics": "Team Building",
    "Hiring": "Team Building",
    "Recruiting": "Team Building",
    "Talent Acquisition": "Team Building",
    "Talent Management": "Team Building",
    "People Management": "Team Building",
    "People Operations": "Team Building",
    "Organizational Design": "Team Building",
    "Org Design": "Team Building",
    "Culture Building": "Team Building",
    "Company Culture": "Team Building",
    "Remote Work": "Team Building",
    "Distributed Teams": "Team Building",
    
    # Company Building
    "Company Building": "Company Building",
    "Startup Strategy": "Company Building",
    "Startup Building": "Company Building",
    "Startup Advice": "Company Building",
    "Entrepreneurship": "Company Building",
    "Founder Journey": "Company Building",
    "Founder Coaching": "Company Building",
    "Founder Experience": "Company Building",
    "CEO Coaching": "Company Building",
    "Business Strategy": "Company Building",
    "Corporate Strategy": "Company Building",
    "Strategic Planning": "Company Building",
    "Business Acquisition": "Company Building",
    "M&A": "Company Building",
    "Scaling Companies": "Company Building",
    "Scaling Startups": "Company Building",
    "Scaling Organizations": "Company Building",
    "Hypergrowth": "Company Building",
    "IPO": "Company Building",
    "Exit Strategy": "Company Building",
    
    # Fundraising/VC
    "Fundraising": "Fundraising",
    "Startup Fundraising": "Fundraising",
    "Seed Fundraising": "Fundraising",
    "Series A": "Fundraising",
    "Pitch Decks": "Fundraising",
    "Investor Relations": "Fundraising",
    "Venture Capital": "Venture Capital",
    "VC": "Venture Capital",
    "Angel Investing": "Venture Capital",
    "Startup Investing": "Venture Capital",
    "Investment Strategy": "Venture Capital",
    
    # Community
    "Community Building": "Community Building",
    "Community Management": "Community Building",
    "Community Growth": "Community Building",
    "Creator Economy": "Community Building",
    "Content Creation": "Community Building",
    "Newsletter Growth": "Community Building",
    "Audience Building": "Community Building",
    
    # Monetization
    "Monetization": "Monetization",
    "Pricing": "Monetization",
    "Pricing Strategy": "Monetization",
    "Revenue Strategy": "Monetization",
    "Business Models": "Monetization",
    "Unit Economics": "Monetization",
    "Financial Strategy": "Monetization",
    
    # Operations
    "Operations": "Operations",
    "Business Operations": "Operations",
    "Operational Excellence": "Operations",
    "Process Improvement": "Operations",
    "Supply Chain": "Operations",
    "Logistics": "Operations",
    "Customer Operations": "Operations",
    "Support Operations": "Operations",
    
    # Career
    "Career Development": "Career Development",
    "Career Growth": "Career Development",
    "Career Transitions": "Career Development",
    "Career Strategy": "Career Development",
    "Professional Development": "Career Development",
    "Job Search": "Career Development",
    "Interview Skills": "Career Development",
}

# Create lowercase lookup for case-insensitive matching
EXPERTISE_MAPPING_LOWER = {k.lower(): v for k, v in EXPERTISE_MAPPING.items()}

# Cache for GPT-suggested mappings
gpt_mapping_cache = {}


def normalize_expertise_direct(expertise):
    """Try to normalize expertise using direct mapping rules."""
    # Check exact match
    if expertise in EXPERTISE_MAPPING:
        return EXPERTISE_MAPPING[expertise]
    
    # Check case-insensitive match
    if expertise.lower() in EXPERTISE_MAPPING_LOWER:
        return EXPERTISE_MAPPING_LOWER[expertise.lower()]
    
    # Check if it's already a standard expertise
    if expertise in STANDARD_EXPERTISE:
        return expertise
    
    # Check case-insensitive standard expertise match
    for std in STANDARD_EXPERTISE:
        if expertise.lower() == std.lower():
            return std
    
    return None


def normalize_expertise_gpt(expertise):
    """Use GPT to suggest best matching standard expertise."""
    global gpt_mapping_cache
    
    # Check cache first
    if expertise in gpt_mapping_cache:
        return gpt_mapping_cache[expertise]
    
    prompt = f"""Given this expertise: "{expertise}"

Choose the BEST matching category from this list:
{json.dumps(STANDARD_EXPERTISE, indent=2)}

Rules:
- Pick the SINGLE best match
- If nothing fits well, pick the closest category
- Return ONLY the exact category name from the list, nothing else

Best match:"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=50
        )
        
        suggestion = response.choices[0].message.content.strip()
        
        # Clean up suggestion (remove quotes, extra text)
        suggestion = suggestion.strip('"\'')
        
        # Validate it's in our standard list
        for std in STANDARD_EXPERTISE:
            if suggestion.lower() == std.lower():
                gpt_mapping_cache[expertise] = std
                return std
        
        # Partial match
        for std in STANDARD_EXPERTISE:
            if std.lower() in suggestion.lower() or suggestion.lower() in std.lower():
                gpt_mapping_cache[expertise] = std
                return std
        
        # Default fallback
        gpt_mapping_cache[expertise] = "Product Strategy"
        return "Product Strategy"
        
    except Exception as e:
        print(f"GPT error for '{expertise}': {e}")
        return "Product Strategy"


def normalize_speaker_expertise(expertise_list):
    """Normalize a list of expertise values for a speaker."""
    normalized = []
    
    for exp in expertise_list:
        # Try direct mapping first
        norm = normalize_expertise_direct(exp)
        
        if norm:
            if norm not in normalized:
                normalized.append(norm)
        else:
            # Use GPT for ambiguous cases
            norm = normalize_expertise_gpt(exp)
            if norm and norm not in normalized:
                normalized.append(norm)
    
    # Keep max 3 expertise per speaker
    return normalized[:3]


def main():
    """Main function to normalize expertise values."""
    print("=" * 60)
    print("Normalizing Speaker Expertise Values")
    print("=" * 60)
    
    # Load input file
    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        profiles = json.load(f)
    
    print(f"\nLoaded {len(profiles)} speaker profiles from {INPUT_FILE}")
    
    # Collect all unique expertise values
    all_expertise = set()
    for profile in profiles.values():
        all_expertise.update(profile.get('expertise', []))
    
    print(f"Original unique expertise values: {len(all_expertise)}")
    print(f"Standard expertise categories: {len(STANDARD_EXPERTISE)}")
    print(f"Manual mapping rules: {len(EXPERTISE_MAPPING)}")
    
    # Statistics
    start_time = datetime.now()
    direct_mappings = 0
    gpt_mappings = 0
    processed_speakers = 0
    
    # Process each speaker
    normalized_profiles = {}
    
    print(f"\nProcessing speakers...\n")
    
    for speaker, profile in profiles.items():
        original_expertise = profile.get('expertise', [])
        
        # Track which method was used
        for exp in original_expertise:
            if normalize_expertise_direct(exp):
                direct_mappings += 1
            else:
                gpt_mappings += 1
                # Small delay for GPT calls
                time.sleep(RATE_LIMIT_DELAY)
        
        # Normalize expertise
        normalized_expertise = normalize_speaker_expertise(original_expertise)
        
        # Create normalized profile
        normalized_profiles[speaker] = {
            "function": profile.get('function', 'Leadership'),
            "expertise": normalized_expertise
        }
        
        processed_speakers += 1
        
        # Progress indicator every 50 speakers
        if processed_speakers % 50 == 0:
            print(f"  Processed {processed_speakers}/{len(profiles)} speakers...")
    
    # Calculate elapsed time
    end_time = datetime.now()
    elapsed = end_time - start_time
    elapsed_str = str(elapsed).split('.')[0]
    
    # Collect final expertise distribution
    final_expertise = {}
    for profile in normalized_profiles.values():
        for exp in profile.get('expertise', []):
            final_expertise[exp] = final_expertise.get(exp, 0) + 1
    
    # Save normalized profiles
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(normalized_profiles, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Speakers processed:       {processed_speakers}")
    print(f"Original unique values:   {len(all_expertise)}")
    print(f"Normalized to:            {len(final_expertise)} categories")
    print(f"Direct mappings used:     {direct_mappings}")
    print(f"GPT mappings used:        {gpt_mappings}")
    print(f"Time elapsed:             {elapsed_str}")
    print(f"Output file:              {OUTPUT_FILE}")
    
    # Show expertise distribution
    print("\nExpertise Distribution (top 15):")
    sorted_expertise = sorted(final_expertise.items(), key=lambda x: -x[1])
    for exp, count in sorted_expertise[:15]:
        bar = "█" * min(count // 2, 30)
        print(f"  {exp:25} {count:3} {bar}")
    
    # Show any expertise that didn't get normalized properly
    unexpected = [exp for exp in final_expertise if exp not in STANDARD_EXPERTISE]
    if unexpected:
        print(f"\nWarning: {len(unexpected)} expertise values not in standard list:")
        for exp in unexpected:
            print(f"  - {exp}")
    
    # Show GPT mapping cache
    if gpt_mapping_cache:
        print(f"\nGPT-suggested mappings ({len(gpt_mapping_cache)}):")
        for original, mapped in list(gpt_mapping_cache.items())[:10]:
            print(f"  '{original}' -> '{mapped}'")
        if len(gpt_mapping_cache) > 10:
            print(f"  ... and {len(gpt_mapping_cache) - 10} more")
    
    print("\nDone!")


if __name__ == "__main__":
    main()
