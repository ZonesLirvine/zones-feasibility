"""
AUP zone standards, keyed by base zone name as returned by Auckland Council's
Unitary Plan Base Zone layer.

SOURCE: read directly out of the operative Auckland Unitary Plan zone chapters
(unitaryplan.aucklandcouncil.govt.nz, Chapter H Zones, July 2026 revision) on
29 Jul 2026. Nothing here is from memory or inference.

H3's values independently match those in the feasibility.co.nz sample report
for 985 Whangaparaoa Road, which is a useful cross-check.

RULE FOR ADDING A ZONE: open the chapter PDF, read the standard, record the
clause reference, set verified=True. Never populate from a search snippet or
from what a number "should" be. These go in front of clients.

PLAN CHANGE 120: the H3 to H6 chapters carry PC 120 modification markers. The
values below are the operative text as it currently reads. H6 is the one zone
where PC 120 has removed the numbers entirely, so it is recorded as pending
rather than guessed at.
"""

# The front-yard fence rule is identical across H2 to H6, so it is defined once.
# It is the standard Zones work bumps into most often.
FENCE_RULE = dict(
    front_yard_m=1.4,
    front_yard_alt="1.8 m over no more than 50% of the frontage with 1.4 m for "
                   "the remainder, or 1.8 m throughout if the fence is at least "
                   "50% visually open when viewed square on to the boundary",
    side_rear_m=2.0,
    plain="Fences in the front yard are limited to 1.4 m. You can go to 1.8 m "
          "over half the frontage, or 1.8 m the whole way if the fence is at "
          "least half visually open. Side and rear boundaries allow 2 m.",
)

# Applies in H1 to H5. Relevant because paving a stream or coastal margin is a
# common request that runs straight into it.
YARD_IMPERVIOUS_PCT = 10

ZONE_STANDARDS = {
    "Residential - Large Lot Zone": dict(
        verified=True, code="H1",
        front_yard_m=10.0, side_yard_m=6.0, rear_yard_m=6.0,
        riparian_yard_m=10.0, lakeside_yard_m=30.0, coastal_yard_m=25.0,
        impervious_pct=35, impervious_cap_m2=1400,
        site_coverage_pct=20, coverage_cap_m2=400,
        landscaped_pct=None,
        yard_impervious_pct=YARD_IMPERVIOUS_PCT,
        fences=None,
        clauses={"yards": "H1.6.5", "impervious": "H1.6.6",
                 "coverage": "H1.6.7"},
        note="Impervious area is capped at 35% of the site or 1,400 m2, "
             "whichever is smaller. Building coverage is capped at 20% or "
             "400 m2, whichever is smaller. This zone has no landscaped area "
             "standard and no fence height standard.",
    ),
    "Residential - Rural and Coastal Settlement Zone": dict(
        verified=True, code="H2",
        front_yard_m=5.0, side_yard_m=1.0, rear_yard_m=1.0,
        riparian_yard_m=10.0, lakeside_yard_m=30.0, coastal_yard_m=20.0,
        impervious_pct=35, impervious_cap_m2=1400,
        site_coverage_pct=20, coverage_cap_m2=400,
        landscaped_pct=None,
        yard_impervious_pct=YARD_IMPERVIOUS_PCT,
        fences=FENCE_RULE,
        clauses={"yards": "H2.6.7", "impervious": "H2.6.8",
                 "coverage": "H2.6.9", "fences": "H2.6.10"},
        note="Impervious area is capped at 35% of the site or 1,400 m2, "
             "whichever is smaller. Building coverage is capped at 20% or "
             "400 m2, whichever is smaller. This zone has no landscaped area "
             "standard.",
    ),
    "Residential - Single House Zone": dict(
        verified=True, code="H3",
        front_yard_m=3.0, side_yard_m=1.0, rear_yard_m=1.0,
        riparian_yard_m=10.0, lakeside_yard_m=30.0, coastal_yard_m=10.0,
        impervious_pct=60, site_coverage_pct=35, landscaped_pct=40,
        front_yard_landscaped_pct=50,
        yard_impervious_pct=YARD_IMPERVIOUS_PCT,
        fences=FENCE_RULE,
        clauses={"yards": "H3.6.8", "impervious": "H3.6.9",
                 "coverage": "H3.6.10", "landscaped": "H3.6.11",
                 "fences": "H3.6.12"},
        note="At least 50% of the front yard must be landscaped (H3.6.11(2)).",
    ),
    "Residential - Mixed Housing Suburban Zone": dict(
        verified=True, code="H4",
        front_yard_m=3.0, side_yard_m=1.0, rear_yard_m=1.0,
        riparian_yard_m=10.0, lakeside_yard_m=30.0, coastal_yard_m=10.0,
        impervious_pct=60, site_coverage_pct=40, landscaped_pct=40,
        front_yard_landscaped_pct=50,
        yard_impervious_pct=YARD_IMPERVIOUS_PCT,
        fences=FENCE_RULE,
        clauses={"yards": "H4.6.7", "impervious": "H4.6.8",
                 "coverage": "H4.6.9", "landscaped": "H4.6.10",
                 "fences": "H4.6.14"},
        note="At least 50% of the front yard must be landscaped.",
    ),
    "Residential - Mixed Housing Urban Zone": dict(
        verified=True, code="H5",
        front_yard_m=2.5, side_yard_m=1.0, rear_yard_m=1.0,
        riparian_yard_m=10.0, lakeside_yard_m=30.0, coastal_yard_m=10.0,
        impervious_pct=60, site_coverage_pct=45, landscaped_pct=35,
        front_yard_landscaped_pct=50,
        yard_impervious_pct=YARD_IMPERVIOUS_PCT,
        fences=FENCE_RULE,
        clauses={"yards": "H5.6.8", "impervious": "H5.6.9",
                 "coverage": "H5.6.10", "landscaped": "H5.6.11",
                 "fences": "H5.6.15"},
        note="At least 50% of the front yard must be landscaped (H5.6.11(2)).",
    ),
}

