"""
Content Digest PDF Generator — AI CoS v5
Modern, scannable PDF digests for content consumption.
One PDF per piece of content (for anything >10 min consumption time).

Usage:
    from content_digest_pdf import generate_digest_pdf
    generate_digest_pdf(analysis_data, output_path)
"""

import json
import os
import textwrap
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable, ListFlowable, ListItem,
    Frame, PageTemplate, BaseDocTemplate, Flowable
)
from reportlab.pdfgen import canvas


# ─── Color Palette ────────────────────────────────────────────────
class C:
    """Modern muted palette with strategic accent colors."""
    # Foundations
    INK = HexColor("#1e293b")          # slate-800
    INK_SOFT = HexColor("#334155")     # slate-700
    BODY = HexColor("#475569")         # slate-600
    MUTED = HexColor("#94a3b8")        # slate-400
    FAINT = HexColor("#cbd5e1")        # slate-300
    GHOST = HexColor("#f1f5f9")        # slate-100
    PAGE = HexColor("#ffffff")

    # Accents
    RED = HexColor("#dc2626")          # red-600
    RED_LIGHT = HexColor("#fef2f2")    # red-50
    AMBER = HexColor("#d97706")        # amber-600
    AMBER_LIGHT = HexColor("#fffbeb")  # amber-50
    GREEN = HexColor("#059669")        # emerald-600
    GREEN_LIGHT = HexColor("#ecfdf5")  # emerald-50
    BLUE = HexColor("#2563eb")         # blue-600
    BLUE_LIGHT = HexColor("#eff6ff")   # blue-50
    VIOLET = HexColor("#7c3aed")       # violet-600
    VIOLET_LIGHT = HexColor("#f5f3ff") # violet-50
    INDIGO = HexColor("#4f46e5")       # indigo-600
    INDIGO_LIGHT = HexColor("#eef2ff") # indigo-50
    TEAL = HexColor("#0d9488")         # teal-600
    TEAL_LIGHT = HexColor("#f0fdfa")   # teal-50

    # Priority
    P0 = HexColor("#dc2626")
    P1 = HexColor("#ea580c")
    P2 = HexColor("#ca8a04")
    P3 = HexColor("#6b7280")

    # Net Newness
    MOSTLY_NEW = HexColor("#7c3aed")
    ADDITIVE = HexColor("#2563eb")
    REINFORCING = HexColor("#059669")
    CONTRA = HexColor("#dc2626")
    MIXED = HexColor("#d97706")


# ─── Layout Constants ─────────────────────────────────────────────
PAGE_W, PAGE_H = A4
MARGIN_L = 42
MARGIN_R = 42
MARGIN_T = 52
MARGIN_B = 42
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R  # ~511pt


# ─── Custom Flowable: Accent Bar ──────────────────────────────────
class AccentBar(Flowable):
    """Thin colored bar spanning full content width."""
    def __init__(self, color=C.INDIGO, thickness=3, width=CONTENT_W):
        Flowable.__init__(self)
        self.color = color
        self.thickness = thickness
        self._width = width
        self.height = thickness

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self._width, self.thickness, fill=1, stroke=0)

    def wrap(self, aW, aH):
        return (self._width, self.thickness)


class LeftBorderBox(Flowable):
    """Content box with colored left border — modern card pattern."""
    def __init__(self, content_table, border_color=C.BLUE, border_width=3, bg_color=None):
        Flowable.__init__(self)
        self.content_table = content_table
        self.border_color = border_color
        self.border_width = border_width
        self.bg_color = bg_color
        self._content_width = CONTENT_W

    def wrap(self, aW, aH):
        w, h = self.content_table.wrap(aW - self.border_width - 4, aH)
        self.content_table._width = w
        self.content_table._height = h
        return (self._content_width, h)

    def draw(self):
        h = self.content_table._height
        # Background
        if self.bg_color:
            self.canv.setFillColor(self.bg_color)
            self.canv.rect(0, 0, self._content_width, h, fill=1, stroke=0)
        # Left border
        self.canv.setFillColor(self.border_color)
        self.canv.rect(0, 0, self.border_width, h, fill=1, stroke=0)
        # Content
        self.content_table.drawOn(self.canv, self.border_width + 6, 0)


