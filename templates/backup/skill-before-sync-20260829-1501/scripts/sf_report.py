"""
The S&F Report: the whole client binder, generated from one address.

Scoping and Feasibility, cover to back page. Design leads: the 2D plan, 3D
render and selections come first, then the YOUR SITE section with its four
feasibility pages generated in place behind the divider rather than produced
separately and pulled in by hand, then scope, timeline, budget and next
steps.

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
    s = SL.blank(prs)
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
        ("The four site feasibility pages behind the YOUR SITE divider are "
         "generated from Council and LINZ records for this address. They are "
         "already in this deck, nothing to import."
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
    """
    s = SL.blank(prs)
    ml, _, cw = SL.content_box(prs)
    SL.rect(s, 0, 0, prs._w, 3.2, BR.GREEN)
    SL.tb(s, ml, 53.3, cw, 8,
          "ZONES LANDSCAPING   ·   AUCKLAND CENTRAL   ·   LEE IRVINE",
          size=10, font=HF, colour=BR.GREEN, bold=True, tracking=2.5)
    SL.tb(s, ml, 64.8, cw, 22, "Scoping & Feasibility", size=40, font=HF,
          colour=BR.INK, bold=True, spacing=1.0)
    SL.tb(s, ml, 85.9, cw, 14, "Report", size=23, font=HF,
          colour=BR.MUTED, spacing=1.0)
    SL.rich(s, ml, 114.3, 152, 32, [
        {"runs": [("Prepared for  ", {"size": 12, "colour": BR.MUTED}),
                  (f["name"], {"size": 13, "bold": True, "colour": BR.INK})]},
        {"text": f["address"], "size": 12, "colour": BR.MUTED},
        {"text": f["date"], "size": 12, "colour": BR.MUTED},
    ], spacing=1.5)
    SL.tb(s, ml, 148.6, 152, 8,
          "By Lee Irvine  ·  Zones Landscaping Auckland Central",
          size=10, colour=BR.GREEN)
    return s


def _personal_note(prs, f):
    """
    The letter, plus a condensed why-choose-Zones panel. The old version
    carried a deliverables list here too, duplicating the Contents page one
    slide over; that's gone, replaced with the credibility content head
    office's template carries as its own section, folded in here instead of
    adding another slide.
    """
    s = SL.blank(prs)
    SL.head(s, prs, "A personal note from Lee", "Hi %s," % f["first"])
    ml, _, cw = SL.content_box(prs)
    lw = 144.8
    rx = ml + lw + 12.7
    rw = cw - lw - 12.7

    SL.rich(s, ml, 39.4, lw, 91.4, [
        "Thank you for the opportunity to work on your project at %s. We have "
        "now completed the Scoping & Feasibility stage, and this report brings "
        "it all together: your brief, what we found on your site, your concept "
        "design, the scope of work, an indicative timeline and a realistic "
        "budget range." % f["address"],
        "",
        "This is the point where your project stops being an idea and becomes "
        "a real, buildable plan. Everything in here has been prepared "
        "specifically for your site and your brief.",
        "",
        "Read it through, and if you have any questions at all, call me on %s. "
        "I'm happy to talk through the design or the numbers before you decide "
        "on next steps." % PHONE,
    ], spacing=1.5)
    SL.rich(s, ml, 139.7, lw, 25.4, [
        {"text": "Lee Irvine", "size": 12, "font": HF, "colour": BR.INK,
         "bold": True},
        {"text": "Managing Director  ·  Aven Limited TA | Zones Landscaping "
                 "Auckland Central", "size": 9},
        {"text": CONTACT, "size": 9},
    ], spacing=1.45)

    SL.rect(s, rx, 39.4, rw, 127, BR.TINT)
    SL.tb(s, rx + 6.35, 45.7, rw - 12.7, 7, "WHY CHOOSE ZONES",
          size=9.5, font=HF, colour=BR.GREEN, bold=True, tracking=2)
    items = ["A complete design and build service, start to finish",
             "One point of contact, so nothing gets lost between trades",
             "Regular updates through our online client portal",
             "Professional project management, on time and on budget"]
    SL.rich(s, rx + 6.35, 54.6, rw - 12.7, 70,
            [{"text": t, "bullet": True} for t in items],
            spacing=1.55, space_after=8)
    SL.tb(s, rx + 6.35, 146.1, rw - 12.7, 17.8,
          "Optional attachments where applicable: QS report (client version), "
          "insurance documentation, warranty documentation.",
          size=8.5, italic=True, colour=BR.MUTED, spacing=1.35)
    SL.footer(s, prs)
    return s


