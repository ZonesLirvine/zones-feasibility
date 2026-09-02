"""
The S&F Report: the whole client binder, generated from one address.

Scoping and Feasibility, cover to back page. Design leads: the 2D plan, 3D
render and selections come first, then the YOUR SITE section with its three
feasibility pages generated in place rather than produced separately and
pulled in by hand, then scope, timeline, budget and next steps.

The page set matches SF_34, the 66 Rhinevale Close deck Lee actually sent.
Anything this generator produces that Lee then has to delete, reorder or
rebuild by hand is a bug in here, not a step in the workflow.

A4 landscape throughout, one slide per ring-binder page, punched on the left.

    import sf_report
    sf_report.build(result, "sf-report.pptx", client="Sarah Thompson",
                    map_path="site-map.png")

`result` is an engine.run() result, or None. With None the site pages fall back
to a placeholder, so the deck still builds when the address is outside Auckland
or Council's API is down. That is deliberate: the binder is never gated on the
site lookup.

Pass `address` either way. A failed lookup means we could not check the
property, not that we do not know where it is, so the address still prints on
the cover, the letter, the divider and the closing page. What a failed lookup
does change is that the divider stops claiming the check happened.

Pages carrying real data: the cover, the personal note, the YOUR SITE divider,
the four feasibility pages, and the closing page. Everything else is the same
bracketed guidance the hand-filled template carried, waiting for Lee.

Later this is where zones-qs drops the budget range and zones-design drops the
2D plan; both already come in as optional parameters that default to the
placeholder.
"""

import datetime
import os

from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Mm

import brand as BR
import deck_export
import slides as SL

HF = BR.HEAD_FONT
BF = BR.BODY_FONT

PHONE = "022 850 0920"
EMAIL = "lee.irvine@zones.co.nz"
CONTACT = "%s  ·  %s" % (PHONE, EMAIL)


def _fields(result, client=None, date=None, address=None):
    """
    The four merge fields.

    The address is known from the moment Lee types it and does not depend on
    the site check: a failed Council lookup means we could not check the
    property, not that we do not know where it is. So the lookup's tidied
    version is preferred when there is one, and the typed address is used
    otherwise. Only the client name can genuinely be unknown here, and it
    stays as its {{token}} so it is visibly still to do rather than blank.
    """
    name = client or "{{Name}}"
    first = client.split()[0] if client else "{{First Name}}"
    site = (result.get("site") or {}).get("display") if result else None
    resolved = site or (result or {}).get("address") or address
    if date is None:
        date = datetime.date.today().strftime("%d %B %Y").lstrip("0")
    return {"name": name, "first": first, "date": date,
            "address": _title_case(resolved) if resolved
                       else "{{Site Address}}"}


def _title_case(text):
    """
    Council returns addresses shouted: 15E BALMAIN ROAD BIRKENHEAD 0626.
    That is fine in a findings table and wrong on a cover.
    """
    if not text.isupper():
        return text
    out = []
    for word in text.split():
        if word.isdigit() or (word[:-1].isdigit() and len(word) <= 4):
            out.append(word)          # 15E, 0626
        else:
            out.append(word.capitalize())
    return " ".join(out)


# ===================================================================== pages

def _how_to_use(prs, has_site):
    s = SL.blank(prs, SL.PAGE_PLAIN)
    ml, mt, cw = SL.content_box(prs)
    SL.tb(s, ml, mt, cw, 10, "HOW TO USE THIS TEMPLATE", size=16,
          font=HF, colour=BR.NOTE_INK, bold=True, spacing=1.0)
    SL.tb(s, ml, mt + 10.5, cw, 7,
          "Internal slide. Delete before presenting or printing.",
          size=10.5, colour=BR.NOTE_INK, bold=True, italic=True)

    points = [
        "This deck is sized exactly A4 landscape. Print at 100% (no scaling) "
        "for the ring binder, and keep the left edge clear, it is punched.",
        "One slide per binder page. Slides marked with an amber OPTIONAL "
        "banner (3D Render, Selections) get deleted when that deliverable is "
        "not part of the project. The 2D site plan slide always stays. "
        "Duplicate the 3D Render slide once per render.",
        "Selections doubles as the mood board: keep it as the plant and "
        "material legend when there's a 3D render, or as the mood board "
        "carrying that character when there isn't. Use one or the other, "
        "not both.",
        # The old version of this slide told Lee to generate the site pages
        # separately and pull them in with Reuse Slides. They now come out of
        # the same command as the rest of the deck.
        ("The three YOUR SITE pages are generated from Council and LINZ "
         "records for this address. They are already in this deck, nothing "
         "to import."
         if has_site else
         "DO NOT SEND THIS FILE. The site check could not be completed for "
         "this job, so the YOUR SITE section is a placeholder, not a result. "
         "The file is named -DRAFT-SITE-INCOMPLETE so it will not get "
         "mistaken for a finished report in the job folder. The rest of the "
         "binder is safe to keep working on. Re-run the tool once the "
         "address resolves or Council's data is back, then rebuild this "
         "report before it goes to the client."),
        "Slide numbers in the footer renumber themselves automatically when "
        "slides are deleted or added.",
        "The Contents slide lists sections without page numbers, so deleting "
        "optional slides breaks nothing, just remove the matching line.",
        "Replace all [square bracket] guidance and {{merge}} placeholders per "
        "job. Delete the amber banners on any optional slides you keep.",
        "Image boxes: drop the image in, send it to back if needed, then "
        "delete the dashed box.",
    ]
    SL.rich(s, ml, 39.5, cw, 142,
            [{"text": t, "bullet": True} for t in points],
            size=10.5, spacing=1.5, space_after=9)
    return s


