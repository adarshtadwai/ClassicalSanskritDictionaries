#!/usr/bin/env python3
"""
Complete PDF to Enriched YAML Pipeline
Converts Sanskrit PDF to YAML using OCR, corrects errors with Claude, and enriches with metadata
"""

import sys
import argparse
from pathlib import Path
import yaml
import json
from anthropic import AnthropicVertex

# Import functions from existing scripts
from pdf_to_yaml import pdf_to_text, extract_slokas, create_yaml_output


def correct_sloka_with_claude(sloka_text, client):
    """
    Use Claude API (via Vertex AI) to correct OCR errors in a Sanskrit sloka

    Args:
        sloka_text: The sloka text with potential OCR errors
        client: Anthropic Vertex AI client

    Returns:
        Corrected sloka text
    """
    prompt = f"""You are a Sanskrit scholar expert in classical Sanskrit texts, particularly kosha (synonym dictionaries) like Amarakosha and Vaijayanti Kosha.

Below is a sloka extracted from OCR that may contain errors. Please correct any OCR errors while maintaining the exact meter and meaning. Common OCR errors in Devanagari include:
- ब/व confusion (ba/va)
- ष/श confusion (ṣa/śa)
- missing anusvara (ं) or visarga (ः)
- ि/ी confusion (i/ī)
- Incorrect matras

Return ONLY the corrected sloka text, nothing else. Keep the same structure with । and ॥ dandas.

Original sloka:
{sloka_text}

Corrected sloka:"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku@20241022",
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        corrected = message.content[0].text.strip()
        return corrected
    except Exception as e:
        print(f"Error correcting sloka: {e}")
        return sloka_text  # Return original if correction fails


def parse_sloka_with_claude(sloka_text, client):
    """
    Use Claude to parse a kosha sloka and extract semantic structure

    Args:
        sloka_text: The sloka to parse
        client: Anthropic Vertex AI client

    Returns:
        Dictionary with parsed entries
    """
    prompt = f"""You are a Sanskrit kosha (synonym dictionary) expert. Parse this sloka from a classical Sanskrit kosha and extract dictionary entries.

Sloka: {sloka_text}

Instructions:
1. Identify groups of synonyms (words with the same meaning)
2. For each group, determine:
   - The headword (main word for that concept)
   - All words in the group with their prātipadika (stem/root form)
   - The gender: m (masculine/पुं), f (feminine/स्त्री), n (neuter/नपुं)
3. Note any qualifiers or contextual information

Rules:
- Words ending in ः are typically masculine (m)
- Words ending in आ/ई are typically feminine (f)
- Words ending in म्‌ are typically neuter (n)
- Look for sandhi and vibhakti to identify word boundaries
- Group words that are synonyms (have the same meaning)
- Use ONLY these gender codes: m, f, n
- IMPORTANT: Write all Sanskrit words (head and prati fields) in Devanagari script, NOT in romanized transliteration

Return ONLY valid JSON in this exact format (no markdown, no explanation):
{{
  "entries": [
    {{
      "head": "prātipadika_of_headword",
      "gender": "m/f/n",
      "syns": [
        {{"prati": "word1", "gender": "m/f/n"}},
        {{"prati": "word2", "gender": "m/f/n"}}
      ]
    }}
  ]
}}

Example for: नागा बहुफणाः सर्पास्तेषां भोगवती पुरी॥
{{
  "entries": [
    {{
      "head": "सर्प",
      "gender": "m",
      "syns": [
        {{"prati": "नाग", "gender": "m"}},
        {{"prati": "बहुफण", "gender": "m"}},
        {{"prati": "सर्प", "gender": "m"}}
      ]
    }},
    {{
      "head": "भोगवती",
      "gender": "f",
      "qual": "तेषां",
      "syns": [
        {{"prati": "पुरी", "gender": "f"}}
      ]
    }}
  ]
}}

