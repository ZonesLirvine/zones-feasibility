"""
Editable exports: PowerPoint and Word.

The PDF is the finished artefact. These two are for when the report needs to
be adapted: adding commentary, dropping a slide into the S&F Report deck, or
reordering things for a particular client.

Everything is native text, tables and pictures, not flattened images, so it
can be edited normally. Findings go into tables specifically because a table
is the easiest thing to add a row of commentary to.

Slides are landscape at the same size as the PDF pages (A3 or A4), so they sit
alongside the printed sheets without rescaling.
"""

import os

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Mm as DMm
from docx.shared import Pt as DPt
from docx.shared import RGBColor as DRGB
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Mm

import layers as L
import render as R
import standards as S

import brand as BR
import slides as SL

# Tokens come from brand.py so these slides and the S&F Report deck stay in
# step; they get printed into the same binder.
GREEN = BR.GREEN
GREEN_SOFT = BR.TINT
INK = BR.INK
BODY_INK = BR.BODY
MUTED = BR.MUTED
RED = BR.STATUS_ON_SITE
AMBER = BR.STATUS_NEARBY
CLEAR = BR.STATUS_CLEAR
WHITE = BR.WHITE
RULE = BR.LINE

HEAD_FONT = BR.HEAD_FONT
BODY_FONT = BR.BODY_FONT

STATUS_WORD = {"on_site": "NEEDS ATTENTION", "abuts": "ADJOINS",
               "nearby": "NEARBY", "error": "NOT CHECKED", "clear": "CLEAR",
               "partial": "NOT CONFIRMED"}
STATUS_RGB = {"on_site": RED, "abuts": AMBER, "nearby": AMBER, "error": MUTED,
              "clear": CLEAR, "partial": AMBER}


# --------------------------------------------------------------- PowerPoint
#
# Page chrome lives in slides.py, shared with the S&F Report deck. The thin
# wrappers below keep this module's original call signatures and defaults.

_rect = SL.rect
_slide = SL.blank
_head = SL.head
_footer = SL.footer
_slide_number = SL.slide_number
_cell_border = SL.cell_border
_style_table = SL.style_table
_cell = SL.cell


def _tb(slide, x, y, w, h, text, size=12, font=BODY_FONT, colour=INK,
        bold=False, italic=False, align=PP_ALIGN.LEFT, spacing=1.15):
    return SL.tb(slide, x, y, w, h, text, size=size, font=font, colour=colour,
                 bold=bold, italic=italic, align=align, spacing=spacing)


# python-pptx cannot measure text, and a pptx table row always grows to fit its
# contents no matter what height it was created at. The height passed to
# add_table is therefore a floor, not a limit, which is how the findings table
# came to print through the "also checked" list on a job with 14 flagged items.
# These two estimate the rendered height well enough to size the table before
# PowerPoint sees it. Calibrated against rendered output at A4; the constants
# are ems, so they hold at A3 too.
PT_MM = 0.3528            # 1pt in mm
_EM_BODY = 0.49           # Open Sans, mixed case, average glyph advance
_EM_BOLD = 0.52
_WRAP_SAFETY = 1.25       # the estimate runs short, so allow for it


