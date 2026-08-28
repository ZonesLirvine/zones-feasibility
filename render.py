"""
Renders a feasibility result as plain-English text.

Two rules drive the layout, both from the client-facing purpose:

1. Everything checked is listed, including the clear results. "We checked
   twenty-eight things and twenty-six are clear" is the deliverable. Showing
   only the hits makes a good site look like no work was done.
2. Nothing is stated as determined. Findings are flagged for investigation.
"""

import layers as L
import soil as SOIL
import standards as S

TICK, FLAG, NEAR, ERR = "[ OK ]", "[FLAG]", "[NEAR]", "[ ?? ]"

SHORT_NOTICE = ("Prepared from Auckland Council, Toitū Te Whenua LINZ and "
                "Manaaki Whenua Landcare Research records. Indicative only: "
                "verify against Auckland Council's GeoMaps viewer before any "
                "design or construction decision. Full notice at the end of "
                "this report.")

# Shown beside the legal description. The parcel is chosen by geocoding an
# address, so the single worst failure this document can have is describing the
# neighbour's land. The defence already exists (legal description and the map),
# but a defence nobody is asked to look at does not work.
PARCEL_CONFIRM = ("Please check this matches your record of title. Everything "
                  "in this report describes the property outlined on the site "
                  "map.")

# Every output says the same thing about an `abuts` finding, so the sentence
# lives here rather than being written five slightly different ways. The overlay
# is real and worth knowing about, it is simply on the other side of the line.
ABUTS_TEXT = ("Your boundary adjoins this, but none of your property is inside "
              "it, so it does not control what you can build. It can still "
              "matter for work along that boundary, and for who the adjoining "
              "owner is.")

# Kills the "found it in a drawer eighteen months later" failure.
VALIDITY = ("Based on Council, LINZ and Manaaki Whenua records as at the date above. Planning "
            "rules and hazard mapping change. Re-run this check before "
            "construction if the report is more than six months old.")

DISCLAIMER_TITLE = "IMPORTANT NOTICE, PLEASE READ"

DISCLAIMER_INTRO = (
    "This site feasibility check is provided for information purposes. It is "
    "indicative, and should not be relied upon as a statement of what can or "
    "cannot be built on this property."
)

DISCLAIMER_POINTS = [
    ("Prepared from publicly available records.",
     "This report draws on Auckland Council's published planning and hazard "
     "datasets, on Land Information New Zealand records, and on Manaaki "
     "Whenua Landcare Research's national soil classification, as those "
     "datasets stood on the date shown above. No site inspection, survey, "
     "measurement, soil test or physical investigation has been carried out "
     "for the purposes of this report."),

    ("It is not a planning assessment.",
     "Nothing in this document is planning advice, a legal opinion, or a "
     "determination of what is permitted on this site. Whether any activity "
     "requires resource consent or building consent can only be confirmed by "
     "Auckland Council, or by a suitably qualified planner assessing an actual "
     "proposal."),

    ("It does not replace consent.",
     "This document forms no part of, and does not shorten or substitute for, "
     "any resource consent, building consent, engineering approval or other "
     "regulatory process."),

    ("It is not exhaustive.",
     "Only the matters listed in this report have been checked. Covenants, "
     "consent notices, easements, encumbrances and other title restrictions are "
     "not held in any public database and are not covered. Underground "
     "services, including power and telecommunications, have not been located."),

    ("The underlying data has limits.",
     "Auckland Council's own guidance is that this information is indicative, "
     "is in places derived from regional-scale modelling, and does not remove "
     "the need for site-specific assessment. Mapped boundaries are approximate. "
     "Data may not reflect recent changes, or plan changes currently in "
     "progress."),

    ("It has a shelf life.",
     "Planning rules, overlays and hazard mapping are all revised over time, "
     "and plan changes are in progress. This report reflects the records as "
     "they stood on the date shown. If it is more than six months old, have it "
     "re-run before any construction decision."),

    ("Verify before committing to anything.",
     "Every matter flagged in this report is identified for further "
     "investigation only, and is not confirmed. All information should be "
     "verified against Auckland Council's official GeoMaps viewer, the "
     "operative Auckland Unitary Plan, and a current record of title, before "
     "any design, construction, purchase or financial decision is made."),
]

DISCLAIMER_LIABILITY = (
    "Aven Limited, trading as Zones Landscaping Auckland Central, accepts no "
    "liability for any loss or damage arising from reliance on this document."
)