# ─── Styles ───────────────────────────────────────────────────────
def get_styles():
    s = getSampleStyleSheet()

    s.add(ParagraphStyle('Title_', fontName='Helvetica-Bold', fontSize=20,
        leading=26, textColor=C.INK, spaceAfter=2))

    s.add(ParagraphStyle('Meta', fontName='Helvetica', fontSize=9,
        leading=13, textColor=C.MUTED, spaceAfter=10))

    s.add(ParagraphStyle('SectionLabel', fontName='Helvetica-Bold', fontSize=10,
        leading=14, textColor=C.INDIGO, spaceBefore=14, spaceAfter=6,
        tracking=0.8))  # uppercase section labels

    s.add(ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=11,
        leading=15, textColor=C.INK, spaceBefore=6, spaceAfter=3))

    s.add(ParagraphStyle('H3', fontName='Helvetica-Bold', fontSize=9.5,
        leading=13, textColor=C.INK_SOFT, spaceBefore=4, spaceAfter=2))

    s.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=9.5,
        leading=14.5, textColor=C.BODY, spaceAfter=5, alignment=TA_JUSTIFY))

    s.add(ParagraphStyle('BodyBold', fontName='Helvetica-Bold', fontSize=9.5,
        leading=14.5, textColor=C.INK_SOFT, spaceAfter=4))

    s.add(ParagraphStyle('BodyCompact', fontName='Helvetica', fontSize=9,
        leading=13.5, textColor=C.BODY, spaceAfter=3))

    s.add(ParagraphStyle('Caption', fontName='Helvetica', fontSize=7.5,
        leading=10, textColor=C.MUTED, spaceAfter=2))

    s.add(ParagraphStyle('Quote', fontName='Helvetica-Oblique', fontSize=9,
        leading=13, textColor=C.INDIGO, leftIndent=14, rightIndent=14,
        spaceBefore=4, spaceAfter=4))

    s.add(ParagraphStyle('QuoteAttr', fontName='Helvetica', fontSize=7.5,
        leading=10, textColor=C.MUTED, leftIndent=14, spaceAfter=6))

    s.add(ParagraphStyle('Timestamp', fontName='Courier', fontSize=8.5,
        leading=12, textColor=C.RED))

    s.add(ParagraphStyle('Badge', fontName='Helvetica-Bold', fontSize=7.5,
        leading=10, textColor=white, alignment=TA_CENTER))

    s.add(ParagraphStyle('Footer', fontName='Helvetica', fontSize=6.5,
        leading=9, textColor=C.MUTED, alignment=TA_CENTER))

    s.add(ParagraphStyle('BulletItem', fontName='Helvetica', fontSize=8.5,
        leading=12.5, textColor=C.BODY, spaceAfter=2,
        leftIndent=12, bulletIndent=0))

    return s


# ─── Helper Functions ─────────────────────────────────────────────

def _badge(text, bg, text_color=white, w=None):
    """Pill badge."""
    sty = ParagraphStyle('_b', fontName='Helvetica-Bold', fontSize=7.5,
        leading=10, textColor=text_color, alignment=TA_CENTER)
    p = Paragraph(text, sty)
    if w is None:
        w = max(len(text) * 5.2 + 18, 40)
    t = Table([[p]], colWidths=[w], rowHeights=[17])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), bg),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    return t


def _card(elements, border_color=C.BLUE, bg_color=None):
    """Left-bordered card from list of flowables."""
    inner = Table([[e] for e in elements], colWidths=[CONTENT_W - 16])
    inner.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (0, 0), 8),
        ('BOTTOMPADDING', (-1, -1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 1),
        ('BOTTOMPADDING', (0, 0), (-1, -2), 1),
    ]))
    return LeftBorderBox(inner, border_color=border_color, bg_color=bg_color)


def _section(label, styles):
    """Section header with uppercase label and accent bar."""
    return [
        Spacer(1, 6),
        AccentBar(C.INDIGO, thickness=2),
        Paragraph(label.upper(), styles['SectionLabel']),
    ]


def _divider():
    return HRFlowable(width="100%", thickness=0.3, color=C.FAINT,
                       spaceBefore=6, spaceAfter=6)


def _nn_color(category):
    return {'Mostly New': C.MOSTLY_NEW, 'Additive': C.ADDITIVE,
            'Reinforcing': C.REINFORCING, 'Contra': C.CONTRA,
            'Mixed': C.MIXED}.get(category, C.MUTED)


