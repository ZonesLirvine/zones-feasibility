# Zones Site Feasibility Check

Auckland-only site feasibility lookup for Zones Landscaping. Give it an address,
it returns the planning facts that bear on a landscaping job: consent triggers,
design constraints, hazards and services.

It also builds the whole S&F Report binder around that lookup, so the output is
written for a client, not a planner.

## Running it

```bash
python run.py "10 Bellwood Avenue, Mount Eden"
```

Options:

- `--report sf-report.pptx` builds the **whole S&F Report binder**, A4 landscape,
  one slide per ring-binder page, with the three site feasibility pages generated
  in place. See below.
- `--client "Sarah Thompson"` fills the client name into the report's merge
  fields. The site address and date fill themselves from the lookup.
- `--plans "drawings.pdf"` puts your own drawing set into the report's design
  section, one binder page per sheet, in order. A PDF or a single image.
- `--pdf report.pdf` renders the client-facing PDF, with the site map included
  automatically
- `--page a3` makes those A3 landscape presentation sheets for the folder
  (default is `a4` portrait report pages)
- `--a3` alongside `--page a4`, also writes an A3 landscape version with two A4
  pages per sheet
- `--pptx report.pptx` exports editable PowerPoint slides
- `--docx report.docx` exports an editable Word document
- `--note "..."` your read on the site in plain words, printed as the headline
  finding near the top of sheet 1
- `--skip-verify` skips the layer health check (not for anything a client sees)
- `--map site-map.png` renders the site map as a standalone PNG
- `--json out.json` also writes the raw findings for further processing
- `--flags-only` hides the clear results (internal use only, see below)

## The S&F Report binder

`sf_report.py`. The whole client document, cover to back page:

```bash
python run.py "10 Bellwood Avenue, Mount Eden" \
      --report sf-report.pptx --client "Sarah Thompson"
```

Sixteen pages when the site check runs: how to use (internal, delete before
printing), cover, a personal note from Lee, contents, the 2D site plan, a 3D
render, selections, the three site feasibility pages, scope of work, timeline,
budget range, allowances and exclusions, how we work, and what happens next.
A heavily flagged site adds one page: ten or more findings need two columns of
cards, so the nearby and clear lists move to a continuation page.

Design leads, the site check follows it, then the commercial pages. The site
pages come out of the same command as everything else, so there is nothing to
import and no second file to keep in step.

**SF_34 is the template.** The 66 Rhinevale Close deck Lee sent is the
reference for every page, not just the page order: the binder is built on
`templates/zones-sf-a4.pptx`, which is that file with the slides deleted, so
the theme, the fonts and the Zones Cover / Zones Page / Zones Page No Logo
layouts come across intact. Footer, brand line, centred live page number and
the top-right logo are layout shapes, identical on every page by construction.

Generating 66 Rhinevale Close and comparing page by page gives zero differences
in position, size, fill, line, font, size, weight, colour or spacing on the
cover, personal note, contents, site overview, findings, How we work and
allowances pages. See `references/the-binder.md` for how to run that comparison
and what the handful of remaining differences are.

Anything this generator produces that then has to be deleted, reordered or
rebuilt by hand before sending is a bug here, not a step in the workflow.

**The binder is never gated on the site lookup.** If the address does not
resolve, Council's API is down, or the layer health check fails, the YOUR SITE
section falls back to a placeholder that says plainly that nothing was checked,
and the rest of the binder still builds. The file is then written as
`<name>-DRAFT-SITE-INCOMPLETE.pptx`, so it cannot be mistaken for a finished
report from the folder listing alone, and `run.py` exits 3.

A failed lookup does not make the address unknown. It still prints on the cover
and the letter, because Lee typed it and has been to the site. What changes is
that every claim about the check itself drops to what we do rather than what we
found: the placeholder page says plainly that the check has not been completed,
and carries a do-not-send banner. Nothing in the deck ever says a site was
checked when it was not.

