"""
Layer registry for the Zones site feasibility check.

Every URL here was resolved from Auckland Council's open data catalogue
(data-aucklandcouncil.opendata.arcgis.com, DCAT feed) on 29 Jul 2026 and
confirmed live. Council data is CC BY 4.0 and requires attribution.

Do not hand-edit URLs. If a layer moves, re-run tools/refresh_layers.py,
which rebuilds this registry from the catalogue.
"""

AC_BASE = "https://services1.arcgis.com/n4yPwebTjJCmXB6W/arcgis/rest/services"

# Council's GeoMaps server, which publishes the actual buried asset networks.
# The open data portal only carries the watershed-model subsets of these: its
# wastewater layer holds 7,825 features against 528,377 here, and its
# stormwater 324,652 against a comparable full network. 528,377 segments is
# about 7,900 km of wastewater, which matches Auckland's real network length,
# so this is reticulation rather than trunk mains. Verified 31 Jul 2026.
UNDERGROUND_SERVICES = ("https://mapspublic.aucklandcouncil.govt.nz/arcgis/"
                        "rest/services/LiveMaps/UndergroundServices/MapServer")

ATTRIBUTION = (
    "Contains data sourced from Auckland Council, Toitū Te Whenua LINZ and "
    "Manaaki Whenua Landcare Research, licensed for re-use under CC BY 4.0. "
    "Data is indicative only. Verify against the official Auckland Council "
    "GeoMaps viewer before any design or construction decision. This report is "
    "not a substitute for professional planning advice."
)

# category: how the finding is grouped and ordered in the client-facing output.
#   consent    - most likely to cost the client time or money, shown first
#   design     - constrains where things can go
#   hazard     - site risk affecting engineering and drainage
#   services   - dig risk
#   background - context, rarely actionable on its own
#
# plain: client-facing sentence used when the layer IS present on the site.
#        Written for a homeowner, not a planner.
# clause: AUP reference, rendered as small print to evidence rigour.
# nearby: whether a within-200m check is meaningful for this layer.

