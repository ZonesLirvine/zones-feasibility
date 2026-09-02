# Data sources and the layer registry

All keyless. Everything is public Auckland Council or LINZ data.

## Contents

- [The servers](#the-servers)
- [The `wm_` trap](#the-wm_-trap)
- [What is checked](#what-is-checked)
- [Position tolerance on buried services](#position-tolerance-on-buried-services)
- [Adding a layer](#adding-a-layer)
- [Map colours](#map-colours)
- [What is deliberately not covered](#what-is-deliberately-not-covered)

## The servers

| Source | Used for |
|---|---|
| Auckland Council Open Data (`services1.arcgis.com/n4yPwebTjJCmXB6W`), CC BY 4.0 | AUP overlays, hazards, zone |
| Council GeoMaps asset server (`mapspublic…/LiveMaps/UndergroundServices`) | every buried service |
| Council Address layer (`mapspublic`) | primary geocoder |
| Council Aerial Basemap, NZTM 2193 | the site map |
| LINZ NZ Primary Parcels | the property boundary and title |
| Manaaki Whenua FSL (`maps.scinfo.org.nz/fsl/wms`), CC BY 4.0 | the soil classification |
| OpenStreetMap Nominatim | fallback geocoder only |

## Soil, and why it is FSL rather than S-map

`soil.py` is the only non-ArcGIS source here. It is a WMS `GetFeatureInfo`
against Manaaki Whenua's Fundamental Soil Layer, keyless like everything else.

**It is not S-map, and must never be labelled as S-map to a client.** S-map is
the newer, finer map and it carries the fields anyone actually wants for a
drainage job: drainage class, clay content, rooting depth, depth to slowly
permeable layer. It has no public keyless API. Its own point service,
`smap.landcareresearch.co.nz/services/point_query/json`, is an internal
endpoint for the AngularJS app and returns HTTP 500 with a Java
NullPointerException when called directly, with WGS84 or NZTM. The documented
route is the LRIS Portal WFS, which needs a registered account and an API key.
Adding that is Lee's call, not a quiet dependency.

**FSL does not map built-up land.** It descends from the NZLRI, which
attributes no soil to urban areas. Measured across 18 real job addresses on
17 Aug 2026, 2 came back mapped: the fringe and greenfield suburbs (Massey,
Swanson, Henderson, The Gardens, Karekare) answer, and established Auckland
Central suburbs do not. Widening the query box does not help, tested to 0.05
degrees. This is why `not_mapped` is a distinct status with wording that says
the mapping has a gap, rather than anything about the site.

MapServer returns HTTP 200 with an XML `ServiceExceptionReport` body when it
fails, the same shape of trap as the retired Council endpoint that answered 200
with a blank IIS page, so `soil.lookup` inspects the body rather than trusting
the status code. Three statuses, and `error` is never the same as
`not_mapped`. `soil.probe()` is wired into `tools/check_layers.py` and queries
a point with a known answer.

Soil is deliberately **not** a `LAYERS` entry and never reaches `findings`. A
soil classification is not a pass or a fail, and putting it there would move
the "40 checked, 9 flagged" counts that the rest of the report is built on.

A retired Council endpoint, `mapspublictest.aucklandcouncil.govt.nz`, answers
HTTP 200 with a blank IIS page. It looks alive and is not. That is why the
health check tests for a non-zero feature count and the expected fields rather
than just a response.

## The `wm_` trap

**Read this before adding or changing any service layer.**

Council publishes the pipe networks twice. The open data portal carries layers
prefixed `wm_` which look like the network and are watershed models, roughly a
tenth of the real asset count:

| Layer | Open data (`wm_`) | GeoMaps asset server |
|---|---|---|
| Wastewater | 7,825 | 528,377 |
| Stormwater | 33,957 (`wm_Stormwater_Assets`) | 325,264 |

528,377 wastewater segments is about 7,900 km, which matches Auckland's real
network length. 7,825 does not.

This was not theoretical. Wired to `wm_Wastewater_Pipes`, the tool told a
Henderson job the nearest wastewater main was 200 m away while two live mains
ran within a metre of the boundary. Lee caught it from local knowledge.

So: buried services come from `UNDERGROUND_SERVICES` in `layers.py`, never from
the open data portal. The AUP overlays are fine on open data, they are not
modelled subsets.

Note the open data `Stormwater_Pipe` layer (324,652) *is* complete and matches
the asset server. It is only the `wm_` prefixed ones that are subsets.

## What is checked

40 layers in five groups, ordered by what costs the client time or money.
`layers.py` is the registry and holds the client-facing wording for each.

| Group | Covers |
|---|---|
| Consent | Significant Ecological Areas, Special Character, Mana Whenua sites, Historic Heritage, Notable Trees, Notable Group of Trees, Natural Stream Management, natural inland wetlands, designations |
| Design | Outstanding Natural Features / Landscapes / Character, volcanic viewshafts, Ridgeline Protection, National Grid Corridor, vehicle access restrictions, height variation controls |
| Hazard | Flood plains, flood prone, flood sensitive, overland flow paths, shallow and large-scale landslide, coastal inundation, coastal erosion across four climate scenarios |
| Services | Stormwater pipes and watercourses, wastewater mains (local and transmission), water mains (local and transmission), other utility pipework, gas pipelines, fuel pipelines, septic tanks |
| Background | Quarry buffer |

Plus base zone with its AUP standards, LINZ title details, and the soil
classification described above, none of which are findings and none of which
change the counts.

Gas and fuel are **grouped**: `service` on those entries is a list, because
Council splits them across layers that mean one sentence to a client.
High-pressure gas, gas transmission and medium-pressure gas are three layers and
one finding. Five "clear" rows for jet fuel on a suburban garden would train the
reader to skip the section.

### Zone standards

Loaded and verified for five residential zones from the operative AUP chapters,
with clause references against every value. H1 and H2 carry absolute caps as
well as percentages and the tool applies whichever is smaller.

**H6 Terrace Housing and Apartment Buildings is deliberately empty.** Its
impervious, coverage and landscaped standards are pending insertion under Plan
Change 120, so the chapter states no figures. The report says so and refers to a
planner rather than guessing.

**Naming trap:** Council's layer says "Apartment **Building** Zone" (singular)
while the AUP chapter says "Buildings". Both spellings are carried in
`standards.py`, and `tools/check_layers.py` verifies every key still exists in
Council's domain. A mismatch here is invisible at runtime.

## Position tolerance on buried services

Service layers carry `tolerance_m`, which widens the on-site test by a couple of
metres. Council's asset geometry and LINZ's parcel geometry come from different
survey lineages and disagree by about a metre. A main laid along a boundary
reads as on or off the property depending on whose line you believe.

For a planning overlay that does not matter. For something a digger might go
through, "just outside the boundary" is not a distinction worth relying on. At
the Henderson job this is what turned 0 hits into 2.

## Adding a layer

1. Add a `dict` to `LAYERS` in `layers.py`. `service` is either a service name
   on the open data portal, a full URL (for GeoMaps), or a list of either.
2. Write the `plain` text as a sentence to a homeowner about what it means for
   their project, not a description of the overlay.
3. Add a style to `STYLES` in `mapper.py` so it draws on the map. Anything
   styled draws whether or not it is in `DRAW_ORDER`; that list only controls
   stacking. This is deliberate, because a layer flagged in the findings table
   and silently missing from the map beside it is worse than no map.
4. Run `python tools/check_layers.py` to confirm it answers and holds features.
5. Run `python tools/check_council_colours.py` to see how Council draws it.

## Map colours

Buried services follow the GeoMaps symbology, which is the view Lee actually
works from: **wastewater red, potable water blue, stormwater green**, other
owners' pipework light purple. Read colours off GeoMaps, not the open data
portal; the two servers symbolise the same assets differently and only one of
them is what anyone looks at.

`tools/check_council_colours.py` reports drift against Council and prints their
current values for the layers we deliberately differ on. Updating is by hand,
because judging whether a colour survives over a dark aerial is not something to
automate. The deliberate departures and their reasons are in the tool's
`DELIBERATE` map and in the `STYLES` comments.

Area overlays are hatched rather than filled, because solid fills stack and turn
the photo to mud. The SEA uses small crosses rather than strokes: every other
pattern is made of lines, so two hatches can only differ by angle and colour,
and a diagonal mesh over an orthogonal one just reads as mesh.

## What is deliberately not covered

Say these plainly rather than half-covering them:

- **Contaminated land / HAIL.** Not in public GIS at all, it is a LIM record.
  `wm_Contaminant_Sources` carries the same `wm_` prefix as the layer that
  misled us and should be treated with the same suspicion.
- **Covenants, consent notices and easements.** No public API. The report
  recommends a title search.
- **Private laterals**, water and wastewater. Nowhere public. beforeUdig.
- **Power and fibre.** Not public. beforeUdig is a manual process by decision:
  asset owners take two business days, plan validity varies by owner, some
  charge, and a silent auto-send failure leaves someone digging on plans nobody
  ordered.
- **BRANZ wind, corrosion, earthquake and climate zones.** Ruled out and not to
  be revisited: build spec rather than planning constraint, display-only tiles
  with no query capability, and licence terms that are not open. For Auckland
  the fields carry almost no information anyway.
