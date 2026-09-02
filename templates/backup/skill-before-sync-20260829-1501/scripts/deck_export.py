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
        bold=False, align=PP_ALIGN.LEFT, spacing=1.15):
    return SL.tb(slide, x, y, w, h, text, size=size, font=font, colour=colour,
                 bold=bold, align=align, spacing=spacing)


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


def build_pptx(result, out_path, map_path=None, size="a3"):
    """The four site slides on their own, as a standalone deck."""
    prs = SL.new_presentation(size)
    build_site_slides(prs, result, map_path)
    prs.save(out_path)
    return out_path


def build_site_slides(prs, result, map_path=None):
    """
    Add the four site slides to an existing presentation.

    Kept separate from build_pptx so the S&F Report generator can drop them in
    behind its YOUR SITE divider rather than Lee pulling them in by hand with
    Reuse Slides. The site-only export is still useful on its own, so both
    entry points stay.
    """
    w_mm, h_mm = prs._w, prs._h
    ml, mr, mt, mb = prs._m
    M = ml
    CW = w_mm - ml - mr
    size = "a3" if w_mm > 300 else "a4"
    scale = 1.0 if size == "a3" else 0.78        # shrink type on A4 slides

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
    s = _slide(prs)
    y = _head(s, prs, "Your site",
              result["site"].get("display", result["address"]),
              "Checked %s against your property boundary by Zones Landscaping "
              "Auckland Central" % result.get("generated", "")) + 4
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
    else:
        # Say why there is no figure. Without this the heading printed with
        # nothing under it on any zone whose standards are not held, which
        # reads as a rendering fault rather than as a deliberate gap. Same
        # wording as the A3 and A4 renderers.
        _tb(s, M + half + gap, y + 8, half, 16,
            S.pending_reason(zone.get("name") or "")
            or "Zone standards for this site are not held by this tool and "
               "need to be confirmed against the Unitary Plan.",
            size=sz(10), colour=MUTED)

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

    # Commentary fills the space below the table rather than sitting in a
    # thin strip with a gap above it.
    cy = y + 24 * scale + 6
    _commentary(s, M, cy, CW, h_mm - cy - mb - 6)
    _footer(s, prs)
    s.notes_slide.notes_text_frame.text = (
        "Site overview. Add commentary on how the constraints shape the "
        "design approach for this property.")

    # ------------------------------------------------------------ slide 2
    if map_path and os.path.exists(map_path):
        s = _slide(prs)
        top = _head(s, prs, "Your site", "Site map",
                    "Auckland Council aerial photography with your boundary "
                    "and everything we flagged") + 3
        from PIL import Image
        iw, ih = Image.open(map_path).size
        avail_w, avail_h = CW, h_mm - top - mb - 30
        k = min(avail_w / iw, avail_h / ih)
        s.shapes.add_picture(map_path, Mm(M + (CW - iw * k) / 2), Mm(top),
                             Mm(iw * k), Mm(ih * k))
        _commentary(s, M, h_mm - mb - 26, CW, 22, "Commentary on the site map")
        _footer(s, prs)

    # ------------------------------------------------------------ slide 3
    s = _slide(prs)
    top = _head(s, prs, "Your site", "What we found",
                "%d planning, hazard and service records checked against your "
                "property boundary" % len(findings)) + 3

    items = errors + on_site + abutting + nearby + partial
    n = len(items) + 1

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

    # ------------------------------------------------------------ slide 4
    s = _slide(prs)
    top = _head(s, prs, "Your site", "Important notice") + 2
    _tb(s, M, top, CW, 10, R.DISCLAIMER_INTRO, size=sz(11), colour=BODY_INK)
    half = (CW - 8) / 2
    # Split the points across the two columns instead of taking three each.
    # The hardcoded slice silently dropped everything past the sixth, so the
    # seventh clause, the one telling the client every finding is for further
    # investigation and must be verified before they commit, never reached
    # the deck. Ceiling division keeps the extra clause in the left column.
    per_col = -(-len(R.DISCLAIMER_POINTS) // 2)
    for col in (0, 1):
        pts = R.DISCLAIMER_POINTS[col * per_col:(col + 1) * per_col]
        txt = "\n\n".join("%d.  %s\n%s" % (col * per_col + i + 1, h, b)
                          for i, (h, b) in enumerate(pts))
        _tb(s, M + col * (half + 8), top + 14, half,
            h_mm - top - mb - 42, txt, size=sz(9), colour=BODY_INK,
            spacing=1.25)
    _tb(s, M, h_mm - mb - 26, CW, 8, R.VALIDITY, size=sz(9),
        colour=RGBColor(0xB8, 0x6B, 0x0A), bold=True)
    _tb(s, M, h_mm - mb - 18, CW, 8, R.DISCLAIMER_LIABILITY, size=sz(9.5),
        colour=INK, bold=True)
    _tb(s, M, h_mm - mb - 9, CW, 8, L.ATTRIBUTION, size=sz(8), colour=MUTED)
    _footer(s, prs)
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

    doc.add_page_break()
    h("Important notice, please read")
    p = doc.add_paragraph()
    _dset(p.add_run(R.DISCLAIMER_INTRO), 10)
    for i, (head, body) in enumerate(R.DISCLAIMER_POINTS, 1):
        p = doc.add_paragraph()
        _dset(p.add_run("%d.  %s" % (i, head)), 10, True)
        p = doc.add_paragraph()
        _dset(p.add_run(body), 9.5, colour=DRGB(0x4A, 0x4F, 0x4A))
        p.paragraph_format.left_indent = DMm(6)
    p = doc.add_paragraph()
    _dset(p.add_run(R.VALIDITY), 9.5, True, DRGB(0xB8, 0x6B, 0x0A))
    p = doc.add_paragraph()
    _dset(p.add_run(R.DISCLAIMER_LIABILITY), 9.5, True)
    p = doc.add_paragraph()
    _dset(p.add_run(L.ATTRIBUTION), 8, colour=DRGB(0x6B, 0x72, 0x6B))
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.save(out_path)
    return out_path
