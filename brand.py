"""
Zones Landscaping Auckland Central - presentation design tokens.

SOURCE OF TRUTH for anything that prints into the client ring binder. The S&F
Report deck and the Site Feasibility slides now come out of the same generator
(sf_report.py and deck_export.py, both on top of slides.py), so colour, type,
margins, header treatment and footer agree by construction rather than by two
files being kept in step by hand.

There used to be a JS mirror at Desktop\\zones-sf-deck\\brand.js feeding a
pptxgenjs build of the deck. It was retired when that build was ported to
Python; nothing reads it now.

Geometry is in millimetres because python-pptx and PyMuPDF both work in mm.
"""

from pptx.dml.color import RGBColor


def _rgb(hexstr):
    return RGBColor(int(hexstr[0:2], 16), int(hexstr[2:4], 16),
                    int(hexstr[4:6], 16))


# -- palette ----------------------------------------------------------------
# GREEN is the only saturated colour carrying meaning. The neutrals are biased
# slightly green so they sit with the brand rather than against it.
GREEN_HEX = "01632F"
INK_HEX = "232823"      # headings and lead text
BODY_HEX = "40483F"     # running body copy
MUTED_HEX = "7B857C"    # captions, sub-labels, footers
LINE_HEX = "E4E8E3"     # hairline rules and row separators
# The same hairline one step darker, for rules drawn *inside* a TINT card.
# E4E8E3 on F2F6F2 is a two-value difference and disappears in print.
CARD_LINE_HEX = "DDE3DD"
TINT_HEX = "F2F6F2"     # panel fill behind supporting content
TINT_GREEN_HEX = "E8F0EA"
PHBG_HEX = "F7FAF7"     # card and placeholder fill
ROW_BAND_HEX = "FAFBFA"  # alternate row band on the timeline chart
PH_EDGE_HEX = "9DB5A3"  # dashed border on an image placeholder
PH_INK_HEX = "31533D"   # placeholder label text
COVER_SUB_HEX = "D9E8DE"
COVER_BRAND_HEX = "BCD9C6"
CAPBAR_HEX = "0B3D22"   # caption bar over full-bleed imagery
# The 5-stage strip greys a stage out once it is behind the client.
STAGE_OFF_RULE_HEX = "CFDCD2"
STAGE_OFF_INK_HEX = "9AA79D"

GREEN = _rgb(GREEN_HEX)
INK = _rgb(INK_HEX)
BODY = _rgb(BODY_HEX)
MUTED = _rgb(MUTED_HEX)
LINE = _rgb(LINE_HEX)
CARD_LINE = _rgb(CARD_LINE_HEX)
TINT = _rgb(TINT_HEX)
TINT_GREEN = _rgb(TINT_GREEN_HEX)
PHBG = _rgb(PHBG_HEX)
ROW_BAND = _rgb(ROW_BAND_HEX)
PH_EDGE = _rgb(PH_EDGE_HEX)
PH_INK = _rgb(PH_INK_HEX)
COVER_SUB = _rgb(COVER_SUB_HEX)
COVER_BRAND = _rgb(COVER_BRAND_HEX)
CAPBAR = _rgb(CAPBAR_HEX)
STAGE_OFF_RULE = _rgb(STAGE_OFF_RULE_HEX)
STAGE_OFF_INK = _rgb(STAGE_OFF_INK_HEX)
WHITE = _rgb("FFFFFF")

# Internal-only markers. Amber never survives into a printed client document:
# it marks what Lee fills in or deletes first.
NOTE_BG = _rgb("F4EFE6")
NOTE_INK = _rgb("8A6D3B")

# Finding status. Semantic, deliberately separate from the brand accent.
# Values taken from SF_34, which is the deck these print into.
STATUS_ON_SITE = _rgb("D14D14")
STATUS_NEARBY = _rgb("E0A32E")
STATUS_CLEAR = _rgb("26994D")

# -- type -------------------------------------------------------------------
# Montserrat for anything structural, Open Sans for anything read as a sentence.
HEAD_FONT = "Montserrat"
BODY_FONT = "Open Sans"

# -- geometry, millimetres --------------------------------------------------
# A4 landscape matches the S&F Report deck exactly. The left margin carries the
# 25mm the ring binder punch eats; nothing may sit inside it.
PAGE = {"a4": (297.0, 210.0), "a3": (420.0, 297.0)}
MARGINS = {                       # left, right, top, bottom
    # Right margin matched to the deck Lee actually sends (66 Rhinevale
    # Close SF_34, 11 Aug 2026): every content slide there runs 246.9mm wide
    # at L=25.1, i.e. 25mm both sides. The generator had 15mm right, making
    # every page 10mm wider than the house standard.
    "a4": (25.0, 25.0, 14.0, 16.0),
    "a3": (30.0, 20.0, 18.0, 20.0),
}

FOOTER_LINE = "ZONES LANDSCAPING · AUCKLAND CENTRAL"


def margins(size):
    return MARGINS[size]


def content_width(size):
    w, _ = PAGE[size]
    ml, mr, _, _ = MARGINS[size]
    return w - ml - mr
