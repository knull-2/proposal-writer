# AI Proposal Writer Pro — Enterprise Edition

> Generate professional, enterprise-grade business proposals and project reports as branded PDFs in seconds — powered by Google Gemini AI.

Built by **Vishvesh Prakash**

---

## What It Does

Fill in a form → AI writes a fully structured, professional document → Downloads as a clean branded PDF instantly.

No templates to fill manually. No Word formatting headaches. Just describe the project and get a client-ready proposal.

---

## Features

- AI-generated proposals and reports using Google Gemini
- 12 enterprise sections — Executive Summary, Tech Stack, Risk Management, Legal Terms, KPIs, and more
- 3 colour themes — Navy, Dark/Red, Green
- Clean PDF with branded header, footer, cover page, and metadata
- Auto-generated Proposal ID and version number
- Realistic INR pricing ranges (no placeholder junk)
- Optional fields — Industry, Budget Range, Timeline, Prepared By
- Generated PDFs saved automatically to `/output` folder

---

## Project Structure

```
proposal-writer/
├── main.py                 # FastAPI app and Gemini AI integration
├── pdf_generator_v2.py     # Enterprise PDF builder (ReportLab)
├── requirements.txt        # Python dependencies
├── README.md               # This file
├── LICENSE                 # Proprietary license
├── start.bat               # One-click launcher (Windows)
├── .gitignore              # Git ignore rules
└── static/
    └── index.html          # Frontend UI
└── output/                 # Generated PDFs saved here (auto-created)
```

---

## Setup & Run

### 1. Prerequisites
- Python 3.12 (recommended — do NOT use 3.14)
- A free Google Gemini API key

### 2. Get Your Free Gemini API Key
1. Go to **https://aistudio.google.com/apikey**
2. Sign in with your Google account
3. Click **"Create API Key"**
4. Copy the key — it looks like `AIzaSy...`

### 3. Create a Virtual Environment

```bash
cd proposal-writer
python -m venv venv
```

Activate it:
```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

You'll see `(venv)` appear at the start of your terminal line.

### 4. Install Dependencies

```bash
pip install -r requirements.txt
pip install google-genai
```

### 5. Set Your Gemini API Key

```bash
# Windows
set GEMINI_API_KEY=AIzaSyYour-key-here

# Mac/Linux
export GEMINI_API_KEY=AIzaSyYour-key-here
```

### 6. Run the Server

```bash
uvicorn main:app --reload --port 8000
```

Open your browser and go to: **http://localhost:8000**

---

## One-Click Start (Windows)

Instead of running all the steps every time, just double-click `start.bat`.

Create a file called `start.bat` in your project folder:

```bat
@echo off
cd /d "C:\path\to\proposal-writer"
call venv\Scripts\activate
set GEMINI_API_KEY=AIzaSyYour-key-here
echo Starting AI Proposal Writer...
start http://localhost:8000
uvicorn main:app --port 8000
pause
```

Replace the path and API key with your actual values.

> ⚠️ Do NOT commit start.bat to GitHub — it contains your API key. It is already listed in .gitignore.

---

## API Usage

### Endpoint
```
POST /generate-report
```

### Request Body
```json
{
  "client_name": "TechStart India Pvt. Ltd.",
  "project_description": "Build a food delivery app with customer, restaurant, and delivery partner modules.",
  "report_type": "proposal",
  "template_id": "default",
  "industry": "Food Tech",
  "budget_range": "INR 15-20 Lakhs",
  "timeline_preference": "6 months",
  "prepared_by": "Vishvesh Prakash, Consultant"
}
```

### Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `client_name` | string | ✅ | Client or company name |
| `project_description` | string | ✅ | Detailed project description |
| `report_type` | string | ✅ | `"proposal"` or `"report"` |
| `template_id` | string | ❌ | `"default"`, `"dark"`, or `"green"` |
| `industry` | string | ❌ | Industry sector for better AI context |
| `budget_range` | string | ❌ | Client budget for realistic pricing |
| `timeline_preference` | string | ❌ | Preferred delivery timeline |
| `prepared_by` | string | ❌ | Author name shown on document |

### curl Example
```bash
curl -X POST http://localhost:8000/generate-report \
  -H "Content-Type: application/json" \
  -d '{
    "client_name": "Acme Corp",
    "project_description": "E-commerce platform with inventory management and analytics dashboard",
    "report_type": "proposal",
    "template_id": "default"
  }' \
  --output proposal.pdf
```

---

## Available Templates

| ID | Colours | Best For |
|----|---------|----------|
| `default` | Navy + Blue | General consulting, IT services |
| `dark` | Dark + Red | Tech startups, agencies |
| `green` | Forest Green | Sustainability, agri, healthcare |

---

## AI Model

Uses **Google Gemini** via the official `google-genai` SDK.

Model priority (tries in order, falls back automatically):
1. `gemini-2.5-flash` — best quality
2. `gemini-2.0-flash` — fast and reliable
3. `gemini-2.0-flash-lite` — lightweight fallback

Free tier: ~200 requests/day on gemini-2.0-flash.
Add billing at **https://aistudio.google.com** for unlimited usage (costs approx ₹0.10–0.50 per report).

---

## API Docs (Auto-generated)

FastAPI generates interactive docs automatically:
- Swagger UI: **http://localhost:8000/docs**
- ReDoc: **http://localhost:8000/redoc**

---

## Every Time You Return to This Project

```bash
# 1. Navigate to project folder
cd proposal-writer

# 2. Activate virtual environment
venv\Scripts\activate          # Windows
source venv/bin/activate       # Mac/Linux

# 3. Set API key
set GEMINI_API_KEY=AIzaSy...   # Windows
export GEMINI_API_KEY=AIzaSy...  # Mac/Linux

# 4. Start server
uvicorn main:app --reload --port 8000
```

Or just double-click `start.bat` on Windows.

---

## Roadmap

- [ ] User login and accounts
- [ ] Razorpay payment integration
- [ ] Usage limits per subscription tier
- [ ] Custom logo upload
- [ ] More templates and themes
- [ ] Deploy to cloud (Render / Railway)
- [ ] White-label support for agencies

---

## Author

**Vishvesh Prakash**
GitHub: [@VishveshPrakash](https://github.com/VishveshPrakash)

---

## License

This project is proprietary software. See [LICENSE](LICENSE) for full terms.