def _lines(text, width_mm, size_pt, bold=False):
    """Number of wrapped lines `text` takes in a box `width_mm` wide."""
    if not text:
        return 1
    per_char = (_EM_BOLD if bold else _EM_BODY) * size_pt * PT_MM
    per_line = max(1, int(width_mm / per_char))
    return max(1, -(-len(text) // per_line))


def _text_height(text, width_mm, size_pt, spacing=1.15, bold=False):
    return _lines(text, width_mm, size_pt, bold) * size_pt * spacing * PT_MM


def _commentary(slide, x, y, w, h=22, prompt="Commentary"):
    """An empty, clearly-marked box for Lee to type into."""
    _rect(slide, x, y, w, h, BR.PHBG, RULE)
    _tb(slide, x + 4, y + 3, w - 8, 6, prompt.upper(), size=8,
        font=HEAD_FONT, colour=MUTED, bold=True)
    _tb(slide, x + 4, y + 9, w - 8, h - 12,
        "Click here to add your notes for this site.", size=10, colour=MUTED)


# ------------------------------------------ the binder's findings page
#
# SF_34's layout. The standalone deck's three-column table has a STATUS column,
# which invites the reader to audit a checklist. In the binder the client is
# not auditing anything, they are being told what matters on their site: so the
# flagged items get cards with room for the explanation, and everything else
# collapses into two summary blocks down the right.

M_LEFT = 25.0               # the binder margin, the ring-binder punch line
_CARD_X = 24.9              # both columns sit a hair inside the margin
_COL2_X = 155.0
_CARD_W = 116.9
_CARD_INSET = 6.1           # text inset from the card's left edge
_CARD_TEXT_W = 105.7
_RULE_W = 1.5               # coloured strip down the left of a card

# Wrapping at card sizes, calibrated against SF_34's own six cards: this em is
# the only value that predicts all six of their line counts. _EM_BODY is left
# alone because it was calibrated on the clear list, which is Title Case names
# and wraps quite differently from sentences.
_EM_CARD = 0.5326
# The clear list is Title Case names separated by mid-dots, which packs far
# tighter per character than sentence text. Calibrated on SF_34's own 28.
_EM_LIST = 0.476


def _card_lines(text, width_mm, size_pt, em=_EM_CARD):
    per_char = em * size_pt * PT_MM
    return max(1, -(-len(text) // max(1, int(width_mm / per_char))))


# Rendered line height as a fraction of size x line-spacing. Measured off
# SF_34: 0.400 at the cards' 7.5pt/115%, 0.388 at the clear list's 6.5pt/125%.
# PowerPoint's autofit is not linear across sizes, so both are kept rather
# than averaged into one value that is wrong at each end.
def _card_text_h(lines, size_pt, spacing, factor=0.400):
    return lines * size_pt * spacing * factor + 1.25


def _card(slide, prs, x, y, w, rule, title, body, size, spacing=1.15):
    """
    One finding: a tint panel with a status-coloured strip down its left,
    a Montserrat title and the plain-English explanation under it.
    """
    lines = _card_lines(body, _CARD_TEXT_W, size)
    body_h = _card_text_h(lines, size, spacing)
    h = 9.15 + body_h + 1.25
    _rect(slide, x, y, w, h, GREEN_SOFT)
    _rect(slide, x, y, _RULE_W, h, rule)
    _tb(slide, x + _CARD_INSET, y + 3.3, _CARD_TEXT_W, 5.1, title,
        size=prs._sz(8.6), font=HEAD_FONT, colour=INK, bold=True, spacing=1.15)
    _tb(slide, x + _CARD_INSET, y + 9.15, _CARD_TEXT_W, body_h, body,
        size=prs._sz(size), colour=BODY_INK, spacing=spacing)
    return h


def _panel(slide, x, y, w, h, rule):
    _rect(slide, x, y, w, h, GREEN_SOFT)
    _rect(slide, x, y, _RULE_W, h, rule)


def _stat_tile(slide, prs, y, label, value, sub, accent):
    """
    One headline number. Four of these run down the left of the overview page.

    The value is set right, hard against the tile's inner edge, so the four
    numbers line up as a column the eye can run down regardless of how long
    each label is.
    """
    _rect(slide, _CARD_X, y, _CARD_W, 23.4, GREEN_SOFT)
    _rect(slide, _CARD_X, y, _RULE_W, 23.4, accent)
    _tb(slide, 31.0, y + 4.6, 55.9, 5.6, label, size=prs._sz(7.5),
        font=HEAD_FONT, colour=MUTED, bold=True, spacing=1.15)
    _tb(slide, 31.0, y + 10.2, 55.9, 11.2, sub, size=prs._sz(7.5),
        colour=MUTED, spacing=1.15)
    _tb(slide, 87.2, y + 5.6, 48.3, 12.2, value, size=prs._sz(20),
        font=HEAD_FONT, colour=accent, bold=True, align=PP_ALIGN.RIGHT,
        spacing=1.15)


def _binder_overview(prs, prsw, h_mm, result, parcel, zone, std, findings,
                     flagged, clear):
    """
    SF_34's opening site page: four headline numbers down the left, the zone
    standards down the right, what it means, and the notice.

    The standalone deck runs the same content across the page with a
    commentary box under it. This one is denser because it has to absorb what
    used to be a separate divider page and a separate notice page.
    """
    s = _slide(prs)
    _head(s, prs, "Your site", result["site"].get("display",
                                                  result["address"]))

    _tb(s, _CARD_X, 29.5, prsw, 6.1,
        "Legal description:  %s   ·   Record of title:  %s"
        % (parcel.get("legal_description") or "-", parcel.get("title") or "-"),
        size=prs._sz(8.6), colour=INK, spacing=1.15)

    # ---- four headline numbers
    _tb(s, _CARD_X, 40.6, _CARD_W, 5.6, "YOUR PROPERTY", size=prs._sz(8.6),
        font=HEAD_FONT, colour=GREEN, bold=True, spacing=1.15)
    area = parcel.get("area_m2")
    hard = S.impervious_allowance(area, std)
    build = S.coverage_allowance(area, std)
    build_txt = ("total hard surface allowed, including the house roof and "
                 "existing driveway.")
    if build:
        build_txt += " Building footprint capped at about %s m²" % f"{build:,.0f}"
    tiles = [
        ("SITE AREA", "%s m²" % f"{area:,}" if area else "-",
         parcel.get("area_source", ""), GREEN),
        ("ZONE", std.get("code") or "-",
         (zone.get("name") or "").replace("Residential - ", ""), GREEN),
        ("FLAGGED FOR ATTENTION", "%d of %d" % (len(flagged), len(findings)),
         "%d checked, %d clear" % (len(findings), len(clear)),
         RED if flagged else GREEN),
        ("WHAT YOU CAN BUILD ON", "%s m²" % f"{hard:,.0f}" if hard else "-",
         build_txt if hard else "Not determined for this zone", GREEN),
    ]
    for i, (label, value, sub, accent) in enumerate(tiles):
        _stat_tile(s, prs, 50.8 + i * 26.9, label, value, sub, accent)

    # ---- zone standards
    _tb(s, _COL2_X, 40.6, _CARD_W, 5.6, "PLANNING STANDARDS FOR THIS ZONE",
        size=prs._sz(8.6), font=HEAD_FONT, colour=GREEN, bold=True,
        spacing=1.15)
    c = std.get("clauses") or {}
    rows = [("Front yard, min", std.get("front_yard_m"), "m", "yards"),
            ("Side yard, min", std.get("side_yard_m"), "m", "yards"),
            ("Rear yard, min", std.get("rear_yard_m"), "m", "yards"),
            ("Max building coverage", std.get("site_coverage_pct"), "%",
             "coverage"),
            ("Max hard surface", std.get("impervious_pct"), "%", "impervious"),
            ("Min landscaped area", std.get("landscaped_pct"), "%",
             "landscaped"),
            ("Riparian yard", std.get("riparian_yard_m"), "m", "yards"),
            ("Coastal yard", std.get("coastal_yard_m"), "m", "yards")]
    for i, (label, val, unit, key) in enumerate(rows):
        ry = 49.3 + i * 9.0
        SL.hline(s, _COL2_X, ry, _CARD_W, BR.CARD_LINE, 0.75)
        _tb(s, _COL2_X, ry + 2.3, 68.6, 5.1, label, size=prs._sz(8.6),
            colour=INK, spacing=1.15)
        _tb(s, 224.9, ry + 1.5, 21.6, 6.6,
            "n/a" if val is None else "%s%s" % (val, unit),
            size=prs._sz(11.5), font=HEAD_FONT, bold=True,
            colour=MUTED if val is None else GREEN, spacing=1.15)
        _tb(s, 247.8, ry + 3.0, 24.1, 5.1, "AUP %s" % c[key] if c.get(key)
            else "", size=prs._sz(6.5), colour=MUTED, align=PP_ALIGN.RIGHT,
            spacing=1.15)
    SL.hline(s, _COL2_X, 49.3 + len(rows) * 9.0, _CARD_W, BR.CARD_LINE, 0.75)

    # ---- what it means, folded in from the divider page the binder no longer
    # has
    _rect(s, _COL2_X, 131.6, _CARD_W, 23.4, GREEN_SOFT)
    _tb(s, 160.1, 134.9, 106.7, 5.6, "WHAT THIS MEANS FOR YOU",
        size=prs._sz(8), font=HEAD_FONT, colour=GREEN, bold=True, spacing=1.15)
    _tb(s, 160.1, 140.7, 106.7, 12.7,
        "Consent surprises are the most expensive thing that can happen to a "
        "landscaping project, and they almost always surface after the build "
        "has started. Doing this work now is what keeps your budget and your "
        "timeline honest.", size=prs._sz(7.6), colour=BODY_INK, spacing=1.15)

    # Zone warnings say the standards above may only hold for part of the
    # property, so they cannot sit quietly at the bottom with the notice.
    for i, w in enumerate(result.get("warnings") or []):
        _tb(s, M_LEFT, 155.5 + i * 5.5, prsw, 5.5, w, size=prs._sz(7),
            colour=RGBColor(0xB8, 0x6B, 0x0A), bold=True, spacing=1.15)

    _tb(s, M_LEFT, 162.6, prsw, 8.1,
        "Checked %s against your property boundary, before a single line of "
        "your design was drawn. %d planning, hazard and service records, "
        "checked against your actual boundary rather than a pin on a map. "
        "Covenants, consent notices, easements, power and fibre are not held "
        "in public records and are not covered."
        % (result.get("generated", ""), len(findings)),
        size=prs._sz(8), colour=MUTED, spacing=1.15)

    # ---- the notice, folded in from the Important notice page
    _rect(s, M_LEFT, 173.2, prsw, 21.3, BR.PHBG)
    SL.rich(s, 30.1, 176.3, 236.7, 15.2, [
        {"text": R.DISCLAIMER_INTRO, "space_after": 2},
        {"text": R.DISCLAIMER_LIABILITY, "space_after": 2},
        {"text": L.ATTRIBUTION},
    ], size=prs._sz(6.5), colour=MUTED, spacing=1.3)
    _footer(s, prs)
    s.notes_slide.notes_text_frame.text = (
        "Site overview. The zone standards are the operative AUP values for "
        "this zone, not an assessment of the design.")
    return s


def _card_h(text, size):
    return 9.15 + _card_text_h(_card_lines(text, _CARD_TEXT_W, size),
                               size, 1.15) + 1.25


def _binder_findings(prs, M, CW, h_mm, mb, findings, attention, minor, clear,
                     body_of):
    bottom = h_mm - mb
    top = 50.8
    avail = bottom - top

    # SF_34 had five flagged items and they sat in one column with the summary
    # blocks beside them. A site like Roys Road comes back with ten, which is
    # two columns of cards on its own, so the summary blocks move to a
    # continuation page rather than the column running off the bottom.
    size, gap = 7.5, 3.3
    heights = [_card_h(body_of(f), size) for f in attention]
    two_col = sum(h + gap for h in heights) - gap > avail
    if two_col:
        for size in (7.5, 7.0, 6.5):
            heights = [_card_h(body_of(f), size) for f in attention]
            if sum(h + gap for h in heights) - gap <= avail * 2:
                break

    s = _slide(prs)
    _head(s, prs, "Your site", "What we found")

    counts = [("%d need attention" % len(attention), attention),
              ("%d %s nearby" % (len(minor), "is" if len(minor) == 1
                                 else "are"), minor),
              ("%d came back clear" % len(clear), clear)]
    said = [t for t, group in counts if group]
    _tb(s, _CARD_X, 29.5, CW, 6.1,
        "%d records checked against your property boundary.  %s."
        % (len(findings), ", ".join(said)),
        size=prs._sz(8.6), colour=INK, spacing=1.15)

    # ---- the items that need attention
    _tb(s, _CARD_X, 40.6, _CARD_W, 5.6, "NEEDS ATTENTION", size=prs._sz(8.6),
        font=HEAD_FONT, colour=GREEN, bold=True, spacing=1.15)

    x, y = _CARD_X, top
    for f, h in zip(attention, heights):
        if two_col and x == _CARD_X and y + h > bottom:
            x, y = _COL2_X, top
        _card(s, prs, x, y, _CARD_W, STATUS_RGB[f["status"]], f["name"],
              body_of(f), size)
        y += h + gap

    if two_col:
        _footer(s, prs)
        s = _slide(prs)
        _head(s, prs, "Your site", "What we found, continued")

    # ---- everything that does not change the design
    #
    # These stack down the right of the findings page when the cards left room,
    # and take a column each on the continuation page when they did not.
    mx = _CARD_X if two_col else _COL2_X
    cx = _CARD_X if (two_col and not minor) else _COL2_X
    y2 = top
    if minor:
        _tb(s, mx, 40.6, _CARD_W, 5.6, "MINOR CONSIDERATIONS",
            size=prs._sz(8.6), font=HEAD_FONT, colour=GREEN, bold=True,
            spacing=1.15)
        note = ("Present within 200 m of your property but not on it. Worth "
                "being aware of, unlikely to control the design.")
        note_h = _card_text_h(
            _card_lines(note, _CARD_TEXT_W, 7.5), 7.5, 1.15)
        step = 7.9
        h = 4.1 + note_h + 3.0 + (len(minor) - 1) * step + 5.1 + 2.5
        _panel(s, mx, y2, _CARD_W, h, AMBER)
        _tb(s, mx + _CARD_INSET, y2 + 4.1, _CARD_TEXT_W, note_h, note,
            size=prs._sz(7.5), colour=MUTED, italic=True, spacing=1.15)
        ny = y2 + 4.1 + note_h + 3.0
        for i, f in enumerate(minor):
            _tb(s, mx + _CARD_INSET, ny, _CARD_TEXT_W, 5.1, f["name"],
                size=prs._sz(8.6), colour=INK, spacing=1.15)
            if i < len(minor) - 1:
                SL.hline(s, mx + _CARD_INSET, ny + 6.1, _CARD_TEXT_W,
                         BR.CARD_LINE, 0.75)
            ny += step
        y2 = top if two_col else y2 + h + 8.6

    # ---- right column, the full checklist that came back clear
    #
    # Never dropped, never abbreviated. It is what evidences the S&F fee, and
    # a client who only sees the problems has no idea what was ruled out.
    if clear:
        head_y = 40.6 if (two_col or not minor) else y2
        _tb(s, cx, head_y, _CARD_W, 5.6, "ALSO CHECKED, NOTHING FOUND",
            size=prs._sz(8.6), font=HEAD_FONT, colour=GREEN, bold=True,
            spacing=1.15)
        y2 = top if (two_col or not minor) else y2 + 7.7
        text = "   ·   ".join(f["name"] for f in clear)
        lines = _card_lines(text, _CARD_TEXT_W, 6.5, em=_EM_LIST)
        text_h = min(_card_text_h(lines, 6.5, 1.25, factor=0.388),
                     bottom - y2 - 6.4)
        _panel(s, cx, y2, _CARD_W, text_h + 6.4, GREEN)
        _tb(s, cx + _CARD_INSET, y2 + 4.0, _CARD_TEXT_W, text_h, text,
            size=prs._sz(6.5), colour=MUTED, spacing=1.25)

    _footer(s, prs)
    s.notes_slide.notes_text_frame.text = (
        "Delete any card not worth raising with this client. Card heights are "
        "estimated from the text, so nudge one if a line looks tight.")
    return s


def build_pptx(result, out_path, map_path=None, size="a3"):
    """The four site slides on their own, as a standalone deck."""
    prs = SL.new_presentation(size)
    build_site_slides(prs, result, map_path)
    prs.save(out_path)
    return out_path


def build_site_slides(prs, result, map_path=None):
    """
    Add the site slides to an existing presentation.

    Kept separate from build_pptx so the S&F Report generator can drop them in
    rather than Lee pulling them in by hand with Reuse Slides. The site-only
    export is still useful on its own, so both entry points stay.

    At A4 this is the shape of the deck Lee actually sends (SF_34, 66
    Rhinevale Close): three pages, findings before the site map, and the
    notice at the foot of the overview page rather than on a page of its own.
    The binder and the standalone export produce the same pages.

    The report is not a contract. Its liability and attribution lines carry on
    the overview page; the terms sit in the signed S&F contract, which is
    where a client goes looking for them. Spending a page restating them here
    made the document look like something it is not.
    """
    w_mm, h_mm = prs._w, prs._h
    ml, mr, mt, mb = prs._m
    M = ml
    CW = w_mm - ml - mr
    size = "a3" if w_mm > 300 else "a4"
    scale = 1.0 if size == "a3" else 0.78        # shrink type on A4 slides
    # The SF_34 pages are laid out in fixed A4 millimetres, so an A3 sheet
    # keeps the older scalable layout, which is also the only output that
    # still gives the full notice a page of its own.
    sf34 = size == "a4"

    parcel = result.get("parcel") or {}
    zone = result.get("zone") or {}
    std = zone.get("standards") or {}
    findings = result["findings"]
    on_site = [f for f in findings if f["status"] == "on_site"]
    # Adjoins the boundary without any of the land being inside it. Flagged and
    # shown, but never counted as on the property.
    abutting = [f for f in findings if f["status"] == "abuts"]
    nearby = [f for f in findings if f["status"] == "nearby"]
    clear = [f for f in findings if f["status"] == "clear"]
    errors = [f for f in findings if f["status"] == "error"]
    # Not confirmed, because the published dataset does not cover it fully.
    # Grouped with the errors so it is surfaced for follow-up, and deliberately
    # kept out of `clear` so it never reaches the "nothing found" list.
    partial = [f for f in findings if f["status"] == "partial"]
    flagged = on_site + abutting + nearby

    def sz(pt):
        return pt * scale

    # ------------------------------------------------------------ slide 1
    if sf34:
        _binder_overview(prs, CW, h_mm, result, parcel, zone, std,
                         findings, flagged, clear)
    else:
        s = _slide(prs)
        y = _head(s, prs, "Your site",
                  result["site"].get("display", result["address"]),
                  "Checked %s against your property boundary by Zones "
                  "Landscaping Auckland Central"
                  % result.get("generated", "")) + 4
        gap = 6
        cw = (CW - gap * 2) / 3
        area = parcel.get("area_m2")
        stats = [("SITE AREA", "%s m²" % f"{area:,}" if area else "-",
                  parcel.get("area_source", ""), GREEN),
                 ("ZONE", std.get("code") or "-",
                  (zone.get("name") or "").replace("Residential - ", ""), GREEN),
                 ("FLAGGED FOR ATTENTION", "%d of %d" % (len(flagged),
                                                         len(findings)),
                  "%d checked, %d clear" % (len(findings), len(clear)),
                  RED if flagged else GREEN)]
        for i, (label, value, sub, colour) in enumerate(stats):
            x = M + i * (cw + gap)
            _rect(s, x, y, cw, 30 * scale, GREEN_SOFT)
            _rect(s, x, y, 1.4, 30 * scale, colour)
            _tb(s, x + 5, y + 4, cw - 8, 6, label, size=sz(9), font=HEAD_FONT,
                colour=MUTED, bold=True)
            _tb(s, x + 5, y + 10, cw - 8, 12, value, size=sz(24), font=HEAD_FONT,
                colour=colour, bold=True)
            _tb(s, x + 5, y + 23 * scale, cw - 8, 6, sub[:46], size=sz(9),
                colour=MUTED)

        y += 30 * scale + 8
        half = (CW - gap) / 2
        _tb(s, M, y, half, 6, "YOUR PROPERTY", size=sz(11), font=HEAD_FONT,
            colour=GREEN, bold=True)
        _tb(s, M, y + 8, half, 20,
            "Legal description:  %s\nRecord of title:  %s"
            % (parcel.get("legal_description") or "-", parcel.get("title") or "-"),
            size=sz(11), spacing=1.5)
        _tb(s, M, y + 22, half, 12, R.PARCEL_CONFIRM, size=sz(9),
            colour=RGBColor(0xB8, 0x6B, 0x0A), bold=True)

        hard = S.impervious_allowance(area, std)
        build = S.coverage_allowance(area, std)
        _tb(s, M + half + gap, y, half, 6, "WHAT YOU CAN BUILD ON", size=sz(11),
            font=HEAD_FONT, colour=GREEN, bold=True)
        if hard:
            _tb(s, M + half + gap, y + 7, half, 12, "%s m²" % f"{hard:,.0f}",
                size=sz(22), font=HEAD_FONT, colour=GREEN, bold=True)
            txt = ("total hard surface allowed, including the house roof and "
                   "existing driveway")
            if build:
                txt += ".  Building footprint capped at about %s m²" % f"{build:,.0f}"
            _tb(s, M + half + gap, y + 19 * scale, half, 12, txt, size=sz(10),
                colour=MUTED)

        # Fixed advance, not scaled: the record-of-title confirmation above wraps to
        # two lines and a scaled advance let it run into this heading on A4.
        y += 38
        _tb(s, M, y, CW, 6, "PLANNING STANDARDS FOR THIS ZONE", size=prs._sz(9.5),
            font=HEAD_FONT, colour=GREEN, bold=True)
        y += 8

        # Zone warnings sit directly under the heading they qualify, because they
        # say the table below may not apply to the whole property. Typically: part
        # of the parcel falls in a second zone, so the standards shown are only
        # right for part of it. The terminal output and the PDF have always carried
        # these; the slides dropped them, which meant the binder Lee actually hands
        # over presented one zone's standards as settled fact. Amber, same as the
        # record-of-title note, because it is something to resolve before design is
        # finalised rather than a finding about the site.
        for w in (result.get("warnings") or []):
            _tb(s, M, y, CW, 10, w, size=sz(9), colour=RGBColor(0xB8, 0x6B, 0x0A),
                bold=True, spacing=1.3)
            y += 11
        c = std.get("clauses") or {}
        rows = [("Front yard, min", std.get("front_yard_m"), "m", "yards"),
                ("Side yard, min", std.get("side_yard_m"), "m", "yards"),
                ("Rear yard, min", std.get("rear_yard_m"), "m", "yards"),
                ("Max building coverage", std.get("site_coverage_pct"), "%",
                 "coverage"),
                ("Max hard surface", std.get("impervious_pct"), "%", "impervious"),
                ("Min landscaped area", std.get("landscaped_pct"), "%",
                 "landscaped"),
                ("Riparian yard", std.get("riparian_yard_m"), "m", "yards"),
                ("Coastal yard", std.get("coastal_yard_m"), "m", "yards")]
        tbl = s.shapes.add_table(3, len(rows), Mm(M), Mm(y), Mm(CW),
                                 Mm(22 * scale)).table
        for i, (label, val, unit, key) in enumerate(rows):
            _cell(tbl, 0, i, label, size=sz(9))
            _cell(tbl, 1, i, "n/a" if val is None else "%s%s" % (val, unit),
                  size=sz(14), bold=True,
                  colour=MUTED if val is None else GREEN, font=HEAD_FONT)
            _cell(tbl, 2, i, "AUP %s" % c[key] if c.get(key) else "", size=sz(8),
                  colour=MUTED)
        _style_table(tbl)
        for i in range(len(rows)):
            _cell(tbl, 0, i, rows[i][0].upper(), size=sz(8.5), bold=True,
                  colour=GREEN, font=HEAD_FONT)
            _cell(tbl, 1, i, "n/a" if rows[i][1] is None
                  else "%s%s" % (rows[i][1], rows[i][2]), size=sz(14), bold=True,
                  colour=MUTED if rows[i][1] is None else GREEN, font=HEAD_FONT)

        cy = y + 24 * scale + 6
        _tb(s, M, cy, CW, 8, R.wind_summary(result.get("wind"),
                                            bool(result.get("wind_error"))),
            size=sz(9), colour=MUTED, spacing=1.25)
        cy += 8
        # Commentary fills the space the closing notice does not need.
        nh = 20
        _commentary(s, M, cy, CW, h_mm - cy - mb - nh - 10)
        SL.rich(s, M, h_mm - mb - nh, CW, nh,
                [{"text": t} for t in R.CLOSING_NOTICE],
                size=sz(7.5), colour=MUTED, spacing=1.25, space_after=2)
        _footer(s, prs)
        s.notes_slide.notes_text_frame.text = (
            "Site overview. Add commentary on how the constraints shape the "
            "design approach for this property.")

    # ------------------------------------------------------- the site map
    #
    # Order differs by output. The standalone feasibility deck shows the map
    # first, as orientation before the detail. The binder puts it after the
    # findings, because by then the reader knows what the pins mean, and that
    # is the order Lee has been reinstating by hand on every job.
    def _map_slide():
        if not (map_path and os.path.exists(map_path)):
            return
        s = _slide(prs)
        top = _head(s, prs, "Your site", "Site map",
                    "Auckland Council aerial photography with your boundary "
                    "and everything we flagged") + 3
        from PIL import Image
        iw, ih = Image.open(map_path).size
        # The binder gives the map the whole page below the head. The
        # standalone deck holds 30mm back for a commentary box.
        if sf34:
            top, avail_h = 38.9, h_mm - mb - 38.9
        else:
            avail_h = h_mm - top - mb - 30
        k = min(CW / iw, avail_h / ih)
        s.shapes.add_picture(map_path, Mm(M + (CW - iw * k) / 2), Mm(top),
                             Mm(iw * k), Mm(ih * k))
        if not sf34:
            _commentary(s, M, h_mm - mb - 26, CW, 22,
                        "Commentary on the site map")
        _footer(s, prs)

    if not sf34:
        _map_slide()

    # ------------------------------------------------------- what we found
    def _body(f):
        if f["status"] == "on_site":
            txt = f.get("plain", "")
            if f.get("clause"):
                txt += "  (AUP %s)" % f["clause"]
            return txt
        if f["status"] == "abuts":
            return R.ABUTS_TEXT
        if f["status"] == "nearby":
            return ("Not on your property, but present within 200 m. Worth "
                    "being aware of, unlikely to control the design.")
        if f["status"] == "partial":
            return f.get("absent", "")
        return "Not confirmed from the available records. To be checked directly."

    if sf34:
        _binder_findings(prs, M, CW, h_mm, mb, findings,
                         errors + partial + on_site + abutting, nearby, clear,
                         _body)
        _map_slide()
        return prs

    s = _slide(prs)
    top = _head(s, prs, "Your site", "What we found",
                "%d planning, hazard and service records checked against your "
                "property boundary" % len(findings)) + 3
    items = errors + on_site + abutting + nearby + partial
    n = len(items) + 1

    # The clear list is the longest single string on the page and it grows every
    # time a layer is added: 28 names on a typical job now, against about 20
    # when this was laid out. Measure it and hang the block off the footer,
    # rather than reserving a fixed band that is too small on an all-clear site
    # and wastes 15mm of table room on a heavily flagged one.
    clear_text = "   ·   ".join(f["name"] for f in clear)
    clear_h = _text_height(clear_text, CW, prs._sz(7.5), 1.1) * _WRAP_SAFETY
    clear_top = h_mm - mb - 0.5 - (6 + clear_h)

    # Row heights, estimated. A table row grows to fit its text whatever height
    # it is created at, so the type has to come down until the table genuinely
    # fits; sizing the shape alone does nothing. Widths are the cell's live area,
    # inside the 1.5mm and 3mm side margins style_table sets.
    cols = (0.26, 0.16, 0.58)
    live = [CW * f - 4.5 for f in cols]
    avail = clear_top - 8 - top

    def _table_height(k, pad):
        h = 2 * pad + _text_height("WHAT IT MEANS FOR YOUR PROJECT", live[2],
                                   sz(8.5) * k)
        for f in items:
            h += 2 * pad + max(
                _text_height(f["name"], live[0], sz(9.5) * k, bold=True),
                _text_height(STATUS_WORD[f["status"]], live[1], sz(8.5) * k,
                             bold=True),
                _text_height(_body(f), live[2], sz(9) * k))
        return h * _WRAP_SAFETY

    # Padding comes off first and type only after it, because a 5.6pt finding
    # on a printed page is worse than a tight one. Last entry is the floor: if
    # even that overflows the table is clipped to the band rather than allowed
    # to print through the list below it.
    k, pad, th = 1.0, 1.6, 0
    for k, pad in ((1.0, 1.6), (1.0, 1.2), (1.0, 1.0), (0.95, 1.0),
                   (0.9, 1.0), (0.85, 0.9), (0.8, 0.8)):
        th = _table_height(k, pad)
        if th <= avail:
            break

    tbl = s.shapes.add_table(n, 3, Mm(M), Mm(top), Mm(CW),
                             Mm(min(th, avail))).table
    for i, frac in enumerate(cols):
        tbl.columns[i].width = Mm(CW * frac)
    _cell(tbl, 0, 0, "WHAT WE CHECKED", bold=True, colour=GREEN,
          font=HEAD_FONT, size=sz(8.5) * k)
    _cell(tbl, 0, 1, "STATUS", bold=True, colour=GREEN, font=HEAD_FONT,
          size=sz(8.5) * k)
    _cell(tbl, 0, 2, "WHAT IT MEANS FOR YOUR PROJECT", bold=True,
          colour=GREEN, font=HEAD_FONT, size=sz(8.5) * k)
    for i, f in enumerate(items, 1):
        _cell(tbl, i, 0, f["name"], size=sz(9.5) * k, bold=True)
        _cell(tbl, i, 1, STATUS_WORD[f["status"]], size=sz(8.5) * k, bold=True,
              colour=STATUS_RGB[f["status"]], font=HEAD_FONT)
        _cell(tbl, i, 2, _body(f), size=sz(9) * k)
    _style_table(tbl, pad=pad)

    # Commentary fills whatever the table left over, so the slide never has a
    # dead band in the middle no matter how many rows the job produced. Only
    # when there is genuinely room: on a heavily flagged site the table takes
    # the whole band and the commentary belongs on the printed page instead.
    cy = top + th + 6
    if clear_top - 6 - cy > 16:
        _commentary(s, M, cy, CW, clear_top - 6 - cy,
                    "Commentary on what this means for the design")

    _tb(s, M, clear_top, CW, 6, "ALSO CHECKED, NOTHING FOUND",
        size=prs._sz(9.5), font=HEAD_FONT, colour=GREEN, bold=True)
    _tb(s, M, clear_top + 6, CW, clear_h + 2, clear_text,
        size=prs._sz(7.5), colour=MUTED, spacing=1.1)
    _footer(s, prs)
    s.notes_slide.notes_text_frame.text = (
        "Add a row to the table for any commentary of your own. Delete rows "
        "that are not worth raising with this client.")

    return prs


# --------------------------------------------------------------------- Word

def _dset(run, size, bold=False, colour=None, font=BODY_FONT):
    run.font.size = DPt(size)
    run.font.bold = bold
    run.font.name = font
    if colour:
        run.font.color.rgb = colour


def build_docx(result, out_path, map_path=None):
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = DMm(210), DMm(297)
    for attr in ("left_margin", "right_margin"):
        setattr(sec, attr, DMm(18))
    sec.top_margin = sec.bottom_margin = DMm(16)

    parcel = result.get("parcel") or {}
    zone = result.get("zone") or {}
    std = zone.get("standards") or {}
    findings = result["findings"]
    on_site = [f for f in findings if f["status"] == "on_site"]
    # Adjoins the boundary without any of the land being inside it. Flagged and
    # shown, but never counted as on the property.
    abutting = [f for f in findings if f["status"] == "abuts"]
    nearby = [f for f in findings if f["status"] == "nearby"]
    clear = [f for f in findings if f["status"] == "clear"]
    errors = [f for f in findings if f["status"] == "error"]

    p = doc.add_paragraph()
    _dset(p.add_run("SITE FEASIBILITY CHECK"), 22, True,
          DRGB(0x01, 0x63, 0x2F), HEAD_FONT)
    p = doc.add_paragraph()
    _dset(p.add_run(result["site"].get("display", result["address"])), 12)
    p = doc.add_paragraph()
    _dset(p.add_run("Prepared %s by Zones Landscaping Auckland Central"
                    % result.get("generated", "")), 9, colour=DRGB(
                        0x6B, 0x72, 0x6B))
    p = doc.add_paragraph()
    _dset(p.add_run(R.SHORT_NOTICE), 8.5, colour=DRGB(0x6B, 0x72, 0x6B))

    def h(text):
        para = doc.add_paragraph()
        _dset(para.add_run(text.upper()), 12, True, DRGB(0x01, 0x63, 0x2F),
              HEAD_FONT)
        return para

    h("Your property")
    t = doc.add_table(rows=3, cols=2)
    t.style = "Light List Accent 1"
    area = parcel.get("area_m2")
    for i, (k, v) in enumerate([
            ("Legal description", parcel.get("legal_description") or "-"),
            ("Record of title", parcel.get("title") or "-"),
            ("Site area", "%s m² (%s)" % (f"{area:,}", parcel["area_source"])
             if area else "-")]):
        t.cell(i, 0).text = k
        t.cell(i, 1).text = str(v)

    h("Zone and standards")
    p = doc.add_paragraph()
    _dset(p.add_run("%s%s" % (zone.get("name") or "Not determined",
                              " (%s)" % std["code"] if std.get("code") else "")),
          12, True)
    c = std.get("clauses") or {}
    rows = [("Front yard, minimum", std.get("front_yard_m"), "m", "yards"),
            ("Side yard, minimum", std.get("side_yard_m"), "m", "yards"),
            ("Rear yard, minimum", std.get("rear_yard_m"), "m", "yards"),
            ("Maximum building coverage", std.get("site_coverage_pct"), "%",
             "coverage"),
            ("Maximum hard surface", std.get("impervious_pct"), "%",
             "impervious"),
            ("Minimum landscaped area", std.get("landscaped_pct"), "%",
             "landscaped"),
            ("Riparian yard", std.get("riparian_yard_m"), "m", "yards"),
            ("Coastal protection yard", std.get("coastal_yard_m"), "m",
             "yards")]
    t = doc.add_table(rows=len(rows) + 1, cols=3)
    t.style = "Light List Accent 1"
    for j, head in enumerate(("Standard", "Value", "AUP clause")):
        t.cell(0, j).text = head
    for i, (label, val, unit, key) in enumerate(rows, 1):
        t.cell(i, 0).text = label
        t.cell(i, 1).text = "n/a" if val is None else "%s%s" % (val, unit)
        t.cell(i, 2).text = c.get(key, "")

    hard = S.impervious_allowance(area, std)
    if hard:
        p = doc.add_paragraph()
        _dset(p.add_run(
            "On %s m², roughly %s m² of hard surface is allowed in total, "
            "including the house roof and the existing driveway."
            % (f"{area:,}", f"{hard:,.0f}")), 10.5)

    # Wind zone. Under the standards, for the same reason as everywhere else:
    # it is a value the site has, not a finding about it, and it belongs with
    # the other numbers a structure gets built to.
    wind = result.get("wind")
    h("Wind zone")
    if wind:
        p = doc.add_paragraph()
        _dset(p.add_run(R.wind_headline(wind)), 11, True)
        p = doc.add_paragraph()
        _dset(p.add_run(wind["plain"]), 10.5)
        for o in wind.get("others") or []:
            if not o["higher"]:
                continue
            p = doc.add_paragraph()
            _dset(p.add_run(
                "Part of the property, %sis mapped %s. Anything built on that "
                "part has to be built to the higher zone."
                % ("" if o["m2"] is None else
                   "about %s m² of it, " % (f"{o['m2']:,.1f}" if o["m2"] < 10
                                            else f"{o['m2']:,.0f}"),
                   o["label"])), 10.5)
        p = doc.add_paragraph()
        _dset(p.add_run(wind["caveat"]), 9, colour=DRGB(0x6B, 0x72, 0x6B))
    else:
        p = doc.add_paragraph()
        _dset(p.add_run(R.WIND_FAILED if result.get("wind_error")
                        else R.WIND_UNKNOWN), 10.5)

    if map_path and os.path.exists(map_path):
        h("Site map")
        doc.add_picture(map_path, width=DMm(174))

    h("What we found")
    p = doc.add_paragraph()
    _dset(p.add_run("%d records checked. %d flagged, %d clear."
                    % (len(findings),
                       len(on_site) + len(abutting) + len(nearby),
                       len(clear))), 10.5)

    items = errors + on_site + abutting + nearby + [f for f in findings
                                         if f["status"] == "partial"]
    t = doc.add_table(rows=len(items) + 1, cols=3)
    t.style = "Light List Accent 1"
    for j, head in enumerate(("What we checked", "Status",
                              "What it means for your project")):
        t.cell(0, j).text = head
    for i, f in enumerate(items, 1):
        t.cell(i, 0).text = f["name"]
        t.cell(i, 1).text = STATUS_WORD[f["status"]]
        if f["status"] == "on_site":
            body = f.get("plain", "")
            if f.get("clause"):
                body += "  (AUP %s)" % f["clause"]
        elif f["status"] == "abuts":
            body = R.ABUTS_TEXT
        elif f["status"] == "nearby":
            body = ("Not on your property, but present within 200 m. Worth "
                    "being aware of, unlikely to control the design.")
        elif f["status"] == "partial":
            body = f.get("absent", "")
        else:
            body = "Not confirmed from the available records. To be checked directly."
        t.cell(i, 2).text = body

    p = doc.add_paragraph()
    _dset(p.add_run("Also checked, nothing found: "), 9, True)
    _dset(p.add_run(", ".join(f["name"] for f in clear)), 9,
          colour=DRGB(0x6B, 0x72, 0x6B))

    p = doc.add_paragraph()
    _dset(p.add_run(""), 6)
    intro, liability, attribution = R.CLOSING_NOTICE
    p = doc.add_paragraph()
    _dset(p.add_run(intro), 8.5, colour=DRGB(0x6B, 0x72, 0x6B))
    p = doc.add_paragraph()
    _dset(p.add_run(liability), 8.5, True)
    p = doc.add_paragraph()
    _dset(p.add_run(attribution), 8, colour=DRGB(0x6B, 0x72, 0x6B))
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.save(out_path)