LAYERS = [
    # ---------------------------------------------------------------- consent
    dict(
        key="sea", name="Significant Ecological Areas Overlay",
        service="Significant_Ecological_Areas_Overlay",
        category="consent", nearby=True, clause="D9.4.1-D9.4.2",
        plain="Part of your site is a Significant Ecological Area. Any earthworks, "
              "vegetation clearance or structures inside it, and within 10 m of a "
              "terrestrial or 5 m of an aquatic area, need resource consent. Planting "
              "beds, retaining and fence lines will need to be set out around it.",
    ),
    dict(
        key="special_character", name="Special Character Areas Overlay",
        service="Special_Character_Areas_Overlay_Residential_and_Business",
        category="consent", nearby=True, clause="D18",
        plain="Your property sits in a Special Character Area. Front fences, walls, "
              "gates and driveway surfaces visible from the street are controlled here, "
              "and removing existing features can need consent. This shapes what the "
              "front of the design can look like.",
    ),
    dict(
        key="mana_whenua", name="Sites and Places of Significance to Mana Whenua",
        service="Sites_and_Places_of_Significance_to_Mana_Whenua_Overlay",
        category="consent", nearby=True, clause="D21",
        plain="Your site is identified as significant to mana whenua. Earthworks, "
              "including post holes and wall foundations, trigger consent and "
              "consultation. This needs to be factored into the programme early.",
    ),
    dict(
        key="heritage", name="Historic Heritage Overlay (Extent of Place)",
        service="Historic_Heritage_Overlay_Extent_of_Place",
        category="consent", nearby=True, clause="D17",
        plain="Your property falls within a historic heritage place. Earthworks and "
              "new structures in the grounds are controlled, not just work on the "
              "building itself.",
    ),
    dict(
        key="notable_trees", name="Notable Trees Overlay",
        service="Notable_Trees_Overlay",
        category="consent", nearby=True, clause="D13",
        plain="There is a scheduled notable tree on or beside your site. Work inside "
              "its protected root zone, including paving, trenching and post holes, "
              "needs consent and usually an arborist report.",
    ),
    dict(
        key="natural_stream", name="Natural Stream Management Areas Overlay",
        service="Natural_Stream_Management_Areas_Overlay",
        category="consent", nearby=True, clause="D12",
        plain="A managed natural stream runs on or near your site. Works near the "
              "stream edge are controlled and a riparian setback applies.",
    ),

    # ----------------------------------------------------------------- design
    dict(
        key="onf", name="Outstanding Natural Features Overlay",
        service="Outstanding_Natural_Features_Overlay",
        category="design", nearby=False, clause="D10",
        plain="Your site includes an outstanding natural feature. Earthworks and "
              "structures around it are restricted.",
    ),
    dict(
        key="onl", name="Outstanding Natural Landscapes Overlay",
        service="Outstanding_Natural_Landscapes_Overlay",
        category="design", nearby=False, clause="D11",
        plain="Your site is in an outstanding natural landscape. Structures are "
              "assessed on how visible they are from public places.",
    ),
    dict(
        key="onc", name="Outstanding Natural Character Overlay",
        service="Outstanding_Natural_Character_Overlay",
        category="design", nearby=False, clause="D10",
        plain="Your site is in an area of outstanding natural character, which is "
              "assessed in the coastal environment.",
    ),
    dict(
        key="viewshaft_regional",
        name="Regionally Significant Volcanic Viewshafts",
        service="Regionally_Significant_Volcanic_Viewshafts_And_Height_Sensitive_Areas_Overlay",
        category="design", nearby=False, clause="D14",
        plain="A protected volcanic viewshaft crosses your site. This caps the height "
              "of anything tall, so pergolas, louvre roofs and shade sails need "
              "checking against it.",
    ),
    dict(
        key="viewshaft_local", name="Locally Significant Volcanic Viewshafts",
        service="Locally_Significant_Volcanic_Viewshafts_Overlay",
        category="design", nearby=False, clause="D14",
        plain="A local volcanic viewshaft crosses your site, which limits the height "
              "of tall structures.",
    ),
    dict(
        key="ridgeline", name="Ridgeline Protection Overlay",
        service="Ridgeline_Protection_Overlay",
        category="design", nearby=False, clause="D15",
        plain="Your site is on a protected ridgeline, so the height and silhouette of "
              "structures is controlled.",
    ),
    dict(
        key="national_grid", name="National Grid Corridor Overlay",
        service="National_Grid_Corridor_Overlay",
        category="design", nearby=True, clause="E26",
        plain="Your site is under or beside a national grid transmission corridor. "
              "There are strict limits on structures, earthworks and tree heights "
              "near the lines. This is a hard constraint, not a preference.",
    ),
    dict(
        key="quarry_buffer", name="Quarry Buffer Area Overlay",
        service="Quarry_Buffer_Area_Overlay",
        category="background", nearby=False, clause="D17",
        plain="Your site is within a quarry buffer area.",
    ),

    # ----------------------------------------------------------------- hazard
    dict(
        key="flood_plain", name="Flood Plains",
        service="Flood_Plains", category="hazard", nearby=True, clause="E36",
        plain="Part of your site is mapped as flood plain. Levels, drainage and any "
              "retaining need to be designed around it, and filling or building in it "
              "is controlled.",
    ),
    dict(
        key="flood_prone", name="Flood Prone Areas",
        service="Flood_Prone_Areas", category="hazard", nearby=True, clause="E36",
        plain="Part of your site is a flood prone area, meaning water ponds here in "
              "heavy rain. It affects where paving and planting can go.",
    ),
    dict(
        key="flood_sensitive", name="Flood Sensitive Areas",
        service="Flood_Sensitive_Areas", category="hazard", nearby=True, clause="E36",
        plain="Part of your site is flood sensitive, so changes to ground levels and "
              "hard surfaces need care.",
    ),
    dict(
        key="overland_flow", name="Overland Flow Paths",
        service="Overland_Flow_Paths", category="hazard", nearby=True, clause="E36",
        plain="An overland flow path crosses your site. This is the route stormwater "
              "takes in a big downpour, and it must not be blocked by walls, raised "
              "beds or paving. It is one of the most common reasons a landscape design "
              "has to be reworked, so it is worth designing around from the start.",
    ),
    dict(
        key="landslide_shallow", name="Shallow Landslide Susceptibility",
        service="Shallow_Landslide_Susceptibility",
        category="hazard", nearby=False, clause="E36",
        plain="Your site is mapped as susceptible to shallow land movement. Retaining "
              "walls here are likely to need engineering input rather than a standard "
              "detail.",
    ),
    dict(
        key="landslide_large", name="Large Scale Landslide Susceptibility",
        service="Large_Scale_Landslide_Susceptibility",
        category="hazard", nearby=False, clause="E36",
        plain="Your site is mapped as susceptible to large scale land movement. Expect "
              "a geotechnical assessment to be required for any retaining.",
    ),
    dict(
        key="coastal_inundation", name="Coastal Inundation 1% AEP +1m Control",
        service="Coastal_Inundation_1_per_cent_AEP_Plus_1m_Control",
        category="hazard", nearby=True, clause="E36",
        plain="Your site is in the coastal inundation control area, which allows for "
              "sea level rise. Ground levels and structures near the boundary are "
              "assessed against it.",
    ),

    # ASCIE coastal erosion, one layer per climate scenario.
    dict(key="ascie_2050", name="Coastal erosion susceptibility 2050 (RCP 8.5)",
         service="Susceptible_Areas_ASCIE_2050_RCP85_Regional",
         category="hazard", nearby=False, clause="E36", scenario="2050 RCP 8.5",
         plain="Your site falls inside the mapped coastal erosion extent for 2050."),
    dict(key="ascie_2080", name="Coastal erosion susceptibility 2080 (RCP 8.5)",
         service="Susceptible_Areas_ASCIE_2080_RCP85_Regional",
         category="hazard", nearby=False, clause="E36", scenario="2080 RCP 8.5",
         plain="Your site falls inside the mapped coastal erosion extent for 2080."),
    dict(key="ascie_2130", name="Coastal erosion susceptibility 2130 (RCP 8.5)",
         service="Susceptible_Areas_ASCIE_2130_RCP85_Regional",
         category="hazard", nearby=False, clause="E36", scenario="2130 RCP 8.5",
         plain="Your site falls inside the mapped coastal erosion extent for 2130."),
    dict(key="ascie_2130p", name="Coastal erosion susceptibility 2130 (RCP 8.5+)",
         service="Susceptible_Areas_ASCIE_2130_RCP85plus_Regional",
         category="hazard", nearby=False, clause="E36", scenario="2130 RCP 8.5+",
         plain="Your site falls inside the mapped coastal erosion extent for 2130 "
               "under the highest scenario."),

    # --------------------------------------------------------------- services
    dict(
        key="stormwater_pipe", name="Stormwater pipe network",
        service="Stormwater_Pipe", category="services", nearby=True,
        plain="There is public stormwater pipework on or beside your site.",
    ),
    dict(
        key="stormwater_watercourse", name="Stormwater watercourse",
        service="Stormwater_Watercourse", category="services", nearby=True,
        plain="There is a mapped watercourse on or beside your site.",
    ),
    dict(
        key="wastewater_pipe", name="Wastewater network",
        service=UNDERGROUND_SERVICES + "/5",     # Wastewater Pipe (Local)
        category="services",
        # This was first wired to the open data layer wm_Wastewater_Pipes,
        # which looked right and was not: 7,825 features region-wide, a
        # watershed-model trunk network. At a Henderson site it reported the
        # nearest main 200 m away while two live mains ran within a metre of
        # the boundary. The asset network here holds 528,377 segments and finds
        # them. Do not go back to the open data layer for buried services.
        #
        # Public mains are now complete, but private laterals are on nearly
        # every property and appear in no public record at all, so a nil result
        # still is not a clear result. partial=True keeps it out of the "also
        # checked, nothing found" list and puts the beforeUdig step in front of
        # Lee instead.
        partial=True,
        # Assets and parcel boundaries come from different survey lineages and
        # disagree by a metre or so. A main laid along a boundary lands just
        # inside or just outside depending on whose geometry you trust, and
        # "just outside" is not a distinction anyone should dig on.
        tolerance_m=2,
        plain="There is a public wastewater main on or right beside your site. "
              "You cannot build over a public main, and working near one needs "
              "Watercare approval, so it constrains where structures, "
              "retaining and deep planting can go. Confirm its exact position "
              "and depth before the design is finalised.",
        absent="No public wastewater main is mapped on or beside this site. "
               "Private laterals are not held in any public record and almost "
               "every property has one, so confirm with a beforeUdig request "
               "before any excavation.",
    ),
    dict(
        key="wastewater_transmission", name="Wastewater transmission main",
        service=UNDERGROUND_SERVICES + "/12",    # Wastewater Pipe (Transmission)
        category="services", nearby=True, tolerance_m=2,
        # Rare, and a hard constraint wherever it turns up: these carry
        # corridors that nothing may be built in.
        plain="A wastewater transmission main runs on or beside your site. "
              "These are major Watercare assets with a protected corridor "
              "around them, and that corridor controls what can be built and "
              "where. Watercare must be engaged early.",
    ),
    dict(
        key="water_pipe", name="Water supply network",
        service=UNDERGROUND_SERVICES + "/52",    # Water Pipe (Local)
        category="services", tolerance_m=2, partial=True,
        # 745,929 segments. Same treatment as wastewater and for the same
        # reason: public mains are complete, the private connection from the
        # toby to the house is not mapped anywhere.
        plain="There is a public water main on or right beside your site. You "
              "cannot build over it, and a strike floods the site immediately, "
              "so its position needs confirming before any excavation or "
              "retaining is set out.",
        absent="No public water main is mapped on or beside this site. The "
               "private connection from the toby to the house is not in any "
               "public record, so confirm with a beforeUdig request before any "
               "excavation.",
    ),
    dict(
        key="water_transmission", name="Water transmission main",
        service=UNDERGROUND_SERVICES + "/61",    # Water Pipe (Transmission)
        category="services", nearby=True, tolerance_m=2,
        plain="A water transmission main runs on or beside your site. These "
              "are major Watercare assets with a protected corridor that "
              "controls what can be built and where. Watercare must be "
              "engaged early.",
    ),
    dict(
        key="other_utility_pipe", name="Other utility pipework",
        service=UNDERGROUND_SERVICES + "/73",    # Non Watercare Pipe
        category="services", nearby=True, tolerance_m=2,
        plain="There is pipework on or beside your site belonging to an asset "
              "owner other than Watercare. Ownership and depth need "
              "confirming before you dig.",
    ),
    dict(
        key="gas_pipeline", name="Gas pipeline",
        # High pressure, transmission and medium pressure. Three layers, one
        # sentence to a client.
        service=[UNDERGROUND_SERVICES + "/89", UNDERGROUND_SERVICES + "/90",
                 UNDERGROUND_SERVICES + "/88"],
        category="services", nearby=True, tolerance_m=2,
        plain="A gas pipeline runs on or beside your site. This is a hard "
              "constraint, not a preference: there are strict limits on "
              "excavation, structures and planting depth near it, and the "
              "asset owner must be engaged before any work starts.",
    ),
    dict(
        key="fuel_pipeline", name="Fuel pipeline",
        # RNZ liquid fuels Marsden to Wiri, LPG, and the Jet A1 line to the
        # airport. Rare, and the highest-consequence thing you can hit.
        service=[UNDERGROUND_SERVICES + "/91", UNDERGROUND_SERVICES + "/93",
                 UNDERGROUND_SERVICES + "/92"],
        category="services", nearby=True, tolerance_m=2,
        plain="A fuel pipeline runs on or beside your site. Nothing may be "
              "excavated, built or deep-planted near it without the pipeline "
              "operator's written approval. Treat this as a stop-work "
              "constraint until it is resolved.",
    ),
    dict(
        key="septic_tank", name="Septic tank",
        service=UNDERGROUND_SERVICES + "/18",
        category="services", nearby=True, tolerance_m=2,
        plain="A septic tank or on-site wastewater system is recorded on or "
              "beside your site. Its tank, field and access all need to be "
              "kept clear, which usually controls where paving and structures "
              "can go.",
    ),
]

