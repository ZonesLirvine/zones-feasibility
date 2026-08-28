"""
A3 landscape presentation sheets.

This is a different thing from report_pdf's A4 report, not a reflow of it. An
A3 sheet in a folder is looked at, not read: it sits open next to design
drawings and gets pointed at across a table. So the layout is panels and pulled
out numbers at presentation scale, with the map given a whole sheet, rather
than continuous body copy in columns.

Sheets:
  1  Your site          headline numbers, property, what you can build on,
                        and the planning standards as a tile grid
  2  Site map           full sheet, aerial with the legend beside it
  3  What we found      flagged items as cards, everything clear as chips
"""

import math
import os

import fitz

import layers as L
import render as R
import standards as S

W, H = 1190.55, 841.89                 # A3 landscape
M = 52                                 # page margin
CONTENT = W - M * 2

GREEN = (0.004, 0.388, 0.184)
GREEN_SOFT = (0.90, 0.94, 0.91)
PANEL = (0.965, 0.972, 0.965)
LINE = (0.85, 0.88, 0.85)
INK = (0.12, 0.12, 0.12)
MUTED = (0.42, 0.45, 0.42)

# Fixed layout. Every job produces exactly four sheets with the same regions
# in the same places, so a folder of jobs looks like one document set rather
# than four different lengths. Content is fitted to the slots, not the other
# way round.
SHEET1 = dict(stats_y=178, stats_h=118,
              read_y=310, read_h=54,
              panels_y=378, panels_h=186,
              std_label_y=584, tiles_y=596, tiles_h=80,
              fences_y=690, notes_y=710, notes_h=34)

# The entries band is fixed top and bottom; rows are distributed inside it.
# Pinning a row height instead leaves a dead void on jobs with few findings,
# which reads as a mistake rather than as deliberate whitespace.
SHEET3 = dict(summary_y=140, entries_y=176, band_h=404, max_row_h=145,
              rows=4, cols=2, note_y=596, tail_y=666, clear_y=718)

# Standing close. Same on every job, so the sheet always ends on a considered
# note rather than simply stopping wherever the findings ran out.
CLOSING_NOTE = (
    "Everything above is identified for further investigation, not confirmed. "
    "These get resolved at Stage 3, Detailed Planning and Costing, where the "
    "consent position is confirmed and the fixed quote is prepared. We design "
    "around the constraints where we can, and tell you early if any of them "
    "need a planner, engineer or arborist, so it does not hold up the "
    "programme."
)

CARD_CHARS = 250          # body text is trimmed to fit a fixed-height card

STATUS = {
    "on_site": ((0.82, 0.30, 0.08), "NEEDS ATTENTION"),
    "abuts":   ((0.88, 0.64, 0.08), "ADJOINS"),
    "nearby":  ((0.88, 0.64, 0.08), "NEARBY"),
    "error":   ((0.50, 0.50, 0.50), "NOT CHECKED"),
    "clear":   ((0.15, 0.60, 0.30), "CLEAR"),
    "partial": ((0.88, 0.64, 0.08), "NOT CONFIRMED"),
}

_USER_FONTS = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Windows\Fonts")
# latin-ext first, latin second. The latin subsets have no macron glyphs, and
# PyMuPDF embeds the file rather than asking the OS for a substitute, so a
# missing glyph is dropped silently: "Toitu Te Whenua" printed with a gap where
# the u-macron belongs, and any Orakei, Mangere or Pukekohe address would have
# lost characters in the header of every page. The pptx path never showed this
# because PowerPoint substitutes a font of its own. Keep both entries: the
# latin files stay as a fallback so the tool still runs on a machine where only
# they are installed, just without macrons.
FONT_FILES = {
    "head": ["montserrat-v31-latin-ext-700.ttf",
             "montserrat-v31-latin-700.ttf"],
    "semi": ["montserrat-v31-latin-ext-600.ttf",
             "montserrat-v31-latin-600.ttf"],
    "body": ["open-sans-v44-latin-ext-regular.ttf",
             "open-sans-v44-latin-regular.ttf"],
    "bold": ["open-sans-v44-latin-ext-600.ttf",
             "open-sans-v44-latin-600.ttf"],
}
BUILTIN = {"head": "hebo", "semi": "hebo", "body": "helv", "bold": "hebo"}


