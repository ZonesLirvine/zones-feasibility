"""
Renders the feasibility result as a client-facing PDF.

Two page setups:

  A4 portrait (default)  595.28 x 841.89 pt, single column. Two of these
                         impose exactly onto one A3 landscape sheet
                         (595.28 x 2 = 1190.55), which is the folder spread.

  A3 landscape           1190.55 x 841.89 pt, two columns. Native full-size
                         pages for an A3 presentation folder, with the site
                         map given a page to itself.

A3 has to be two-column. A single text column 1,100 pt wide runs to roughly
170 characters a line, which nobody reads comfortably. Two columns bring the
measure back to about the same as the A4 version.

Brand fonts are Montserrat for headings and Open Sans for body, both installed
on Lee's machine. Falls back to Helvetica if missing so this runs elsewhere.
"""

import os

import fitz

import layers as L
import render as R
import soil as SOIL
import standards as S

A4_PORTRAIT = (595.28, 841.89)
A3_LANDSCAPE = (1190.55, 841.89)

PAGES = {"a4": A4_PORTRAIT, "a3": A3_LANDSCAPE}
COLUMNS = {"a4": 1, "a3": 2}

MARGIN = 42
GUTTER = 42
GREEN = (0.004, 0.388, 0.184)          # Zones 01632F
INK = (0.13, 0.13, 0.13)
MUTED = (0.45, 0.45, 0.45)
RULE = (0.85, 0.85, 0.85)

STATUS_COLOUR = {
    "on_site": (0.85, 0.33, 0.10),     # needs attention
    "abuts":   (0.90, 0.68, 0.10),     # shares a boundary, not on the land
    "nearby":  (0.90, 0.68, 0.10),     # worth knowing
    "clear":   (0.16, 0.62, 0.32),     # checked, nothing found
    "error":   (0.55, 0.55, 0.55),     # could not be checked
    "partial": (0.90, 0.68, 0.10),     # published data does not cover it fully
}
STATUS_WORD = {"on_site": "FLAGGED", "abuts": "ADJOINS", "nearby": "NEARBY",
               "clear": "CLEAR", "error": "NOT CHECKED",
               "partial": "NOT CONFIRMED"}

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