# Added 2 Aug 2026 after an audit of what a landscaping job actually runs into.
# These are the AUP overlays that were missing rather than buried services.
LAYERS += [
    dict(
        key="notable_tree_group", name="Notable Group of Trees Overlay",
        service="Notable_Group_of_Trees_Overlay",
        category="consent", nearby=True, clause="D13",
        # Separate overlay from Notable_Trees_Overlay. We checked one and not
        # the other, so a protected grove read as clear.
        plain="A scheduled group of notable trees stands on or beside your "
              "site. Work inside the protected root zone, including paving, "
              "trenching and post holes, needs consent and usually an "
              "arborist report.",
    ),
    dict(
        key="vehicle_access", name="Vehicle Access Restriction Control",
        service="Vehicle_Access_Restriction_Control",
        category="design", nearby=False, clause="E27",
        plain="Your frontage carries a vehicle access restriction, which "
              "controls where a driveway or vehicle crossing may go, and "
              "sometimes prevents one entirely. Confirm this before any "
              "driveway or parking layout is designed.",
    ),
    dict(
        key="designation", name="Designation",
        service="Designation", category="consent", nearby=True, clause="K",
        plain="Part of your site is designated for a public work. The "
              "requiring authority's rules override the ordinary zone for "
              "that land, so what you can build there has to be checked with "
              "them, not just with Council.",
    ),
    dict(
        key="wetland", name="Natural inland wetland",
        service="NaturalInlandWetlandsConsultationVersion",
        category="consent", nearby=True, clause="E3",
        plain="A natural inland wetland is mapped on or beside your site. "
              "Earthworks, drainage and vegetation clearance within it and "
              "its setback are tightly controlled under the national "
              "freshwater rules, which sit above the Unitary Plan.",
    ),
    dict(
        key="height_variation", name="Height Variation Control",
        service="Height_Variation_Control",
        category="design", nearby=False, clause="D19",
        plain="A height variation control applies to your site, changing the "
              "standard height limit for the zone. Anything tall, a pergola, "
              "louvre roof or shade sail, needs checking against it rather "
              "than against the zone standard.",
    ),
]

# Base zone is handled separately: it is always present and drives the
# standards table rather than being a yes/no flag.
ZONE_LAYER = dict(key="zone", name="Unitary Plan Base Zone",
                  service="Unitary_Plan_Base_Zone")

COASTLINE_LAYER = dict(key="coastline", name="Indicative Coastline",
                       service="Indicative_Coastline")

CATEGORY_ORDER = ["consent", "design", "hazard", "services", "background"]

CATEGORY_TITLES = {
    "consent": "Consent requirements identified",
    "design": "Design constraints on the site",
    "hazard": "Site hazards to design around",
    "services": "Services located on or near the site",
    "background": "Other site context",
}


def url_for(service, layer_index=0):
    """
    Resolve a registry entry to a queryable layer URL.

    Most layers are FeatureServers on Council's open data org, named by
    service. A few live on Council's GeoMaps server instead, which is where the
    real asset networks are published, and those entries carry a full URL. See
    UNDERGROUND_SERVICES below.
    """
    if service.startswith("http"):
        return service
    return "%s/%s/FeatureServer/%d" % (AC_BASE, service, layer_index)
