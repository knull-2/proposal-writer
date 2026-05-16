"""
pdf_generator_v2.py — Enterprise-grade PDF builder.
Fixes all issues from executive review:
- Clean bullet rendering (no encoded symbols)
- Two-column header with metadata
- Proper section styling with accent bars
- License-ready template system
"""
from __future__ import annotations

import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, KeepTogether,
)

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm

# ── Template Definitions (easy to add more = more revenue) ─────────────────
TEMPLATES: dict[str, dict] = {
    "default": {
        "company_name":  "Acme Consulting Group",
        "logo_text":     "ACG",
        "tagline":       "Strategy • Technology • Growth",
        "primary":       colors.HexColor("#1a365d"),
        "accent":        colors.HexColor("#2b6cb0"),
        "light":         colors.HexColor("#ebf4ff"),
        "footer_left":   "contact@acmeconsulting.com",
        "footer_right":  "+91 98765 43210  |  www.acmeconsulting.in",
    },
    "dark": {
        "company_name":  "Apex Digital Solutions",
        "logo_text":     "ADS",
        "tagline":       "Engineering Tomorrow's Products",
        "primary":       colors.HexColor("#1a1a2e"),
        "accent":        colors.HexColor("#e94560"),
        "light":         colors.HexColor("#f5f5f5"),
        "footer_left":   "hello@apexdigital.in",
        "footer_right":  "+91 99999 00000  |  www.apexdigital.in",
    },
    "green": {
        "company_name":  "GreenBridge Consulting",
        "logo_text":     "GBC",
        "tagline":       "Sustainable Business Solutions",
        "primary":       colors.HexColor("#1a4731"),
        "accent":        colors.HexColor("#2d8653"),
        "light":         colors.HexColor("#eafaf1"),
        "footer_left":   "info@greenbridge.in",
        "footer_right":  "+91 88888 11111  |  www.greenbridge.in",
    },
}


# ── Style Builder ──────────────────────────────────────────────────────────
def build_styles(t: dict) -> dict:
    primary = t["primary"]
    accent  = t["accent"]

    return {
        "h2": ParagraphStyle("H2",
            fontSize=11, fontName="Helvetica-Bold",
            textColor=primary, spaceBefore=10, spaceAfter=3, leading=15),

        "body": ParagraphStyle("Body",
            fontSize=9.5, fontName="Helvetica",
            textColor=colors.HexColor("#2d3748"),
            leading=15, spaceAfter=4, alignment=TA_JUSTIFY),

        "bullet": ParagraphStyle("Bullet",
            fontSize=9.5, fontName="Helvetica",
            textColor=colors.HexColor("#2d3748"),
            leading=14, spaceAfter=3,
            leftIndent=12, firstLineIndent=0),

        "sub_bullet": ParagraphStyle("SubBullet",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#4a5568"),
            leading=13, spaceAfter=2,
            leftIndent=24, firstLineIndent=0),

        "numbered": ParagraphStyle("Numbered",
            fontSize=9.5, fontName="Helvetica",
            textColor=colors.HexColor("#2d3748"),
            leading=14, spaceAfter=4,
            leftIndent=14, firstLineIndent=0),

        "meta": ParagraphStyle("Meta",
            fontSize=8.5, fontName="Helvetica",
            textColor=colors.HexColor("#718096"),
            leading=13, spaceAfter=2),

        "cover_title": ParagraphStyle("CoverTitle",
            fontSize=24, fontName="Helvetica-Bold",
            textColor=primary, spaceAfter=6, leading=30),

        "cover_sub": ParagraphStyle("CoverSub",
            fontSize=12, fontName="Helvetica",
            textColor=accent, spaceAfter=3),

        "cover_meta": ParagraphStyle("CoverMeta",
            fontSize=9, fontName="Helvetica",
            textColor=colors.HexColor("#718096"), spaceAfter=2),

        "note": ParagraphStyle("Note",
            fontSize=7.5, fontName="Helvetica-Oblique",
            textColor=colors.HexColor("#a0aec0"),
            alignment=TA_CENTER),

        "risk_label": ParagraphStyle("RiskLabel",
            fontSize=9.5, fontName="Helvetica-Bold",
            textColor=primary, leading=14, spaceAfter=2),
    }