class Doc:
    """Flowing multi-column layout over PyMuPDF."""

    def __init__(self, title, size="a4"):
        self.doc = fitz.open()
        self.title = title
        self.W, self.H = PAGES[size]
        self.cols = COLUMNS[size]
        self.size = size
        self.fonts = {k: _font_path(v) for k, v in FONT_FILES.items()}

        # fitz.get_text_length only knows the base-14 fonts, so metrics for
        # the embedded brand fonts come from Font objects instead.
        self.metrics = {}
        for key, path in self.fonts.items():
            try:
                self.metrics[key] = (fitz.Font(fontfile=path) if path
                                     else fitz.Font(BUILTIN[key]))
            except Exception:                     # noqa: BLE001
                self.fonts[key] = None
                self.metrics[key] = fitz.Font(BUILTIN[key])

        self.page = None
        self.col = 0
        self.ncols = self.cols
        self.y = 0
        self.top = 0

    # ------------------------------------------------------------- geometry
    @property
    def col_w(self):
        total = self.W - MARGIN * 2
        if self.ncols == 1:
            return total
        return (total - GUTTER * (self.ncols - 1)) / self.ncols

    @property
    def col_x(self):
        return MARGIN + self.col * (self.col_w + GUTTER)

    @property
    def bottom(self):
        return self.H - 58

    def set_columns(self, n):
        """Switch column count. Resets to the first column."""
        self.ncols = n
        self.col = 0

    def width(self, s, font="body", size=10):
        return self.metrics[font].text_length(s, fontsize=size)

    # ---------------------------------------------------------------- pages
    def new_page(self, band=False):
        self.page = self.doc.new_page(width=self.W, height=self.H)
        for key, path in self.fonts.items():
            if path:
                self.page.insert_font(fontname=key, fontfile=path)
        band_h = 96 if self.size == "a4" else 104
        if band:
            self.page.draw_rect(fitz.Rect(0, 0, self.W, band_h), color=None,
                                fill=GREEN)
            self.y = band_h + 24
        else:
            self.page.draw_rect(fitz.Rect(0, 0, self.W, 8), color=None,
                                fill=GREEN)
            self.y = MARGIN + 14
        self.col = 0
        self.top = self.y
        return self.page

    def need(self, h):
        """Move to the next column, or a new page, if h will not fit."""
        if self.y + h <= self.bottom:
            return
        if self.col < self.ncols - 1:
            self.col += 1
            self.y = self.top
        else:
            self.new_page()

    def fname(self, key):
        return key if self.fonts.get(key) else BUILTIN[key]

    def space(self, h):
        self.y += h

    # ----------------------------------------------------------------- text
    def text(self, s, size=10, font="body", colour=INK, indent=0,
             leading=1.35, gap=0):
        w = self.col_w - indent
        lines = max(1, int(self.width(s, font, size) / w) + 1)
        self.need(lines * size * leading + gap + 6)
        rect = fitz.Rect(self.col_x + indent, self.y,
                         self.col_x + indent + w, self.bottom + 40)
        rc = self.page.insert_textbox(
            rect, s, fontname=self.fname(font), fontsize=size, color=colour,
            align=0, lineheight=leading)
        used = (rect.height - rc) if rc >= 0 else rect.height
        self.y += used + gap
        return used

    def heading(self, s, size=13, gap=8):
        self.need(46)
        self.page.insert_text((self.col_x, self.y + size), s.upper(),
                              fontname=self.fname("head"), fontsize=size,
                              color=GREEN)
        self.y += size + 6
        self.page.draw_line(fitz.Point(self.col_x, self.y),
                            fitz.Point(self.col_x + self.col_w, self.y),
                            color=GREEN, width=1.2)
        self.y += gap

    def row(self, label, value, size=10):
        self.need(20)
        label_w = min(210, self.col_w * 0.46)
        self.page.insert_text((self.col_x, self.y + size), label,
                              fontname=self.fname("body"), fontsize=size,
                              color=MUTED)
        self.page.insert_text((self.col_x + label_w, self.y + size),
                              str(value), fontname=self.fname("bold"),
                              fontsize=size, color=INK)
        self.y += size + 8

    # --------------------------------------------------------------- output
    def save(self, path):
        self._footers()
        self.doc.save(path, deflate=True)
        return path

    def _footers(self):
        n = len(self.doc)
        for i, page in enumerate(self.doc, 1):
            for key, fp in self.fonts.items():
                if fp:
                    page.insert_font(fontname=key, fontfile=fp)
            page.draw_line(fitz.Point(MARGIN, self.H - 44),
                           fitz.Point(self.W - MARGIN, self.H - 44),
                           color=RULE, width=0.7)
            page.insert_text((MARGIN, self.H - 30), self.title[:110],
                             fontname=self.fname("body"), fontsize=7.5,
                             color=MUTED)
            lbl = "Indicative only  \u00b7  Page %d of %d" % (i, n)
            w = self.width(lbl, "body", 7.5)
            page.insert_text((self.W - MARGIN - w, self.H - 30), lbl,
                             fontname=self.fname("body"), fontsize=7.5,
                             color=MUTED)


# --------------------------------------------------------------- sections

def _cover(d, result):
    p = d.page
    big = 21 if d.size == "a4" else 26
    p.insert_text((MARGIN, 46), "SITE FEASIBILITY CHECK",
                  fontname=d.fname("head"), fontsize=big, color=(1, 1, 1))
    p.insert_text((MARGIN, 72),
                  result["site"].get("display", result["address"])[:100],
                  fontname=d.fname("body"), fontsize=11,
                  color=(0.85, 0.93, 0.88))
    p.insert_text((MARGIN, 89),
                  "Prepared %s by Zones Landscaping Auckland Central"
                  % result.get("generated", ""),
                  fontname=d.fname("body"), fontsize=8.5,
                  color=(0.75, 0.88, 0.80))

    d.text(R.SHORT_NOTICE, size=8.5, colour=MUTED, gap=14)

    parcel = result.get("parcel")
    if parcel:
        d.heading("Your property")
        d.row("Legal description", parcel.get("legal_description") or "-")
        d.row("Record of title", parcel.get("title") or "-")
        if parcel.get("area_m2"):
            d.row("Site area", "%s m\u00b2  (%s)" % (
                f"{parcel['area_m2']:,}", parcel["area_source"]))
        d.space(4)
        d.text(R.PARCEL_CONFIRM, size=9.5, font="bold",
               colour=(0.72, 0.42, 0.04), gap=8)
        d.text("Covenants, consent notices and easements are not held in any "
               "public database and are not covered by this check. We "
               "recommend a title search before the design is finalised.",
               size=9, colour=MUTED, gap=16)