def _nn_marker(category):
    """Unicode marker for net newness."""
    return {'Mostly New': '\u25c6', 'Additive': '\u25b2',
            'Reinforcing': '\u2713', 'Contra': '\u2716',
            'Mixed': '\u25cf'}.get(category, '\u25cb')


def _safe(data, *keys, default=''):
    """Safely navigate nested dict keys."""
    val = data
    for k in keys:
        if isinstance(val, dict):
            val = val.get(k, default)
        else:
            return default
    return val if val else default


def _priority_color(p):
    p = str(p).upper()
    if 'P0' in p: return C.P0
    if 'P1' in p: return C.P1
    if 'P2' in p: return C.P2
    return C.P3


def _priority_label(p):
    p = str(p).upper()
    if 'P0' in p: return ('P0', 'ACT NOW')
    if 'P1' in p: return ('P1', 'THIS WEEK')
    if 'P2' in p: return ('P2', 'THIS MONTH')
    return ('P3', 'BACKLOG')


# ─── Page Template ────────────────────────────────────────────────

def _header_footer(canvas_obj, doc):
    canvas_obj.saveState()

    # Top accent stripe
    canvas_obj.setFillColor(C.INDIGO)
    canvas_obj.rect(0, PAGE_H - 4, PAGE_W, 4, fill=1, stroke=0)

    # Header text
    canvas_obj.setFont('Helvetica', 6.5)
    canvas_obj.setFillColor(C.MUTED)
    canvas_obj.drawString(MARGIN_L, PAGE_H - 18, "AI CoS Content Digest")
    canvas_obj.drawRightString(PAGE_W - MARGIN_R, PAGE_H - 18,
                                datetime.now().strftime("%d %b %Y"))

    # Footer
    canvas_obj.setFont('Helvetica', 6.5)
    canvas_obj.setFillColor(C.MUTED)
    canvas_obj.drawCentredString(PAGE_W / 2, 20, f"Page {doc.page}")

    # Bottom line
    canvas_obj.setStrokeColor(C.GHOST)
    canvas_obj.setLineWidth(0.5)
    canvas_obj.line(MARGIN_L, 30, PAGE_W - MARGIN_R, 30)

    canvas_obj.restoreState()


# ─── Main Generator ──────────────────────────────────────────────