def _font_path(names):
    for n in names:
        for base in (_USER_FONTS, r"C:\Windows\Fonts"):
            p = os.path.join(base, n)
            if os.path.exists(p):
                return p
    return None


class Sheet:
    def __init__(self, title):
        self.doc = fitz.open()
        self.title = title
        self.fonts = {k: _font_path(v) for k, v in FONT_FILES.items()}
        self.metrics = {}
        for k, p in self.fonts.items():
            try:
                self.metrics[k] = (fitz.Font(fontfile=p) if p
                                   else fitz.Font(BUILTIN[k]))
            except Exception:                     # noqa: BLE001
                self.fonts[k] = None
                self.metrics[k] = fitz.Font(BUILTIN[k])
        self.page = None

    def f(self, key):
        return key if self.fonts.get(key) else BUILTIN[key]

    def w(self, s, font="body", size=12):
        return self.metrics[font].text_length(s, fontsize=size)

    # ---------------------------------------------------------------- sheet
    def new(self, kind, heading=None, sub=None, note=None):
        """kind 'cover' gives the deep band, 'inner' a slim bar."""
        p = self.doc.new_page(width=W, height=H)
        for k, path in self.fonts.items():
            if path:
                p.insert_font(fontname=k, fontfile=path)
        self.page = p

        if kind == "cover":
            p.draw_rect(fitz.Rect(0, 0, W, 150), color=None, fill=GREEN)
            p.insert_text((M, 68), "SITE FEASIBILITY", fontname=self.f("head"),
                          fontsize=40, color=(1, 1, 1))
            p.insert_text((M, 100), (sub or "")[:96], fontname=self.f("body"),
                          fontsize=17, color=(0.86, 0.94, 0.89))
            p.insert_text((M, 124), note or "", fontname=self.f("body"),
                          fontsize=10.5, color=(0.74, 0.88, 0.79))
            return 192

        p.draw_rect(fitz.Rect(0, 0, W, 14), color=None, fill=GREEN)
        p.insert_text((M, 74), (heading or "").upper(),
                      fontname=self.f("head"), fontsize=26, color=GREEN)
        if sub:
            p.insert_text((M, 98), sub, fontname=self.f("body"), fontsize=12,
                          color=MUTED)
        return 124 if sub else 106

    # --------------------------------------------------------------- pieces
    def panel(self, rect, title=None, fill=PANEL):
        self.page.draw_rect(rect, color=LINE, fill=fill, width=0.8)
        if title:
            self.page.insert_text((rect.x0 + 22, rect.y0 + 32), title.upper(),
                                  fontname=self.f("head"), fontsize=13,
                                  color=GREEN)
            return rect.y0 + 54
        return rect.y0 + 22

    def stat(self, rect, value, label, sub=None, colour=GREEN):
        self.page.draw_rect(rect, color=None, fill=GREEN_SOFT)
        self.page.draw_rect(fitz.Rect(rect.x0, rect.y0, rect.x0 + 5, rect.y1),
                            color=None, fill=colour)
        self.page.insert_text((rect.x0 + 24, rect.y0 + 34), label.upper(),
                              fontname=self.f("head"), fontsize=11,
                              color=MUTED)
        self.page.insert_text((rect.x0 + 24, rect.y0 + 82), str(value),
                              fontname=self.f("head"), fontsize=36,
                              color=colour)
        if sub:
            self.page.insert_text((rect.x0 + 24, rect.y0 + 104), sub,
                                  fontname=self.f("body"), fontsize=11,
                                  color=MUTED)

    def para(self, x, y, width, s, size=11.5, font="body", colour=INK,
             leading=1.4):
        rect = fitz.Rect(x, y, x + width, H)
        rc = self.page.insert_textbox(rect, s, fontname=self.f(font),
                                      fontsize=size, color=colour,
                                      lineheight=leading)
        return y + (rect.height - rc if rc >= 0 else rect.height)

    def kv(self, x, y, label, value, width, size=12):
        self.page.insert_text((x, y), label, fontname=self.f("body"),
                              fontsize=size, color=MUTED)
        self.page.insert_text((x + width * 0.42, y), str(value),
                              fontname=self.f("bold"), fontsize=size,
                              color=INK)
        return y + size + 11

    def tile(self, rect, value, label, clause=None, dim=False):
        self.page.draw_rect(rect, color=LINE,
                            fill=(0.975, 0.975, 0.975) if dim else (1, 1, 1),
                            width=0.8)
        self.page.insert_text((rect.x0 + 16, rect.y0 + 38), str(value),
                              fontname=self.f("head"), fontsize=25,
                              color=(0.72, 0.74, 0.72) if dim else GREEN)
        self.page.insert_text((rect.x0 + 16, rect.y0 + 58), label,
                              fontname=self.f("body"), fontsize=10,
                              color=MUTED)
        if clause:
            self.page.insert_text((rect.x0 + 16, rect.y0 + 73), clause,
                                  fontname=self.f("body"), fontsize=8.5,
                                  color=(0.62, 0.66, 0.62))

    # --------------------------------------------------------------- output
    def save(self, path):
        n = len(self.doc)
        for i, p in enumerate(self.doc, 1):
            for k, fp in self.fonts.items():
                if fp:
                    p.insert_font(fontname=k, fontfile=fp)
            p.draw_line(fitz.Point(M, H - 46), fitz.Point(W - M, H - 46),
                        color=LINE, width=0.8)
            p.insert_text((M, H - 30), self.title[:120],
                          fontname=self.f("body"), fontsize=9, color=MUTED)
            lbl = "Indicative only  \u00b7  Sheet %d of %d" % (i, n)
            p.insert_text((W - M - self.w(lbl, "body", 9), H - 30), lbl,
                          fontname=self.f("body"), fontsize=9, color=MUTED)
        self.doc.save(path, deflate=True)
        return path


