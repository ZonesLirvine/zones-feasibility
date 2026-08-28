# Safeguards

Every guard here closes a specific way this document could tell a client
something untrue. They look like extra work until you picture the client
standing in their garden holding the report.

Read this before changing `engine.py`, `layers.py`, or any status handling.

## The failure this whole tool is built against

A **false all-clear**: the report saying nothing was found when something is
there, or when nothing was actually checked. It is the worst error available
here because it reads exactly like a good result. A crash is obvious and
harmless by comparison.

Every guard below is a version of the same instinct: *silence is not the same as
absence, and absence is not the same as safety.*

## The guards

### Checks run against the whole parcel, not a point

A point-based check at the validation address missed an ecological area and all
four coastal erosion extents the property genuinely sits in. Point checking
produces false all-clears. The parcel polygon comes from LINZ.

### Base zone is looked up at the parcel centroid

Not by polygon intersect, because every residential parcel abuts a road and the
intersect returns "Road" as often as the real zone. Other zones are looked up
separately against the whole parcel and reported as a warning, but only after
the boundary test below proves they are actually on the land.

The centroid maths translates to a local origin first. At Auckland's coordinates
the shoelace formula loses its result to floating-point cancellation; without
the translation a Devonport parcel's centroid landed outside its own bounding
box and the site came back zoned "Road". There is a bounding-box sanity check
behind it. This is commented in `engine.py` where it happens.

### A layer that fails is an error, never a clear

Silent nulls are how a wrong all-clear reaches a client. If a layer cannot
answer, it says so.

### The layer health check runs before any client document

All 44 layers are probed for existence, fields and a non-zero feature count.
If any fails, the build refuses. The dangerous failure is silent: a layer
renamed or emptied upstream keeps rendering clean pages that say "clear". A
check nobody is forced to run is not a check.

`--skip-verify` exists and should never be used for client work.

### Incomplete coverage can never report "clear"

`partial=True` on a layer makes anything short of a direct hit come back as
status `partial`, rendered everywhere as NOT CONFIRMED with that layer's own
`absent` wording, and kept out of the "also checked, nothing found" list.

Wastewater and water are the cases. Public mains are complete, but private
laterals exist on nearly every property and are in no public record. A homeowner
reading "clear" beside wastewater would be misled.

Nearby is no better than clear for these, which is why it is not offered: a
trunk main 150 m away is not actionable, and its absence from the parcel proves
nothing about what is buried there.

### A shared boundary is not an overlay on the land

**This is the one guard that points the other way, so it gets the most scrutiny.**

An area overlay that only shares a boundary with the parcel still satisfies an
intersects test. LINZ's parcel edge and Council's overlay edge come from
different survey lineages, so where they are meant to be the same line they
disagree by fractions of a millimetre, and the intersection is a degenerate
sliver of essentially no area.

Found at 12B Margate Road, which backs onto Glenavon School for the full 18.4 m
of its rear boundary. Overlap with the school designation was **0.0000 m²**, and
the report told the owner part of her land was designated for a public work.
That is a false alarm rather than a false all-clear, but it is still the
document being wrong about her property, and a client who checks one claim and
finds it untrue has no reason to trust the other thirty-nine.

`MIN_OVERLAP_M2 = 0.5` in `engine.py`. At or below it, the finding becomes
`abuts` rather than `on_site`.

What keeps this from becoming a false all-clear:

- **It never reaches `clear`.** `abuts` is flagged, listed in the findings
  table, drawn on the map with an "(adjoins)" legend entry, and excluded from
  the "also checked, nothing found" list. Nothing disappears; the wording
  changes from "part of your site is X" to "your boundary adjoins X".
- **It cannot be measured, it stays `on_site`.** `overlap_m2` returning None,
  a missing `shapely`, a layer that returns lines instead of rings: every one
  of those falls through to the old behaviour.

#### The same guard applies to the secondary zone list

The guard above was written for the overlay layers and did not reach the
secondary-zone query, which is a separate `esriSpatialRelIntersects` call. So
the identical failure survived there: any property backing onto a reserve,
park, school or differently-zoned neighbour was told part of it might be in
that zone.

