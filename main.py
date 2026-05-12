import os
import re
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from google.genai import types

from pdf_generator import generate_pdf

# ── Setup ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="AI Proposal & Report Writer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

# Configure Gemini client
gemini = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

# ── Models ─────────────────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    client_name: str
    project_description: str
    report_type: str = "proposal"   # "proposal" or "report"
    template_id: str = "default"

# ── Prompt ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional business consultant and technical writer.
Generate structured, polished documents in Markdown. Be concise yet thorough.
Use ## for section headings. Use bullet points where appropriate."""

def build_user_prompt(req: ReportRequest) -> str:
    doc_type = "Business Proposal" if req.report_type == "proposal" else "Project Report"
    return f"""Write a professional {doc_type} for the following:

Client: {req.client_name}
Project: {req.project_description}

Include ALL of these sections in order, using ## as the heading level:

## Executive Summary
## Problem Statement
## Proposed Solution / Methodology
## Timeline & Deliverables
## Pricing
## Next Steps

Rules:
- Professional, confident tone
- Keep Pricing as a placeholder showing "$XXX" with a note that a detailed quote will follow
- Timeline should include realistic phases (e.g. Week 1-2, Week 3-4 ...)
- Next Steps should list 3-5 concrete action items
- Do NOT include a title at the top — just start with ## Executive Summary
"""

# ── AI call ────────────────────────────────────────────────────────────────
def generate_content(req: ReportRequest) -> str:
    # All confirmed available from your ListModels output
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-2.0-flash-lite",
    ]
    last_err = None

    for model_name in models_to_try:
        try:
            response = gemini.models.generate_content(
                model=model_name,
                contents=build_user_prompt(req),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.7,
                    max_output_tokens=1800,
                ),
            )
            return response.text
        except Exception as e:
            last_err = e
            continue

    raise HTTPException(status_code=502, detail=f"Gemini error: {last_err}")

# ── Routes ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/generate-report")
def create_report(req: ReportRequest):
    if req.report_type not in ("proposal", "report"):
        raise HTTPException(status_code=400, detail="report_type must be 'proposal' or 'report'")

    markdown_content = generate_content(req)

    filename = f"{req.report_type}_{re.sub(r'[^a-z0-9]', '_', req.client_name.lower())}_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = OUTPUT_DIR / filename

    generate_pdf(
        markdown_text=markdown_content,
        output_path=str(pdf_path),
        client_name=req.client_name,
        report_type=req.report_type,
        template_id=req.template_id,
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )