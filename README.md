# Classical Sanskrit Dictionaries

A toolkit for digitizing and processing classical Sanskrit dictionaries (Kosha) using OCR and AI-powered error correction.

## Overview

This project provides scripts to:
- Extract pages from Sanskrit dictionary PDFs
- Convert scanned PDFs to structured YAML format using OCR
- Correct OCR errors using Claude AI (via Anthropic API or Google Cloud Vertex AI)
- **Enrich with semantic metadata** (word splitting, headwords, synonyms, genders)
- Organize dictionaries by Kosha → Khanda → Adhyaya
- **All-in-one pipeline**: Single command for complete PDF → enriched YAML transformation

## Project Structure

```
ClassicalSanskritDictionaries/
├── books/                  # Source PDF files
├── Input/                  # Extracted PDF pages organized by Kosha
│   └── Vaijayanti_Kosha/
│       └── 1_SvargaKhanda/
│           └── 1_AdiDevaadhyaayah.pdf
├── Output/                 # Processed YAML files
│   └── Vaijayanti_Kosha/
│       └── 1_SvargaKhanda/
│           └── 1_AdiDevaadhyaayah.yaml
└── Scripts/
    └── AIGenerated/        # Processing scripts
```

## Scripts

### 1. Extract PDF Pages
Extract specific pages from a dictionary PDF:

```bash
python3 Scripts/AIGenerated/extract_pdf_pages.py \\
  books/vaijayanti_kosa.pdf \\
  -f 17 -t 18 \\
  --kosha Vaijayanti_Kosha \\
  --khanda 1_SvargaKhanda \\
  --file 2_Lokapaaladhyayah.pdf
```

### 2. OCR + Correction + Enrichment (Recommended - All-in-One)
Convert Sanskrit PDF to enriched YAML with word splitting, headwords, and genders (all Sanskrit metadata in Devanagari):

```bash
python3 Scripts/AIGenerated/pdf_to_corrected_yaml.py \\
  Input/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.pdf \\
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.yaml \\
  --project-id YOUR_GCP_PROJECT_ID \\
  --title "लोकपालाध्यायः" \\
  --khanda "स्वर्गकाण्डः"
```

**Skip enrichment (OCR + correction only):**
```bash
python3 Scripts/AIGenerated/pdf_to_corrected_yaml.py \\
  Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \\
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \\
  --project-id YOUR_GCP_PROJECT_ID \\
  --skip-enrichment
```

### 3. Alternative: Separate Steps (Legacy)

**OCR Only:**
```bash
python3 Scripts/AIGenerated/pdf_to_yaml.py \\
  Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \\
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \\
  --title "आदिदेवाध्यायः" \\
  --khanda "स्वर्गकाण्डः"
```

**Correction (Vertex AI):**
```bash
python3 Scripts/AIGenerated/correct_ocr_errors_vertex.py \\
  Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \\
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah_corrected.yaml \\
  --project-id YOUR_GCP_PROJECT_ID
```

**Enrichment Only:**
```bash
python3 Scripts/AIGenerated/enrich_with_metadata.py \\
  Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \\
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah_enriched.yaml \\
  --project-id YOUR_GCP_PROJECT_ID
```

**Correction (Anthropic API):**
```bash
export ANTHROPIC_API_KEY=your_key_here
python3 Scripts/AIGenerated/correct_ocr_errors.py \\
  input.yaml -o corrected.yaml
```

## Installation

### Prerequisites
```bash
# Python packages
pip3 install PyPDF2 pdf2image pytesseract Pillow pyyaml anthropic

# For Vertex AI support
pip3 install 'anthropic[vertex]'

# System dependencies (macOS)
brew install tesseract tesseract-lang

# For Sanskrit OCR
brew install tesseract-lang  # Includes Sanskrit
```

### Authentication

**For Vertex AI:**
```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
```

**For Anthropic API:**
```bash
export ANTHROPIC_API_KEY=your_api_key
```

## YAML Format

### Basic Format (OCR only or with `--skip-enrichment`)
```yaml
स्वर्गं नाकः सुरालयः त्रिदिवं त्रिविष्टपम् ॥: {}
देवा विबुधाः त्रिदशाः सुराः अमराः ॥: {}
```

### Enriched Format (Default - with semantic metadata in Devanagari)
```yaml
इन्द्रो दुश्चबनो वज्री धृतराष्ट्रौ सभो दृढः । बद्धश्रवाः श्यैनासीरः सहस्राक्षो दिशः पतिः ॥:
  entries:
  - head: इन्द्र              # Headword in Devanagari
    verify: false           # Manual verification flag
    gender: m               # Gender: m/f/n
    syns:
    - prati: इन्द्र         # Synonym prātipadika in Devanagari
      gender: m
    - prati: दुश्चबन
      gender: m
    - prati: वज्रिन्
      gender: m
  - head: राष्ट्र
    verify: false
    gender: m
    syns:
    - prati: धृतराष्ट्र
      gender: m
    - prati: सभा
      gender: f
    qual: dṛḍha (firm/strong)
```

**Fields:**
- `head`: Headword (main word for the synonym group)
- `verify`: Boolean flag for manual verification (default: false)
- `gender`: m (masculine), f (feminine), n (neuter)
- `syns`: List of synonyms with their prātipadika (stem form) and gender
- `qual`: Optional qualifier or contextual information

## Features

- **Automatic OCR**: Extracts Sanskrit text from scanned PDFs using Tesseract
- **AI Error Correction**: Uses Claude to fix common OCR errors (ब/व confusion, missing anusvara, etc.)
- **Semantic Enrichment**: AI-powered word splitting, headword extraction, and gender identification
- **Structured Output**: Organizes data by Kosha → Khanda → Adhyaya
- **Verification Tracking**: Adds `verify: false` field for manual proofreading workflow
- **Complete Slokas**: Properly combines lines ending with double danda (॥)
- **Integrated Pipeline**: Single command for complete PDF → enriched YAML transformation

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Add your license here]

## Acknowledgments

- OCR powered by Tesseract
- Error correction powered by Claude AI (Anthropic)
- Sanskrit text from archive.org