**Your own drawings go in with `--plans`.** Give it the job's drawing set as a
PDF and every sheet becomes a binder page in the design section, in the order
they appear, replacing the 2D plan and 3D render placeholders. Selections is
kept: it is not an image slot but a numbered legend keyed to markers on the
plan, and a drawing set's own materials and planting pages show character
rather than listing what goes where. The
sheets are drawn at A3 landscape, which is the same shape as an A4 binder page,
so they land at 1:1 with nothing cropped and no reflowing. Each keeps its own
title block and gets the deck's footer and live page number, and sits inside
the margins so the punch still misses the drawing.

Sheets are rasterised at 200 dpi, which holds 1:100 annotations legible at A4.
The intermediates go to a working directory, never beside the output, because
the output usually lands in the client's job folder on Drive.

Budget figures are a parameter on `sf_report.build()` that defaults to the
placeholder treatment, ready for `zones-qs` to fill later.

## The client PDF

`report_pdf.py`. Montserrat headings, Open Sans body, Zones green, brand fonts
embedded from the machine with a Helvetica fallback so it still runs elsewhere.

Pages: property and zone standards, site map, what we checked. The closing
notice sits at the foot of the findings, not on a page of its own.

Two page setups:

- **A4 portrait, single column.** 595.28 × 2 = 1190.55 pt, which is A3 landscape
  to the point, so `--a3` imposes two pages per sheet edge to edge with no
  scaling and everything prints at true size.
- **A3 landscape presentation sheets** (`--page a3`). A separate design in
  `presentation_a3.py`, not the report reflowed. See below.

Findings are grouped by consequence, consent triggers first. Flagged items get
the full plain-English explanation and the AUP clause; clear items get a compact
one-line tick. That is deliberate: the full checklist is what evidences the S&F
fee, so the clear results are shown, never hidden.

## The A3 presentation sheets

`presentation_a3.py`. A3 in a folder is looked at rather than read: it sits open
next to design drawings and gets pointed at across a table. So this is panels
and pulled-out numbers at presentation scale, not body copy in columns.

Three sheets:

1. **Your site.** Headline numbers (site area, zone, how many records flagged),
   property details, what the hard-surface rule actually allows in m2, the
   zone standards as a tile grid with clause references, and the closing
   notice along the foot.
2. **Site map.** Whole sheet, aerial with the legend beside it.
3. **What we found.** Set editorially: a quiet figure strip, then numbered
   entries with hairline rules and muted category labels, then the nearby and
   clear lists as flowing text. Deliberately not cards and chips, which read as
   a dashboard rather than a document.

The map switches to a landscape view for these sheets (`layout="wide"`, 1.32:1)
so it fills the sheet instead of sitting square in the middle with dead space
either side.

## Editable exports

`deck_export.py`. The PDF is the finished artefact; these are for adapting it
or adding commentary.

`build_site_slides()` adds the site pages to a presentation that is already
under way, which is how `sf_report.py` puts them inside the binder.
`build_pptx()` wraps it to produce them as a file on their own.

**Page design follows the page size, and there is only the one design.** At A4
both callers produce the same three pages: the four stat tiles and zone
standards on the overview, the flagged findings as cards, the map filling the
page, in that order. The map goes last because by then the reader knows what
the pins mean.

Those pages are laid out in fixed A4 millimetres, so `--page a3` keeps the
older scalable layout. That is the only output that still has the three-across
tiles, the findings table, the commentary boxes, the map-first order, and the
full notice on a page of its own.

**The disclaimer is the short form, on the overview page.** Intro, liability
and attribution, which are the parts that carry. The report is a feasibility
read, not a contract, and the terms are in the signed S&F contract, which is
where a client goes looking for them. A page restating them made the document
look like something it is not.