def _zone(d, result):
    zone = result.get("zone") or {}
    std = zone.get("standards")
    d.heading("Zone and standards")

    name = zone.get("name") or "Not determined"
    if std and std.get("code"):
        name = "%s (%s)" % (name, std["code"])
    d.text(name, size=12, font="bold", gap=10)

    if std:
        c = std.get("clauses") or {}
        rows = [("Front yard, minimum", std.get("front_yard_m"), "m", "yards"),
                ("Side yard, minimum", std.get("side_yard_m"), "m", "yards"),
                ("Rear yard, minimum", std.get("rear_yard_m"), "m", "yards"),
                ("Maximum building coverage", std.get("site_coverage_pct"),
                 "%", "coverage"),
                ("Maximum hard surface", std.get("impervious_pct"), "%",
                 "impervious"),
                ("Minimum landscaped area", std.get("landscaped_pct"), "%",
                 "landscaped"),
                ("Riparian yard, if a stream", std.get("riparian_yard_m"),
                 "m", "yards"),
                ("Coastal protection yard", std.get("coastal_yard_m"), "m",
                 "yards")]
        for label, val, unit, key in rows:
            if val is None:
                continue
            clause = c.get(key)
            d.row(label, "%s%s%s" % (
                val, unit, "      AUP %s" % clause if clause else ""))
        if std.get("note"):
            d.space(4)
            d.text(std["note"], size=9, colour=MUTED, gap=10)

        area = (result.get("parcel") or {}).get("area_m2")
        hard = S.impervious_allowance(area, std)
        build = S.coverage_allowance(area, std)
        if hard:
            d.space(2)
            d.text("What that means on your site", size=10, font="bold", gap=4)
            msg = ("On %s m\u00b2 you are allowed roughly %s m\u00b2 of hard "
                   "surface in total. That includes the house roof and the "
                   "existing driveway, not just new paving, so the amount "
                   "available for new work is lower."
                   % (f"{area:,}", f"{hard:,.0f}"))
            if build:
                msg += (" Building footprint is capped at about %s m\u00b2."
                        % f"{build:,.0f}")
            d.text(msg, size=9.5, gap=10)

        if std.get("fences"):
            d.text("Fences", size=10, font="bold", gap=4)
            d.text(std["fences"]["plain"] + (
                "   (AUP %s)" % c["fences"] if c.get("fences") else ""),
                size=9.5, gap=10)

        if std.get("yard_impervious_pct"):
            d.text("Inside a riparian, lakeside or coastal protection yard, "
                   "no more than %d%% of that yard may be hard surface."
                   % std["yard_impervious_pct"], size=9, colour=MUTED, gap=12)
    else:
        reason = S.pending_reason(zone.get("name") or "")
        d.text(reason or "Standards for this zone are not held by this tool "
                         "and need to be read from the relevant Unitary Plan "
                         "chapter.", size=9.5, colour=MUTED, gap=12)

    for w in result.get("warnings", []):
        d.space(2)
        d.text("Please note: " + w, size=9, colour=(0.75, 0.45, 0.05), gap=8)