# The disclaimer every client-facing output carries, and the only one.
#
# Lee's call, 14 Aug 2026: the report is a feasibility read, not a contract,
# and the full terms are already in the signed S&F contract, which is where a
# client goes looking for them. Restating them over a whole page made the
# document look like something it is not.
#
# What stays is what actually carries: this is indicative, we accept no
# liability for reliance on it, and here is where the data came from with the
# instruction to verify it. DISCLAIMER_POINTS and VALIDITY are kept for the
# terminal output, which is internal.
#
# It sits at the foot of the site overview page in every deck, and at the end
# of the PDF. Do not give it a page of its own again without asking Lee.
CLOSING_NOTICE = (DISCLAIMER_INTRO, DISCLAIMER_LIABILITY, L.ATTRIBUTION)


# Wind zone wording, shared by every output so the terminal, the PDF, the
# slides and the Word export cannot drift into saying different things about
# the same site.
#
# The design gust is quoted with its source on the face of the document. It is
# a real published figure from NZS 3604:2011 Table 5.4, and a number in a
# client document without a source beside it is indistinguishable from one we
# made up.
WIND_UNKNOWN = ("Council holds no mapped wind zone over this property. Most "
                "of the region outside the old city council areas is "
                "unmapped. It has to be confirmed with Council or assessed by "
                "a designer under NZS 3604 before anything roofed, solid or "
                "over standard height is designed or priced.")

WIND_FAILED = ("The wind zone could not be read from Council's records for "
               "this run. That is not the same as there being none: it has "
               "to be checked before it is relied on.")


def wind_headline(wind):
    """One line: the zone, and the design gust it stands for."""
    if not wind:
        return "Not determined"
    if wind.get("speed"):
        return "%s (NZS 3604:2011 Table 5.4, design gust %d m/s)" % (
            wind["label"], wind["speed"])
    return wind["label"]


def wind_summary(wind, failed=False):
    """
    The whole wind zone in one line, for the slides.

    The A4 binder page and the A3 sheets are fixed layouts with a few
    millimetres of clear space under the standards table, which is the right
    place for this and has room for a line rather than a paragraph.
    """
    if not wind:
        return ("Wind zone:  not read on this run, confirm before use."
                if failed else
                "Wind zone:  not mapped by Council here, so it has to be "
                "confirmed before anything roofed or over height is priced.")
    spec = L.WIND_ZONES.get(wind["code"], {})
    head = "Wind zone:  %s" % wind["label"]      # "Not recorded" for code U
    if wind.get("speed"):
        head += " (design gust %d m/s, NZS 3604 Table 5.4)" % wind["speed"]
    short = spec.get("short") or "confirm with a designer under NZS 3604"
    line = "%s.  %s." % (head, short[0].upper() + short[1:])
    if any(o["higher"] for o in wind.get("others") or []):
        line += "  Part of the site is mapped higher."
    return line


def wind_lines(wind, indent=3, failed=False):
    """The wind block as plain text, for the terminal report."""
    pad = " " * indent
    if not wind:
        return [_wrap(pad + (WIND_FAILED if failed else WIND_UNKNOWN), indent)]
    out = [pad + "Wind zone: %s" % wind_headline(wind), ""]
    if wind.get("plain"):
        out.append(_wrap(pad + wind["plain"], indent))
    for o in wind.get("others") or []:
        if not o["higher"]:
            continue
        out.append(_wrap(
            pad + "Part of the property, %sis mapped %s. Anything built on "
            "that part has to be built to the higher zone."
            % ("" if o["m2"] is None else
               "about %s m2 of it, " % (f"{o['m2']:,.1f}" if o["m2"] < 10
                                        else f"{o['m2']:,.0f}"),
               o["label"]), indent))
    out.append("")
    out.append(_wrap(pad + wind["caveat"], indent))
    return out