# ── Safe Paragraph Helper ──────────────────────────────────────────────────
def safe(text: str, style) -> Paragraph:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    # bold **text**
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    # italic *text*
    text = re.sub(r"\*(.+?)\*", r"<i>\1</i>", text)
    return Paragraph(text, style)


# ── Markdown Parser ────────────────────────────────────────────────────────
def md_to_flowables(markdown: str, styles: dict, t: dict) -> list:
    story = []
    lines = markdown.splitlines()
    accent = t["accent"]
    primary = t["primary"]

    # Clean up any leftover encoded bullets the AI might produce
    def clean(line: str) -> str:
        line = re.sub(r"&#8226;&#160;&#160;", "", line)
        line = re.sub(r"&#8226;", "", line)
        line = re.sub(r"&amp;#8226.*?;", "", line)
        line = re.sub(r"^\*\s+", "", line)   # asterisk bullets → clean
        return line.strip()

    num_counter = [0]
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()

        # ── Section heading ────────────────────────────────────────────
        if line.startswith("## "):
            heading = clean(line[3:])
            story.append(Spacer(1, 5 * mm))
            # Coloured left-bar effect using a thin table
            bar_data = [[
                Paragraph("", ParagraphStyle("x")),
                safe(heading, styles["h2"])
            ]]
            bar_table = Table(bar_data, colWidths=[3, PAGE_W - 2 * MARGIN - 3])
            bar_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0), accent),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(bar_table)
            story.append(HRFlowable(
                width="100%", thickness=0.5,
                color=colors.HexColor("#e2e8f0"), spaceAfter=4))
            num_counter[0] = 0  # reset numbering per section

        # ── Numbered list  ─────────────────────────────────────────────
        elif re.match(r"^\d+\.\s+", line):
            text = re.sub(r"^\d+\.\s+", "", clean(line))
            num_counter[0] += 1
            story.append(safe(f"{num_counter[0]}.  {text}", styles["numbered"]))

        # ── Sub-bullet (indented - or *) ───────────────────────────────
        elif re.match(r"^\s{2,}[-*]\s+", line):
            text = re.sub(r"^\s+[-*]\s+", "", clean(line))
            story.append(safe(f"\u2013  {text}", styles["sub_bullet"]))

        # ── Top-level bullet ───────────────────────────────────────────
        elif re.match(r"^[-*]\s+", line):
            text = re.sub(r"^[-*]\s+", "", clean(line))
            story.append(safe(f"\u2022  {text}", styles["bullet"]))

        # ── Blank line ─────────────────────────────────────────────────
        elif line.strip() == "":
            story.append(Spacer(1, 2 * mm))

        # ── Normal paragraph ───────────────────────────────────────────
        else:
            text = clean(line)
            if text:
                story.append(safe(text, styles["body"]))

        i += 1

    return story