# ------------------------------------------------------------------ sheets

def _wind_stat_sub(wind, failed=False):
    """
    Sub-caption for the wind tile: the zone in words, and its design gust.

    Short by necessity, the tile holds one line. The version with what it
    means for the build, and the caveat that a designer confirms it, is in the
    PDF and the terminal report.
    """
    if not wind:
        return "not read this run" if failed else "not mapped by Council"
    if wind.get("speed"):
        return "%s, gust %d m/s" % (wind["label"], wind["speed"])
    return wind["label"][:30]


def _sheet_site(s, result, note=None):
    parcel = result.get("parcel") or {}
    zone = result.get("zone") or {}
    std = zone.get("standards")
    findings = result["findings"]
    flagged = [f for f in findings
               if f["status"] in ("on_site", "abuts", "nearby")]

    s.new("cover", sub=result["site"].get("display", result["address"]),
          note="Prepared %s by Zones Landscaping Auckland Central"
               % result.get("generated", ""))

    # Every region below sits at a fixed y so this sheet is identical across
    # jobs regardless of how much was flagged.
    G = SHEET1
    y = G["stats_y"]

    # Four headline numbers. Wind sits here rather than in the standards grid
    # below, because it reads the way the zone does, a short code with the
    # full name under it, and it is one of the few things about a site that
    # decides what can be built on it.
    gap = 22
    n_stats = 4
    cw = (CONTENT - gap * (n_stats - 1)) / n_stats
    area = parcel.get("area_m2")
    wind = result.get("wind")
    s.stat(fitz.Rect(M, y, M + cw, y + G["stats_h"]),
           "%s m\u00b2" % f"{area:,}" if area else "-", "Site area",
           parcel.get("area_source", ""))
    s.stat(fitz.Rect(M + cw + gap, y, M + cw * 2 + gap,
                     y + G["stats_h"]),
           (std or {}).get("code") or "-", "Zone",
           (zone.get("name") or "").replace("Residential - ", "")[:30])
    s.stat(fitz.Rect(M + (cw + gap) * 2, y, M + cw * 3 + gap * 2,
                     y + G["stats_h"]),
           # "U" is Council's code for no data, which is not a wind zone and
           # must not be printed as if it were one.
           wind["code"] if wind and wind["code"] in L.WIND_ORDER else "-",
           "Wind zone",
           _wind_stat_sub(wind, bool(result.get("wind_error"))))
    s.stat(fitz.Rect(M + (cw + gap) * 3, y, W - M, y + G["stats_h"]),
           "%d of %d" % (len(flagged), len(findings)), "Flagged for attention",
           "%d checked, %d clear"
           % (len(findings), len(findings) - len(flagged)),
           colour=(0.82, 0.30, 0.08) if flagged else GREEN)

    # The headline finding, in Lee's words. This is the one thing the data
    # cannot produce: five separate flags are often one feature, and only a
    # person can say which. Always rendered so the sheet keeps its shape.
    ry_ = G["read_y"]
    s.page.draw_rect(fitz.Rect(M, ry_, W - M, ry_ + G["read_h"]),
                     color=None, fill=GREEN_SOFT)
    s.page.draw_rect(fitz.Rect(M, ry_, M + 5, ry_ + G["read_h"]),
                     color=None, fill=GREEN)
    s.page.insert_text((M + 24, ry_ + 20), "OUR READ ON THIS SITE",
                       fontname=s.f("head"), fontsize=10, color=MUTED)
    s.para(M + 24, ry_ + 28, CONTENT - 48,
           note or "To be completed before this pack is issued.",
           size=13 if note else 11, font="semi" if note else "body",
           colour=INK if note else (0.62, 0.66, 0.62))

    y = G["panels_y"]

    # Property, and what the rules allow.
    half = (CONTENT - gap) / 2
    ph = G["panels_h"]
    left = fitz.Rect(M, y, M + half, y + ph)
    ty = s.panel(left, "Your property")
    ty = s.kv(M + 22, ty + 8, "Legal description",
              parcel.get("legal_description") or "-", half - 44)
    ty = s.kv(M + 22, ty, "Record of title", parcel.get("title") or "-",
              half - 44)
    ty = s.para(M + 22, ty + 4, half - 44, R.PARCEL_CONFIRM, size=10,
                font="bold", colour=(0.72, 0.42, 0.04))
    s.para(M + 22, ty + 6, half - 44,
           "Covenants, consent notices and easements are not held in any public "
           "database and are not covered here. We recommend a title search "
           "before the design is finalised.", size=9.5, colour=MUTED)

    right = fitz.Rect(M + half + gap, y, W - M, y + ph)
    ry = s.panel(right, "What you can build on")
    hard = S.impervious_allowance(area, std)
    build = S.coverage_allowance(area, std)
    if hard:
        s.page.insert_text((M + half + gap + 22, ry + 42),
                           "%s m\u00b2" % f"{hard:,.0f}",
                           fontname=s.f("head"), fontsize=34, color=GREEN)
        s.page.insert_text((M + half + gap + 22, ry + 62),
                           "total hard surface allowed on this site",
                           fontname=s.f("body"), fontsize=11, color=MUTED)
        txt = ("That covers the house roof and the existing driveway as well "
               "as any new paving, so the amount available for new work is "
               "lower.")
        if build:
            txt += (" Building footprint is capped at about %s m\u00b2."
                    % f"{build:,.0f}")
        s.para(M + half + gap + 22, ry + 82, half - 44, txt, size=10.5)
    else:
        s.para(M + half + gap + 22, ry + 10, half - 44,
               S.pending_reason(zone.get("name") or "")
               or "Zone standards for this site are not held by this tool and "
                  "need to be confirmed against the Unitary Plan.",
               size=10.5, colour=MUTED)

    # Planning standards. Always the same eight tiles in the same order, with
    # "n/a" where a zone has no such standard, so the row is identical on
    # every job. H1 and H2 have no landscaped area standard, for example.
    s.page.insert_text((M, G["std_label_y"]), "PLANNING STANDARDS FOR THIS ZONE",
                       fontname=s.f("head"), fontsize=13, color=GREEN)
    std = std or {}
    c = std.get("clauses") or {}
    tiles = [(std.get("front_yard_m"), "m", "Front yard, min", "yards"),
             (std.get("side_yard_m"), "m", "Side yard, min", "yards"),
             (std.get("rear_yard_m"), "m", "Rear yard, min", "yards"),
             (std.get("site_coverage_pct"), "%", "Max building coverage",
              "coverage"),
             (std.get("impervious_pct"), "%", "Max hard surface", "impervious"),
             (std.get("landscaped_pct"), "%", "Min landscaped area",
              "landscaped"),
             (std.get("riparian_yard_m"), "m", "Riparian yard", "yards"),
             (std.get("coastal_yard_m"), "m", "Coastal yard", "yards")]
    tg, n = 12, len(tiles)
    tw = (CONTENT - tg * (n - 1)) / n
    ty = G["tiles_y"]
    for i, (val, unit, label, key) in enumerate(tiles):
        r = fitz.Rect(M + i * (tw + tg), ty, M + i * (tw + tg) + tw,
                      ty + G["tiles_h"])
        if val is None:
            s.tile(r, "n/a", label, None, dim=True)
        else:
            s.tile(r, "%s%s" % (val, unit), label,
                   "AUP %s" % c[key] if c.get(key) else None)

    fences = std.get("fences")
    s.para(M, G["fences_y"], CONTENT,
           ("Fences.  " + fences["plain"]) if fences else
           "Fences.  This zone has no fence height standard in the Unitary "
           "Plan chapter. Confirm before design.", size=10.5, colour=MUTED)

    # Fixed-height notes strip: always present, so the sheet never changes
    # height depending on whether there happened to be a warning.
    ny = G["notes_y"]
    warns = result.get("warnings") or []
    s.page.draw_rect(fitz.Rect(M, ny, W - M, ny + G["notes_h"]),
                     color=LINE, fill=(0.995, 0.985, 0.96), width=0.8)
    s.para(M + 16, ny + 13, CONTENT - 32,
           ("Please note.  " + "  ".join(warns)) if warns else
           "No additional zone notes for this property.",
           size=10, colour=(0.68, 0.42, 0.06) if warns else MUTED)

    # The closing notice, which used to have sheet 4 to itself. See
    # render.CLOSING_NOTICE.
    cy = ny + G["notes_h"] + 8
    for i, line in enumerate(R.CLOSING_NOTICE):
        cy = s.para(M, cy, CONTENT, line, size=7.5, leading=1.25,
                    colour=INK if i == 1 else MUTED,
                    font="bold" if i == 1 else "body") + 2


