# Sanskrit Dictionary Digitization Workflow

Complete step-by-step guide for digitizing classical Sanskrit dictionaries (Kosha) using OCR and AI-powered error correction.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Workflow Overview](#workflow-overview)
3. [Step-by-Step Guide](#step-by-step-guide)
4. [File Organization](#file-organization)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- macOS, Linux, or Windows with WSL
- Python 3.8 or higher
- Google Cloud Platform account (for Vertex AI)

### Software Installation

#### 1. Install Python Packages
```bash
# Core OCR and PDF processing
pip3 install PyPDF2 pdf2image pytesseract Pillow pyyaml

# For AI-powered error correction
pip3 install 'anthropic[vertex]'
```

#### 2. Install Tesseract OCR
```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu/Debian
sudo apt-get install tesseract-ocr tesseract-ocr-san

# Verify installation
tesseract --list-langs  # Should show 'san' for Sanskrit
```

#### 3. Set Up Google Cloud Authentication
```bash
# Login to Google Cloud
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set quota project
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

#### 4. Enable Claude in Vertex AI
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to: **Vertex AI → Model Garden**
3. Search for **"Anthropic"** or **"Claude"**
4. Click on **Claude 3.5 Haiku** (or other Claude models)
5. Click **Enable** to activate the model for your project

---

## Workflow Overview

```
┌─────────────────────┐
│  Source PDF Book    │
│  (Sanskrit Kosha)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step 1: Extract    │
│  Specific Pages     │
│  (extract_pdf_      │
│   pages.py)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Step 2: OCR +      │
│  AI Correction      │
│  (pdf_to_corrected_ │
│   yaml.py)          │
│                     │
│  Temp OCR YAML →    │
│  Claude AI →        │
│  Final YAML         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Final Corrected    │
│  YAML File          │
│  (Clean, no         │
│   metadata)         │
└─────────────────────┘
```

---

## Step-by-Step Guide

### Step 1: Extract Pages from PDF

Extract specific pages from your source Sanskrit dictionary PDF.

**Script:** `Scripts/AIGenerated/extract_pdf_pages.py`

**Command:**
```bash
python3 Scripts/AIGenerated/extract_pdf_pages.py \
  books/vaijayanti_kosa.pdf \
  -f 15 -t 16 \
  --kosha Vaijayanti_Kosha \
  --khanda 1_SvargaKhanda \
  --file 1_AdiDevaadhyaayah.pdf
```

**Parameters:**
- `books/vaijayanti_kosa.pdf` - Source PDF file
- `-f 15` - Starting page number (1-indexed)
- `-t 16` - Ending page number (inclusive)
- `--kosha` - Name of the dictionary (e.g., Vaijayanti_Kosha, Amarakosha)
- `--khanda` - Section name (e.g., 1_SvargaKhanda)
- `--file` - Output PDF filename

**Output:**
```
Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf
```

**What it does:**
- Extracts pages 15-16 from the source PDF
- Creates organized directory structure: `Input/[Kosha]/[Khanda]/`
- Saves the extracted pages as a new PDF file

---

### Step 2: OCR Extraction, AI Correction, and Enrichment (Combined)

Extract Sanskrit text from PDF using OCR, correct errors with Claude AI, and enrich with semantic metadata (word splitting, headwords, synonyms, genders - all in Devanagari script) in a single streamlined step.

**Script:** `Scripts/AIGenerated/pdf_to_corrected_yaml.py`

**Command (Full Pipeline with Enrichment):**
```bash
python3 Scripts/AIGenerated/pdf_to_corrected_yaml.py \
  Input/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.pdf \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.yaml \
  --project-id YOUR_GCP_PROJECT_ID \
  --title "लोकपालाध्यायः" \
  --khanda "स्वर्गकाण्डः"
```

**Command (Skip Enrichment - OCR + Correction Only):**
```bash
python3 Scripts/AIGenerated/pdf_to_corrected_yaml.py \
  Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \
  --project-id YOUR_GCP_PROJECT_ID \
  --skip-enrichment
```

**Parameters:**
- First argument: Input PDF file path
- `-o` - Output enriched YAML file path
- `--project-id` - Your Google Cloud Project ID
- `--region` - Vertex AI region (default: us-east5)
- `--title` - Chapter title in Devanagari (optional)
- `--khanda` - Section name in Devanagari (optional)
- `--skip-enrichment` - Skip enrichment step, only do OCR + correction (optional)

**Output:**
```
Output/Vaijayanti_Kosha/1_SvargaKhanda/2_Lokapaaladhyayah.yaml
```

**What it does:**
1. Converts PDF pages to images (300 DPI)
2. Runs Tesseract OCR with Sanskrit language model
3. Extracts complete slokas (verses ending with ॥)
4. Removes verse numbers
5. Creates temporary YAML structure (in memory, not saved)
6. Sends each sloka to Claude 3.5 Haiku via Vertex AI for correction
7. Claude corrects based on:
   - Sanskrit grammar rules
   - Poetic meter (chandas)
   - Context from kosha dictionaries
   - Common OCR error patterns
8. **[NEW]** Enriches with semantic metadata (all in Devanagari):
   - Splits slokas into word groups
   - Identifies headwords for each synonym group (in Devanagari)
   - Extracts prātipadika (stem form) for each word (in Devanagari)
   - Determines gender (m/f/n) for each word
   - Adds `verify: false` field for manual proofreading
9. Saves final enriched YAML with structured entries (Sanskrit fields in Devanagari)

**Example Final YAML Output (Enriched with Devanagari metadata):**
```yaml
इन्द्रो दुश्चबनो वज्री धृतराष्ट्रौ सभो दृढः । बद्धश्रवाः श्यैनासीरः सहस्राक्षो दिशः पतिः ॥:
  entries:
  - head: इन्द्र              # Headword in Devanagari
    verify: false           # Manual verification needed
    gender: m               # Masculine
    syns:
    - prati: इन्द्र         # Synonym stem in Devanagari
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

**Common OCR Errors Corrected:**
- ब/व confusion (ba/va)
- ष/श confusion (ṣa/śa)
- Missing anusvara (ं) or visarga (ः)
- ि/ी confusion (i/ī)
- Incorrect matras

**Performance:**
- OCR + Correction: ~2-3 seconds per sloka
- Enrichment: ~2-3 seconds per sloka
- **Total for 61 slokas: ~4-6 minutes** (with enrichment)
- **Total for 61 slokas: ~2-3 minutes** (without enrichment)
- Typical correction rate: 95-97% of slokas improved

---

### Alternative: Separate Steps (Legacy)

**Note:** The integrated pipeline above is recommended for most use cases. However, if you prefer to run steps separately, you can use the individual scripts:

**Step 2A: OCR Only**
```bash
python3 Scripts/AIGenerated/pdf_to_yaml.py \
  Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \
  -o /tmp/temp_ocr.yaml \
  --title "आदिदेवाध्यायः" \
  --khanda "स्वर्गकाण्डः"
```

**Step 2B: Correction Only**
```bash
python3 Scripts/AIGenerated/correct_ocr_errors_vertex.py \
  /tmp/temp_ocr.yaml \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \
  --project-id YOUR_GCP_PROJECT_ID
```

---

## File Organization

### Directory Structure
```
ClassicalSanskritDictionaries/
├── books/                          # Source PDF files
│   └── vaijayanti_kosa.pdf
│
├── Input/                          # Extracted PDF pages
│   └── Vaijayanti_Kosha/
│       └── 1_SvargaKhanda/
│           └── 1_AdiDevaadhyaayah.pdf
│
├── Output/                         # Processed YAML files (AI-corrected)
│   └── Vaijayanti_Kosha/
│       └── 1_SvargaKhanda/
│           └── 1_AdiDevaadhyaayah.yaml           # Final corrected YAML
│
└── Scripts/
    └── AIGenerated/                # Processing scripts
        ├── extract_pdf_pages.py
        ├── pdf_to_corrected_yaml.py # Combined OCR + correction (Recommended)
        ├── pdf_to_yaml.py           # OCR only (if needed separately)
        ├── correct_ocr_errors_vertex.py # Correction only (Vertex AI)
        └── correct_ocr_errors.py    # Correction only (Direct Anthropic API)
```

### Naming Conventions

**Kosha (Dictionary) Names:**
- `Vaijayanti_Kosha`
- `Amarakosha`
- Format: CamelCase with underscore

**Khanda (Section) Names:**
- `1_SvargaKhanda`
- `2_BhumiKhanda`
- Format: Number_SectionName

**Adhyaya (Chapter) Files:**
- `1_AdiDevaadhyaayah.pdf`
- `2_Bhuvanaadhyaayah.yaml`
- Format: Number_ChapterName.extension

---

## Troubleshooting

### Issue: Tesseract doesn't recognize Sanskrit

**Solution:**
```bash
# Check if Sanskrit is installed
tesseract --list-langs | grep san

# If not found, install language data
brew reinstall tesseract-lang  # macOS
```

### Issue: Claude models not found in Vertex AI

**Error:** `Publisher Model 'claude-3-5-haiku@20241022' was not found`

**Solution:**
1. Go to [Vertex AI Model Garden](https://console.cloud.google.com/vertex-ai/model-garden)
2. Search for "Anthropic" or "Claude"
3. Click on Claude model and enable it
4. Wait 2-3 minutes for activation

### Issue: Which model should I use?

**Available Claude Models:**
- **Claude 3.5 Haiku** - Fast, cost-effective (Recommended)
- **Claude 3.5 Sonnet** - More accurate for complex cases
- **Claude Sonnet 4.5** - Most capable (if available)

To test which models are available:
```bash
python3 Scripts/AIGenerated/test_vertex_models.py
```

### Issue: Authentication errors with Google Cloud

**Error:** `You do not currently have an active account selected`

**Solution:**
```bash
# Re-authenticate
gcloud auth application-default login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Set quota project
gcloud auth application-default set-quota-project YOUR_PROJECT_ID
```

### Issue: OCR quality is poor

**Possible causes and solutions:**

1. **Low resolution images:**
   - The script uses 300 DPI by default
   - For better quality, edit `pdf_to_yaml.py` and increase DPI to 400 or 600

2. **Poor quality source PDF:**
   - Use higher quality scans if available
   - Consider pre-processing images (contrast, brightness)

3. **Wrong language model:**
   - Verify Sanskrit is being used: `--lang san`
   - Check that Tesseract has the correct training data

### Issue: Slokas are split across multiple lines in YAML

**Solution:** Already fixed! The `width=float('inf')` parameter in `yaml.dump()` prevents line wrapping.

If you still see this issue, verify you're using the latest version of the scripts.

### Issue: Verse numbers appearing in slokas

**Solution:** The script automatically removes common number patterns:
- `॥ १॥` at the end
- `। १।` at the end
- Numbers before dandas

If numbers still appear, they may be in an unusual format. Check the sloka and modify the regex patterns in `extract_slokas()` function.

---

## Complete Example Workflow

Here's a complete example digitizing pages 15-16 of Vaijayanti Kosha:

```bash
# 1. Extract pages
python3 Scripts/AIGenerated/extract_pdf_pages.py \
  books/vaijayanti_kosa.pdf \
  -f 15 -t 16 \
  --kosha Vaijayanti_Kosha \
  --khanda 1_SvargaKhanda \
  --file 1_AdiDevaadhyaayah.pdf

# Verify extraction
ls Input/Vaijayanti_Kosha/1_SvargaKhanda/

# 2. Run OCR
python3 Scripts/AIGenerated/pdf_to_yaml.py \
  Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \
  --title "आदिदेवाध्यायः" \
  --khanda "स्वर्गकाण्डः"

# Verify OCR output
head -20 Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml

# 3. Correct OCR errors with AI
python3 Scripts/AIGenerated/correct_ocr_errors_vertex.py \
  Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah_corrected.yaml \
  --project-id YOUR_PROJECT_ID

# Compare results
echo "Original OCR slokas:"
grep -c ": {}" Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml

echo "Corrected slokas:"
grep -c "corrected: true" Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah_corrected.yaml
```

**Expected output:**
```
✓ Extracted pages 15-16 to Input/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.pdf
✓ Created YAML with 65 slokas
✓ Corrected 63/65 slokas (97% improvement rate)
```

---

## Alternative: Using Direct Anthropic API

If you prefer not to use Vertex AI, you can use the direct Anthropic API:

### Setup
```bash
# Get API key from https://console.anthropic.com
export ANTHROPIC_API_KEY=your_api_key_here
```

### Usage
```bash
python3 Scripts/AIGenerated/correct_ocr_errors.py \
  Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah.yaml \
  -o Output/Vaijayanti_Kosha/1_SvargaKhanda/1_AdiDevaadhyaayah_corrected.yaml
```

**Note:** This uses Claude 3.5 Sonnet and will incur costs directly through Anthropic.

---

## Cost Estimation

### Vertex AI (Recommended)
- **Claude 3.5 Haiku:** ~$0.001 per sloka
- **For 65 slokas:** ~$0.065 (less than 7 cents)
- **For 1000 slokas:** ~$1.00

### Direct Anthropic API
- **Claude 3.5 Sonnet:** ~$0.003 per sloka
- **For 65 slokas:** ~$0.20
- **For 1000 slokas:** ~$3.00

Prices are approximate and subject to change. Check current pricing at:
- [Vertex AI Pricing](https://cloud.google.com/vertex-ai/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)

---

## Tips for Best Results

1. **Use high-quality source PDFs** - 300+ DPI scans work best
2. **Extract reasonable page ranges** - 1-5 pages at a time for manageable processing
3. **Review corrections** - While AI is accurate, always spot-check critical texts
4. **Organize by hierarchy** - Follow Kosha → Khanda → Adhyaya structure
5. **Keep original OCR** - The corrected YAML preserves originals for reference
6. **Version control** - Use git to track changes to corrected texts

---

## Next Steps

After digitization, you can:
1. **Build a searchable database** - Import YAML into MongoDB or PostgreSQL
2. **Create a web interface** - Display slokas with search functionality
3. **Add annotations** - Enhance metadata with meanings, cross-references
4. **Link related slokas** - Connect synonyms across different koshas
5. **Generate concordance** - Create word indices and frequency lists

---

## License

This workflow and associated scripts are part of the Classical Sanskrit Dictionaries project.

## Credits

- OCR: Tesseract OCR with Sanskrit language data
- AI Correction: Claude (Anthropic) via Google Cloud Vertex AI
- PDF Processing: PyPDF2, pdf2image
