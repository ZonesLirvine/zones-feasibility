"""
Soil lookup for the Zones site feasibility check.

Source is Manaaki Whenua Landcare Research's Fundamental Soil Layer (FSL),
New Zealand Soil Classification, served keyless over WMS GetFeatureInfo at
maps.scinfo.org.nz. Same no-account, no-API-key principle as every other
source in this tool.

WHY THIS IS FSL AND NOT S-MAP
-----------------------------
S-map is the newer, finer national soil map and it is the one you actually
want: it carries drainage class, clay content, rooting depth and depth to
slowly permeable layer. It has no public keyless API.

  - Its own point service, /services/point_query/json on
    smap.landcareresearch.co.nz, is an internal endpoint for the AngularJS
    app. Called directly it routes but returns HTTP 500 with a Java
    NullPointerException, with or without NZTM coordinates. Probed 17 Aug 2026.
  - The documented route is the LRIS Portal WFS, which needs a registered
    account and an API key. That breaks the "no keys, nothing to configure"
    design of this tool and would need Lee's decision, not a quiet dependency.

FSL is the keyless one. It is mapped at roughly 1:50,000, which is a regional
read rather than a statement about one section, and the report says so. Do not
label FSL output as S-map anywhere a client can see it.

If S-map ever needs to be added properly, it is an API key and a settings file,
not a drop-in for this module.

COVERAGE: READ THIS BEFORE EXPECTING A RESULT
---------------------------------------------
FSL does not map built-up land. It descends from the NZLRI, which classifies
urban areas as town and attributes no soil to them, so established suburbs
come back not_mapped.

Measured across 18 real Zones job addresses on 17 Aug 2026, 2 were mapped:

    mapped        Massey (Ultic / Albic), The Gardens (Ultic / Yellow),
                  and separately Swanson, Henderson, Karekare
    not mapped    Stonefields, Waterview, Morningside, Greenlane, Remuera,
                  Mt Roskill, Mt Albert, New Windsor, Mt Eden, Sandringham,
                  Birkenhead, Avondale, Titirangi, Westmere, Pakuranga,
                  Birkdale, Herne Bay, Blockhouse Bay, Tindalls Beach

So this earns its keep on fringe and greenfield jobs and stays quiet on most
of Auckland Central. That is a real limit, not a bug, and it is why the
not_mapped wording says the mapping has a gap rather than implying anything
about the site. Widening the bbox does not help; it was tested to 0.05 degrees
at Herne Bay and there is genuinely no polygon there.
"""

import re
import urllib.parse
import urllib.request

FSL_WMS = "https://maps.scinfo.org.nz/fsl/wms"
FSL_LAYER = "fsl_nzsc_groups"

SCALE_NOTE = ("Mapped at approximately 1:50,000, so this describes the soil "
              "across the area rather than this section specifically. On a "
              "recent subdivision the top half metre is often engineered fill "
              "that no soil map has seen. Confirm with a test hole.")

ATTRIBUTION = ("Soil classification from Manaaki Whenua Landcare Research, "
               "Fundamental Soil Layer, licensed for re-use under CC BY 4.0.")

# What the classification means for a landscaping build, keyed on words that
# appear in the NZSC group or order name. Deliberately short: Manaaki Whenua's
# own group and order descriptions are already plain English and are reported
# verbatim, so this only adds the bit they do not cover, which is what it does
# to a drainage or planting design.
#
# Anything not listed here gets no Zones sentence at all. A soil we have not
# thought about is better left described in Manaaki Whenua's words than given
# a confident sentence we invented.
_IMPLICATIONS = [
    ("impeded",
     "A layer like this stops water draining down through the profile, so "
     "water perches above it and the ground stays wet long after the rain "
     "stops. Subsoil drainage and a genuine soil rebuild matter more here "
     "than topsoil depth does, and soakage pits are unlikely to work."),
    ("perch-gley",
     "Water perches on a dense layer and sits, so expect seasonal "
     "waterlogging. Drainage needs a piped outfall rather than soakage."),
    ("gley",
     "Poorly drained and seasonally waterlogged by nature, not just by "
     "compaction. Assume drainage is required rather than optional, and "
     "choose planting that tolerates wet feet."),
    ("podzol",
     "Strongly leached, often with a hard pan and poor drainage. Expect low "
     "fertility and check for a cemented layer when digging."),
    ("pallic",
     "Dense, slowly permeable subsoil that is wet in winter and hard in "
     "summer. Cultivation timing matters, working it wet does lasting damage."),
    ("ultic",
     "Clay-rich, slowly permeable subsoil prone to waterlogging, and "
     "structurally fragile once worked wet."),
    ("sandy",
     "Free draining, so drainage is rarely the problem here. Watch water "
     "holding and nutrient retention instead."),
    ("allophanic",
     "Allophanic soils dig easily and hold structure well, but they smear and "
     "lose that structure if worked wet. Rip and cultivate dry."),
]