def _contents(prs):
    s = SL.blank(prs)
    SL.head(s, prs, "Contents", "What's in this report")
    ml, _, cw = SL.content_box(prs)
    items = [
        "Your concept design, 2D site plan, vision and key features",
        "3D renders  [delete line if not included]",
        "Selections, plants, palette and materials  [delete line if not "
        "included]",
        "Your site, the planning checks we ran",
        "Scope of work, exclusions and consents",
        "Your timeline",
        "Your budget range",
        "What happens next",
    ]
    for i, text in enumerate(items):
        y = 42.7 + i * 12.3
        main, _, tail = text.partition("  [")
        runs = [(main, {"colour": BR.BODY})]
        if tail:
            runs.append(("   [" + tail, {"italic": True, "colour": BR.MUTED,
                                         "size": 9}))
        SL.rich(s, ml, y, cw, 10, [{"runs": runs}], size=11.5, spacing=1.1)
        if i < len(items) - 1:
            SL.hline(s, ml, y + 9.9, cw * 0.62, BR.LINE, 0.5)
    SL.footer(s, prs)
    return s




def _site_divider(prs, result, f):
    """
    The YOUR SITE divider. The feasibility pages follow it directly.

    With a lookup this reports the real record count and how many were flagged,
    so the section opens with the finding rather than a generic promise.

    Without one it must not say we checked anything. The address is still
    printed, because a failed lookup does not make the address unknown, but
    every claim about the check itself moves to what we do rather than what we
    found. Stating "we checked your property at 42 Somewhere Terrace" over a
    section that is a placeholder is exactly the false all-clear this whole
    tool exists to avoid.
    """
    s = SL.blank(prs)
    ml, _, cw = SL.content_box(prs)
    if not result:
        SL.banner(s, prs, "DO NOT SEND TO CLIENT. The site check has not been "
                          "completed, so this section describes the check "
                          "rather than reporting it.")
    SL.tb(s, ml, 15.7, cw, 7, "YOUR SITE", size=10.5, font=HF,
          colour=BR.GREEN, bold=True, tracking=2, spacing=1.0)
    SL.tb(s, ml, 22.9, cw, 11,
          "What we checked before we designed anything" if result
          else "What we check before we design anything",
          size=17, font=HF, colour=BR.INK, bold=True, spacing=1.0)

    lw = 149.9
    rx = ml + lw + 12.7
    rw = cw - lw - 12.7

    known = not f["address"].startswith("{{")
    where = "your property at %s" % f["address"] if known else "your property"

    if result:
        findings = result["findings"]
        flagged = [x for x in findings
                   if x["status"] in ("on_site", "abuts", "nearby")]
        opening = (
            "Before a single line of your design was drawn, we checked %s "
            "against the Auckland Unitary Plan and Council's hazard, heritage "
            "and services records. %d separate records, checked against your "
            "actual property boundary rather than a pin on a map. %d of them "
            "came back flagged for your attention."
            % (where, len(findings), len(flagged)))
        closing = ("The pages that follow show your property and zone "
                   "standards, a site map of everything we flagged, what we "
                   "found and what each item means for your project, and the "
                   "checks that came back clear.")
    else:
        opening = (
            "Before a single line of your design is drawn, we check %s against "
            "the Auckland Unitary Plan and Council's hazard, heritage and "
            "services records. Twenty-seven separate records, checked against "
            "your actual property boundary rather than a pin on a map. That "
            "check has not been completed for this property yet."
            % where)
        closing = ("Once it has run, the pages that follow will show your "
                   "property and zone standards, a site map of everything we "
                   "flagged, what we found and what each item means for your "
                   "project, and the checks that came back clear.")

    SL.rich(s, ml, 41.9, lw, 86.4, [
        opening,
        "",
        "This is what tells us what you are allowed to build, where the "
        "constraints sit, and which parts of your project will need consent. "
        "It is the difference between a design that looks good on paper and "
        "one that can actually be built.",
        "",
        closing,
    ], spacing=1.5)

    SL.rect(s, rx, 41.9, rw, 59.7, BR.TINT)
    SL.tb(s, rx + 6.35, 48.3, rw - 12.7, 7, "WHAT THIS MEANS FOR YOU",
          size=9.5, font=HF, colour=BR.GREEN, bold=True, tracking=2)
    SL.tb(s, rx + 6.35, 58.4, rw - 12.7, 35.6,
          "Consent surprises are the most expensive thing that can happen to a "
          "landscaping project, and they almost always surface after the build "
          "has started. Doing this work now is what keeps your budget and your "
          "timeline honest.", size=10, spacing=1.5)

    SL.tb(s, ml, 135.9, cw, 14,
          "Source: Auckland Council Open Data (CC BY 4.0) and LINZ NZ Primary "
          "Parcels. Covenants, consent notices, easements, wastewater, power "
          "and fibre are not covered by these records, see the full notice in "
          "the pages that follow.",
          size=8.5, italic=True, colour=BR.MUTED, spacing=1.35)
    SL.footer(s, prs)
    return s