def _sheet_map(s, result, map_path):
    s.new("inner", heading="Site map",
          sub="Auckland Council aerial photography with your boundary and "
              "everything we flagged")
    img = fitz.Pixmap(map_path)
    top = 122
    avail_w, avail_h = CONTENT, H - top - 62
    scale = min(avail_w / img.width, avail_h / img.height)
    w, h = img.width * scale, img.height * scale
    s.page.insert_image(fitz.Rect(M + (CONTENT - w) / 2, top,
                                  M + (CONTENT - w) / 2 + w, top + h),
                        filename=map_path)


def trim(text, limit=CARD_CHARS):
    """Cut to a whole sentence within the limit, so cards stay a fixed size."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = cut.rfind(". ")
    return (cut[:stop + 1] if stop > limit * 0.5 else cut.rstrip() + "…")


def _chip_row(s, items, x0, y, colour, max_rows, size=9.5):
    """Chips wrapped to a fixed number of rows. Returns rows used."""
    x, row = x0, 0
    for i, label in enumerate(items):
        cw = s.w(label, "body", size) + 34
        if x + cw > W - M:
            row += 1
            if row >= max_rows:
                left = len(items) - i
                if left > 0:
                    s.page.insert_text((x, y + row * 24 - 24 + 13),
                                       "and %d more" % left,
                                       fontname=s.f("body"), fontsize=size,
                                       color=MUTED)
                return max_rows
            x = x0
        cy = y + row * 24
        s.page.draw_rect(fitz.Rect(x, cy, x + cw, cy + 19), color=LINE,
                         fill=(0.985, 0.99, 0.985), width=0.7)
        s.page.draw_circle(fitz.Point(x + 12, cy + 9.5), 3.4, color=None,
                           fill=colour)
        s.page.insert_text((x + 22, cy + 13), label, fontname=s.f("body"),
                           fontsize=size, color=(0.3, 0.32, 0.3))
        x += cw + 8
    return row + 1


CATEGORY_META = {
    "consent": "Consent likely required",
    "design": "Design constraint",
    "hazard": "Site hazard",
    "services": "Services present",
    "background": "Site context",
}


def _fit_para(s, x, y, width, text, room, size=10.0, lead=1.45,
              colour=(0.36, 0.38, 0.36)):
    """Set `text` at the largest size that still fits in `room` points.

    `para` draws into a rect running to the foot of the sheet, so it does not
    clip: an overlong list prints straight over whatever sits below it. These
    lists grow with the job, and the blocks under them are pinned to fixed y
    positions, so shrink to fit rather than trusting them to stay short.
    """
    while size > 7.5 and \
            math.ceil(s.w(text, "body", size) / width) * size * lead > room:
        size -= 0.25
    return s.para(x, y, width, text, size=size, leading=lead, colour=colour)


def _sheet_findings(s, result):
    """
    Editorial layout, not a card UI.

    The earlier version used eight equal boxes with shouted status labels and
    chip tags, which reads like a dashboard. This is set as a numbered list
    with hairline rules, muted category labels and a flowing tail paragraph.
    Status is carried by a small rule and the number colour rather than by
    coloured words repeated eight times.
    """
    findings = result["findings"]
    on_site = [f for f in findings if f["status"] == "on_site"]
    # Shares a boundary but sits outside the title. Grouped with nearby because
    # the one thing it is definitely not is on the property, and kept out of the
    # card grid for the same reason.
    abutting = [f for f in findings if f["status"] == "abuts"]
    nearby = [f for f in findings if f["status"] == "nearby"] + abutting
    clear = [f for f in findings if f["status"] == "clear"]
    # Not confirmed because the published dataset is incomplete. These get an
    # entry of their own like a finding does, but they are counted separately:
    # "not confirmed" is not the same claim as "on your property", and the
    # figure strip must not imply we found something on the site when what we
    # actually have is a gap in the data.
    errors = [f for f in findings if f["status"] == "error"]
    unconfirmed = [f for f in findings if f["status"] == "partial"]

    s.new("inner", heading="What we found",
          sub="Every planning, hazard and service record we hold was checked "
              "against your property boundary")

    G = SHEET3
    # Quiet figure strip. Small caps, hairline separated, no colour blocks.
    fy = G["summary_y"]
    figures = [(str(len(findings)), "records checked"),
               (str(len(on_site) + len(errors)), "on your property"),
               (str(len(nearby)),
                "adjoining or nearby" if abutting else "nearby"),
               (str(len(clear)), "clear")]
    # Only shown when there is one, so the figures always sum to the records
    # checked rather than quietly losing a row.
    if unconfirmed:
        figures.append((str(len(unconfirmed)), "to confirm"))
    fx = M
    for i, (num, label) in enumerate(figures):
        s.page.insert_text((fx, fy), num, fontname=s.f("head"), fontsize=17,
                           color=GREEN if i != 1 or not on_site
                           else STATUS["on_site"][0])
        w = s.w(num, "head", 17) + 8
        s.page.insert_text((fx + w, fy), label, fontname=s.f("body"),
                           fontsize=11, color=MUTED)
        fx += w + s.w(label, "body", 11) + 30
        if i < len(figures) - 1:
            s.page.draw_line(fitz.Point(fx - 17, fy - 12),
                             fitz.Point(fx - 17, fy + 3), color=LINE,
                             width=0.8)
    s.page.draw_line(fitz.Point(M, fy + 18), fitz.Point(W - M, fy + 18),
                     color=LINE, width=0.8)

    slots = G["rows"] * G["cols"]
    gap = 44
    colw = (CONTENT - gap) / 2
    # Unconfirmed items go ahead of the on-site findings so they always get a
    # detailed slot: a data gap is the thing most worth reading in full.
    ranked = errors + unconfirmed + on_site

    # The sheet is one fixed A3 page, so the detailed cards have a hard
    # ceiling. What used to happen past that ceiling was the bug: the
    # remainder was appended to the "nearby, not on your property" line, so on
    # a job with more than eight findings we told the owner that something
    # sitting on their land was somewhere down the road. Nothing is dropped
    # and nothing is relabelled now: the overflow keeps its own honest
    # heading, and buys the room for it by giving up one row of cards.
    if len(ranked) > slots:
        slots -= G["cols"]
    entries = ranked[:slots]
    extra = ranked[slots:]

    # Height reserved under the grid for the overflow block, taken off the
    # band so the cards shrink to fit rather than printing over it.
    extra_h = 86 if extra else 0
    rows_used = max(1, math.ceil(len(entries) / G["cols"])) if entries else 1
    row_h = min(G["max_row_h"], (G["band_h"] - extra_h) / rows_used)

    for i, f in enumerate(entries):
        colour = STATUS[f["status"]][0]
        col, row = i % G["cols"], i // G["cols"]
        x = M + col * (colw + gap)
        cy = G["entries_y"] + row * row_h

        s.page.draw_line(fitz.Point(x, cy), fitz.Point(x + colw, cy),
                         color=LINE, width=0.8)
        s.page.draw_line(fitz.Point(x, cy), fitz.Point(x + 30, cy),
                         color=colour, width=2.2)

        s.page.insert_text((x, cy + 30), "%02d" % (i + 1),
                           fontname=s.f("head"), fontsize=20,
                           color=(0.80, 0.85, 0.81))
        tx = x + 44
        s.page.insert_text((tx, cy + 26), f["name"][:52],
                           fontname=s.f("semi"), fontsize=13, color=INK)
        meta = CATEGORY_META.get(f.get("category"), "Site context")
        if f["status"] in ("error", "partial"):
            meta = "Not confirmed"
        s.page.insert_text((tx, cy + 40), meta.upper(), fontname=s.f("head"),
                           fontsize=8, color=colour)

        body = (f.get("plain", "") if f["status"] == "on_site"
                else f.get("absent") if f["status"] == "partial"
                else "Not confirmed from the available records. To be checked "
                     "directly before this report is relied on.")
        body = trim(body, CARD_CHARS)
        if f.get("clause"):
            body += "   AUP %s" % f["clause"]
        s.para(tx, cy + 50, colw - 44, body, size=10.5, leading=1.5,
               colour=(0.32, 0.34, 0.32))

    if not entries:
        s.para(M, G["entries_y"] + 16, CONTENT,
               "Nothing was found on the property itself. Everything we "
               "checked is either clear, or present nearby only.", size=13,
               colour=MUTED)

    if extra:
        # Same tier as the cards above, named rather than described. The
        # explanation a card carries is what varies; the fact that the record
        # touches the property is what matters here, and that is in the
        # heading. Split by status so neither claim is made about the other.
        ex_site = [f["name"] for f in extra if f["status"] == "on_site"]
        ex_gap = [f["name"] for f in extra if f["status"] != "on_site"]
        ey = G["entries_y"] + rows_used * row_h + 14
        s.page.draw_line(fitz.Point(M, ey - 12), fitz.Point(W - M, ey - 12),
                         color=LINE, width=0.8)
        s.page.insert_text((M, ey), "ALSO ON YOUR PROPERTY" if not ex_gap
                           else "ALSO IDENTIFIED", fontname=s.f("head"),
                           fontsize=9, color=STATUS["on_site"][0] if ex_site
                           else MUTED)
        ex_parts = []
        if ex_site:
            ex_parts.append("Present on your land and identified for further "
                            "investigation at Stage 3:  "
                            + ",  ".join(ex_site) + ".")
        if ex_gap:
            ex_parts.append("Not confirmed from the available records, to be "
                            "checked directly:  " + ",  ".join(ex_gap) + ".")
        _fit_para(s, M, ey + 12, CONTENT, "  ".join(ex_parts),
                  room=G["note_y"] - (ey + 12) - 10,
                  colour=(0.32, 0.34, 0.32))

    ny_ = G["note_y"]
    s.page.insert_text((M, ny_), "WHAT HAPPENS NEXT", fontname=s.f("head"),
                       fontsize=9, color=GREEN)
    # Full measure, not 0.72. At the narrower width this wraps to three lines
    # and the third ran into the hairline above the nearby list below.
    s.para(M, ny_ + 12, CONTENT, CLOSING_NOTE, size=10.5, leading=1.5,
           colour=(0.32, 0.34, 0.32))

    # Tail: flowing text rather than chip tags.
    ty = G["tail_y"]
    s.page.draw_line(fitz.Point(M, ty - 22), fitz.Point(W - M, ty - 22),
                     color=LINE, width=0.8)

    labels = [f["name"] for f in nearby if f["status"] != "abuts"]
    s.page.insert_text((M, ty),
                       "ADJOINING OR NEARBY, NOT ON YOUR PROPERTY" if abutting
                       else "NEARBY, NOT ON YOUR PROPERTY",
                       fontname=s.f("head"), fontsize=9, color=MUTED)
    # Two claims, kept apart. "Within 200 m" is not true of something the
    # boundary runs along, and "adjoining" is not true of something 150 m away.
    parts = []
    if abutting:
        parts.append("Adjoining your boundary but not inside your land:  "
                     + ",  ".join(f["name"] for f in abutting) + ".")
    if labels:
        parts.append("Present within 200 m and worth being aware of, though "
                     "unlikely to control the design:  "
                     + ",  ".join(labels) + ".")
    tail_text = ("  ".join(parts) if parts
                 else "Nothing flagged within 200 m of the property.")
    _fit_para(s, M, ty + 10, CONTENT, tail_text,
              room=G["clear_y"] - (ty + 10) - 6)

    cy = G["clear_y"]
    s.page.insert_text((M, cy), "CHECKED AND CLEAR", fontname=s.f("head"),
                       fontsize=9, color=MUTED)
    s.para(M, cy + 10, CONTENT, ",  ".join(f["name"] for f in clear) + ".",
           size=9.5, leading=1.5, colour=(0.52, 0.55, 0.52))


# ------------------------------------------------------------------ public

def build(result, out_path, map_path=None, note=None):
    s = Sheet("Site feasibility check  \u00b7  %s" % result["address"])
    _sheet_site(s, result, note)
    if map_path and os.path.exists(map_path):
        _sheet_map(s, result, map_path)
    _sheet_findings(s, result)
    return s.save(out_path)