Everything is native text, tables and pictures, not flattened images, so it
edits normally. Findings go into a table because a table is the easiest thing
to add a commentary row to. Each slide carries a marked-up commentary box that
expands to fill whatever space the content left, so there is never a dead band
in the middle regardless of how many items a job flagged.

Slides are landscape at the same size as the PDF (`--page a3` gives 420 x 297
slides, `--page a4` gives 297 x 210 to match the existing S&F deck).

Note: python-pptx table cells inherit Office's blue default theme. Cell fills
are painted explicitly, because setting run colours alone leaves the table
looking nothing like the brand.

## Safeguards

Three deliberate guards, each closing a specific failure:

**The layer health check runs before any document is built.** All 44 layers are
probed for existence, fields and a non-zero feature count. If any fails, the
build refuses. The dangerous failure here is silent: a layer renamed or emptied
upstream keeps rendering clean pages that quietly say "clear". A check nobody is
forced to run is not a check. `--skip-verify` exists but should not be used for
client work.

**The client is asked to confirm the parcel.** The parcel is chosen by geocoding
an address, so the worst failure this document can have is describing the
neighbour's land. The legal description and the map were already the defence,
but nothing asked anyone to look at them.

**The report states its own shelf life.** Six months, after which it should be
re-run. Planning rules and hazard mapping change, and a report found in a drawer
eighteen months later looks exactly like a current one.

**A layer with incomplete published coverage can never report clear.** Marking a
layer `partial=True` in `layers.py` makes anything short of a direct hit come
back as status `partial`, rendered everywhere as NOT CONFIRMED with that
layer's own `absent` wording, and kept out of the "also checked, nothing found"
list. Wastewater is the case this exists for: finding nothing in a dataset that
only holds trunk mains says nothing at all about what is buried on the site, and
a homeowner reading "clear" beside wastewater would be being misled.

**Buried services carry a position tolerance.** `tolerance_m` on a layer widens
the on-site test by a couple of metres. Council's asset geometry and LINZ's
parcel geometry come from different survey lineages and disagree by about a
metre, so a main laid along a boundary reads as on or off the property
depending on whose line you believe. For a planning overlay that does not
matter. For something a digger might go through, "just outside" is not a
distinction worth relying on.

## The headline finding

`--note` prints a plain-English read of the site at the top of sheet 1, above
the detail.

This is the one thing the data cannot produce. On a bush-gully site the tool
correctly reports an ecological area, a watercourse, an overland flow path and
two landslide layers as five separate findings. They are one feature with five
regulatory consequences, and only a person can say that. Without the note the
band renders "to be completed before this pack is issued", so the gap is visible
rather than silently absent.

## Consistent length across jobs

Every job produces exactly three sheets with the same regions in the same
places, so a folder of jobs reads as one document set. Content is fitted to
the slots rather than the slots growing to fit:

- The planning standards row is always the same eight tiles in the same order,
  showing `n/a` where a zone has no such standard. H1 and H2 have no landscaped
  area standard, for example.
- The notes strip is always present, with a fallback line when there is nothing
  to say.
- Cards on the findings sheet are only ever used for things actually on the
  property, which is the small variable set (3 to 9 across test addresses).
  Nearby and clear items all carry identical boilerplate, so they become chips
  and cost a predictable amount of space.
- The entries grid is a fixed 2 x 4. Anything beyond eight drops into the
  nearby line rather than pushing the sheet longer.
- Entries are distributed inside a fixed band rather than pinned to a fixed row
  height, so a job with few findings does not leave a dead void mid-page.
- The sheet always closes with a standing "what happens next" note, so it ends
  deliberately rather than stopping wherever the findings ran out.

## The site map

`mapper.py` composites Auckland Council's aerial basemap (2024/2025 urban
imagery) with the LINZ parcel boundary and the geometry of whatever the report
flagged. Everything is done in NZTM 2193, the projection Council publishes the
imagery in, and overlay geometry is requested with `outSR=2193` so the server
handles reprojection. No pyproj dependency.