def generate_digest_pdf(data, output_path):
    """
    Generate a modern PDF content digest from pipeline analysis data.
    Handles both v3 demo format and actual pipeline JSON format.
    """
    styles = get_styles()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        topMargin=MARGIN_T, bottomMargin=MARGIN_B,
        leftMargin=MARGIN_L, rightMargin=MARGIN_R,
    )

    story = []

    # ══════════════════════════════════════════════════════════════
    # HEADER
    # ══════════════════════════════════════════════════════════════

    story.append(Paragraph(data.get('title', 'Untitled'), styles['Title_']))

    # Meta line with source link
    meta_parts = [p for p in [
        data.get('channel', ''),
        data.get('duration', ''),
        data.get('content_type', ''),
    ] if p]
    if data.get('upload_date'):
        meta_parts.append(data['upload_date'])
    meta_line = " \u00b7 ".join(meta_parts)

    url = data.get('url', '')
    if url:
        meta_line += (f'  \u00b7  <font color="#dc2626">'
                      f'<b><a href="{url}" color="#dc2626">'
                      f'\u25b6 Watch Source</a></b></font>')

    story.append(Paragraph(meta_line, styles['Meta']))

    # ── Dashboard Strip ──────────────────────────────────────────

    # Handle net_newness as either string or dict
    nn_raw = data.get('net_newness', 'Mixed')
    if isinstance(nn_raw, dict):
        nn_cat = nn_raw.get('category', 'Mixed')
    else:
        nn_cat = nn_raw

    relevance = data.get('relevance_score', 'Medium')
    nn_color = _nn_color(nn_cat)

    watch_n = len(data.get('watch_sections', []))
    rabbit_n = len(data.get('rabbit_holes', []))
    contra_n = len(data.get('contra_signals', []))
    action_n = len(data.get('proposed_actions', []))

    # Row 1: badges
    badge_row = [
        _badge(f"{_nn_marker(nn_cat)}  {nn_cat.upper()}", nn_color, w=110),
        _badge(f"RELEVANCE: {relevance.upper()}",
               C.RED if relevance == 'High' else C.BLUE if relevance == 'Medium' else C.MUTED,
               w=110),
    ]
    badge_table = Table([badge_row], colWidths=[120, 120])
    badge_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(badge_table)
    story.append(Spacer(1, 6))

    # Row 2: counts as compact metrics — darker for readability
    metrics_style = ParagraphStyle('_metrics', fontName='Helvetica', fontSize=8.5,
        leading=12, textColor=C.INK_SOFT)
    metrics_text = (
        f"<b>{watch_n}</b> sections to watch  \u00b7  "
        f"<b>{rabbit_n}</b> rabbit holes  \u00b7  "
        f"<b>{contra_n}</b> contra signals  \u00b7  "
        f"<b>{action_n}</b> actions"
    )
    story.append(Paragraph(metrics_text, metrics_style))

    # Buckets
    buckets = data.get('connected_buckets', [])
    if buckets:
        story.append(Spacer(1, 3))
        bucket_text = " \u00b7 ".join(buckets)
        story.append(Paragraph(f"<b>Buckets:</b> {bucket_text}", styles['Caption']))

    story.append(Spacer(1, 8))

    # ══════════════════════════════════════════════════════════════
    # ESSENCE
    # ══════════════════════════════════════════════════════════════

    story.extend(_section("Essence", styles))

    essence = data.get('essence_notes', {})
    essence_parts = []

    # Handle both formats: core_argument (string) and core_arguments (list)
    core_arg = essence.get('core_argument', '')
    core_args = essence.get('core_arguments', [])
    if core_arg:
        essence_parts.append(
            Paragraph(f"<b>Core Argument:</b> {core_arg}", styles['Body']))
    elif core_args:
        essence_parts.append(Paragraph("<b>Core Arguments:</b>", styles['BodyBold']))
        for i, arg in enumerate(core_args[:4], 1):  # cap at 4 for space
            essence_parts.append(
                Paragraph(f"<font color='#4f46e5'>{i}.</font> {arg}", styles['BodyCompact']))

    # Evidence / data points
    evidence = essence.get('evidence', '')
    data_points = essence.get('data_points', [])
    if evidence:
        essence_parts.append(
            Paragraph(f"<b>Evidence:</b> {evidence}", styles['Body']))
    if data_points:
        essence_parts.append(Paragraph("<b>Key Data Points:</b>", styles['BodyBold']))
        for dp in data_points[:5]:
            essence_parts.append(
                Paragraph(f"\u2022 {dp}", styles['BodyCompact']))

    # Frameworks
    framework = essence.get('framework', '')
    frameworks = essence.get('frameworks', [])
    if framework:
        essence_parts.append(
            Paragraph(f"<b>Framework:</b> {framework}", styles['Body']))
    elif frameworks:
        essence_parts.append(Paragraph("<b>Frameworks:</b>", styles['BodyBold']))
        for fw in frameworks[:3]:
            essence_parts.append(
                Paragraph(f"\u25b8 {fw}", styles['BodyCompact']))

    if essence_parts:
        story.append(KeepTogether([
            _card(essence_parts, border_color=C.GREEN, bg_color=C.GREEN_LIGHT),
            Spacer(1, 4),
        ]))

    # ── Key Quotes ──
    # Handle both: key_quotes[].text and key_quotes[].quote
    quotes = essence.get('key_quotes', [])
    if quotes:
        story.append(Paragraph("<b>Key Quotes</b>", styles['H3']))
        for q in quotes[:4]:  # cap at 4
            if isinstance(q, dict):
                q_text = q.get('text', '') or q.get('quote', '')
                q_speaker = q.get('speaker', '')
                q_ts = q.get('timestamp', '')
                if q_text:
                    story.append(
                        Paragraph(f"\u201c{q_text}\u201d", styles['Quote']))
                    attr_parts = [p for p in [q_speaker, q_ts] if p]
                    if attr_parts:
                        story.append(
                            Paragraph(f"\u2014 {', '.join(attr_parts)}", styles['QuoteAttr']))
            elif isinstance(q, str) and q:
                story.append(Paragraph(f"\u201c{q}\u201d", styles['Quote']))

    # ── Predictions ──
    predictions = essence.get('predictions', [])
    if predictions:
        story.append(Spacer(1, 4))
        story.append(Paragraph("<b>Predictions</b>", styles['H3']))
        for pred in predictions[:5]:
            story.append(
                Paragraph(f"\u2192 {pred}", styles['BodyCompact']))

    # ══════════════════════════════════════════════════════════════
    # NET NEWNESS ASSESSMENT (moved up — replaces Summary section)
    # ══════════════════════════════════════════════════════════════

    if isinstance(nn_raw, dict) and nn_raw.get('reasoning'):
        story.extend(_section("Net Newness Assessment", styles))
        nn_els = [
            Paragraph(f"<b>Category: {nn_cat}</b>", styles['BodyBold']),
            Paragraph(nn_raw['reasoning'], styles['BodyCompact']),
        ]
        story.append(_card(nn_els, border_color=_nn_color(nn_cat), bg_color=C.GHOST))

    # ══════════════════════════════════════════════════════════════
    # WATCH THESE SECTIONS
    # ══════════════════════════════════════════════════════════════

    watch_sections = data.get('watch_sections', [])
    if watch_sections:
        story.extend(_section("Watch These Sections", styles))

        # Cap: ~1 section per 8 min of content, max 8
        try:
            dur_str = data.get('duration', '60')
            dur_min = int(''.join(c for c in dur_str.split(':')[0] if c.isdigit()) or '60')
        except (ValueError, IndexError):
            dur_min = 60
        max_sections = min(max(dur_min // 8, 4), 8)
        capped = watch_sections[:max_sections]

        for ws in capped:
            ts = ws.get('timestamp_range', '')
            title = ws.get('title', '')
            why = ws.get('why_watch', '')
            conn = ws.get('connects_to', '')

            card_els = [
                Paragraph(
                    f"<font color='#dc2626'><b>{ts}</b></font>  "
                    f"<b>{title}</b>",
                    styles['BodyBold']),
                Paragraph(why, styles['BodyCompact']),
            ]
            if conn:
                card_els.append(
                    Paragraph(f"<i>\u2192 {conn}</i>", styles['Caption']))

            story.append(KeepTogether([
                _card(card_els, border_color=C.AMBER, bg_color=C.AMBER_LIGHT),
                Spacer(1, 4),
            ]))

    # (Topic Map section removed — adds bulk without actionability)

    # ══════════════════════════════════════════════════════════════
    # CONTRA SIGNALS
    # ══════════════════════════════════════════════════════════════

    contra_signals = data.get('contra_signals', [])
    if contra_signals:
        story.extend(_section("Contra Signals", styles))

        for cs in contra_signals:
            # Handle both 'what' and 'challenge' field names
            what = cs.get('what', '') or cs.get('challenge', '')
            evidence_text = cs.get('evidence', '')
            strength = cs.get('strength', 'Moderate')
            implication = cs.get('implication', '')

            strength_color = (C.RED if strength == 'Strong'
                              else C.AMBER if strength == 'Moderate'
                              else C.MUTED)

            card_els = [
                Paragraph(f"<b>{what}</b>", styles['BodyBold']),
                Paragraph(evidence_text, styles['BodyCompact']),
            ]
            if implication:
                card_els.append(
                    Paragraph(
                        f"<font color='#94a3b8'><b>Strength:</b> {strength}</font>  \u00b7  "
                        f"<b>Implication:</b> {implication}",
                        styles['BodyCompact']))

            story.append(KeepTogether([
                _card(card_els, border_color=strength_color, bg_color=C.RED_LIGHT),
                Spacer(1, 4),
            ]))

    # ══════════════════════════════════════════════════════════════
    # RABBIT HOLES
    # ══════════════════════════════════════════════════════════════

    rabbit_holes = data.get('rabbit_holes', [])
    if rabbit_holes:
        story.extend(_section("Rabbit Holes", styles))

        for rh in rabbit_holes:
            title = rh.get('title', '')
            what = rh.get('what', '')
            why = rh.get('why_matters', '')
            entry = rh.get('entry_point', '')
            newness = rh.get('newness', '')

            card_els = [
                Paragraph(f"<b>{title}</b>", styles['BodyBold']),
                Paragraph(what, styles['BodyCompact']),
            ]
            if why:
                card_els.append(
                    Paragraph(f"<b>Why it matters:</b> {why}", styles['BodyCompact']))
            if entry:
                card_els.append(
                    Paragraph(f"<b>Entry point:</b> {entry}", styles['BodyCompact']))
            if newness:
                card_els.append(
                    Paragraph(f"<i>{newness}</i>", styles['Caption']))

            story.append(KeepTogether([
                _card(card_els, border_color=C.VIOLET, bg_color=C.VIOLET_LIGHT),
                Spacer(1, 4),
            ]))

    # ══════════════════════════════════════════════════════════════
    # CONNECTIONS & ACTIONS (unified section)
    # Portfolio companies + Thesis threads + all proposed actions
    # grouped by parent entity.
    # ══════════════════════════════════════════════════════════════

    portfolio_conns = data.get('portfolio_connections', [])
    thesis_conns = data.get('thesis_connections', [])
    actions = data.get('proposed_actions', [])

    # ── Group actions by company / thesis ─────────────────────
    # Actions with a company → keyed by company name
    # Actions without company → try to match to a thesis thread via thesis_connection
    # Remaining → "General"
    company_actions = {}   # company_name -> [action, ...]
    thesis_actions = {}    # thread_name -> [action, ...]
    general_actions = []

    # Build thesis name list for fuzzy matching
    thesis_names = [tc.get('thread', '') or tc.get('thread_name', '') for tc in thesis_conns]

    for action in actions:
        co = action.get('company', '') or ''
        if co:
            company_actions.setdefault(co, []).append(action)
        else:
            # Try to match to a thesis thread
            tc_hint = action.get('thesis_connection', '')
            matched = False
            for tn in thesis_names:
                if tn and (tn.lower() in tc_hint.lower() or
                           any(w in tc_hint.lower() for w in tn.lower().split('/') if len(w) > 3)):
                    thesis_actions.setdefault(tn, []).append(action)
                    matched = True
                    break
            if not matched:
                general_actions.append(action)

    # Sort helper
    def _p_sort(a):
        p = str(a.get('priority', 'P3')).upper()
        return {'P0': 0, 'P1': 1, 'P2': 2}.get(p[:2], 3)

    # Inline action line style
    act_inline = ParagraphStyle('_ai', fontName='Helvetica', fontSize=8.5,
        leading=12.5, textColor=C.BODY, leftIndent=4)

    def _render_action_lines(action_list):
        """Render a compact list of actions for inside a card."""
        elements = []
        sorted_acts = sorted(action_list, key=_p_sort)
        for a in sorted_acts:
            pri = str(a.get('priority', 'P3')).upper()[:2]
            pc = _priority_color(pri)
            a_text = a.get('action', '')
            a_type = a.get('type', '') or a.get('action_type', '')
            assigned = a.get('assigned_to', '')

            # Color hex for inline priority badge
            p_hex = {'P0': '#dc2626', 'P1': '#ea580c', 'P2': '#ca8a04'}.get(pri, '#6b7280')
            type_tag = f"  <font color='#94a3b8'>[{a_type}]</font>" if a_type else ''
            owner_tag = f"  <font color='#94a3b8'>\u2192 {assigned}</font>" if assigned else ''

            elements.append(Paragraph(
                f"<font color='{p_hex}'><b>{pri}</b></font>  "
                f"{a_text}{type_tag}{owner_tag}",
                act_inline))
        return elements

    if portfolio_conns or thesis_conns or actions:
        story.extend(_section("Connections & Actions", styles))

        # ── Portfolio Companies ───────────────────────────────
        if portfolio_conns:
            story.append(Paragraph("<b>Portfolio Companies</b>", styles['H3']))
            for pc in portfolio_conns:
                company = pc.get('company', '')
                relevance_text = pc.get('relevance', '')
                kq = pc.get('key_question_link', '') or pc.get('key_question_impact', '')

                card_els = [
                    Paragraph(f"<b>{company}</b>", styles['BodyBold']),
                    Paragraph(relevance_text, styles['BodyCompact']),
                ]
                if kq:
                    card_els.append(
                        Paragraph(f"<i>Key Q: {kq}</i>", styles['Caption']))

                # Add actions for this company
                co_acts = company_actions.get(company, [])
                if co_acts:
                    card_els.append(Spacer(1, 4))
                    card_els.append(Paragraph("<b>Actions:</b>", styles['Caption']))
                    card_els.extend(_render_action_lines(co_acts))

                # Color by conviction impact
                impact = pc.get('conviction_impact', '')
                if 'challenge' in str(impact).lower():
                    bc = C.AMBER
                elif 'validate' in str(impact).lower():
                    bc = C.GREEN
                else:
                    bc = C.BLUE

                story.append(KeepTogether([
                    _card(card_els, border_color=bc, bg_color=C.BLUE_LIGHT),
                    Spacer(1, 4),
                ]))

        # ── Thesis Threads (as cards, same treatment) ─────────
        if thesis_conns:
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>Thesis Threads</b>", styles['H3']))
            for tc in thesis_conns:
                thread = tc.get('thread', '') or tc.get('thread_name', '')
                connection = tc.get('connection', '')
                strength = tc.get('strength', '')
                direction = tc.get('evidence_direction', '')

                dir_marker = ('\u2191' if direction == 'for'
                              else '\u2193' if direction == 'against'
                              else '\u2194')
                strength_color = (C.GREEN if strength == 'Strong'
                                  else C.AMBER if strength == 'Moderate'
                                  else C.MUTED)

                card_els = [
                    Paragraph(
                        f"<b>{thread}</b>  "
                        f"<font color='#94a3b8'>({strength}) {dir_marker}</font>",
                        styles['BodyBold']),
                    Paragraph(connection, styles['BodyCompact']),
                ]

                # Add actions for this thesis thread
                th_acts = thesis_actions.get(thread, [])
                if th_acts:
                    card_els.append(Spacer(1, 4))
                    card_els.append(Paragraph("<b>Actions:</b>", styles['Caption']))
                    card_els.extend(_render_action_lines(th_acts))

                story.append(KeepTogether([
                    _card(card_els, border_color=strength_color, bg_color=C.GHOST),
                    Spacer(1, 4),
                ]))

        # ── General Actions (not tied to specific company/thesis) ─
        if general_actions:
            story.append(Spacer(1, 4))
            story.append(Paragraph("<b>General Actions</b>", styles['H3']))
            gen_els = _render_action_lines(general_actions)
            story.append(KeepTogether([
                _card(gen_els, border_color=C.INDIGO, bg_color=C.GHOST),
                Spacer(1, 4),
            ]))

    # ══════════════════════════════════════════════════════════════
    # FOOTER
    # ══════════════════════════════════════════════════════════════

    story.append(Spacer(1, 16))
    story.append(AccentBar(C.INDIGO, thickness=1))
    story.append(Spacer(1, 4))

    story.append(
        Paragraph(
            f"AI CoS Content Pipeline v5 \u00b7 {datetime.now().strftime('%d %b %Y %H:%M')}",
            styles['Footer']))

    # Build
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path


# ─── Batch Generator ─────────────────────────────────────────────

def generate_batch_digests(analyses, output_dir):
    """Generate PDFs for a batch of analyzed videos."""
    os.makedirs(output_dir, exist_ok=True)
    paths = []
    for analysis in analyses:
        title = analysis.get('title', 'untitled')
        safe_title = "".join(c if c.isalnum() or c in ' -_' else '' for c in title)
        safe_title = safe_title.strip()[:60]
        filename = f"digest_{safe_title}.pdf"
        output_path = os.path.join(output_dir, filename)
        generate_digest_pdf(analysis, output_path)
        paths.append(output_path)
        print(f"Generated: {filename}")
    return paths


# ─── CLI ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) >= 2:
        json_path = sys.argv[1]
        out_path = sys.argv[2] if len(sys.argv) >= 3 else "/tmp/digest_output.pdf"
        with open(json_path) as f:
            data = json.load(f)
        result = generate_digest_pdf(data, out_path)
        print(f"Generated: {result}")
    else:
        print("Usage: python content_digest_pdf.py <analysis.json> [output.pdf]")
        print("No arguments provided — running demo...")
        # Minimal demo
        demo = {
            "title": "Demo Digest",
            "channel": "Test Channel",
            "duration": "30 min",
            "content_type": "Interview",
            "relevance_score": "High",
            "net_newness": "Additive",
            "summary": "This is a demo digest to verify the PDF generator works.",
            "key_insights": ["Insight one", "Insight two"],
            "watch_sections": [],
            "topic_map": [],
            "contra_signals": [],
            "rabbit_holes": [],
            "essence_notes": {"core_argument": "Test argument"},
            "portfolio_connections": [],
            "thesis_connections": [],
            "proposed_actions": [],
            "connected_buckets": ["New Cap Tables"],
        }
        result = generate_digest_pdf(demo, "/tmp/digest_demo.pdf")
        print(f"Demo: {result}")