def _fmt_standards(zone, standards_module=None):
    if not zone or not zone.get("name"):
        return ["Base zone could not be determined for this location."]

    name = zone["name"]
    std, status = zone.get("standards"), zone.get("standards_status")
    label = "%s (%s)" % (name, std["code"]) if std and std.get("code") else name
    lines = ["Your site is zoned: %s" % label]

    if status == "verified" and std:
        c = std.get("clauses") or {}
        lines.append("")
        rows = [
            ("Front yard (minimum)", std.get("front_yard_m"), "m", "yards"),
            ("Side yard (minimum)", std.get("side_yard_m"), "m", "yards"),
            ("Rear yard (minimum)", std.get("rear_yard_m"), "m", "yards"),
            ("Maximum building coverage", std.get("site_coverage_pct"), "%",
             "coverage"),
            ("Maximum hard surface", std.get("impervious_pct"), "%",
             "impervious"),
            ("Minimum landscaped area", std.get("landscaped_pct"), "%",
             "landscaped"),
            ("Riparian yard (if a stream)", std.get("riparian_yard_m"), "m",
             "yards"),
            ("Coastal protection yard", std.get("coastal_yard_m"), "m", "yards"),
        ]
        for text, val, unit, key in rows:
            if val is None:
                continue
            clause = c.get(key)
            lines.append("   %-32s %s%s%s" % (
                text, val, unit, "  (%s)" % clause if clause else ""))

        if std.get("note"):
            lines.append("")
            lines.append(_wrap("   Note: " + std["note"], 9))

        if std.get("fences"):
            f = std["fences"]
            lines.append("")
            lines.append("   FENCES")
            lines.append(_wrap("   " + f["plain"], 3))
            if c.get("fences"):
                lines.append("   Reference: AUP %s" % c["fences"])

        if std.get("yard_impervious_pct"):
            lines.append("")
            lines.append(_wrap(
                "   Inside a riparian, lakeside or coastal protection yard, no more "
                "than %d%% of that yard may be hard surface. Paving near a stream "
                "or the coast runs into this quickly."
                % std["yard_impervious_pct"], 3))

    elif status == "plan_change_pending":
        reason = (standards_module.pending_reason(name)
                  if standards_module else None)
        lines.append("")
        lines.append(_wrap("   " + (reason or "Standards for this zone are "
                                    "currently subject to a plan change."), 3))
    else:
        lines.append("")
        lines.append(_wrap(
            "   Standards for this zone are not held by this tool. They need to be "
            "read from the relevant Unitary Plan chapter before they can be "
            "quoted.", 3))
    return lines


def _fmt_soil(soil):
    """
    Terminal block for the soil classification.

    Renders in all three states. A failed lookup prints as a failure rather
    than being dropped, because a missing section reads as "nothing to say
    about the soil" and that is the same false all-clear the rest of the tool
    is built to avoid.
    """
    if not soil:
        return []

    out = ["SOIL", "-" * 78]
    status = soil.get("status")

    if status == "ok":
        head = SOIL.headline(soil)
        if head:
            out.append("   %s" % head)
            if soil.get("code"):
                out.append("   NZ Soil Classification: %s" % soil["code"])
            out.append("")
        for key in ("group_description", "order_description"):
            if soil.get(key):
                out.append(_wrap("   " + soil[key], 3))
                out.append("")
        if soil.get("means"):
            out.append("   WHAT THAT MEANS FOR THE BUILD")
            out.append(_wrap("   " + soil["means"], 3))
            out.append("")
        out.append(_wrap("   " + soil.get("scale_note", ""), 3))
    elif status == "not_mapped":
        out.append(_wrap("   This location is not covered by the national soil "
                         "map, so no soil classification is held for it. That "
                         "is a gap in the mapping, not a finding about the "
                         "site.", 3))
    else:
        out.append(_wrap("   The soil classification could not be retrieved, "
                         "so nothing is known about the soil here from this "
                         "check. This is a failed lookup, not a clear result.",
                         3))
        if soil.get("error"):
            out.append("   Reason: %s" % soil["error"])

    out.append("")
    return out