Now parse the given sloka and return JSON:"""

    try:
        message = client.messages.create(
            model="claude-3-5-haiku@20241022",
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text.strip()

        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            lines = response_text.split('\n')
            response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        if response_text.endswith('```'):
            response_text = response_text[:-3]

        response_text = response_text.strip()

        # Parse JSON
        parsed = json.loads(response_text)
        return parsed

    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from Claude: {e}")
        return {"entries": []}
    except Exception as e:
        print(f"Error parsing sloka: {e}")
        return {"entries": []}


def main():
    parser = argparse.ArgumentParser(
        description='Convert Sanskrit PDF to enriched YAML (OCR + AI correction + enrichment)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline: PDF → OCR → AI Correction → Enrichment → Final YAML
  python pdf_to_corrected_yaml.py \\
    Input/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.pdf \\
    -o Output/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.yaml \\
    --project-id my-project \\
    --title "लोकपालाध्यायः" \\
    --khanda "स्वर्गकाण्डः"

  # Skip enrichment step (only OCR + correction)
  python pdf_to_corrected_yaml.py \\
    Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \\
    -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \\
    --project-id my-project --skip-enrichment

Note: This script combines OCR, AI correction, and enrichment in a single step.
        """
    )

    parser.add_argument('input_pdf', help='Input PDF file path')
    parser.add_argument('-o', '--output', required=True,
                        help='Output enriched YAML file path')
    parser.add_argument('--project-id', required=True,
                        help='Google Cloud project ID')
    parser.add_argument('--region', default='us-east5',
                        help='Vertex AI region (default: us-east5)')
    parser.add_argument('--title', default='आदिदेवाध्यायः',
                        help='Title of the adhyaya')
    parser.add_argument('--khanda', default='स्वर्गकाण्डः',
                        help='Name of the khanda')
    parser.add_argument('-l', '--lang', default='san',
                        help='Language code for OCR (default: san for Sanskrit)')
    parser.add_argument('--skip-enrichment', action='store_true',
                        help='Skip the enrichment step (only OCR + correction)')

    args = parser.parse_args()

    # Check if input file exists
    if not Path(args.input_pdf).exists():
        print(f"Error: Input file not found: {args.input_pdf}")
        sys.exit(1)

    print("=" * 80)
    print("SANSKRIT PDF TO ENRICHED YAML PIPELINE")
    print("=" * 80)

    # Step 1: Extract text from PDF using OCR
    print("\n[1/5] Running OCR on PDF...")
    text_content = pdf_to_text(args.input_pdf, args.lang)

    # Step 2: Extract slokas from text
    print("\n[2/5] Extracting slokas from OCR text...")
    slokas = extract_slokas(text_content)
    print(f"Found {len(slokas)} slokas")

    # Step 3: Create temporary YAML structure
    print("\n[3/5] Creating temporary YAML structure...")
    yaml_data = create_yaml_output(slokas, args.title, args.khanda)

    # Step 4: Correct OCR errors with Claude
    print("\n[4/5] Correcting OCR errors with Claude AI...")
    print(f"Initializing Vertex AI client (region: {args.region})...")

    try:
        client = AnthropicVertex(region=args.region, project_id=args.project_id)
    except Exception as e:
        print(f"\nError: Failed to initialize Vertex AI client: {e}")
        print("\nMake sure you have:")
        print("1. Authenticated: gcloud auth application-default login")
        print("2. Enabled Claude models in Vertex AI Model Garden")
        sys.exit(1)

    # Correct each sloka
    corrected_data = {}
    total = len(yaml_data)
    for i, (sloka, metadata) in enumerate(yaml_data.items(), 1):
        print(f"Correcting sloka {i}/{total}...", end='\r')
        corrected_sloka = correct_sloka_with_claude(sloka, client)

        # Remove any newlines to ensure single-line format
        corrected_sloka = corrected_sloka.replace('\n', ' ')
        # Clean up multiple spaces
        corrected_sloka = ' '.join(corrected_sloka.split())
        # Normalize double danda: replace ।। (two singles) with ॥ (proper double)
        corrected_sloka = corrected_sloka.replace('।।', '॥')

        corrected_data[corrected_sloka] = {}

    print(f"\nCompleted correction of {total} slokas")

    # Step 5: Enrich with metadata (if not skipped)
    if not args.skip_enrichment:
        print("\n[5/5] Enriching with semantic metadata...")
        enriched_data = {}

        for i, (sloka, metadata) in enumerate(corrected_data.items(), 1):
            print(f"Parsing sloka {i}/{total}...", end='\r')

            parsed = parse_sloka_with_claude(sloka, client)

            # Add verify: false right after head for proofreading tracking
            for entry in parsed.get('entries', []):
                if 'head' in entry:
                    # Create ordered dict with verify right after head
                    new_entry = {'head': entry['head'], 'verify': False}
                    # Add remaining fields
                    for key, value in entry.items():
                        if key != 'head':
                            new_entry[key] = value
                    # Replace entry with ordered version
                    entry.clear()
                    entry.update(new_entry)

            enriched_data[sloka] = parsed

        print(f"\nCompleted enrichment of {total} slokas")
        final_data = enriched_data
    else:
        print("\n[5/5] Skipping enrichment step...")
        final_data = corrected_data

    # Write final YAML
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nWriting final YAML to: {args.output}")
    with open(args.output, 'w', encoding='utf-8') as f:
        yaml.dump(final_data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2, width=float('inf'))

    print("\n" + "=" * 80)
    print(f"✓ Successfully created YAML with {total} slokas")
    if not args.skip_enrichment:
        print(f"✓ Enriched with semantic metadata (headwords, synonyms, genders)")
    print(f"✓ Output saved to: {args.output}")
    print("=" * 80)


if __name__ == '__main__':
    main()