Found at 66 Rhinevale Close, which backs onto a conservation reserve. Measured
overlap with Open Space - Conservation was **0.0 m²** on a 705 m² section, and
the report told the owner the Single House standards might only apply to part
of his land. Three of the five addresses in `verifying.md` carried the same
false warning, which is how routine it is.

`zone_is_on_the_land()` in `engine.py` measures it with the same `overlap_m2`
helper and the same `MIN_OVERLAP_M2` threshold, so the two behave alike, and
fails safe the same way: unmeasurable means real. Verified discriminating
rather than blanket-suppressing at 33 Marine Parade, where two spurious zones
drop and the genuine Coastal - General Coastal Marine overlap is kept.

### A base zone of Road means the wrong parcel was checked

Nobody's garden is in the road reserve. When the address resolves to the
carriageway rather than the property, the parcel lookup returns the road
parcel and all 40 checks run against it, so every finding in the report is for
the wrong piece of land.

This used to surface by accident: the real residential zone next door came back
as a "second zone" warning, which at least looked odd enough to check. The
boundary test above correctly suppresses that, so the condition is now stated
directly instead. Seen at 12B Margate Road.
- **Lines and points are exempt.** Buried services carry `tolerance_m` and are
  meant to flag on proximity. The test only runs at zero tolerance.
- **It never reaches the consent draft**, which stays `on_site` only.
- **The margin is enormous.** Across the test addresses the smallest genuine
  overlap measured is 55.67 m², and the smallest at Margate Road is 13.05 m².
  The threshold is over an order of magnitude below anything real, and the
  sliver it catches was 0.0000007 m². If a real finding ever lands near 0.5 m²,
  that is a signal to look at the layer, not to move the number.

Re-measure before changing the threshold. `engine._sliver_area(service, geometry)`
returns the number for any layer and address.

### The client is asked to confirm the parcel

The parcel is chosen by geocoding an address, so describing the neighbour's land
is the worst realistic failure. The legal description and the map were already
the defence, but nothing asked anyone to look at them. Now it does, in amber, in
every output format.

### The report states its own shelf life

Six months. Planning rules and hazard mapping are revised constantly, and a
report found in a drawer eighteen months later looks exactly like a current one.

### Zone warnings reach every output

When part of a property falls in a second zone, the standards table is only
right for part of it. That warning renders in the terminal, the PDF, the A3
sheets **and** the slides. It was missing from the slides for a while, which
meant the binder Lee actually hands over presented one zone's standards as
settled fact.

### The binder degrades, it does not refuse

If the lookup fails or the health check fails, the YOUR SITE section becomes a
placeholder and everything else still builds, because Lee still needs his
binder. But:

- the file is named `-DRAFT-SITE-INCOMPLETE.pptx` and `run.py` exits 3
- the placeholder page says plainly that nothing was checked, and never implies
  the site is clear
- nothing in the section claims the check happened, and the placeholder carries
  a do-not-send banner

The address still prints throughout, because a failed lookup means Council could
not tell us about the property, not that we do not know where it is.

### The consent draft never concludes

The scope page can draft a consent position from the flagged findings, but it
only ever puts the evidence in front of Lee. It does not assert that consent is
or is not required. Nothing in this tool knows about the design, the earthworks
volumes or the building line, and an all-clear site check does not mean no
consent is needed. That is the one wrong answer this document must never give
on its own.

### Clear results are shown, never hidden

"We checked 40 things and 28 are clear" is a large part of what the S&F fee
buys. `--flags-only` exists for internal use and should not reach a client.

### The headline finding is a person's job

`--note` prints Lee's plain-English read at the top of A3 sheet 1. On a bush
gully site the tool correctly reports an ecological area, a watercourse, an
overland flow path and two landslide layers as five separate findings. They are
one feature with five regulatory consequences, and only a person can say that.
Without the note the band renders "to be completed before this pack is issued",
so the gap is visible rather than silently absent.

## If you are tempted to relax one of these

Ask what it would look like on the day it fails. Most of these were added after
a specialist review or after a real miss, and the cost of the guard is a few
seconds of runtime or one extra line in a table. The cost of removing it is a
client who trusted the document.

If a guard genuinely is wrong, say so plainly and explain why rather than
quietly working around it.