def render(result, show_clear=True):
    out = []
    site = result["site"]

    out.append("=" * 78)
    out.append("SITE FEASIBILITY CHECK")
    out.append(result["address"])
    out.append("Located as: %s" % site["display"])
    out.append("Prepared %s by Zones Landscaping Auckland Central"
               % result.get("generated", ""))
    out.append("=" * 78)
    out.append(_wrap(SHORT_NOTICE, 0))
    out.append("")

    parcel = result.get("parcel")
    if parcel:
        out.append("YOUR PROPERTY")
        out.append("-" * 78)
        out.append("   %-34s %s" % ("Legal description",
                                    parcel.get("legal_description") or "-"))
        out.append("   %-34s %s" % ("Record of title",
                                    parcel.get("title") or "-"))
        if parcel.get("area_m2"):
            out.append("   %-34s %s m2  (%s)" % (
                "Site area", f"{parcel['area_m2']:,}", parcel["area_source"]))
        out.append("")
        out.append("   Covenants, consent notices and easements are not held in any "
                   "public database and are not covered by this check. They need a "
                   "title search, which we recommend before design is finalised.")
        out.append("")

    out.append("ZONE AND STANDARDS")
    out.append("-" * 78)
    out += _fmt_standards(result.get("zone"), S)

    std = (result.get("zone") or {}).get("standards")
    area = (parcel or {}).get("area_m2")
    hard = S.impervious_allowance(area, std)
    build = S.coverage_allowance(area, std)
    if hard:
        out.append("")
        out.append("   WHAT THAT MEANS ON YOUR SITE")
        out.append(_wrap(
            "   On %s m2, you are allowed roughly %s m2 of hard surface in total. "
            "That includes the house roof and the existing driveway, not just new "
            "paving, so the figure available for new work is lower."
            % (f"{area:,}", f"{hard:,.0f}"), 3))
        if build:
            out.append(_wrap("   Building footprint is capped at about %s m2."
                             % f"{build:,.0f}", 3))
    out.append("")

    out.append("WIND ZONE")
    out.append("-" * 78)
    out += wind_lines(result.get("wind"),
                      failed=bool(result.get("wind_error")))
    out.append("")

    out += _fmt_soil(result.get("soil"))

    if result.get("warnings"):
        out.append("BEFORE YOU RELY ON THIS")
        out.append("-" * 78)
        for w in result["warnings"]:
            out.append(_wrap("   " + w, 3))
        out.append("")

    findings = result["findings"]
    by_cat = {}
    for f in findings:
        by_cat.setdefault(f["category"], []).append(f)

    flagged = [f for f in findings
               if f["status"] in ("on_site", "abuts", "nearby")]
    errored = [f for f in findings if f["status"] == "error"]
    clear = [f for f in findings if f["status"] == "clear"]
    partial = [f for f in findings if f["status"] == "partial"]

    out.append("SUMMARY")
    out.append("-" * 78)
    out.append("  %d checks run against Auckland Council planning and hazard data."
               % len(findings))
    out.append("  %d flagged for attention, %d clear, %d could not be checked."
               % (len(flagged), len(clear), len(errored)))
    if partial:
        out.append("  %d not confirmed: the published data does not cover them "
                   "fully." % len(partial))
    out.append("")

    for cat in L.CATEGORY_ORDER:
        items = by_cat.get(cat, [])
        if not items:
            continue
        shown = items if show_clear else [
            i for i in items if i["status"] != "clear"]
        if not shown:
            continue

        out.append(L.CATEGORY_TITLES[cat].upper())
        out.append("-" * 78)
        # Flagged first inside each category.
        order = {"on_site": 0, "abuts": 1, "nearby": 2, "error": 3,
                 "partial": 4, "clear": 5}
        for f in sorted(shown, key=lambda x: order.get(x["status"], 9)):
            if f["status"] == "partial":
                out.append("%s %s" % (ERR, f["name"]))
                out.append("       %s" % _wrap(f.get("absent", ""), 7))
            elif f["status"] == "on_site":
                out.append("%s %s" % (FLAG, f["name"]))
                out.append("       %s" % _wrap(f.get("plain", ""), 7))
                if f.get("clause"):
                    out.append("       Reference: AUP %s" % f["clause"])
            elif f["status"] == "abuts":
                out.append("%s %s" % (NEAR, f["name"]))
                out.append("       %s" % _wrap(ABUTS_TEXT, 7))
            elif f["status"] == "nearby":
                out.append("%s %s" % (NEAR, f["name"]))
                out.append("       Not on your site, but present within %d m. Worth "
                           "being aware of, unlikely to control the design."
                           % 200)
            elif f["status"] == "error":
                out.append("%s %s" % (ERR, f["name"]))
                out.append("       Not confirmed. %s" % f.get("error", ""))
                out.append("       This must be checked manually before relying on "
                           "this report.")
            else:
                out.append("%s %s" % (TICK, f["name"]))
            out.append("")

    out.append("=" * 78)
    out.append(DISCLAIMER_TITLE)
    out.append("=" * 78)
    out.append(_wrap(DISCLAIMER_INTRO, 0))
    out.append("")
    for i, (heading, body) in enumerate(DISCLAIMER_POINTS, 1):
        out.append("%d. %s" % (i, heading))
        out.append(_wrap("   " + body, 3))
        out.append("")
    out.append(_wrap(DISCLAIMER_LIABILITY, 0))
    out.append("")
    out.append(_wrap(L.ATTRIBUTION, 0))
    out.append("=" * 78)
    return "\n".join(out)


def _wrap(text, indent, width=78):
    import textwrap
    return textwrap.fill(text, width=width, subsequent_indent=" " * indent)