def _cover(prs, f):
    """
    White, not full-bleed green. The ring binder itself is green; a green
    cover page on top of a green folder is doubling up on the same signal.

    The title block is inset to 57mm rather than sitting on the 25mm binder
    margin. That is a title-page treatment, and it is what SF_34 does.
    """
    s = SL.blank(prs, SL.COVER)
    SL.rect(s, 0, 0, prs._w, 3.2, BR.GREEN)
    SL.tb(s, 57.0, 53.3, 214.9, 8,
          "ZONES LANDSCAPING   ·   AUCKLAND CENTRAL   ·   LEE IRVINE",
          size=10, font=HF, colour=BR.GREEN, bold=True, tracking=2.5)
    SL.tb(s, 57.0, 64.8, 214.9, 22, "Scoping & Feasibility", size=40, font=HF,
          colour=BR.INK, bold=True, spacing=1.0)
    SL.tb(s, 57.0, 85.9, 214.9, 14, "Report", size=23, font=HF,
          colour=BR.MUTED, spacing=1.0)
    SL.rich(s, 57.0, 114.3, 146.0, 32, [
        {"runs": [("Prepared for  ", {"size": 12, "colour": BR.MUTED}),
                  (f["name"], {"size": 13, "bold": True, "colour": BR.INK})]},
        {"text": f["address"], "size": 12, "colour": BR.MUTED},
        {"text": f["date"], "size": 12, "colour": BR.MUTED},
    ], spacing=1.5)
    SL.tb(s, 57.0, 148.6, 146.0, 8,
          "By Lee Irvine  ·  Zones Landscaping Auckland Central",
          size=10, colour=BR.GREEN)
    SL.logo(s, 227.3, 180.6, 44.7, 12.3, wordmark=True)
    return s


def _personal_note(prs, f):
    """
    The letter, running the full width of the page.

    The why-choose-Zones panel that used to sit down the right of this page has
    moved to the closing Stage 3 page, where the client is actually deciding.
    So has the optional-attachments note, which is gone: it described what
    might be stapled to the back of a document the client is holding.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    SL.tb(s, 32.9, 25.9, 170.6, 4.5, "A PERSONAL NOTE FROM LEE", size=10.5,
          font=HF, colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 32.9, 31.5, 170.6, 7.8, "Hi %s," % f["first"], size=17, font=HF,
          colour=BR.INK, bold=True, spacing=1.15)

    SL.rich(s, 32.9, 46.0, 206.4, 76.3, [
        "Thank you for considering Zones to handle your project at %s. We have "
        "now completed the Scoping & Feasibility stage on your project at %s, "
        "and this report brings it all together: your brief, what we found on "
        "your site, your concept design, the scope of work, an indicative "
        "timeline and a realistic budget range. [Add anything specific to this "
        "job here: what the proposal has been built around, and anything you "
        "want to flag before they read the numbers.]"
        % (f["address"], f["address"]),
        "",
        "This is the point where your project stops being an idea and becomes "
        "a real, buildable plan. Everything in here has been prepared "
        "specifically for your site and your brief.",
        "",
        "Read it through, and if you have any questions at all, call me on %s. "
        "I'm happy to talk through the design or the numbers before you decide "
        "on next steps." % PHONE,
    ], spacing=1.5)
    SL.rich(s, 33.7, 128.7, 139.1, 23.6, [
        {"text": "Lee Irvine", "size": 12, "font": HF, "colour": BR.INK,
         "bold": True},
        {"text": "Managing Director Aven Limited TA | Zones Landscaping "
                 "Auckland Central", "size": 9},
        {"text": CONTACT, "size": 9},
    ], spacing=1.45)
    SL.logo(s, 32.9, 156.7, 46.1, 18.3)
    return s


def _contents(prs):
    """
    Nine sections, no page numbers.

    The bracketed "[delete line if not included]" prompts are gone. They were
    there because the 3D render and Selections slides are optional, but the
    prompt itself printed on the client's page if Lee kept the line, which is
    the failure it was meant to prevent. Deleting a line off this list needs no
    instruction.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    SL.tb(s, 34.5, 27.4, 180.5, 4.5, "CONTENTS", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 34.5, 33.0, 180.5, 7.8, "What's in this report", size=17,
          font=HF, colour=BR.INK, bold=True, spacing=1.15)
    items = [
        "Your concept design, 2D site plan, vision and key features",
        "Selections, plants, palette and materials",
        "3D visualisation",
        "Your site, the planning checks we ran",
        "Scope of work, what's included",
        "Your timeline",
        "Your budget range",
        "Allowances and exclusions",
        "How we work, and what happens next",
    ]
    # Taken off SF_34 rather than stepped. The nominal step is 12.325mm, which
    # rounds inconsistently at 0.1mm and puts two of the nine rows a tenth out.
    tops = (56.0, 68.4, 80.7, 93.0, 105.3, 117.6, 130.0, 142.3, 154.6)
    for i, (text, y) in enumerate(zip(items, tops)):
        SL.tb(s, 34.5, y, 180.5, 5.1, text, size=11.5, colour=BR.BODY,
              spacing=1.1)
        if i < len(items) - 1:
            SL.hline(s, 34.5, y + 9.9, 111.9, BR.LINE, 0.5)
    return s




def _site_template_note(prs):
    """
    The site section as it appears in the hand-fill master.

    Not the do-not-send placeholder: nothing has gone wrong here, these three
    pages simply are not hand-filled. They come out of the address.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    ml, _, cw = SL.content_box(prs)
    top = SL.head(s, prs, "Your site", "The planning checks we ran")
    SL.placeholder(s, prs, ml, top + 8, cw, 90,
                   "Three pages, generated from the address",
                   "Delete this slide once they are in.")
    SL.tb(s, ml, top + 104, cw, 24,
          "This section is not filled in by hand. Run the feasibility tool "
          "with the site address and it writes three pages here: the property "
          "and its zone standards, what the check flagged and what each item "
          "means, and the site map. Forty Council and LINZ records, checked "
          "against the real boundary.",
          size=10, colour=BR.MUTED, spacing=1.4)
    SL.tb(s, ml, top + 132, cw, 8,
          'python run.py "<address>" --report "<job>.pptx" '
          '--client "<Client Name>"',
          size=9.5, font=BF, colour=BR.NOTE_INK, spacing=1.3)
    return s


def _site_placeholder(prs, reason):
    """
    Stand-in for the four feasibility pages when the lookup did not run.

    The binder is never gated on the site check, so this page says plainly
    what is missing and why. It never implies the site came back clear.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    ml, _, cw = SL.content_box(prs)
    SL.banner(s, prs, "DO NOT SEND TO CLIENT. Site check incomplete, this "
                      "section is a placeholder, not a result. Re-run and "
                      "rebuild before sending.")
    top = SL.head(s, prs, "Your site", "Site feasibility check")
    SL.placeholder(s, prs, ml, top + 8, cw, 90,
                   "Site feasibility pages not generated",
                   reason)
    SL.tb(s, ml, top + 104, cw, 20,
          "No site check has been carried out for this address. This is not "
          "the same as a site that came back clear: nothing has been checked "
          "against the Auckland Unitary Plan or Council's hazard records yet. "
          "This report is not ready to send until this section is replaced "
          "with real findings.",
          size=10, colour=BR.NOTE_INK, bold=True, spacing=1.4)
    SL.footer(s, prs)
    return s