Only layers that actually flagged are drawn, so the legend never lists something
the viewer cannot see.

**Area overlays are hatched, not filled.** Solid fills stack: three overlapping
overlays turn the photo to mud and you cannot tell which is which. Each area
layer gets its own hatch pattern and angle, so overlaps stay separable and the
aerial reads through. Layers sharing a pattern are offset so their strokes
interleave rather than coincide. Legend swatches use the same pattern, so the
legend matches what is on the map rather than being colour-coded only.

**The SEA uses small crosses rather than strokes.** Angle alone does not carry
enough difference once several layers stack: a diagonal mesh over an orthogonal
one just reads as mesh, and the SEA is usually the largest area on the map with
the flood layers sitting over it. A discrete mark is a different kind of
texture and separates at a glance. A cross rather than a dot because it carries
more ink for the same spacing, and the SEA is normally over dark bush canopy
where a fine stipple disappears.

**Colours follow Auckland Council's own symbology where they can.** Council
publish a renderer with every layer, so their exact RGB is readable rather than
guessable, and anyone used to GeoMaps then reads this map without the legend.

Buried services follow the GeoMaps UndergroundServices renderers, which is the
view Lee actually works from: **wastewater red, potable water blue, stormwater
green**, other owners' pipework light purple. Read these off GeoMaps, not the
open data portal. The two servers symbolise the same assets differently and
only one of them is what anyone looks at: overland flow is cyan on GeoMaps and
blue on the open data portal, and the blue sat close enough to the water main
to be indistinguishable on an aerial.

Flood plain, flood prone, flood sensitive, historic heritage, coastal
inundation and natural inland wetlands also use Council's published values.

Five layers deliberately do not match, because copying Council literally makes
this map worse rather than more familiar. Council use the same green for
stormwater pipes and watercourses, so the watercourse takes teal instead.
High-pressure gas is the same red as wastewater, which works on GeoMaps because
you choose which layer to switch on and does not work here, so gas takes
Council's gas-transmission magenta. Fuel pipelines are a brown that vanishes
against a dark aerial, and a fuel line is the most dangerous thing that can
cross a site, so legibility wins. Both landslide layers are dark browns and
olives drawn over a pale basemap, which disappear over aerial photography.
Special Character has no fill at all, just an outline, so it cannot carry a
hatch.

```bash
python tools/check_council_colours.py
```

reports any layer we match Council on that Council has since restyled, and
prints their current values for the ones we deliberately differ on. It only
reads. Updating is deliberately by hand, because judging whether a colour
survives over an aerial is not something to automate.

**Layers covering the whole view are noted, not drawn.** A layer blanketing the
entire extent tells you nothing about where it is and destroys legibility for
every other layer. Above 90% coverage it is dropped from the map and the legend
says "covers this whole view". The landslide susceptibility layers are regional
wash surfaces rather than boundaries, so they are held to a stricter 50%: they
only get drawn when they genuinely distinguish part of the site.

Health check before anything that matters:

```bash
python tools/check_layers.py
```

No API keys needed. PyMuPDF and Pillow are required for the PDF and map;
python-pptx and python-docx only for the editable exports.

## What it checks

40 layers across five groups, ordered by what costs the client time or money:

| Group | Covers |
|---|---|
| Consent | Significant Ecological Areas, Special Character, Mana Whenua sites, Historic Heritage, Notable Trees, Notable Group of Trees, Natural Stream Management, natural inland wetlands, designations |
| Design | Outstanding Natural Features / Landscapes / Character, volcanic viewshafts, Ridgeline Protection, National Grid Corridor, vehicle access restrictions, height variation controls |
| Hazard | Flood plains, flood prone, flood sensitive, overland flow paths, shallow and large scale landslide, coastal inundation, coastal erosion across four climate scenarios |
| Services | Stormwater pipes and watercourses, wastewater mains (local and transmission), water mains (local and transmission), other utility pipework, gas pipelines, fuel pipelines, septic tanks |
| Background | Quarry buffer |