def _implication(group, order):
    """Zones' read on what the classification does to a build, or None."""
    hay = ("%s %s" % (group or "", order or "")).lower()
    for key, text in _IMPLICATIONS:
        if key in hay:
            return text
    return None


def _parse_plain(body):
    """Attributes out of a MapServer text/plain GetFeatureInfo response."""
    attrs = {}
    for m in re.finditer(r"^\s*(\w+)\s*=\s*'(.*)'\s*$", body, re.M):
        attrs[m.group(1)] = m.group(2).strip()
    return attrs


def lookup(lon, lat, timeout=25):
    """
    NZ Soil Classification at a point, in WGS84.

    Returns a dict that always carries a status, never a bare None, because a
    lookup that failed and a location genuinely off the soil map have to read
    differently in the report. Statuses:

        ok          classification returned
        not_mapped  the service answered and there is no soil polygon here
        error       the service could not answer. NEVER the same as not_mapped

    Called with the parcel centroid, in the same 4326 the rest of the engine
    works in, so this costs no extra reprojection round trip.
    """
    d = 0.0005                                    # ~50 m box, point is centre
    params = {
        "service": "WMS", "version": "1.1.1", "request": "GetFeatureInfo",
        "layers": FSL_LAYER, "query_layers": FSL_LAYER, "srs": "EPSG:4326",
        "bbox": "%f,%f,%f,%f" % (lon - d, lat - d, lon + d, lat + d),
        "width": "101", "height": "101", "x": "50", "y": "50",
        "info_format": "text/plain", "feature_count": "1",
    }
    url = FSL_WMS + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "zones-feasibility"})

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "replace")
    except Exception as exc:                      # noqa: BLE001
        return dict(status="error", error=str(exc)[:200], source="FSL")

    # MapServer answers HTTP 200 with an XML ServiceExceptionReport when it
    # fails, so a 200 is not evidence of an answer. Same shape of trap as the
    # retired Council endpoint that returned a blank IIS page.
    if "ServiceException" in body:
        detail = re.search(r"<ServiceException[^>]*>(.*?)</ServiceException>",
                           body, re.S)
        return dict(status="error", source="FSL",
                    error=(detail.group(1).strip()[:200] if detail
                           else "service exception"))

    attrs = _parse_plain(body)
    if not attrs or not attrs.get("soil_order"):
        return dict(status="not_mapped", source="FSL")

    order = attrs.get("soil_order") or None
    group = attrs.get("soil_group") or None

    return dict(
        status="ok",
        source="FSL",
        code=attrs.get("nzsc_group") or None,
        order=order,
        order_description=attrs.get("soil_order_description") or None,
        group=group,
        group_description=attrs.get("soil_group_description") or None,
        means=_implication(group, order),
        scale_note=SCALE_NOTE,
    )


def headline(soil):
    """One-line summary for a heading, or None."""
    if not soil or soil.get("status") != "ok":
        return None
    if soil.get("group") and soil.get("order"):
        return "%s %s Soil" % (soil["group"], soil["order"])
    return soil.get("order") or soil.get("group")


def probe():
    """
    Health check. Returns (status, detail) in the same shape as
    engine.probe_layer, so tools/check_layers.py can treat it like any layer.

    Probes a fixed point with a known answer rather than just asking whether
    the host responds, because the failure that matters is the service
    answering cleanly with nothing in it.
    """
    got = lookup(174.59396887997767, -36.85609362689236)   # 6E Crows Road
    if got.get("status") == "error":
        return "FAIL", got.get("error", "error")
    if got.get("status") != "ok":
        return "FAIL", "no soil returned at a point known to be mapped"
    if not got.get("order"):
        return "FAIL", "answered without a soil order"
    return "OK", "%s / %s" % (got.get("order"), got.get("group"))