# Zones recognised but with no quotable standards, and why. Kept separate from
# "unknown" so the report can explain itself rather than look broken.
#
# NOTE ON NAMING: keys must match the zone names the Council layer actually
# returns, which are not always the AUP chapter titles. The chapter is called
# "Terrace Housing and Apartment Buildings Zone" but the layer says "Apartment
# Building Zone", singular. Both spellings are carried so a rename at either
# end cannot silently drop the zone into "unknown".
PENDING = {
    "Residential - Terrace Housing and Apartment Building Zone": (
        "The impervious area, building coverage and landscaped area standards "
        "for this zone (H6.6.10 to H6.6.12) are currently marked as pending "
        "insertion under Plan Change 120, so the operative chapter states no "
        "figures. These must be confirmed with a planner rather than assumed."
    ),
    "Residential - Low Density Residential Zone": (
        "This zone is not one of the H1 to H6 chapters this tool holds "
        "standards for. Its setbacks and coverage limits need to be read from "
        "the relevant Unitary Plan chapter before they can be quoted."
    ),
    "Two-Storey Medium Density Residential Area": (
        "This is a density area rather than one of the H1 to H6 base zone "
        "chapters. Its standards need to be confirmed against the plan text "
        "before they can be quoted."
    ),
    "Two-Storey Single Dwelling Residential Area": (
        "This is a density area rather than one of the H1 to H6 base zone "
        "chapters. Its standards need to be confirmed against the plan text "
        "before they can be quoted."
    ),
}
# Deliberate alias: the AUP chapter title spelling, kept so a rename at
# Council's end cannot silently drop the zone. Excluded from the name drift
# check in tools/check_layers.py, which would otherwise flag it every run.
ALIASES = {"Residential - Terrace Housing and Apartment Buildings Zone"}

PENDING["Residential - Terrace Housing and Apartment Buildings Zone"] = \
    PENDING["Residential - Terrace Housing and Apartment Building Zone"]


def lookup(zone_name):
    """Return (standards_dict_or_None, status)."""
    if zone_name in ZONE_STANDARDS:
        return ZONE_STANDARDS[zone_name], "verified"
    if zone_name in PENDING:
        return None, "plan_change_pending"
    return None, "unknown"


def pending_reason(zone_name):
    return PENDING.get(zone_name)


def impervious_allowance(site_area_m2, standards):
    """
    Total hard surface the site is allowed, in m2.

    This is the number that bites on a landscaping job: paving, driveway and
    roof all count, so an ambitious paving scheme can breach it before anyone
    has drawn a plan. Honours the absolute cap in H1 and H2. Returns None if
    it cannot be worked out.
    """
    if not standards or not site_area_m2 or not standards.get("impervious_pct"):
        return None
    allowed = site_area_m2 * standards["impervious_pct"] / 100.0
    cap = standards.get("impervious_cap_m2")
    return min(allowed, cap) if cap else allowed


def coverage_allowance(site_area_m2, standards):
    """Total building footprint allowed, in m2. Honours the H1/H2 cap."""
    if not standards or not site_area_m2 or not standards.get("site_coverage_pct"):
        return None
    allowed = site_area_m2 * standards["site_coverage_pct"] / 100.0
    cap = standards.get("coverage_cap_m2")
    return min(allowed, cap) if cap else allowed