def _site_placeholder(prs, reason):
    """
    Stand-in for the four feasibility pages when the lookup did not run.

    The binder is never gated on the site check, so this page says plainly
    what is missing and why. It never implies the site came back clear.
    """
    s = SL.blank(prs)
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
    The plan does the heavy lifting. Vision and key factors are a blurb
    attached to it, not a slide of their own, the plan and the render carry
    the weight of the proposal.
    """
    s = SL.blank(prs)
    SL.head(s, prs, "Your concept design", "2D site plan")
    ml, _, cw = SL.content_box(prs)
    iw = cw * 0.66
    rx = ml + iw + 12.7
    rw = cw - iw - 12.7

    if plan_image and os.path.exists(plan_image):
        _fit_picture(s, plan_image, ml, 38.1, iw, 139.7)
    else:
        SL.placeholder(s, prs, ml, 38.1, iw, 139.7,
                       "Add 2D site plan, fill this area",
                       "Delete this box once your plan is in.")

    SL.tb(s, rx, 38.1, rw, 8, "Vision", size=11.5, font=HF, colour=BR.INK,
          bold=True)
    SL.tb(s, rx, 47.0, rw, 42,
          "[Personalise this, 2 to 3 sentences. Reflect back what the client "
          "described at the initial consultation, the picture of the "
          "finished space we're designing towards.]",
          size=9.5, italic=True, colour=BR.MUTED, spacing=1.45)

    SL.tb(s, rx, 92.7, rw, 8, "Key features", size=11.5, font=HF,
          colour=BR.INK, bold=True)
    SL.rich(s, rx, 101.6, rw, 76.2, [
        {"runs": [("1  ", {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("[e.g. Custom louvre roof]", {"bold": True,
                                                  "colour": BR.INK}),
                  ("   ·   [All-weather outdoor entertaining for the "
                   "family]", {"colour": BR.MUTED, "italic": True})]},
        {"runs": [("2  ", {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("[e.g. Garden upgrade]", {"bold": True,
                                             "colour": BR.INK}),
                  ("   ·   [Easy-care planting that looks good year "
                   "round]", {"colour": BR.MUTED, "italic": True})]},
        {"runs": [("3  ", {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("[Component]", {"bold": True, "colour": BR.INK}),
                  ("   ·   [Motivation / desired outcome]",
                   {"colour": BR.MUTED, "italic": True})]},
    ], size=9.5, spacing=1.6, space_after=10)
    SL.footer(s, prs)
    return s


def _design_sheet(prs, path, caption=None):
    """
    One of Lee's own drawing sheets, placed as a full page.

    The sheets come out of the drawing set already designed, at A3 landscape
    with their own title block and Zones logo. A3 and A4 are the same shape, so
    a sheet drops onto an A4 binder page at 1:1 with nothing cropped and no
    reflowing. It is placed inside the margins rather than bled to the edge, so
    the 25 mm punch still misses the drawing, and it keeps the deck's footer so
    the page still numbers itself with the rest of the binder.

    No eyebrow or subhead: the sheet carries its own title block, and putting
    ours above it would brand the same page twice.
    """
    s = SL.blank(prs)
    ml, mr, mt, mb = prs._m
    cw = prs._w - ml - mr
    avail_h = prs._h - mt - mb - 2
    _fit_picture(s, path, ml, mt, cw, avail_h)
    if caption:
        SL.tb(s, ml, prs._h - mb - 1, cw, 6, caption, size=8.5, italic=True,
              colour=BR.MUTED)
    SL.footer(s, prs)
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
    s = SL.blank(prs)
    SL.full_bleed(s, BR.TINT_GREEN)
    ml, _, cw = SL.content_box(prs)
    _, mr, _, _ = prs._m
    SL.banner(s, prs, "OPTIONAL SLIDE, delete if 3D renders are not a "
                      "deliverable. Duplicate this slide per render. Delete "
                      "this banner if keeping the slide.")
    SL.rich(s, 50.8, 86.4, prs._w - 101.6, 25.4, [
        {"text": "[ Add 3D render, full bleed, edge to edge ]", "size": 12,
         "bold": True, "italic": True, "colour": BR.PH_INK},
        {"text": "One render per slide for maximum impact. Set the image to "
                 "fill the whole slide, then delete this text.", "size": 9,
         "italic": True, "colour": BR.MUTED},
    ], align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, spacing=1.4)
    SL.rect(s, 0, prs._h - 19.8, prs._w, 19.8, BR.CAPBAR)
    SL.rich(s, ml, prs._h - 19.8, 177.8, 19.8, [
        {"runs": [("Your concept design  ·  ", {}),
                  ("[area this render shows]", {"italic": True})]},
    ], size=12.5, font=HF, colour=BR.WHITE, bold=True,
        valign=MSO_ANCHOR.MIDDLE)
    SL.tb(s, prs._w - mr - 76.2, prs._h - 19.8, 76.2, 19.8,
          "3D RENDER [01] OF [04]", size=8.5, font=HF, colour=BR.COVER_BRAND,
          align=PP_ALIGN.RIGHT, valign=MSO_ANCHOR.MIDDLE, tracking=2)
    return s


def _swatch_page(prs, eyebrow, sub, n, headers, fracs, rows, note,
                 box_label, banner_text):
    """Selections: a strip of image boxes over a table."""
    s = SL.blank(prs)
    ml, _, cw = SL.content_box(prs)
    SL.banner(s, prs, banner_text)
    SL.tb(s, ml, 15.7, cw, 7, eyebrow.upper(), size=10.5, font=HF,
          colour=BR.GREEN, bold=True, tracking=2, spacing=1.0)
    SL.tb(s, ml, 22.9, cw, 11, sub, size=17, font=HF, colour=BR.INK,
          bold=True, spacing=1.0)
    gap = 4.6
    bw = (cw - gap * (n - 1)) / n
    for i in range(n):
        SL.placeholder(s, prs, ml + i * (bw + gap), 39.4, bw, 48.3, box_label,
                       label_size=8)
    SL.brand_table(s, prs, ml, 96.5, cw, 40, fracs, headers, rows)
    SL.tb(s, ml, 148, cw, 8, note, size=8.5, italic=True, colour=BR.MUTED)
    SL.footer(s, prs)
    return s


def _selections(prs):
    """
    Plants, palette and materials, one page attached to the design, numbered
    to match markers on the 2D plan rather than a disconnected swatch table.

    Doubles as the mood board when a job has no 3D render: nothing else in
    the deck then shows material and planting character, so this page
    carries it instead.
    """
    return _swatch_page(
        prs, "Selections", "Plants, palette and materials",
        6, ["No.", "Item", "Type", "Notes"], [0.08, 0.26, 0.16, 0.5],
        [[("1", True), ("[e.g. Lomandra Tanika]", True), ("Plant", True),
          ("[e.g. Border along driveway, hardy and low maintenance]", True)],
         [("2", True), ("[e.g. Deck]", True), ("Material", True),
          ("[e.g. Kwila, oiled finish]", True)],
         [("3", True), ("[e.g. Paving]", True), ("Material", True),
          ("[e.g. Concrete pavers, charcoal]", True)],
         [("[No.]", True), ("[Item]", True), ("[Plant / Material]", True),
          ("[Notes]", True)]],
        "Numbers correspond to markers on the 2D plan. Plant and material "
        "selections shown are indicative, final selections, grades and "
        "specifications are confirmed in the next stage.",
        "Selection photo",
        "OPTIONAL SLIDE. Legend if keeping the 3D render, mood board if "
        "not, use one or the other. Delete this banner if keeping the "
        "slide.")


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
    Scope, allowances, assumptions, exclusions and consents, condensed onto
    one slide rather than split across two, matching how head office's own
    content structure treats scope of work as a single section.
    """
    s = SL.blank(prs)
    SL.head(s, prs, "Scope of work", "What's included, and what isn't")
    ml, _, cw = SL.content_box(prs)
    half = (cw - 14) / 2
    rx = ml + half + 14

    SL.brand_table(s, prs, ml, 38.1, half, 50, [0.55, 0.45], ["Item", "Notes"],
                   [["{{Scope Item %d}}" % i, " "] for i in range(1, 5)])
    SL.tb(s, ml, 92.1, half, 8, "Allowances and assumptions", size=11.5,
          font=HF, colour=BR.INK, bold=True)
    SL.rich(s, ml, 101.0, half, 70, [
        {"text": "Some items are carried as allowances at this stage, "
                 "estimated figures confirmed once selections are finalised "
                 "in the next stage.", "size": 9, "italic": True,
         "colour": BR.MUTED},
        "",
        {"text": "[e.g. Existing drainage is compliant with current "
                 "regulations]", "bullet": True},
        {"text": "[Assumption 2]", "bullet": True},
    ], size=9.5, spacing=1.45, space_after=5)

    SL.tb(s, rx, 38.1, half, 8, "Exclusions", size=11.5, font=HF,
          colour=BR.INK, bold=True)
    SL.rich(s, rx, 47.0, half, 54, [
        {"text": t, "bullet": True} for t in [
            "Council consents or permits (unless specifically stated)",
            "Irrigation or lighting (unless specifically stated)",
            "Plant supply (unless specifically stated)",
            "Any work outside the scope described above",
            "Unforeseen underground services or contaminated material"]],
        size=9, spacing=1.35, space_after=4)

    SL.tb(s, rx, 104.1, half, 8, "Consents, what your project needs",
          size=11.5, font=HF, colour=BR.INK, bold=True)
    draft = _consent_draft(result)
    y = 113.0
    if draft:
        SL.rect(s, rx, y, half, 24, BR.NOTE_BG)
        SL.tb(s, rx + 4, y + 2.3, half - 8, 6, "FROM THE SITE CHECK, YOUR CALL",
              size=7.5, font=HF, colour=BR.NOTE_INK, bold=True, tracking=1.3)
        SL.tb(s, rx + 4, y + 8.3, half - 8, 14.5, draft, size=8,
              colour=BR.NOTE_INK, spacing=1.3)
        y += 28
    SL.tb(s, rx, y, half, 34,
          "[State clearly whether resource consent, building consent, both "
          "or neither is required, and why, referencing the site check "
          "findings that drive it.]",
          size=9, italic=True, colour=BR.MUTED, spacing=1.4)
    SL.footer(s, prs)
    return s


