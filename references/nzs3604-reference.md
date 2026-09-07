# NZS 3604:2011 — working reference for landscaping structures

Source document: `G:\My Drive\_Zones\Supply partners\NZS-36042011\NZS-36042011.pdf`
(449 pages, embedded PDF bookmarks/TOC, extractable with PyMuPDF — `pdftoppm`/poppler
is NOT installed on this machine, so the `Read` tool's page-render path fails on this
file; go via `python -c "import fitz; ..."` instead).

**Licensing note.** The standard is free to read (MBIE-funded public access under
building-levy sponsorship, per the PDF's own front matter), but Standards New
Zealand's copyright notice on every page prohibits reproducing or distributing it.
The numbers below are restated in our own words/format as a working reference for
Zones jobs, not a copy of the standard's text or table layouts — always check the
source PDF (or an engineer) before a figure below drives a stamped drawing or a
safety-critical call.

Zones builds decks, fences, pergolas/canopies and retaining walls, not whole
houses, so this reference only covers the sections of NZS 3604 that actually
touch that work: site/soil, durability, wind zones, piles and footings, posts,
and timber decks. Full section list is in the PDF's TOC (16 sections + index);
sections not summarised here (walls, roof framing rafters/purlins, claddings,
linings, ceilings, 3 kPa floors, snow loading, composite lintels) are house-framing
detail Zones doesn't need.

## Contents

- [1. Site requirements (good ground)](#1-site-requirements-good-ground)
- [2. Durability / exposure zones](#2-durability--exposure-zones)
- [3. Wind zones](#3-wind-zones)
- [4. Piles and footings](#4-piles-and-footings)
- [5. Posts (pergolas, verandahs, canopies)](#5-posts-pergolas-verandahs-canopies)
- [6. Timber decks](#6-timber-decks)
- [7. Expansive soils](#7-expansive-soils)
- [Where this plugs into the existing tools](#where-this-plugs-into-the-existing-tools)

## 1. Site requirements (good ground)

Section 3. "Good ground" is the whole standard's foundation assumption; anything
that fails it needs specific engineering design (SED).

- Good ground = ultimate bearing capacity **≥ 300 kPa**, confirmed by a Scala
  penetrometer test or geotechnical report — no buried services, fill, organic
  topsoil, peat, soft/very soft clay or expansive clay under the footing.
- Minimum footing depth below cleared ground level: **200 mm**.
- Fill within 3 m of a foundation: max **0.6 m** deep above natural ground.
- Top-of-bank rule: a foundation must sit **0.6 m back** from the bank's crest;
  only applies where the bank's horizontal run (H) is ≤ 3 m and the slope beyond
  it is ≤ 5° for 10 m — steeper/taller banks are SED territory.
- "Cleared ground level" (not final landscaped level) is the depth datum
  specifically so later landscaping doesn't change what a footing depth means.
- Tree roots: a tree draws moisture from soil roughly out to a radius equal to
  its own height, which is the practical rule of thumb for keeping new
  structures clear of established trees on shrink-swell ground.

## 2. Durability / exposure zones

Section 4. Three exposure zones, driven mostly by distance to the coast, and
they set what grade of fixings and what concrete strength a job needs —
directly relevant since a lot of Zones' work is Auckland's coastal fringe.

| Zone | Definition |
|---|---|
| **B — Low** | Inland, little wind-blown sea-salt risk |
| **C — Medium** | Coastal-inland, moderate salt risk |
| **D — High** | **Within 500 m of the sea/harbour, or 100 m of a tidal estuary/sheltered inlet** (plus all offshore islands e.g. Waiheke, Great Barrier) |

Microclimate overrides that force SED regardless of zone: industrial/agri-chemical
contamination, or within 50 m of a geothermal hot spot (bore, mud pool, steam vent).

**Fixings/fasteners** (steel, excluding nails/screws — nails/screws have their
own, similar table):
- Zone B & C, sheltered: hot-dip galvanized steel is fine.
- Zone B & C, exposed (below the 45° line off a deck/roof/floor edge — see
  fig. 4.3(a)): Type 304 stainless.
- Zone D, any location (sheltered or exposed): **Type 304 stainless required**
  for all structural fixings.
- Timber pile connections within 600 mm of the ground: stainless regardless of
  zone.
- Timber treated with copper-based preservatives (ACQ, Copper Azole — i.e.
  most treated pine H3.2+): stainless in exposed/sheltered locations, minimum
  hot-dip galvanized elsewhere. Never bare mild steel against copper-treated
  timber.

**Concrete strength (28-day, MPa)** for reinforced concrete exposed to weather:
Zone B 17.5, Zone C 20, Zone D 25. Unreinforced mass concrete (footings) only
needs 10 MPa minimum everywhere.

**Timber decks specifically (4.3.5):** preservative treatment must follow
NZS 3602 (which is what actually assigns H-hazard classes like H3.2/H5 by end
use — NZS 3604 just requires compliance with it, the treatment schedule itself
lives in NZS 3602).

## 3. Wind zones

Section 5.2. This is what the feasibility tool's `wind_zone()` in
`engine.py` and `WIND_ZONES` in `layers.py` already surface from Council's GIS
layer — the standard's own determination procedure (for when there's no
mapped Council layer, or to sanity-check one) is:

1. Wind region: **A** (most of the country) or **W** (windier — parts of
   Wellington/Marlborough/the top of the South Island) — fig. 5.1.
2. Lee zone: sites in a mapped lee zone get bumped (see below).
3. Ground roughness: **Urban** (>10 obstructions/houses/3m+ trees per hectare)
   vs **Open** (pasture, beachfront, airfields — and a 500 m fringe either side
   of the urban/open boundary defaults to Open).
4. Site exposure: **Sheltered** (2+ rows of similar permanent obstructions all
   round) vs **Exposed** (steep sites, adjacent to playing fields, beaches,
   rivers, motorways, or a wind channel >100 m wide).
5. Topographic class **T1–T4**, from hill/escarpment height and "smoothed
   gradient" (rise over the lesser of 3× hill height or 500 m): Gentle <1:20,
   Low 1:20–1:10, Mild 1:10–1:6.7, Moderate 1:6.7–1:5, Steep >1:5 (max slope
   1:5). Crest zones escalate faster than outer zones; anywhere with <10 m of
   relief and gradient <1:20 is automatically T1.
6. Final zone from the region/roughness/topo-class/exposure matrix: **L
   (32 m/s) → M (37) → H (44) → VH (50) → EH (55) → SED** (SED = outside the
   standard's scope, needs an engineer).

**Lee zone escalation** (table 5.4 note) — a site mapped in a lee zone jumps a
band regardless of the matrix result: Low→High, Medium→Very High, High and
above→SED. Worth checking if a hillside site's Council-mapped wind zone looks
surprisingly mild.

**Decks are explicitly exempted from wind bracing** (5.2.9): *"Wind bracing
demand for decks may be ignored."* Only earthquake bracing applies to decks
(see §6 below) — useful when a deck's wind zone would otherwise suggest heavier
subfloor bracing than it actually needs.

Existing `layers.py` wind speeds (32/37/44/50 m/s for L/M/H/VH) match the
standard exactly; it doesn't currently carry an Extra High (55 m/s, SED) band
or the lee-zone escalation rule — both edge cases, but worth knowing they exist
if a site ever reads oddly.

## 4. Piles and footings

Section 6. Directly sizes deck/pergola subfloor structure.

**Timber piles:** must be treated to **H5** (NZS 3640) — this is a harder
requirement than most treated-pine framing (which is typically H3.2). A pile
cut after treatment needs the cut face brush-treated (creosote, zinc
naphthenate, TBTO/TBTN) and can't be re-cut for fixings within 150 mm of
finished ground level.

**Pile dimensions (minimum):** round timber 140 mm dia., square timber
125 mm sides, parallel concrete 200 mm sides/dia., concrete masonry 190 mm
sides.

**Pile height limits above cleared ground:** ordinary piles under jack studs
600 mm max; cantilever piles 1.2 m; anchor piles 600 mm to highest connection;
concrete/masonry braced or ordinary piles 1.5 m; **timber ordinary/braced piles
directly supporting a bearer: 3.0 m** (the tallest option, relevant for a
sloping-site deck).

**Footings (all piles except driven timber need one):**
- Minimum thickness: ordinary precast 100 mm, ordinary timber 200 mm, braced
  piles 450 mm, anchor piles 900 mm.
- Minimum depth below cleared ground: the footing's own thickness, but never
  less than 200 mm.
- Minimum embedment of the pile into its footing: 100 mm of concrete below the
  pile base.
- Minimum plan size for anchor/braced pile footings: 350×350 mm square or
  400 mm dia. round, even where the span table would allow smaller.
- Plan size otherwise scales with bearer/joist span and storeys supported
  (Table 6.1) — e.g. at a 2 m bearer span / 2 m joist span, a single-storey
  ordinary pile footing is 200 mm square (230 dia.), rising to 450 mm square
  (510 dia.) for a 3-storey load at the same spans. A deck (no storey load
  above) sits at the lightest end of this table.
- 24-hour cure minimum before full dead-load loading (48 hours if concrete
  temp is under 10°C or slump exceeds 60 mm).

## 5. Posts (pergolas, verandahs, canopies)

Section 9 — short, and squarely the section UGS's own build-methods doc
(`zones-qs\docs\ugs-build-methods.md` §7 and §11) flags as missing from the
aluminium-canopy engineering (Prendos PS1 covers the glazing bar/box only, not
posts/bearers/footings — "sized as per NZS3604/engineer"). **This section is
that missing piece for a timber post build-up** (not applicable to aluminium
kitset canopies, which fall under AS/NZS 1170.2 instead, per that doc's §11).

- Applies to isolated **100×100 mm posts up to 3 m long** supporting a beam
  that itself supports rafters or bearers — i.e. verandah/deck-roof/pergola
  posts, explicitly ("this clause gives guidance on support for verandahs or
  decks" — commentary to 9.2.1).
- **Uplift bracing is only required where the roof is open to wind on one, two
  adjacent, or three sides.** Medium and Low wind zone: **no uplift securement
  needed at all**, any roof area. That covers most of Auckland's ordinary
  suburban sites (Medium is "the ordinary case across most of Auckland" per
  `layers.py`).
- Where uplift bracing IS needed (High/VH/EH zones, or exposed sides), the
  standard gives two linked figures per wind zone and roof area supported: a
  minimum **concrete footing volume** (Table 9.1) and a minimum **post/beam
  connection capacity in kN** (Table 9.2). Both scale roughly linearly with
  roof area and step up sharply from High→VH→EH. Order-of-magnitude for a
  light roof, 8 m² supported: High needs 0.40 m³ of footing concrete and an
  11.8 kN connection; Very High needs 0.50 m³ and 15.8 kN; Extra High needs
  0.61 m³ and 19.2 kN. Heavy roofs need slightly less footing volume than
  light roofs for the same wind zone (more dead weight already resists uplift)
  but the pattern holds.
- Post/beam connection details (fig. 9.2–9.4) are steel brackets/straps rated
  6.8–25.5 kN depending on config (1 vs 2 bolts, bracket vs strap) — these are
  the concrete numbers behind "Lumberlok joist hangers or similar approved, to
  NZS 3604" in the UGS doc.

## 6. Timber decks

Section 7.4. Scope: decks off the main building, **≤ 3.0 m high** (cleared
ground to deck surface) — beyond that height it's a different (SED) problem.

- **Bracing exemption:** a deck bolted to the building on one or more sides,
  projecting **≤ 2 m**, needs no subfloor bracing at all. Beyond 2 m
  projection, it needs anchor/braced-pile bracing at **half** the demand of
  table 5.8's lightest cladding combination (light/light/light, 0° roof, for
  "subfloor structures") — i.e. an earthquake-only check, since wind bracing
  on decks is exempt outright (§3 above).
- **Decking thickness:** minimum **32 mm at 600 mm joist centres**, or
  **19 mm at 450 mm centres**.
- **Slip resistance:** any deck surface used as the main access to a building
  needs a wet slip resistance ≥ 0.4 — the standard's own commentary notes
  uncoated smooth timber only manages 0.20–0.35 (fails), profiled timber
  manages 0.45–0.60 (passes). Relevant if a client wants smooth-face decking
  on a main entry path.
- Joists/bearers/piles for decks are sized off the ordinary floor tables
  (7.1(b) for joists, 6.4(b) for bearers, section 6 for piles/footings), not a
  separate deck-specific span table.
- Cantilevered balustrade decks (glass or aluminium balustrade posts fixed
  through the deck edge) have detailed boundary-joist/nogging/strap
  requirements (7.4.1.3, figs 7.10a–c) — worth a look if a job spec's a
  frameless glass balustrade on a deck edge, since the joist build-up differs
  materially from a standard timber-rail deck.

## 7. Expansive soils

Section 17 — informative only, not mandatory clauses. Flags that clays with
liquid limit >50% and linear shrinkage >15% are excluded from "good ground"
and need classification under AS 2870 (classes S/M/H/E) with footings designed
to that standard's sections 3/5/6, not NZS 3604's own footing tables. Relevant
context for Auckland clay sites (West Auckland, parts of the North Shore) where
retaining walls or heavy paving sit on reactive clay — the standard itself says
this needs a geomechanical engineer or soils lab, not a table lookup.

## Where this plugs into the existing tools

- **`zones-feasibility\engine.py` / `layers.py`** already reads Council's
  mapped wind zone and reports it with plain-English consequences
  (`WIND_ZONES` dict). It does not currently read or report an **exposure
  zone** (coastal distance → fixing/concrete spec), which §2 above shows is a
  real, separate check — every Zones coastal job (Rothesay Bay is already a
  named test case in the tool's history) is a Zone D candidate on the
  500 m/100 m rule, which changes the fixings and concrete strength the S&F
  report should be flagging alongside wind zone. Worth raising with Lee as a
  possible addition, not made here since the feasibility tool's own README/
  safeguards should govern how a new finding gets added.
- **`zones-qs\docs\ugs-build-methods.md`** (§7, §11) already correctly
  identifies that NZS 3604 doesn't cover aluminium kitset canopy structural
  design (that's AS/NZS 1170.2 territory) but flags posts/bearers/footings as
  an open gap for the "build up from components" option. For a **timber**
  post/beam pergola build (not the aluminium kitset), §5 above (NZS 3604
  section 9) is a real, in-scope, free answer to that gap: the uplift
  footing-volume and connection-capacity tables. Also relevant to
  `screw-pile-enquiry.md`: NZS 3604's pile section only recognises timber and
  concrete/masonry piles, not screw piles, so any screw-pile hold-down rating
  has to come from the manufacturer's own engineering, not from this standard.
