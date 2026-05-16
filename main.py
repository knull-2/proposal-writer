import os
import re
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from google import genai
from google.genai import types

from pdf_generator_v2 import generate_pdf

# ── Setup ──────────────────────────────────────────────────────────────────
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

app = FastAPI(title="AI Proposal & Report Writer", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

gemini = genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))

# ── Request Model ──────────────────────────────────────────────────────────
class ReportRequest(BaseModel):
    client_name: str
    project_description: str
    report_type: str = "proposal"
    template_id: str = "default"
    # Optional extra context fields
    industry: str = ""
    budget_range: str = ""
    timeline_preference: str = ""
    prepared_by: str = "Business Development Team"

# ── System Prompt ──────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a senior business consultant and technical proposal writer with 15 years
of experience writing enterprise-grade proposals for Indian B2B clients.

Your writing style:
- Precise and specific — never vague or generic
- Use measurable statements instead of adjectives where possible
- Avoid overused words: robust, scalable, seamless, powerful, comprehensive, cutting-edge, leverage
- Write in short, clear executive-friendly sentences
- Every claim should feel credible and grounded
- Use INR for all pricing references
- Format cleanly using only ## for headings and - for bullet points. No asterisks, no encoded symbols.
"""

# ── Prompt Builder ─────────────────────────────────────────────────────────
def build_prompt(req: ReportRequest) -> str:
    doc_type = "Business Proposal" if req.report_type == "proposal" else "Project Report"
    proposal_id = f"PROP-{datetime.now().strftime('%Y%m')}-{uuid.uuid4().hex[:4].upper()}"
    date_str = datetime.now().strftime("%B %d, %Y")

    extra_context = ""
    if req.industry:
        extra_context += f"\nIndustry: {req.industry}"
    if req.budget_range:
        extra_context += f"\nClient Budget Range: {req.budget_range}"
    if req.timeline_preference:
        extra_context += f"\nPreferred Timeline: {req.timeline_preference}"

    return f"""Write a professional enterprise-grade {doc_type} with the following details:

CLIENT: {req.client_name}
PROJECT: {req.project_description}
PREPARED BY: {req.prepared_by}
PROPOSAL ID: {proposal_id}
DATE: {date_str}{extra_context}

Generate ALL sections below in exact order. Use ## for headings and - for bullets only.
Never use asterisks (*) or encoded symbols like &#8226; anywhere.

## Document Information
- Proposal ID: {proposal_id}
- Version: 1.0
- Date: {date_str}
- Prepared By: {req.prepared_by}
- Confidentiality: Confidential — For Recipient Use Only
- Validity: This proposal is valid for 30 days from the date of issue

## Executive Summary
Write 3-4 short, sharp sentences. State what we are proposing, for whom, and the core business outcome.
Avoid adjectives. Focus on value delivered. Do not start with "We are pleased to..."

## Problem Statement
Describe the business challenge clearly. Include at least one realistic market insight or industry trend
relevant to the project. Reference the competitive landscape briefly. Keep it grounded and specific.

## Proposed Solution / Methodology
Describe the solution and approach. List all major components using clean bullet points.
Under each component list 3-5 specific features. Use plain English feature names, not marketing language.
End with a paragraph on development methodology (Agile/Sprint-based).

## Assumptions & Exclusions
List what IS included in scope and what is NOT included.
- Inclusions: list 4-5 items
- Exclusions: list 4-5 items (e.g. third-party API costs, App Store fees, hosting after go-live, content population)
- Revision policy: state revision rounds included

## Technology Stack
List the recommended technology stack in these categories:
- Mobile Applications
- Backend / API
- Database
- Cloud & Hosting
- Payment Integration
- Real-time Communication
- DevOps & CI/CD

## Timeline & Deliverables
Break into phases. For each phase include: phase name, duration (Week X-Y), and specific deliverables.
Include milestone review points and client approval checkpoints.
End with: "Post-launch technical support: 60 days covering critical bug fixes and performance issues."
Do not use "Ongoing" as a deliverable — be specific.

## Team Structure
List the team that will work on this project:
- Project Manager
- Backend Developers
- Mobile Developers (iOS/Android)
- UI/UX Designer
- QA Engineer
- DevOps Engineer

## Pricing & Commercial Terms
Do NOT use $XXX. Instead write:
"The estimated investment for this engagement is INR [realistic range based on project scope].
Final pricing will be confirmed after the discovery workshop."

Then list payment milestones:
- Advance on signing
- On design approval
- On backend completion
- On UAT sign-off
- On go-live

Then add:
- GST applicable as per Government of India norms
- Proposal validity: 30 days
- All prices in Indian Rupees (INR)

## Risk Management
List 4-5 realistic project risks and their mitigation strategies in a clean format:
Risk: [name] — Mitigation: [strategy]

## Legal & Compliance
- Intellectual property ownership transfers to client on final payment
- Source code will be delivered via private Git repository
- NDA terms apply from date of proposal acceptance
- Data handled in compliance with Indian DPDP Act 2023
- Payment security compliant with PCI-DSS standards

## KPIs & Success Metrics
List 5-6 measurable success criteria for the project:
- App uptime target
- Order processing time
- API response time
- Concurrent user capacity
- App Store rating target
- Bug resolution SLA

## Next Steps
List exactly these 5 steps as a numbered list:
1. Review and formally approve this proposal
2. Schedule project discovery workshop (2-3 hours) with key stakeholders
3. Execute Non-Disclosure Agreement and engagement letter
4. Finalize commercial terms and process advance payment
5. Begin sprint planning and assign dedicated project team

## About Us
Write 3-4 sentences about a professional consulting/development firm. Mention experience delivering
digital platforms, commitment to quality, and client-first approach. Keep it credible and brief.
Do not invent specific client names or awards.
"""

# ── AI Call ────────────────────────────────────────────────────────────────
def generate_content(req: ReportRequest) -> str:
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
                contents=build_prompt(req),
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=0.65,
                    max_output_tokens=4000,
                ),
            )
            return response.text
        except Exception as e:
            last_err = e
            continue

    raise HTTPException(
        status_code=429,
        detail="AI service is temporarily unavailable. Please try again in a few minutes."
    )

# ── Routes ─────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/generate-report")
def create_report(req: ReportRequest):
    if req.report_type not in ("proposal", "report"):
        raise HTTPException(status_code=400, detail="report_type must be 'proposal' or 'report'")

    markdown_content = generate_content(req)

    safe_name = re.sub(r'[^a-z0-9]', '_', req.client_name.lower())
    filename = f"{req.report_type}_{safe_name}_{uuid.uuid4().hex[:6]}.pdf"
    pdf_path = OUTPUT_DIR / filename

    generate_pdf(
        markdown_text=markdown_content,
        output_path=str(pdf_path),
        client_name=req.client_name,
        report_type=req.report_type,
        template_id=req.template_id,
        prepared_by=req.prepared_by,
    )

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