def _timeline(prs):
    s = SL.blank(prs)
    SL.head(s, prs, "Your timeline", "An indicative programme")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 38.1, cw, 8,
          "The timeline below shows the expected high-level programme for your "
          "project from here.", size=10)
    SL.brand_table(
        s, prs, ml, 50.8, cw, 55, [0.62, 0.38],
        ["Milestone", "Indicative timing"],
        [[("[e.g. Detailed specification and fixed pricing]", True),
          ("[e.g. 2 to 3 weeks]", True)],
         [("[e.g. Build start]", True), ("[e.g. Month]", True)],
         [("[e.g. Build duration]", True), ("[e.g. X weeks]", True)],
         [("[e.g. Handover]", True), ("[e.g. Month]", True)]])
    SL.tb(s, ml, 116.8, cw, 8,
          "This is an indicative programme only. We'll confirm firm dates when "
          "your build contract is signed.", size=8.5, italic=True,
          colour=BR.MUTED)
    SL.footer(s, prs)
    return s


def _budget(prs, budget=None):
    """
    budget is (low, high) in whole dollars, or None for the placeholder.
    This is the hook zones-qs plugs into once the QS can price a concept.
    """
    s = SL.blank(prs)
    SL.head(s, prs, "Your budget range", "What your project will cost")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 38.1, cw, 19.1,
          "We believe every landscaping project should start with a concept "
          "design and an agreed budget indication, so we're all on the same "
          "page before any build commitment is made. The range below covers "
          "the overall project cost for the design shown in this report: all "
          "trades, subcontractors and materials, less any exclusions listed "
          "above.", size=10, spacing=1.5)

    lw = 116.8
    rx = ml + lw + 14
    rw = cw - lw - 14
    SL.rect(s, ml, 63.5, lw, 63.5, BR.GREEN)
    SL.tb(s, ml + 8.9, 76.2, lw - 17.8, 7, "YOUR INDICATIVE BUDGET RANGE",
          size=9, font=HF, colour=BR.COVER_BRAND, bold=True, tracking=2)
    figure = ("${:,.0f} to ${:,.0f}".format(*budget) if budget
              else "${{XX,000}} to ${{YY,000}}")
    # Real figures fit the panel at 23pt. The merge tokens are half again as
    # long and wrapped onto a second line that ran into the +GST line below.
    SL.tb(s, ml + 8.9, 85.1, lw - 17.8, 18, figure,
          size=23 if budget else 17, font=HF, colour=BR.WHITE, bold=True,
          spacing=1.0)
    SL.tb(s, ml + 8.9, 104.1, lw - 17.8, 8,
          "+GST  ·  confirmed as a fixed price in Stage 3", size=9.5,
          colour=BR.COVER_SUB)

    SL.tb(s, rx, 63.5, rw, 8, "Components that could move the budget",
          size=11.5, font=HF, colour=BR.INK, bold=True)
    SL.tb(s, rx, 72.4, rw, 12.7,
          "If the range is above or below where you'd like to be, these are "
          "the levers we can adjust together:", size=10, spacing=1.4)
    SL.rich(s, rx, 87.6, rw, 35.6, [
        {"text": "[Component that could be altered, and its approximate "
                 "value]", "bullet": True},
        {"text": "[Component 2, approximate value]", "bullet": True},
        {"text": "[Component 3, approximate value]", "bullet": True},
    ], size=10, italic=True, colour=BR.MUTED, spacing=1.5, space_after=6)

    SL.rect(s, ml, 138.4, cw, 21.6, BR.TINT)
    SL.rect(s, ml, 138.4, 1.1, 21.6, BR.GREEN)
    SL.rich(s, ml + 6.35, 138.4, cw - 12.7, 21.6, [
        {"runs": [("What this means for you  ·  ",
                   {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("An agreed budget range now is what protects you from "
                   "budget surprises later. In the next stage it becomes a "
                   "contractual fixed price, before any build commitment is "
                   "made.", {})]},
    ], size=10, valign=MSO_ANCHOR.MIDDLE, spacing=1.4)
    SL.tb(s, ml, 165.1, cw, 8,
          "Please note this is a budget range indication only. Zones "
          "Landscaping cannot guarantee budget figures until a formal "
          "fixed-price quote has been completed in the next stage.",
          size=8.5, italic=True, colour=BR.MUTED)
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
    SL.head(s, prs, "Your budget range", "Allowances and exclusions")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 30.5, cw, 8,
          "These are the things that could still move the number on the "
          "previous page, and the things that are not in it.", size=10)

    half = (cw - 14) / 2
    rx = ml + half + 14

    SL.tb(s, ml, 44.5, half, 8, "Allowances and assumptions",
          size=11.5, font=HF, colour=BR.INK, bold=True)
    SL.rich(s, ml, 54.6, half, 76, [
        {"text": "[Site-specific allowance, e.g. buried service depth to be "
                 "confirmed on site]", "bullet": True},
        {"text": "Existing drainage is compliant and is reused where it is "
                 "not disturbed by the works.", "bullet": True},
        {"text": "Ground conditions are as described in the geotechnical "
                 "report provided.", "bullet": True},
        {"text": "[Access constraint, e.g. tight against the house. "
                 "Equipment is sized to suit]", "bullet": True},
        {"text": "[Third party works, e.g. fibre relocation by the network "
                 "provider. Allowance covers coordination only]",
         "bullet": True},
        {"text": "Engineer to confirm construction detail before the fixed "
                 "price is issued.", "bullet": True},
    ], size=9.5, spacing=1.45, space_after=5)

    SL.tb(s, rx, 44.5, half, 8, "Exclusions",
          size=11.5, font=HF, colour=BR.INK, bold=True)
    SL.rich(s, rx, 54.6, half, 76, [
        {"text": "Detailed planning and costing fees (contracted separately)",
         "bullet": True},
        {"text": "Council fees (these can be paid direct to council)",
         "bullet": True},
        {"text": "Topographical and boundary survey", "bullet": True},
        {"text": "Geotechnical construction monitoring", "bullet": True},
        {"text": "Repair, replacement or relocation of any existing "
                 "underground services", "bullet": True},
        {"text": "Irrigation or lighting (unless specifically stated)",
         "bullet": True},
        {"text": "Unforeseen underground services or contaminated or "
                 "hazardous material", "bullet": True},
        {"text": "Relocation charges levied directly by a network provider",
         "bullet": True},
        {"text": "Any work outside the scope described above", "bullet": True},
    ], size=9.5, spacing=1.45, space_after=5)

    SL.rect(s, ml, 165.3, cw, 21.6, BR.TINT)
    SL.rect(s, ml, 165.3, 1.1, 21.6, BR.GREEN)
    SL.rich(s, ml + 6.35, 165.3, cw - 12.7, 21.6, [
        {"runs": [("What this means for you  ·  ",
                   {"font": HF, "bold": True, "colour": BR.GREEN}),
                  ("Some items are carried as allowances at this stage. These "
                   "are estimated figures, confirmed once selections and site "
                   "investigations are finalised in the next stage.", {})]},
    ], size=10, valign=MSO_ANCHOR.MIDDLE, spacing=1.4)
    SL.footer(s, prs)
    return s


def _how_we_work(prs):
    s = SL.blank(prs)
    SL.head(s, prs, "How we work", "The Zones 5-Stage Process")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 38.1, cw, 8,
          "Every Zones project follows our proven process from concept to "
          "completion. You have now completed Stage 2.", size=10)
    stages = [
        ("01", "Initial Consultation",
         "We meet on-site, understand your vision and assess the space.",
         "COMPLETE"),
        ("02", "Scoping & Feasibility",
         "We survey the site and produce your concept plans. This report is "
         "the outcome of this stage.", "COMPLETE"),
        ("03", "Detailed Specification",
         "We refine the design together until it's exactly right, and prepare "
         "a fixed price build contract.", "YOUR NEXT STEP"),
        ("04", "Build",
         "Your project is professionally managed from first sod to final "
         "detail.", None),
        ("05", "Handover",
         "Your completed outdoor space, on time, on budget, to your brief.",
         None),
    ]
    gap, y0, ch = 6.35, 54.6, 83.8
    bw = (cw - gap * 4) / 5
    for i, (num, title, desc, state) in enumerate(stages):
        x = ml + i * (bw + gap)
        active = state is not None
        pad = 0.0
        if state == "YOUR NEXT STEP":
            SL.rect(s, x, y0, bw, ch, BR.TINT)
            pad = 3.8
        SL.rect(s, x, y0, bw, 1.1,
                BR.GREEN if active else BR.STAGE_OFF_RULE)
        SL.tb(s, x + pad, y0 + 3.8, bw - pad * 2, 9, num, size=15, font=HF,
              colour=BR.GREEN if active else BR.STAGE_OFF_INK, bold=True,
              spacing=1.0)
        SL.tb(s, x + pad, y0 + 14, bw - pad * 2, 14, title, size=10.5,
              font=HF, colour=BR.INK, bold=True, spacing=1.2)
        SL.tb(s, x + pad, y0 + 29.2, bw - pad * 2, 38.1, desc, size=8.5,
              spacing=1.45)
        if state:
            SL.tb(s, x + pad, y0 + ch - 10.7, bw - pad * 2, 8, state, size=7.5,
                  font=HF, colour=BR.GREEN, bold=True, tracking=1.5)
    SL.tb(s, ml, 148.6, cw, 8,
          "Each stage is contracted separately. There's no obligation to "
          "continue beyond this point, though in our experience, clients who "
          "reach this stage rarely opt out.", size=8.5, italic=True,
          colour=BR.MUTED)
    SL.footer(s, prs)
    return s


