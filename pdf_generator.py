"""
PDF generation: converts AI-generated Markdown to a branded PDF via ReportLab.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import List, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ── Brand / template config ────────────────────────────────────────────────
TEMPLATES: dict[str, dict] = {
    "default": {
        "company_name": "Acme Consulting Group",
        "logo_text": "ACG",          # text placeholder when no real logo
        "primary_color": colors.HexColor("#1a365d"),   # dark navy
        "accent_color":  colors.HexColor("#2b6cb0"),   # blue
        "footer_text":   "Acme Consulting Group  •  contact@acmeconsulting.com  •  +1 (555) 000-0000",
    }
}

PAGE_W, PAGE_H = A4
MARGIN = 20 * mm


# ── Style helpers ──────────────────────────────────────────────────────────
def build_styles(primary: colors.Color, accent: colors.Color):
    base = getSampleStyleSheet()

    heading1 = ParagraphStyle(
        "SectionHeading",
        parent=base["Normal"],
        fontSize=13,
        leading=18,
        textColor=primary,
        fontName="Helvetica-Bold",
        spaceBefore=14,
        spaceAfter=4,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#2d3748"),
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "Bullet",
        parent=body,
        leftIndent=14,
        bulletIndent=4,
        spaceAfter=3,
    )
    label = ParagraphStyle(
        "Label",
        parent=body,
        fontSize=8,
        textColor=colors.HexColor("#718096"),
    )
    return {"h1": heading1, "body": body, "bullet": bullet, "label": label}


# ── Markdown → ReportLab flowables ────────────────────────────────────────
def md_to_flowables(markdown: str, styles: dict) -> list:
    flowables = []
    lines = markdown.splitlines()

    def safe_para(text: str, style) -> Paragraph:
        # Escape XML special chars, then restore basic markdown bold/italic
        text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # **bold**
        text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
        # *italic*
        text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
        return Paragraph(text, style)

    i = 0
    while i < len(lines):
        line = lines[i].rstrip()

        # Section heading
        if line.startswith("## "):
            heading_text = line[3:].strip()
            flowables.append(Spacer(1, 4 * mm))
            flowables.append(
                HRFlowable(width="100%", thickness=1, color=styles["h1"].textColor, spaceAfter=2)
            )
            flowables.append(safe_para(heading_text, styles["h1"]))

        # Bullet point (- or *)
        elif re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", line)
            flowables.append(safe_para(f"&#8226;&#160;&#160;{text}", styles["bullet"]))

        # Numbered list
        elif re.match(r"^\d+\.\s+", line):
            text = re.sub(r"^\d+\.\s+", "", line)
            flowables.append(safe_para(f"&#8226;&#160;&#160;{text}", styles["bullet"]))

        # Blank line
        elif line.strip() == "":
            flowables.append(Spacer(1, 3 * mm))

        # Normal paragraph
        else:
            flowables.append(safe_para(line, styles["body"]))

        i += 1

    return flowables


# ── Header / footer callbacks ──────────────────────────────────────────────
def make_header_footer(template: dict, client_name: str, report_type: str, doc_date: str):
    primary   = template["primary_color"]
    accent    = template["accent_color"]
    company   = template["company_name"]
    logo_text = template["logo_text"]
    footer    = template["footer_text"]
    title     = f"{'Project Proposal' if report_type == 'proposal' else 'Project Report'} — {client_name}"

    def draw(canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── Header bar ──────────────────────────────────────────────────
        canvas.setFillColor(primary)
        canvas.rect(0, h - 22 * mm, w, 22 * mm, fill=True, stroke=False)

        # Logo placeholder circle
        canvas.setFillColor(accent)
        canvas.circle(MARGIN + 8 * mm, h - 11 * mm, 7 * mm, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawCentredString(MARGIN + 8 * mm, h - 13 * mm, logo_text)

        # Company name
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(MARGIN + 18 * mm, h - 10 * mm, company)

        # Doc title (right-aligned)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#bee3f8"))
        canvas.drawRightString(w - MARGIN, h - 10 * mm, title)

        # Date under company name
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#90cdf4"))
        canvas.drawString(MARGIN + 18 * mm, h - 16 * mm, doc_date)

        # ── Footer bar ──────────────────────────────────────────────────
        canvas.setFillColor(primary)
        canvas.rect(0, 0, w, 12 * mm, fill=True, stroke=False)

        canvas.setFillColor(colors.HexColor("#bee3f8"))
        canvas.setFont("Helvetica", 7.5)
        canvas.drawCentredString(w / 2, 4.5 * mm, footer)

        # Page number
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(w - MARGIN, 4.5 * mm, f"Page {doc.page}")

        canvas.restoreState()

    return draw


# ── Public entry point ─────────────────────────────────────────────────────
def generate_pdf(
    markdown_text: str,
    output_path: str,
    client_name: str,
    report_type: str = "proposal",
    template_id: str = "default",
) -> None:
    template = TEMPLATES.get(template_id, TEMPLATES["default"])
    primary  = template["primary_color"]
    accent   = template["accent_color"]

    doc_date = datetime.now().strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=30 * mm,      # room for header
        bottomMargin=20 * mm,   # room for footer
    )

    styles    = build_styles(primary, accent)
    draw_page = make_header_footer(template, client_name, report_type, doc_date)

    # ── Cover block ────────────────────────────────────────────────────────
    doc_title = "Project Proposal" if report_type == "proposal" else "Project Report"
    cover_style = ParagraphStyle(
        "Cover",
        fontSize=22,
        fontName="Helvetica-Bold",
        textColor=primary,
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "CoverSub",
        fontSize=12,
        fontName="Helvetica",
        textColor=accent,
        spaceAfter=2,
    )
    meta_style = ParagraphStyle(
        "Meta",
        fontSize=9,
        fontName="Helvetica",
        textColor=colors.HexColor("#718096"),
        spaceAfter=2,
    )

    story = [
        Spacer(1, 6 * mm),
        Paragraph(doc_title, cover_style),
        Paragraph(f"Prepared for: {client_name}", sub_style),
        Paragraph(f"Date: {doc_date}", meta_style),
        HRFlowable(width="100%", thickness=2, color=accent, spaceBefore=4, spaceAfter=8),
    ]

    # ── Body from Markdown ─────────────────────────────────────────────────
    story.extend(md_to_flowables(markdown_text, styles))
    story.append(Spacer(1, 8 * mm))

    # ── Confidentiality note ───────────────────────────────────────────────
    note_style = ParagraphStyle(
        "Note",
        fontSize=8,
        fontName="Helvetica-Oblique",
        textColor=colors.HexColor("#a0aec0"),
        alignment=TA_CENTER,
    )
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 3 * mm))
    story.append(
        Paragraph(
            "This document is confidential and intended solely for the named recipient.",
            note_style,
        )
    )

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