Plus base zone with its AUP standards, and LINZ title details.

## Data sources

- **Auckland Council Open Data**, CC BY 4.0, attribution is in the report footer
- **Auckland Council GeoMaps asset server** (`mapspublic`, LiveMaps /
  UndergroundServices) for buried services. **Use this, not the open data
  portal, for anything you might dig through.** The open data wastewater layer
  `wm_Wastewater_Pipes` looks like the network and is a watershed model: 7,825
  segments region-wide, against 528,377 in the asset layer. On a Henderson site
  it put the nearest main 200 m away while two live mains ran within a metre of
  the boundary. The `wm_` prefix marks these model subsets throughout, roughly
  a tenth of the real asset count
- **Auckland Council Address layer**, primary geocoder
- **LINZ NZ Primary Parcels** via LINZ's own ArcGIS Online account, no key needed
- **OpenStreetMap Nominatim**, fallback geocoder only

Not used, deliberately: BRANZ wind, corrosion, earthquake and climate zones.
They are build spec rather than planning constraint, their data is display-only
vector tiles with no query capability, and their licence terms are not open.

## Validated against

The feasibility.co.nz sample report for 985 Whangaparaoa Road, Tindalls Beach
(7 Jul 2026). Every field this tool covers matches: zone, site area, legal
description, title number, the SEA overlay, coastal inundation, all four coastal
erosion scenarios, both landslide layers, and all four flood layers reading
clear.

## Design decisions worth knowing

**Checks run against the whole parcel, not a point.** A point-based check at the
sample address missed the SEA and all four coastal erosion extents that the
property genuinely sits in. Point checking produces false all-clears, which is
the worst error this document can make. The parcel polygon comes from LINZ.

**Base zone is looked up at the parcel centroid**, not by polygon intersect,
because every residential parcel abuts a road and the intersect returns "Road"
as often as the real zone. Other zones touching the parcel are reported
separately as a warning.

**A layer that fails is reported as an error, never as clear.** Silent nulls are
how a wrong all-clear reaches a client.

**Clear results are shown, not hidden.** "We checked 40 things and 28 are clear"
is the deliverable. `--flags-only` exists for internal use and should not be
used for anything a client sees.

## Zone standards

Loaded and verified for the five residential zones that have quotable figures,
read directly out of the operative AUP chapters (July 2026 revision) with clause
references recorded against each value:

| Zone | Front | Side | Rear | Hard surface | Coverage | Landscaped |
|---|---|---|---|---|---|---|
| H1 Large Lot | 10 m | 6 m | 6 m | 35% or 1,400 m² | 20% or 400 m² | none |
| H2 Rural and Coastal Settlement | 5 m | 1 m | 1 m | 35% or 1,400 m² | 20% or 400 m² | none |
| H3 Single House | 3 m | 1 m | 1 m | 60% | 35% | 40% |
| H4 Mixed Housing Suburban | 3 m | 1 m | 1 m | 60% | 40% | 40% |
| H5 Mixed Housing Urban | 2.5 m | 1 m | 1 m | 60% | 45% | 35% |

H1 and H2 carry absolute caps as well as percentages, and the tool applies
whichever is smaller.

Also carried: the front and side/rear fence height rule (identical across H2 to
H6), the 10% hard surface limit inside riparian, lakeside and coastal protection
yards, and the 50% front yard landscaping requirement in H3 to H5.

**H6 Terrace Housing and Apartment Building is deliberately not populated.** Its
impervious, coverage and landscaped area standards are marked as pending
insertion under Plan Change 120, so the operative chapter states no figures. The
report says so and refers the user to a planner rather than guessing.

## Known limitations