def _soil(d, result):
    """
    Soil classification block.

    Always renders once a soil dict exists, in all three states. A failed
    lookup prints as a failure rather than vanishing: a section that is simply
    absent reads to a client as "nothing to report about the soil", which is
    the false all-clear this tool exists to avoid.
    """
    soil = result.get("soil")
    if not soil:
        return

    # Keep the block whole. Left to flow it splits after the heading and
    # strands the classification on the previous page from the sentence that
    # explains it, which is the one pairing a reader needs to see together.
    d.need(260)

    d.heading("Soil")
    status = soil.get("status")

    if status == "ok":
        head = SOIL.headline(soil)
        if head:
            label = head
            if soil.get("code"):
                label = "%s (%s)" % (head, soil["code"])
            d.text(label, size=12, font="bold", gap=10)
        for key in ("group_description", "order_description"):
            if soil.get(key):
                d.text(soil[key], size=9.5, gap=10)
        if soil.get("means"):
            d.text("What that means for the build", size=10, font="bold",
                   gap=4)
            d.text(soil["means"], size=9.5, gap=10)
        d.text(soil.get("scale_note", ""), size=9, colour=MUTED, gap=10)
        d.text(SOIL.ATTRIBUTION, size=8.5, colour=MUTED, gap=14)
    elif status == "not_mapped":
        d.text("This location is not covered by the national soil map, so no "
               "soil classification is held for it. That is a gap in the "
               "mapping, not a finding about the site.",
               size=9.5, colour=MUTED, gap=14)
    else:
        d.text("The soil classification could not be retrieved, so nothing is "
               "known about the soil here from this check. This is a failed "
               "lookup, not a clear result.",
               size=9.5, font="bold", colour=(0.72, 0.42, 0.04), gap=14)


def _map_in_column(d, map_path):
    """
    Place the map in the next column on the current page.

    On A3 the cover content only fills one column, so without this the right
    half of the opening sheet is dead space. Putting the map there makes the
    first sheet a proper spread and saves a page.
    """
    d.col = min(d.col + 1, d.ncols - 1)
    d.y = d.top
    d.heading("Site map")
    d.space(2)
    img = fitz.Pixmap(map_path)
    scale = min(d.col_w / img.width, (d.bottom - d.y) / img.height)
    w, h = img.width * scale, img.height * scale
    x = d.col_x + (d.col_w - w) / 2
    d.page.insert_image(fitz.Rect(x, d.y, x + w, d.y + h), filename=map_path)
    d.y += h


def _map_page(d, map_path):
    """The map gets a page to itself, spanning all columns."""
    d.new_page()
    d.set_columns(1)
    d.heading("Site map")
    d.space(2)
    img = fitz.Pixmap(map_path)
    avail_w = d.W - MARGIN * 2
    avail_h = d.bottom - d.y
    scale = min(avail_w / img.width, avail_h / img.height)
    w, h = img.width * scale, img.height * scale
    x = (d.W - w) / 2
    d.page.insert_image(fitz.Rect(x, d.y, x + w, d.y + h), filename=map_path)
    d.y += h
    d.set_columns(d.cols)