def _site_plan(prs, plan_image=None):
    """
    The concept plan, full page.

    No vision blurb, no key-features list, no header band. The drawing is the
    argument, and it comes off the drawing set already titled and annotated;
    anything set beside it competes with it and gets deleted. SF_34 runs it
    edge to edge with the Zones mark top left and a detail called out in an
    oval, which is what this places.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    if plan_image and os.path.exists(plan_image):
        _fit_picture(s, plan_image, 0, 1.3, prs._w, 190.0)
    else:
        SL.placeholder(s, prs, 0, 1.3, prs._w, 190.0,
                       "Add the 2D concept plan, full page",
                       "Edge to edge. Delete this box once the plan is in.",
                       fill=BR.WHITE)
    SL.logo(s, 20.6, 9.9, 65.4, 25.9)
    SL.oval_picture_box(s, prs, 7.9, 100.5, 54.5, 68.4,
                        "[ Section detail, optional ]")
    return s


def _design_sheet(prs, path, caption=None):
    """
    One of Lee's own drawing sheets, full page.

    The sheets come out of the drawing set already designed, at A3 landscape
    with their own title block and Zones logo. A3 and A4 are the same shape,
    so a sheet drops onto an A4 binder page at 1:1 with nothing cropped and no
    reflowing.

    Run edge to edge, the way SF_34 runs its plan, rather than inset inside
    the margins: a drawing shrunk to fit a text margin loses the scale that
    makes it readable. The drawing's own whitespace keeps the punch clear.
    No logo added, unlike the placeholder page: these sheets carry one in
    their title block already.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    _fit_picture(s, path, 0, 1.3, prs._w, 190.0)
    if caption:
        ml, mr, _, mb = prs._m
        SL.tb(s, ml, prs._h - mb - 1, prs._w - ml - mr, 6, caption, size=8.5,
              italic=True, colour=BR.MUTED)
    return s


def _fit_picture(slide, path, x, y, w, h):
    """Fit inside the box, centred, without distorting the aspect ratio."""
    from PIL import Image
    from pptx.util import Mm
    iw, ih = Image.open(path).size
    k = min(w / iw, h / ih)
    slide.shapes.add_picture(path, Mm(x + (w - iw * k) / 2),
                             Mm(y + (h - ih * k) / 2), Mm(iw * k), Mm(ih * k))