- **Non-residential zones are not loaded.** Business, Open Space and Rural zones
  report that standards are not held rather than guessing. Add them to
  `standards.py` the same way if they start coming up.
- **Wastewater public mains are covered; private laterals are not.** The public
  network comes from Council's GeoMaps asset server and is complete. Laterals
  are private, appear in no public record, and exist on nearly every property,
  so this check can never return "clear": see the status note below.
- **Power and fibre are not covered.** Not public. beforeUdig is the route and
  that is a manual, separate process by design.
- **Covenants, consent notices and easements are not covered.** Not available
  through any public API. The report says so and recommends a title search.
- Runs about 8 to 12 seconds per address, most of it waiting on Council.

## Working on this

**A dead Council endpoint can look alive.** The retired
`mapspublictest.aucklandcouncil.govt.nz` answers HTTP 200 and serves a blank IIS
placeholder page. A health check that only asks "did it respond" passes against
it happily. That is why `tools/check_layers.py` tests for a non-zero feature
count and the expected fields, not just a response. Keep it that way: the whole
point of the gate is catching an upstream change that would otherwise render
clean pages saying "clear".

**Verifying document output on this machine.** There is no `soffice`, no
`pdftoppm` and no LibreOffice here, so the pptx skill's rendering instructions
will fail. Use the real Office apps over COM instead, which is more faithful
anyway. Build, render to PDF, then rasterise:

```powershell
$ppt = New-Object -ComObject PowerPoint.Application
$p = $ppt.Presentations.Open("$env:TEMP\out.pptx", $true, $false, $false)
$p.SaveAs("$env:TEMP\out.pdf", 32); $p.Close(); $ppt.Quit()
```

```python
import fitz
for i, page in enumerate(fitz.open("out.pdf")):
    page.get_pixmap(dpi=110).save("p%02d.png" % (i + 1))
```

Check every page, not a sample. Watch for text overflowing its box and for
anything creeping inside the 25 mm left margin, which is the ring binder punch.

Write the findings once with `--json`, then rebuild documents from that file
rather than re-running the address. It saves the 8 to 12 second wait per
iteration and keeps you off Council's API while you are only changing layout.

**Fonts.** Montserrat and Open Sans are installed to this machine's user font
store. They render from the web in Google Docs, but Office needs them present
locally. If a fresh machine renders the deck in Calibri, that is why.

**Test addresses**, each exercising a different shape of job:

| Address | Exercises |
|---|---|
| `15e Balmain Road, Birkenhead` | H3, bush gully, 13 of 40 flagged, so both the flagged and clear paths |
| `33 Marine Parade, Herne Bay` | 9 on-property findings, fills and overflows the card grid |
| `75 Karekare Road, Karekare` | H2 zone, exercises the `n/a` standards tiles |
| `985 Whangaparaoa Road, Tindalls Beach` | the validation case against the feasibility.co.nz sample report |

## Files

| File | Purpose |
|---|---|
| `run.py` | CLI |
| `engine.py` | geocoding, parcel lookup, layer queries |
| `layers.py` | layer registry and the client-facing wording for each |
| `standards.py` | AUP zone standards table |
| `render.py` | plain-English report, and the shared disclaimer wording |
| `mapper.py` | aerial site map with overlays and boundary dimensions |
| `report_pdf.py` | A4 portrait report |
| `presentation_a3.py` | A3 landscape presentation sheets |
| `brand.py` | design tokens: palette, type, page geometry, margins |
| `slides.py` | shared PowerPoint furniture, used by both decks below |
| `deck_export.py` | the site pages, as slides or as Word |
| `sf_report.py` | the whole S&F Report binder |
| `tools/check_layers.py` | endpoint health check |
| `tools/check_council_colours.py` | map colours vs Council's published symbology |

`brand.py` and `slides.py` are why the site pages and the rest of the binder
agree on colour, type, margins, headers and footers: they are the same code, not
two implementations kept in step by hand.