# ── Header / Footer ────────────────────────────────────────────────────────
def make_header_footer(t: dict, client_name: str, report_type: str, doc_date: str):
    primary  = t["primary"]
    accent   = t["accent"]
    company  = t["company_name"]
    logo     = t["logo_text"]
    tagline  = t["tagline"]
    f_left   = t["footer_left"]
    f_right  = t["footer_right"]
    doc_label = "Project Proposal" if report_type == "proposal" else "Project Report"

    def draw(canvas, doc):
        canvas.saveState()
        w, h = A4

        # ── Header background ──────────────────────────────────────────
        canvas.setFillColor(primary)
        canvas.rect(0, h - 20 * mm, w, 20 * mm, fill=True, stroke=False)

        # Accent strip at very top
        canvas.setFillColor(accent)
        canvas.rect(0, h - 2 * mm, w, 2 * mm, fill=True, stroke=False)

        # Logo badge
        canvas.setFillColor(accent)
        canvas.roundRect(MARGIN, h - 16 * mm, 14 * mm, 11 * mm, 2, fill=True, stroke=False)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawCentredString(MARGIN + 7 * mm, h - 11 * mm, logo)

        # Company name + tagline
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 10)
        canvas.drawString(MARGIN + 17 * mm, h - 9 * mm, company)
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(colors.HexColor("#90cdf4"))
        canvas.drawString(MARGIN + 17 * mm, h - 14 * mm, tagline)

        # Right side — doc type + client
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.drawRightString(w - MARGIN, h - 9 * mm, doc_label)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#bee3f8"))
        canvas.drawRightString(w - MARGIN, h - 14 * mm, f"Prepared for: {client_name}")

        # ── Footer ────────────────────────────────────────────────────
        canvas.setFillColor(primary)
        canvas.rect(0, 0, w, 11 * mm, fill=True, stroke=False)

        canvas.setFillColor(colors.HexColor("#bee3f8"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(MARGIN, 4 * mm, f_left)

        canvas.setFillColor(colors.HexColor("#90cdf4"))
        canvas.drawRightString(w - MARGIN, 4 * mm, f_right)

        # Page number centred
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawCentredString(w / 2, 4 * mm, f"Page {doc.page}")

        canvas.restoreState()

    return draw


# ── Cover Page ─────────────────────────────────────────────────────────────
def build_cover(client_name: str, report_type: str, prepared_by: str,
                doc_date: str, styles: dict, t: dict) -> list:
    accent  = t["accent"]
    primary = t["primary"]
    light   = t["light"]
    company = t["company_name"]

    doc_label = "Project Proposal" if report_type == "proposal" else "Project Report"

    story = [Spacer(1, 8 * mm)]

    # Title block
    story.append(safe(doc_label, styles["cover_title"]))
    story.append(safe(f"Prepared for: {client_name}", styles["cover_sub"]))
    story.append(HRFlowable(
        width="100%", thickness=2, color=accent,
        spaceBefore=4, spaceAfter=8))

    # Metadata table
    meta_data = [
        ["Date", doc_date],
        ["Prepared By", prepared_by],
        ["Prepared For", client_name],
        ["Confidentiality", "Confidential — Recipient Use Only"],
    ]
    meta_table = Table(meta_data, colWidths=[40 * mm, PAGE_W - 2 * MARGIN - 40 * mm])
    meta_table.setStyle(TableStyle([
        ("FONTNAME",    (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",    (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE",    (0, 0), (-1, -1), 9),
        ("TEXTCOLOR",   (0, 0), (0, -1), primary),
        ("TEXTCOLOR",   (1, 0), (1, -1), colors.HexColor("#2d3748")),
        ("BACKGROUND",  (0, 0), (-1, -1), light),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [light, colors.white]),
        ("TOPPADDING",  (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6 * mm))

    return story


# ── Public Entry Point ─────────────────────────────────────────────────────
def generate_pdf(
    markdown_text: str,
    output_path: str,
    client_name: str,
    report_type: str = "proposal",
    template_id: str = "default",
    prepared_by: str = "Business Development Team",
) -> None:
    t       = TEMPLATES.get(template_id, TEMPLATES["default"])
    primary = t["primary"]
    accent  = t["accent"]
    doc_date = datetime.now().strftime("%B %d, %Y")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=26 * mm,
        bottomMargin=18 * mm,
    )

    styles    = build_styles(t)
    draw_page = make_header_footer(t, client_name, report_type, doc_date)

    story = []
    story.extend(build_cover(client_name, report_type, prepared_by, doc_date, styles, t))
    story.extend(md_to_flowables(markdown_text, styles, t))

    # Confidentiality footer note
    story.append(Spacer(1, 8 * mm))
    story.append(HRFlowable(
        width="100%", thickness=0.5, color=colors.HexColor("#e2e8f0")))
    story.append(Spacer(1, 3 * mm))
    story.append(safe(
        f"This document is confidential and prepared exclusively for {client_name}. "
        "Unauthorized reproduction or distribution is strictly prohibited.",
        styles["note"]
    ))

    doc.build(story, onFirstPage=draw_page, onLaterPages=draw_page)