def _findings(d, result):
    findings = result["findings"]
    flagged = [f for f in findings
               if f["status"] in ("on_site", "abuts", "nearby")]
    clear = [f for f in findings if f["status"] == "clear"]
    errors = [f for f in findings if f["status"] == "error"]

    d.new_page()
    d.set_columns(1)
    d.heading("What we checked")
    d.text("We checked %d planning, hazard and service records against your "
           "property boundary. %d were flagged for attention and %d are "
           "clear.%s"
           % (len(findings), len(flagged), len(clear),
              "  %d could not be checked and need to be confirmed manually."
              % len(errors) if errors else ""),
           size=9.5, gap=14)
    d.set_columns(d.cols)
    d.top = d.y                      # columns start below the intro

    by_cat = {}
    for f in findings:
        by_cat.setdefault(f["category"], []).append(f)

    order = {"on_site": 0, "abuts": 1, "nearby": 2, "error": 3, "partial": 4,
             "clear": 5}
    for cat in L.CATEGORY_ORDER:
        items = by_cat.get(cat)
        if not items:
            continue
        d.need(72)
        d.space(4)
        d.text(L.CATEGORY_TITLES[cat], size=10.5, font="bold", colour=GREEN,
               gap=6)

        for f in sorted(items, key=lambda x: order.get(x["status"], 9)):
            status = f["status"]
            col = STATUS_COLOUR[status]

            if status == "clear":
                d.need(18)
                right = d.col_x + d.col_w
                d.page.draw_rect(
                    fitz.Rect(d.col_x, d.y + 2, d.col_x + 7, d.y + 9),
                    color=None, fill=col)
                d.page.insert_text((d.col_x + 15, d.y + 9), f["name"],
                                   fontname=d.fname("body"), fontsize=9,
                                   color=INK)
                w = d.width("CLEAR", "bold", 7.5)
                d.page.insert_text((right - w, d.y + 9), "CLEAR",
                                   fontname=d.fname("bold"), fontsize=7.5,
                                   color=col)
                d.y += 15
                continue

            d.need(58)
            right = d.col_x + d.col_w
            d.page.draw_rect(fitz.Rect(d.col_x, d.y, d.col_x + 3.5, d.y + 13),
                             color=None, fill=col)
            d.page.insert_text((d.col_x + 12, d.y + 10), f["name"],
                               fontname=d.fname("bold"), fontsize=10,
                               color=INK)
            word = STATUS_WORD[status]
            w = d.width(word, "bold", 7.5)
            d.page.insert_text((right - w, d.y + 10), word,
                               fontname=d.fname("bold"), fontsize=7.5,
                               color=col)
            d.y += 16

            if status == "on_site":
                body = f.get("plain", "")
                if f.get("clause"):
                    body += "   (AUP %s)" % f["clause"]
            elif status == "abuts":
                body = R.ABUTS_TEXT
            elif status == "nearby":
                body = ("Not on your property, but present within 200 m. "
                        "Worth being aware of, unlikely to control the design.")
            elif status == "partial":
                body = f.get("absent", "")
            else:
                body = ("This was not confirmed from the available records and "
                        "must be checked directly before this report is "
                        "relied on.")
            d.text(body, size=9, colour=(0.3, 0.3, 0.3), indent=12, gap=9)


def _notice(d):
    d.new_page()
    d.heading("Important notice, please read")
    d.text(R.DISCLAIMER_INTRO, size=9.5, gap=12)
    for i, (h, b) in enumerate(R.DISCLAIMER_POINTS, 1):
        d.need(62)
        d.text("%d.  %s" % (i, h), size=9.5, font="bold", gap=3)
        d.text(b, size=9, colour=(0.32, 0.32, 0.32), indent=16, gap=10)
    d.space(6)
    d.text(R.VALIDITY, size=9, font="bold", colour=(0.72, 0.42, 0.04), gap=12)
    d.text(R.DISCLAIMER_LIABILITY, size=9, font="bold", gap=12)
    d.text(L.ATTRIBUTION, size=8, colour=MUTED)


# ------------------------------------------------------------------ public

def build(result, out_path, map_path=None, size="a4"):
    title = "Site feasibility check  \u00b7  %s" % result["address"]
    d = Doc(title, size=size)
    d.new_page(band=True)
    _cover(d, result)
    _zone(d, result)
    _soil(d, result)
    if map_path and os.path.exists(map_path):
        # A3 has a spare column beside the cover content, so the map goes
        # there. A4 is single column, so it gets its own page.
        if size == "a3" and d.col == 0:
            _map_in_column(d, map_path)
        else:
            _map_page(d, map_path)
    _findings(d, result)
    _notice(d)
    return d.save(out_path)


def impose_a3(pdf_path, out_path):
    """
    Two A4 portrait pages side by side on each A3 landscape sheet.

    595.28 x 2 = 1190.55 pt, which is A3 landscape exactly, so pages sit edge
    to edge with no scaling and print at true size.
    """
    src = fitz.open(pdf_path)
    out = fitz.open()
    for i in range(0, len(src), 2):
        sheet = out.new_page(width=A3_LANDSCAPE[0], height=A3_LANDSCAPE[1])
        for slot in (0, 1):
            if i + slot >= len(src):
                break
            x = slot * A4_PORTRAIT[0]
            sheet.show_pdf_page(
                fitz.Rect(x, 0, x + A4_PORTRAIT[0], A4_PORTRAIT[1]),
                src, i + slot)
    out.save(out_path, deflate=True)
    src.close()
    out.close()
    return out_path