def _render_3d(prs):
    """
    The 3D visualisation, full bleed, nothing on top of it.

    The old version put a green caption bar and a "3D RENDER 01 OF 04" tag
    over the bottom of the image. SF_34 has neither: the render fills the
    page and the footer carries the page number like every other page.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    SL.banner(s, prs, "OPTIONAL SLIDE, delete if 3D renders are not a "
                      "deliverable. Duplicate this slide per render. Delete "
                      "this banner if keeping the slide.")
    SL.placeholder(s, prs, 0, 0, prs._w, prs._h,
                   "Add the 3D render, full bleed, edge to edge",
                   "One render per slide. Delete this box once it is in.",
                   fill=BR.WHITE)
    return s


def _selections(prs):
    """
    Plants, palette and materials: the schedule on the left, the photographs
    on the right.

    The numbers down the left column key to markers on the 2D plan, so the
    client can read a name off the drawing and find the picture of it. The
    photographs are circular because a grid of rectangles reads as a
    catalogue; circles read as a palette, which is what this is.

    Doubles as the mood board when a job has no 3D render: nothing else in the
    deck then shows material and planting character.
    """
    s = SL.blank(prs)
    SL.banner(s, prs, "OPTIONAL SLIDE. Legend if keeping the 3D render, mood "
                      "board if not, use one or the other. Delete this banner "
                      "if keeping the slide.")
    SL.tb(s, 25.1, 15.7, 246.9, 7.0, "SELECTIONS", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=2)
    SL.tb(s, 25.1, 22.9, 246.9, 11.0, "Plants, palette and materials",
          size=17, font=HF, colour=BR.INK, bold=True, spacing=1.0)

    rows = [("1", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("2", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("3", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("4", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("5", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("6", "Plant", "[Plant name]", "[Common name, and where it goes]"),
            ("7", "Material", "[Material]", "[Specification, and where it "
                                            "goes]"),
            ("8", "Material", "[Material]", "[Specification, and where it "
                                            "goes]"),
            ("9", "Material", "[Material]", "[Specification, and where it "
                                            "goes]"),
            ("10", "Material", "[Material]", "[Specification, and where it "
                                             "goes]"),
            ("11", "Material", "[Material]", "[Specification, and where it "
                                             "goes]"),
            ("12", "Material", "[Material]", "[Specification, and where it "
                                             "goes]")]
    _selection_table(s, 23.1, 32.7, rows)

    # The photo panel. One dashed ellipse per row of the table, captioned, so
    # it is obvious which picture belongs to which line.
    SL.rect(s, 179.7, 28.3, 93.4, 162.3, BR.PHBG, BR.PH_EDGE, width=1)
    for i in range(12):
        col, row = i % 3, i // 3
        x = 183.7 + col * 29.6
        y = 32.5 + row * 37.37
        SL.circle_photo(s, x, y, 26.2)
        SL.tb(s, x - 1.1, y + 28.2, 28.3, 7.2, "[Name]", size=8,
              colour=BR.PH_INK, bold=True, italic=True,
              align=PP_ALIGN.CENTER, spacing=1.15)
    return s


def _selection_table(slide, x, y, rows):
    """
    The selections schedule. No rules and no banding at all: the numbers and
    the type column already group it, and lines would fight the photographs
    beside it.
    """
    tbl = slide.shapes.add_table(len(rows) + 1, 4, Mm(x), Mm(y), Mm(142.7),
                                 Mm(6.7 + len(rows) * 11.1)).table
    for i, w in enumerate((8.8, 21.2, 55.7, 57.0)):
        tbl.columns[i].width = Mm(w)
    tbl.rows[0].height = Mm(6.7)
    for r in range(1, len(rows) + 1):
        tbl.rows[r].height = Mm(11.1)
    for c, head in enumerate(("NO.", "TYPE", "NAME", "COMMENTS")):
        SL.cell(tbl, 0, c, head, size=7.5, bold=True, colour=BR.GREEN,
                font=HF)
    for r, (num, kind, name, note) in enumerate(rows, 1):
        SL.cell(tbl, r, 0, num, size=8.5, colour=BR.MUTED)
        SL.cell(tbl, r, 1, kind.upper(), size=7.5, bold=True, colour=BR.MUTED,
                font=HF)
        SL.cell(tbl, r, 2, name, size=9, bold=True, colour=BR.INK, font=HF)
        SL.cell(tbl, r, 3, note, size=8.5, colour=BR.MUTED)
    SL.plain_table(tbl)
    return tbl


def _consent_draft(result):
    """
    A first draft of the consent position, from what the site check flagged.

    Deliberately never concludes. An all-clear site check does not mean no
    consent is required, and this document must never be the thing that says
    it does: nothing here knows about the design, the earthworks volumes or
    the building line. What it can do is put the relevant findings in front of
    Lee so he is writing from the evidence rather than from memory.
    """
    if not result:
        return None
    flagged = [f for f in result["findings"] if f["status"] == "on_site"]
    if not flagged:
        return ("The site check found nothing on the property itself. That "
                "does not settle the consent question: earthworks volumes, "
                "structure heights, boundary proximity and the zone standards "
                "on the previous pages can all trigger consent on a site that "
                "is otherwise clear. State the position for this design.")
    names = ", ".join(f["name"] for f in flagged[:4])
    if len(flagged) > 4:
        names += " and %d more" % (len(flagged) - 4)
    return ("The site check flagged %d item%s on the property: %s. Work "
            "through each against the design as it now stands." %
            (len(flagged), "" if len(flagged) == 1 else "s", names))


def _scope(prs, result):
    """
    Scope of work, as SF_34 sets it: two columns of category headings with
    dash bullets under each, not a table.

    A table made the reader compare rows. The scope is a list of statements
    about what will be built, grouped the way the build is actually sequenced,
    so it reads as prose in columns.

    Every item is job specific, so this ships the categories and the bracketed
    prompts. The consent draft from the site check goes at the foot of the
    right column, still never concluding.
    """
    s = SL.blank(prs)
    SL.tb(s, 25.1, 14.0, 246.9, 6.0, "SCOPE OF WORK", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 25.1, 19.6, 199.0, 7.8, "What's included", size=17, font=HF,
          colour=BR.INK, bold=True, spacing=1.15)
    SL.tb(s, 25.1, 31.3, 246.9, 9.0,
          "[One line on what this scope covers for this job. Add or delete "
          "trade sections below to suit it.] Everything below is drawn on "
          "your concept plan. Quantities and specifications are confirmed as "
          "a fixed price in Stage 3.",
          size=9.5, spacing=1.15)

    def column(x, w, groups):
        paras = []
        for k, (heading, items) in enumerate(groups):
            if k:
                paras.append({"text": "", "size": 4})
            paras.append({"text": heading.upper(), "size": 10, "font": HF,
                          "colour": BR.GREEN, "bold": True, "space_after": 4})
            paras += [{"text": t, "bullet": 3.8, "size": 8.5,
                       "space_after": 3} for t in items]
        SL.rich(s, x, 46.7, w, 110.3, paras, spacing=1.15)

    column(25.1, 125.2, [
        ("Preliminary and general", [
            "Initial planning, consultation and consents, with engineering, "
            "Council, construction and third parties.",
            "Detailed design and building consent documentation.",
            "[Consents included in scope, and the final CCC documentation]"]),
        ("Access and demolition", [
            "[Service relocations, e.g. fibre along the existing wall]",
            "[What comes out, and what is protected]",
            "[Excavation and foundation preparation]"]),
        ("Retaining walls", [
            "[Wall, height, material and construction detail]",
            "[Second wall run, and where it steps]",
            "[What existing structure is retained]"])])
    column(155.2, 116.8, [
        ("Drainage", [
            "[Drain coil behind all new retaining, and where it connects]",
            "[Surface drainage, e.g. pebble strip at the base of the wall]"]),
        ("Fencing", [
            "[Fence type and height above the retaining]",
            "[Fall barrier where one is required]"]),
        ("Paving and surfaces", [
            "[New paving, and what it replaces]",
            "[Existing paving retained, and at what level]"]),
        ("Planting and lawn", [
            "[Hedging, and where it runs]",
            "[Garden planting]",
            "[Lawn reinstatement]",
            "[Edging to lawn and garden]"])])

    # The consent position from the site check. It puts the evidence in front
    # of Lee and stops short of the conclusion, which no generator can make.
    draft = _consent_draft(result)
    if draft:
        SL.rect(s, 155.2, 160.2, 116.8, 24, BR.NOTE_BG)
        SL.tb(s, 159.2, 162.5, 108.8, 6, "FROM THE SITE CHECK, YOUR CALL",
              size=7.5, font=HF, colour=BR.NOTE_INK, bold=True, tracking=1.3)
        SL.tb(s, 159.2, 168.5, 108.8, 14.5, draft, size=8,
              colour=BR.NOTE_INK, spacing=1.3)
    return s


def _timeline(prs):
    """
    The programme as a Gantt, not a two-column table of milestones.

    A table of "2 to 3 weeks" rows does not show the thing that actually
    matters to the client, which is that Council processing runs in parallel
    with nothing and sets the start date. Bars show that at a glance, and the
    consents panel above says what is being waited on.

    Amber bars are time that belongs to Council or Watercare, green is time
    that belongs to Zones. The distinction is the whole point of the page.
    """
    s = SL.blank(prs)
    SL.tb(s, 25.1, 14.0, 246.9, 6.0, "YOUR TIMELINE", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 25.1, 19.6, 246.9, 9.0, "An indicative programme", size=17,
          font=HF, colour=BR.INK, bold=True, spacing=1.15)

    SL.rect(s, 24.9, 31.0, 246.9, 35.2, BR.TINT)
    SL.rect(s, 24.9, 31.0, 1.3, 35.2, BR.GREEN)
    SL.tb(s, 31.6, 35.1, 233.7, 5.1,
          "CONSENTS, WHAT YOUR PROJECT NEEDS BEFORE IT CAN START", size=8,
          font=HF, colour=BR.GREEN, bold=True, spacing=1.15, tracking=0.9)
    for i, consent in enumerate(["[Building consent]",
                                 "[Other approval, e.g. Watercare works over]"]):
        SL.rich(s, 31.6, 43.2 + i * 6.1, 233.7, 3.8, [
            {"runs": [(consent, {"bold": True, "colour": BR.INK}),
                      (".", {})]}], size=8.5, spacing=1.15)
    SL.tb(s, 31.6, 57.4, 233.7, 3.5,
          "Council allow 20 working days, and the clock stops each time they "
          "come back for more information.", size=7.5, italic=True,
          colour=BR.MUTED, spacing=1.15)

    # ---- the chart
    #
    # Five months across a fixed grid. SF_34's was dragged by hand and its
    # month marks are not evenly spaced; this one is, so a bar's position
    # means something you can read off the gridlines.
    x0, months = 98.6, 5
    mw = (260.3 - x0) / (months - 1)          # month to month
    week = mw / 4.35
    for i in range(months):
        SL.tb(s, x0 + i * mw - 8.9, 73.7, 17.8, 3.2, "M%d" % (i + 1), size=7,
              font=HF, colour=BR.MUTED, bold=True, align=PP_ALIGN.CENTER,
              spacing=1.15)
    for i in range(months * 2 - 1):
        SL.vline(s, x0 + i * mw / 2, 79.4, 89.9, BR.LINE, 0.75)

    # Weeks from the start of M1. The grid runs M1 to M5, so nothing may start
    # later than week 17 or it falls off the chart.
    rows = [
        ("Preliminary planning", 0, 1, True),
        ("[Survey and CCTV]", 0.5, 1, True),
        ("Detailed design and consent docs", 1, 2, True),
        ("Building consent, Council processing", 3, 3.5, False),
        ("Council RFI responses", 4, 2.5, False),
        ("[Works over approval]", 3.5, 1.5, False),
        ("Stage 3, fixed price contract", 6.5, 1.5, True),
        ("Construction", 8, 6, True),
        ("Completion and handover", 14, 1, True),
        ("Code Compliance Certificate", 15, 2, False),
    ]
    for i, (label, start, length, ours) in enumerate(rows):
        y = 81.9 + i * 8.65
        if i % 2 == 0:
            SL.rect(s, 24.9, y, 246.9, 7.9, BR.ROW_BAND)
        SL.tb(s, 24.9, y + 1.3, 68.6, 5.1, label, size=8, spacing=1.15)
        bx = x0 + start * week - 5.6
        SL.rounded(s, bx, y + 1.7,
                   max(5.0, min(length * week, 260.3 - bx)), 4.9,
                   BR.GREEN if ours else BR.STATUS_NEARBY)

    ly = 81.9 + len(rows) * 8.65 + 2
    SL.rounded(s, 24.9, ly, 11.4, 4.0, BR.GREEN)
    SL.tb(s, 39.6, ly, 60, 5, "Design and build", size=8, colour=BR.MUTED,
          spacing=1.15)
    SL.rounded(s, 100.6, ly, 11.4, 4.0, BR.STATUS_NEARBY)
    SL.tb(s, 115.3, ly, 90, 5, "Council and Watercare processing", size=8,
          colour=BR.MUTED, spacing=1.15)
    SL.tb(s, 191.9, ly, 80, 5, "[About X months to CCC]", size=8,
          italic=True, colour=BR.MUTED, align=PP_ALIGN.RIGHT, spacing=1.15)
    SL.tb(s, 24.9, ly + 6.5, 160, 5,
          "[Bars show a typical consented programme. Drag them to this job.]",
          size=8, italic=True, colour=BR.NOTE_INK, spacing=1.15)
    return s


def _budget(prs, budget=None):
    """
    budget is (low, high) in whole dollars, or None for the placeholder.
    This is the hook zones-qs plugs into once the QS can price a concept.
    """
    s = SL.blank(prs)
    SL.tb(s, 25.1, 14.0, 246.9, 6.0, "YOUR BUDGET RANGE", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 25.1, 19.6, 246.9, 9.0, "What your project will cost", size=17,
          font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.tb(s, 25.1, 33.8, 246.9, 19.1,
          "We believe every landscaping project should start with a concept "
          "design and an agreed budget indication, so we're all on the same "
          "page before any build commitment is made. The range below covers "
          "the overall build cost for the design shown in this report: all "
          "trades, subcontractors and materials, less any exclusion.",
          size=10, spacing=1.5)

    # The number goes in solid green, on its own, big. It is the one thing on
    # this page the client will look for first.
    SL.rect(s, 25.1, 59.2, 112.2, 76.8, BR.GREEN)
    SL.tb(s, 33.6, 76.2, 95.1, 4.1, "YOUR INDICATIVE BUDGET RANGE",
          size=9, font=HF, colour=BR.COVER_BRAND, bold=True, spacing=1.15,
          tracking=2)
    figure = ("${:,.0f} to ${:,.0f}".format(*budget) if budget
              else "${{XX,000}} to ${{YY,000}}")
    # Real figures fit the panel at 24pt. The merge tokens are half again as
    # long and wrapped onto a second line that ran into the line below.
    SL.rich(s, 33.6, 86.6, 101.9, 10.3, [
        {"runs": [(figure, {"size": 24 if budget else 17}),
                  (" +GST", {"size": 12})]},
    ], font=HF, colour=BR.WHITE, bold=True, spacing=1.15)
    SL.tb(s, 35.0, 99.3, 95.1, 4.4, "Confirmed as a fixed price in Stage 3",
          size=9.5, colour=BR.COVER_SUB, spacing=1.15)

    SL.tb(s, 150.7, 58.0, 121.2, 8.0, "Components that could move the budget",
          size=11.5, font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.tb(s, 150.7, 65.4, 130.2, 17.4,
          "If the range is above or below where you'd like to be these are "
          "the levers we can adjust together or implement in stages. Also "
          "listed items which are yet to be defined which could impact the "
          "budget:", size=10, spacing=1.4)
    SL.rich(s, 150.7, 85.1, 121.2, 31.4, [
        {"text": "[Component that could be altered or staged]",
         "bullet": True},
        {"text": "[Component 2]", "bullet": True},
        {"text": "[Component 3]", "bullet": True},
        {"text": "[Item not yet defined that could move the number]",
         "bullet": True},
    ], size=10, italic=True, colour=BR.MUTED, spacing=1.5, space_after=6)

    SL.tb(s, 25.1, 140.6, 116.4, 12.3,
          "Please note this is a construction budget range for indication "
          "only. Zones Landscaping cannot guarantee budget figures until a "
          "formal fixed-price quote has been completed in the next stage.",
          size=8.5, italic=True, colour=BR.MUTED, spacing=1.15)

    SL.rect(s, 25.1, 159.7, 246.9, 21.6, BR.TINT)
    SL.rect(s, 25.1, 159.7, 1.1, 21.6, BR.GREEN)
    SL.rich(s, 31.2, 159.7, 234.7, 21.6, [
        {"runs": [("What this means for you  ·  ",
                   {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("An agreed budget range now is what protects you from "
                   "budget surprises later. In the next stage it becomes a "
                   "contractual fixed price, before any build commitment is "
                   "made.", {})]},
    ], size=10, spacing=1.4)
    SL.footer(s, prs)
    return s


def _allowances_exclusions(prs):
    """
    The page that qualifies the budget range: what is carried as an allowance
    and what is not in the number at all.

    Added 11 Aug 2026 from the 66 Rhinevale Close deck Lee actually sent
    (SF_34). The binder previously went straight from the budget range to How
    we work, which left every assumption behind the number unstated and every
    exclusion unsaid. On a consented job that is the page that protects you.

    Site-specific allowances are bracketed like the rest of the template.
    The exclusions list is generic and holds for any job.
    """
    s = SL.blank(prs)
    SL.tb(s, 25.1, 14.0, 246.9, 6.0, "YOUR BUDGET RANGE", size=10.5,
          font=HF, colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 25.1, 19.6, 246.9, 9.0, "Allowances and exclusions", size=17,
          font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.tb(s, 24.9, 30.5, 246.9, 7.1,
          "These are the things that could still move the number on the "
          "previous page, and the things that are not in it.", size=9.5,
          spacing=1.15)


    SL.tb(s, 24.9, 44.5, 116.8, 7.6, "Allowances and assumptions",
          size=11.5, font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.rich(s, 24.9, 54.6, 116.8, 76.6, [
        {"text": "[Site-specific allowance, e.g. buried service depth to be "
                 "confirmed on site]", "bullet": 3.8},
        {"text": "[Existing drainage, e.g. compliant and reused where the "
                 "works do not disturb it]", "bullet": 3.8},
        {"text": "[Ground conditions, e.g. as described in the geotechnical "
                 "report provided]", "bullet": 3.8},
        {"text": "[Access constraint, e.g. tight against the house. "
                 "Equipment is sized to suit]", "bullet": 3.8},
        {"text": "[Third party works, e.g. fibre relocation by the network "
                 "provider. Allowance covers coordination only]",
         "bullet": 3.8},
        {"text": "[Engineering input, e.g. engineer to confirm construction "
                 "detail before the fixed price is issued]", "bullet": 3.8},
    ], size=9, spacing=1.15, space_after=6)

    SL.tb(s, 155.1, 44.5, 116.8, 7.6, "Exclusions",
          size=11.5, font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.rich(s, 155.1, 54.6, 116.8, 56.6, [
        {"text": "Detailed planning and costing fees (contracted separately)",
         "bullet": 3.8},
        {"text": "Council fees (these can be paid direct to council)",
         "bullet": 3.8},
        {"text": "Topographical and boundary survey", "bullet": 3.8},
        {"text": "Geotechnical construction monitoring", "bullet": 3.8},
        {"text": "Repair, replacement or relocation of any existing "
                 "underground services", "bullet": 3.8},
        {"text": "Irrigation or lighting (unless specifically stated)",
         "bullet": 3.8},
        {"text": "Unforeseen underground services or contaminated or "
                 "hazardous material", "bullet": 3.8},
        {"text": "Relocation charges levied directly by a network provider",
         "bullet": 3.8},
        {"text": "Any work outside the scope described above", "bullet": 3.8},
    ], size=9, spacing=1.15, space_after=6)

    SL.rect(s, 25.1, 160.2, 246.9, 21.6, BR.TINT)
    SL.rect(s, 25.2, 160.2, 1.1, 21.6, BR.GREEN)
    SL.rich(s, 31.2, 165.3, 234.7, 11.4, [
        {"runs": [("What this means for you  ·  ",
                   {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("Some items are carried as allowances at this stage. These "
                   "are estimated figures, confirmed once selections and site "
                   "investigations are finalised in the next stage.", {})]},
    ], size=10, spacing=1.4)
    SL.footer(s, prs)
    return s


def _how_we_work(prs):
    """
    The five stages, titled as the page the client is actually looking at
    rather than as the name of the diagram on it. "The Zones 5-Stage Process"
    describes the graphic; "Where you are, and what happens next" is what the
    reader wants from it, and it sets up the Stage 3 page that follows.
    """
    s = SL.blank(prs)
    SL.head(s, prs, "How we work", "Where you are, and what happens next")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 38.1, cw, 8,
          "Every Zones project follows our proven process from concept to "
          "completion. You have completed Stage 2, and Stage 3 is next.",
          size=10)
    stages = [
        ("01", "Initial Consultation",
         "We meet on-site, understand your vision and assess the space.",
         "COMPLETE"),
        ("02", "Scoping & Feasibility",
         "We survey the site and produce your concept plans. This report is "
         "the outcome of this stage.", "COMPLETE"),
        # Named to match the contract and invoice the client signs and pays in
        # this stage, and the page that follows. It was "Detailed
        # Specification" here and Detailed Planning & Costing everywhere else.
        ("03", "Detailed Planning & Costing",
         "We finalise the design and selections, and confirm your fixed "
         "price.", "YOUR NEXT STEP"),
        ("04", "Build",
         "Your project is professionally managed from first sod to final "
         "detail.", None),
        ("05", "Handover",
         "Your completed outdoor space, on time, on budget, to your brief.",
         None),
    ]
    # Five equal columns. The stage the client is being asked to buy next sits
    # on a tint panel that runs the full height of the strip, so the eye lands
    # on it before it reads any of the words.
    xs = (25.0, 75.5, 126.3, 176.9, 227.4)
    bw = 44.5
    for i, (x, (num, title, desc, state)) in enumerate(zip(xs, stages), 1):
        active = state is not None
        if state == "YOUR NEXT STEP":
            SL.rect(s, x - 3.6, 52.1, bw + 7.3, 101.6, BR.TINT)
            SL.rect(s, x - 3.6, 52.1, bw + 7.3, 1.1, BR.GREEN)
        else:
            SL.rect(s, x, 52.1, bw, 1.1,
                    BR.GREEN if active else BR.STAGE_OFF_RULE)
        SL.tb(s, x, 55.9, bw, 8.9, num, size=15, font=HF,
              colour=BR.GREEN if active else BR.STAGE_OFF_INK, bold=True,
              spacing=1.0)
        SL.tb(s, x, 66.0, bw, 11.2, title, size=10.5, font=HF, colour=BR.INK,
              bold=True, spacing=1.2)
        SL.stage_photo(s, i, x, 80.0, bw, 38.1)
        SL.tb(s, x, 123.2, bw, 15.7, desc, size=8.5, spacing=1.45)
        if state:
            SL.tb(s, x, 142.7, bw, 7.1, state, size=7.5, font=HF,
                  colour=BR.GREEN, bold=True, spacing=1.15, tracking=1.5)
    SL.tb(s, 42.4, 173.3, 210.3, 3.9,
          "Each stage is contracted separately. There's no obligation to "
          "continue beyond this point, though in our experience, clients who "
          "reach this stage rarely opt out.", size=8.5, italic=True,
          colour=BR.MUTED, spacing=1.15)
    SL.footer(s, prs)
    return s


def _what_happens_next(prs):
    """
    The closing page: what Stage 3 delivers, and the four steps to start it.

    Replaces "Ready to go", which was three vague steps ending in a follow-up
    meeting, plus a box about insurance. This is the page Lee rebuilt by hand
    on SF_34: the client is deciding whether to pay for Stage 3, so the page
    has to say what Stage 3 produces, and the steps have to be the actual
    commercial sequence, sign then pay then start.
    """
    s = SL.blank(prs, SL.PAGE_PLAIN)
    SL.tb(s, 25.0, 14.0, 246.9, 6.1, "WHAT HAPPENS NEXT", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1.5)
    SL.tb(s, 25.0, 19.6, 246.9, 8.9, "Stage 3, Detailed Planning & Costing",
          size=17, font=HF, colour=BR.INK, bold=True, spacing=1.15)
    SL.tb(s, 23.8, 29.8, 208.0, 5.8,
          "The next stage turns your concept into a fully documented, fixed "
          "price build. Here is what it delivers, and how we get there.",
          size=10, spacing=1.15)

    SL.tb(s, 25.1, 42.7, 60.9, 5.6, "WHAT STAGE 3 DELIVERS", size=9.5,
          font=HF, colour=BR.GREEN, bold=True, spacing=1.0, tracking=1)
    cards = [
        (25.0, 95.2, 66.0, "Design work",
         "Detailed designs, working drawings for construction, with any "
         "changes made as required by client, council, engineer."),
        (115.2, 48.0, 59.2, "Full project plan",
         "A detailed scope of work, costings, specifications and selections, "
         "and the documentation needed for good project management."),
        (195.5, 31.5, 59.1, "Fixed Quote",
         "Confirmation of your final budget as a contractual fixed price for "
         "the build."),
    ]
    for x, label_w, body_w, title, body in cards:
        SL.tb(s, x, 53.4, label_w, 6.1, title, size=11, font=HF,
              colour=BR.GREEN, bold=True, spacing=1.0)
        SL.tb(s, x, 60.5, body_w, 15.7, body, size=9.5, spacing=1.4)

    # The steps panel is set 4mm wider than the text column on both sides, so
    # the green spine sits outside the type rather than beside it.
    SL.rect(s, 21.0, 88.4, 246.9, 60.2, BR.TINT)
    SL.rect(s, 21.0, 88.4, 1.3, 60.2, BR.GREEN)
    SL.tb(s, 35.1, 93.0, 97.7, 7.6, "YOUR NEXT STEPS", size=10, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.0, tracking=1)
    steps = [
        (103.6, "You confirm the budget range fits your expectations"),
        (113.5, "Sign the Detailed Planning & Costing contract"),
        (123.7, "Pay the Detailed Planning & Costing invoice"),
        (134.6, "We begin the Detailed Planning and preparation of council "
                "documents"),
    ]
    for i, (y, text) in enumerate(steps, 1):
        SL.rich(s, 35.6, y, 168.1, 6.3, [
            {"runs": [("%02d" % i, {"font": HF, "bold": True,
                                    "colour": BR.GREEN}),
                      ("   " + text, {})]},
        ], size=10, spacing=1.2)

    SL.tb(s, 28.9, 156.4, 53.1, 4.3, "WHY CHOOSE ZONES", size=9.5, font=HF,
          colour=BR.GREEN, bold=True, spacing=1.15, tracking=2)
    SL.rich(s, 94.9, 154.4, 103.1, 34.3,
            [{"text": t, "bullet": True} for t in [
                "A complete design and build service, start to finish",
                "One point of contact, so nothing gets lost between trades",
                "Unique and superior insurance policies",
                "Professional project management, on time and on budget"]],
            size=10, spacing=1.55, space_after=8)
    SL.logo(s, 22.3, 163.8, 65.4, 25.9)
    return s


# ====================================================================== build

def _template_result():
    """
    A stand-in engine result for the hand-fill master.

    The three YOUR SITE pages are the ones nobody fills in by hand, so a
    template that only describes them leaves the reader guessing. These draw
    the real pages with the real checklist, and put a token everywhere a
    property's own answer would go: the master is a template, not a copy of
    somebody's report.
    """
    import layers as L
    names = [lay["name"] for lay in L.LAYERS]
    flagged = [{"name": "[What was flagged, item %d]" % i, "status": "on_site",
                "plain": "[What it is, and what it means for the design and "
                         "the budget. One or two sentences, plain English.]",
                "clause": "[AUP ref]"} for i in range(1, 4)]
    nearby = [{"name": "[Nearby item %d]" % i, "status": "nearby"}
              for i in range(1, 4)]
    clear = [{"name": n, "status": "clear"}
             for n in names[:len(names) - len(flagged) - len(nearby)]]
    return {
        "address": "{{Site Address}}",
        "site": {"display": "{{SITE ADDRESS}}"},
        "generated": "[date and time]",
        "warnings": [],
        "parcel": {"legal_description": "[Lot 00 DP 000000]",
                   "title": "[NA00A/000]", "area_m2": None,
                   "area_source": "[LINZ survey]"},
        "zone": {"name": "[Zone name]", "standards": {
            "code": "[H0]", "front_yard_m": "[0.0]", "side_yard_m": "[0.0]",
            "rear_yard_m": "[0.0]", "site_coverage_pct": "[00]",
            "impervious_pct": "[00]", "landscaped_pct": "[00]",
            "riparian_yard_m": "[0.0]", "coastal_yard_m": "[0.0]",
            "clauses": {}}},
        "findings": flagged + nearby + clear,
    }


def build_template(out_path, result=None, map_path=None):
    """
    The hand-fill master: every page of the current design, no job data.

    Built by the generator rather than maintained by hand, which is the only
    way the template and the tool stay the same document. Merge fields stay as
    {{tokens}} and guidance stays in [brackets], the way the template has
    always carried them.

    The three YOUR SITE pages are drawn the way a real job draws them, from
    `_template_result()`, so the master shows that part of the design instead
    of describing it. Pass a real `result` only when you deliberately want a
    worked example; the master itself must not carry a client's data.
    """
    prs = SL.new_presentation("a4")
    f = {"name": "{{Name}}", "first": "{{First Name}}",
         "date": "{{Date}}", "address": "{{Site Address}}"}
    _how_to_use(prs, has_site=True)
    _cover(prs, f)
    _personal_note(prs, f)
    _contents(prs)
    _site_plan(prs)
    _selections(prs)
    _render_3d(prs)
    deck_export.build_site_slides(prs, result or _template_result(),
                                  map_path, template=result is None)
    _scope(prs, None)
    _timeline(prs)
    _budget(prs)
    _allowances_exclusions(prs)
    _how_we_work(prs)
    _what_happens_next(prs)
    prs.save(out_path)
    return out_path


def build(result, out_path, client=None, map_path=None, date=None,
          plan_image=None, budget=None, site_reason=None, address=None,
          design_sheets=None):
    """
    Build the whole binder.

    result         engine.run() result, or None to fall back to placeholders
    address        the address as typed, used for the merge fields when the
                   lookup failed. Always pass it: the site check failing does
                   not make the address unknown.
    client         client name for the merge fields, e.g. "Sarah Thompson"
    map_path       site map PNG for the feasibility pages
    design_sheets  Lee's own drawing sheets, in order, one page each. When
                   given, these ARE the design section and the three
                   placeholder pages are dropped: the drawings already cover
                   the plan, the visuals and the selections, so keeping empty
                   boxes beside them would just be pages to delete by hand.
    plan_image     single 2D plan, used only when design_sheets is not given
    budget         (low, high) dollars, later from zones-qs
    site_reason    why the site pages are missing, shown on the placeholder
    """
    prs = SL.new_presentation("a4")
    f = _fields(result, client, date, address)

    _how_to_use(prs, has_site=bool(result))
    _cover(prs, f)
    _personal_note(prs, f)
    _contents(prs)

    if design_sheets:
        # The sheets replace the 2D plan and 3D render placeholders, which are
        # just image slots the drawings fill. Selections stays: it is not an
        # image slot but a numbered legend keyed to markers on the plan, and
        # the drawing set's own materials and planting pages show character
        # rather than listing what goes where. Losing it silently took a
        # standard page out of the binder with nothing saying so.
        for sheet in design_sheets:
            _design_sheet(prs, sheet)
        _selections(prs)
    else:
        _site_plan(prs, plan_image)
        _selections(prs)
        _render_3d(prs)

    if result:
        deck_export.build_site_slides(prs, result, map_path)
    else:
        _site_placeholder(prs, site_reason or
                          "The address lookup did not run for this job.")

    _scope(prs, result)
    _timeline(prs)
    _budget(prs, budget)
    _allowances_exclusions(prs)
    _how_we_work(prs)
    _what_happens_next(prs)

    prs.save(out_path)
    return out_path