def _ready_to_go(prs, f):
    s = SL.blank(prs)
    SL.head(s, prs, "Ready to go", "What happens next")
    ml, _, cw = SL.content_box(prs)
    SL.tb(s, ml, 38.1, cw, 12.7,
          "In Stage 3 we refine the design with you, finalise selections and "
          "specifications, and confirm your final budget as a contractual "
          "fixed price for the build. Three simple steps:", size=10,
          spacing=1.5)
    steps = [
        "Let us know the budget range fits your expectations, or tell us which "
        "levers to adjust.",
        "Accept the Stage 3 proposal, we'll provide this alongside this report.",
        "We arrange a follow-up meeting at %s to finalise the layout and start "
        "selections." % f["address"],
    ]
    gap = 7.6
    bw = (cw - gap * 2) / 3
    for i, text in enumerate(steps):
        x = ml + i * (bw + gap)
        SL.rect(s, x, 54.6, bw, 39.4, BR.PHBG, BR.LINE)
        SL.tb(s, x + 5.6, 59.7, bw - 11.2, 8, "%02d" % (i + 1), size=13,
              font=HF, colour=BR.GREEN, bold=True)
        SL.tb(s, x + 5.6, 69.1, bw - 11.2, 21.6, text, size=9.5, spacing=1.4)
    SL.tb(s, ml, 102.9, cw, 8,
          "From there we lock in the right team to manage every aspect of your "
          "project from start to finish.", size=10)
    SL.rect(s, ml, 120.7, cw, 25.4, BR.TINT_GREEN)
    SL.rich(s, ml + 7.6, 120.7, cw - 15.2, 25.4, [
        {"text": "Client Protection with Zones Landscaping", "size": 11.5,
         "font": HF, "bold": True, "colour": BR.GREEN},
        {"text": "Zones Landscaping has unique and superior insurance "
                 "protection policies to ensure projects are completed to the "
                 "highest standards.", "size": 9.5, "italic": True},
    ], align=PP_ALIGN.CENTER, valign=MSO_ANCHOR.MIDDLE, spacing=1.45)
    SL.tb(s, ml, 154.9, cw, 8, "Questions? Contact Lee Irvine:  %s" % CONTACT,
          size=9.5, colour=BR.MUTED, align=PP_ALIGN.CENTER)
    SL.footer(s, prs)
    return s


# ====================================================================== build

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
        _render_3d(prs)
        _selections(prs)

    _site_divider(prs, result, f)
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
    _ready_to_go(prs, f)

    prs.save(out_path)
    return out_path
