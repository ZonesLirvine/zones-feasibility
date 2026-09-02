"""
Query engine for the Zones site feasibility check.

Two design rules, both driven by this being a client-facing document:

1. A layer that fails to answer is recorded as "error", never as "not
   affected". Silently treating a dead endpoint as a clear result is the
   failure mode that puts a wrong all-clear in front of a client.

2. Checks run against the whole parcel polygon, not a single point. Verified
   on 29 Jul 2026: a point-based check at 985 Whangaparaoa Road missed the
   Significant Ecological Area and all four coastal erosion extents that the
   parcel genuinely sits in. Point checking produces false all-clears, which
   is the worst possible error for this document.
"""

import json
import math
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import layers as L
import soil as SOIL
import standards as S

USER_AGENT = "ZonesLandscaping-SiteFeasibility/0.1 (lee.irvine@zones.co.nz)"
TIMEOUT = 40

# LINZ publish NZ Primary Parcels on ArcGIS Online under their own account,
# no API key required. Verified against the sample report: returns appellation,
# title number and survey area matching LINZ Landonline exactly.
PARCEL_URL = ("https://services.arcgis.com/xdsHIIxuCWByZiCB/arcgis/rest/"
              "services/LINZ_NZ_Primary_Parcels/FeatureServer/0")

# Auckland only. Every data source here is Auckland-only, so a lookup outside
# this box is a typo or an out-of-area enquiry.
AUCKLAND_BBOX = dict(min_lon=174.0, max_lon=175.6, min_lat=-37.6, max_lat=-36.0)

NEARBY_M = 200

# An area overlay that merely shares a boundary with the parcel satisfies an
# intersects test, because the LINZ parcel edge and Council's overlay edge come
# from different survey lineages and disagree by fractions of a millimetre. The
# result is a degenerate sliver of essentially no area, reported to the client
# as "part of your site is X".
#
# The case that found this: 12B Margate Road backs onto Glenavon School for the
# full 18.4 m of its rear boundary. Overlap with the school designation was
# 0.0000 m2, and the report told the owner part of her land was designated for a
# public work. In Auckland a great many properties abut a school, reserve,
# heritage extent or ecological area, so this is routine rather than rare.
#
# Anything at or below this reports as `abuts` instead of `on_site`. It is still
# flagged, still drawn on the map, and still shown to the client; what changes is
# that it says the boundary adjoins the overlay rather than that the site is
# inside it. It is never demoted to clear, and it never reaches the consent
# draft. Lines and points are exempt: buried services carry `tolerance_m` for
# the opposite reason and must keep flagging on proximity.
MIN_OVERLAP_M2 = 0.5


class LookupError_(Exception):
    pass


def _post(url, params):
    data = urllib.parse.urlencode(params).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={
        "User-Agent": USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url, params=None):
    if params:
        url = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return json.loads(r.read().decode("utf-8"))


# --------------------------------------------------------------- geocoding

AC_ADDRESS_URL = ("https://mapspublic.aucklandcouncil.govt.nz/arcgis/rest/"
                  "services/Address/MapServer/0")

_ADDR_NOISE = {"AUCKLAND", "NEW", "ZEALAND", "NZ", "AOTEAROA"}

# Used to find where the street name ends and the suburb begins.
_STREET_TYPES = {
    "ROAD", "RD", "STREET", "ST", "AVENUE", "AVE", "TERRACE", "TCE", "DRIVE",
    "DR", "LANE", "PLACE", "PL", "CRESCENT", "CRES", "WAY", "CLOSE", "GROVE",
    "PARADE", "PDE", "QUAY", "RISE", "VIEW", "HEIGHTS", "BOULEVARD", "CIRCLE",
    "COURT", "CT", "CRESENT", "PROMENADE", "ESPLANADE", "MEWS", "WALK",
}


def _ac_query(words, number):
    like = "%" + "%".join(w.replace("'", "''") for w in words) + "%"
    try:
        data = _post(AC_ADDRESS_URL + "/query", {
            "where": "UPPER(FullAddress) LIKE '%s'" % like,
            "outFields": "FullAddress,FullNumber",
            "returnGeometry": "true", "outSR": 4326,
            "resultRecordCount": 100, "f": "json",
        })
    except Exception:                             # noqa: BLE001
        return []
    if "error" in data:
        return []
    feats = data.get("features", [])
    if number:
        feats = [f for f in feats
                 if str(f["attributes"].get("FullNumber", "")).upper() == number]
    return feats


def geocode_ac(address):
    """
    Auckland Council's own street address layer. Authoritative for Auckland,
    no rate limit and no key, so it is tried before Nominatim, whose NZ
    address coverage has gaps (verified: it could not find a real Milford
    address that Council returns instantly).

    Tried twice: first with the suburb the user typed, then with the street
    alone. The second pass matters because the suburb people use in
    conversation often is not the one on the official address record. Vauxhall
    Road reads as Devonport locally but is recorded against Narrow Neck.
    """
    tokens = [t for t in address.upper().replace(",", " ").split() if t]
    if not tokens:
        return None
    number = tokens[0] if tokens[0][0].isdigit() else None
    words = [t for t in tokens[1:] if t not in _ADDR_NOISE and not t.isdigit()]
    if not words:
        return None

    feats = _ac_query(words, number)

    if not feats:
        # Retry on street name only, cutting at the street type word.
        for i, w in enumerate(words):
            if w in _STREET_TYPES:
                street_only = words[:i + 1]
                if street_only != words:
                    feats = _ac_query(street_only, number)
                    # Ambiguous across suburbs with no way to choose: defer.
                    if len({f["attributes"]["FullAddress"] for f in feats}) > 1:
                        return None
                break

    if not feats:
        return None

    f = feats[0]
    g = f.get("geometry") or {}
    if "x" not in g or "y" not in g:
        return None
    return dict(lat=g["y"], lon=g["x"],
                display=f["attributes"].get("FullAddress", address),
                precision="council_address", source="Auckland Council")


def geocode(address):
    """
    Address to coordinates. Council's address layer first, OpenStreetMap
    Nominatim as fallback. Neither needs an API key.

    Accuracy only needs to be good enough to land inside the right parcel,
    since the LINZ parcel lookup then takes over and supplies the geometry
    everything else is measured against.
    """
    hit = geocode_ac(address)
    if hit:
        return hit

    # Nominatim asks for max 1 request/second and a real User-Agent.
    time.sleep(1.0)
    data = _get("https://nominatim.openstreetmap.org/search", {
        "q": address, "format": "json", "countrycodes": "nz", "limit": 5,
        "addressdetails": 1,
    })
    if not data:
        raise LookupError_("Address not found: %s" % address)

    for hit in data:
        lat, lon = float(hit["lat"]), float(hit["lon"])
        if (AUCKLAND_BBOX["min_lat"] <= lat <= AUCKLAND_BBOX["max_lat"]
                and AUCKLAND_BBOX["min_lon"] <= lon <= AUCKLAND_BBOX["max_lon"]):
            return dict(lat=lat, lon=lon, display=hit.get("display_name", address),
                        precision=hit.get("type", "unknown"),
                        source="OpenStreetMap")

    raise LookupError_(
        "Address geocoded outside the Auckland region: %s. This tool covers "
        "Auckland only." % data[0].get("display_name", address))


# ------------------------------------------------------------------ parcel

def ring_centroid(rings):
    """
    Area-weighted centroid of a polygon's outer ring.

    Needed because the base zone must be looked up at a point inside the
    property. A polygon intersect picks up every zone the boundary touches,
    and since every residential parcel abuts a road, that returns "Road" as
    often as not.
    """
    ring = rings[0]
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]

    # Translate to a local origin before applying the shoelace formula. At
    # Auckland's coordinates (lon ~174.8, lat ~-36.8) the cross products are
    # around -6400 while the differences between them are ~1e-8, so computing
    # this on raw degrees loses the entire result to floating point
    # cancellation. Verified: without this, a Devonport parcel's centroid
    # landed on the road outside its own bounding box, and the site came back
    # zoned "Road".
    ox, oy = xs[0], ys[0]

    a = cx = cy = 0.0
    for i in range(len(ring) - 1):
        x0, y0 = ring[i][0] - ox, ring[i][1] - oy
        x1, y1 = ring[i + 1][0] - ox, ring[i + 1][1] - oy
        cross = x0 * y1 - x1 * y0
        a += cross
        cx += (x0 + x1) * cross
        cy += (y0 + y1) * cross

    if a == 0:                                    # degenerate, fall back to mean
        return sum(xs) / len(xs), sum(ys) / len(ys)

    a *= 0.5
    cx, cy = cx / (6 * a) + ox, cy / (6 * a) + oy

    # An L-shaped or concave parcel can put the true centroid outside the
    # polygon. Cheap sanity check: if it escapes the bounding box, something
    # is wrong, so fall back to the vertex mean.
    if not (min(xs) <= cx <= max(xs) and min(ys) <= cy <= max(ys)):
        return sum(xs) / len(xs), sum(ys) / len(ys)
    return cx, cy


def zone_is_on_the_land(feature, parcel_rings, lon0, lat0):
    """Does this zone actually cover part of the property?

    Same failure as the boundary-sliver case above, in the one place that guard
    did not reach. The secondary-zone query uses esriSpatialRelIntersects, so a
    zone sharing nothing with the parcel but a boundary line comes back as a
    second zone on the property. Found at 66 Rhinevale Close, which backs onto
    a conservation reserve: overlap with Open Space - Conservation was 0.0 m2
    and the report told the owner part of their section might be zoned for it.

    Measured with the same helper and the same threshold as the overlay slivers
    so the two behave alike. Fails safe: anything that cannot be measured, or a
    service that returns no geometry, counts as a real overlap.
    """
    rings = (feature.get("geometry") or {}).get("rings")
    if not rings:
        return True
    area = overlap_m2(parcel_rings, rings, lon0, lat0)
    if area is None:                       # unmeasurable, assume it is real
        return True
    return area > MIN_OVERLAP_M2


def parcel_at(lon, lat):
    """The LINZ primary parcel containing this point, or None."""
    data = _get(PARCEL_URL + "/query", {
        "geometry": "%f,%f" % (lon, lat),
        "geometryType": "esriGeometryPoint",
        "inSR": 4326, "outSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*", "returnGeometry": "true", "f": "json",
    })
    if "error" in data or not data.get("features"):
        return None
    f = data["features"][0]
    a = f["attributes"]
    # "Part Lot" parcels often carry no surveyed area, so fall back to the
    # calculated area from the geometry and say which one is being shown.
    survey = a.get("survey_area")
    calc = round(a.get("calc_area") or 0) or None
    return dict(
        legal_description=a.get("appellation"),
        title=a.get("titles"),
        survey_area_m2=survey,
        calc_area_m2=calc,
        area_m2=survey or calc,
        area_source="LINZ survey" if survey else "calculated from boundary",
        land_district=a.get("land_district"),
        rings=f.get("geometry", {}).get("rings"),
    )


# ------------------------------------------------------------ layer queries

def _geom_params(geometry, distance_m=0):
    if geometry["type"] == "polygon":
        p = {
            "geometry": json.dumps({"rings": geometry["rings"],
                                    "spatialReference": {"wkid": 4326}}),
            "geometryType": "esriGeometryPolygon",
        }
    else:
        p = {
            "geometry": "%f,%f" % (geometry["lon"], geometry["lat"]),
            "geometryType": "esriGeometryPoint",
        }
    p.update({"inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
              "outFields": "*", "returnGeometry": "false", "f": "json"})
    if distance_m:
        p["distance"] = distance_m
        p["units"] = "esriSRUnit_Meter"
    return p


def _metric(rings, lon0, lat0):
    """
    Rings to metres on a local equirectangular frame centred on the site.

    Good to well under a percent over a suburban parcel, which is far tighter
    than a 0.5 m2 decision needs, and it avoids both a projection dependency and
    a second round trip to re-fetch the parcel in NZTM.
    """
    kx = 111320.0 * math.cos(math.radians(lat0))
    ky = 110540.0
    return [[((x - lon0) * kx, (y - lat0) * ky) for x, y in ring]
            for ring in rings]


def overlap_m2(parcel_rings, feature_rings, lon0, lat0):
    """
    Area in m2 shared by the parcel and a set of overlay rings.

    Returns None when it cannot be computed, which the caller must treat as
    "assume a real overlap". Failing safe here means over-flagging, never
    silently clearing something that is genuinely on the property.
    """
    try:
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
    except ImportError:
        return None
    try:
        def build(rings):
            return unary_union([Polygon(r).buffer(0)
                                for r in _metric(rings, lon0, lat0)
                                if len(r) >= 4])
        return build(parcel_rings).intersection(build(feature_rings)).area
    except Exception:                                 # noqa: BLE001
        return None


def query_layer(service, geometry, distance_m=0, with_geometry=False):
    """
    Intersect a layer with the site geometry, or within a distance of it.

    `service` may be a list, in which case the layers are treated as one check
    and the features are pooled. Council splits some networks across several
    layers that mean the same thing to a client: high-pressure gas, gas
    transmission and medium-pressure gas are three layers and one sentence.
    Reporting them separately would put five "clear" rows for fuel pipelines on
    every suburban garden and train the reader to skip the section.
    """
    if isinstance(service, (list, tuple)):
        pooled = []
        for one in service:
            pooled.extend(query_layer(one, geometry, distance_m, with_geometry))
        return pooled
    params = _geom_params(geometry, distance_m)
    if with_geometry:
        params["returnGeometry"] = "true"
        params["outSR"] = 4326
    # POST: a parcel polygon in the query string can exceed URL length limits.
    data = _post(L.url_for(service) + "/query", params)
    if "error" in data:
        raise LookupError_(data["error"].get("message", "layer error"))
    return data.get("features", [])


def zone_domain():
    """
    Zone comes back as an integer code. The service publishes its own coded
    value domain, so the mapping is fetched live rather than hardcoded and
    stays correct if Council edits the list.
    """
    meta = _get(L.url_for(L.ZONE_LAYER["service"]), {"f": "json"})
    for f in meta.get("fields", []):
        dom = f.get("domain") or {}
        if f["name"] == "ZONE" and dom.get("codedValues"):
            return {c["code"]: c["name"] for c in dom["codedValues"]}
    return {}


def probe_layer(service):
    """
    Confirm one layer exists, answers, and actually holds features.

    Returns (status, detail). Anything other than "OK" means the layer cannot
    be trusted to produce a real result, which is different from a layer that
    correctly returns nothing for this parcel.
    """
    if isinstance(service, (list, tuple)):
        # A grouped check is only as good as its weakest layer, so report the
        # first that is not OK rather than the best of them.
        results = [probe_layer(one) for one in service]
        bad = [r for r in results if r[0] != "OK"]
        if bad:
            return bad[0]
        return "OK", ", ".join(r[1] for r in results)
    url = L.url_for(service)
    try:
        meta = _get(url, {"f": "json"})
        if "error" in meta:
            return "ERROR", meta["error"].get("message", "")
        if not meta.get("fields"):
            return "SUSPECT", "responded but has no fields"
        count = _get(url + "/query", {"where": "1=1",
                                      "returnCountOnly": "true", "f": "json"})
        n = count.get("count")
        if n is None:
            return "SUSPECT", "count query returned nothing"
        if n == 0:
            return "EMPTY", "layer exists but holds 0 features"
        return "OK", "%s features" % f"{n:,}"
    except Exception as exc:                      # noqa: BLE001
        return "DOWN", str(exc)[:70]


def verify_layers(workers=8):
    """
    Health-check every layer the report depends on.

    Returns a list of (name, status, detail) for anything that is not OK.
    An empty list means everything answered.

    This exists because the dangerous failure here is silent: a layer that is
    renamed or emptied upstream keeps rendering clean pages that quietly say
    "clear". A check nobody is forced to run is not a check, so the document
    builders call this before they will produce anything.
    """
    specs = ([dict(name=s["name"], service=s["service"]) for s in L.LAYERS]
             + [L.ZONE_LAYER, L.COASTLINE_LAYER])
    problems = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for spec, (status, detail) in zip(
                specs, pool.map(lambda s: probe_layer(s["service"]), specs)):
            if status != "OK":
                problems.append((spec["name"], status, detail))
    return problems


def _sliver_area(service, geometry):
    """
    Total area this layer actually shares with the parcel, or None if it is not
    an area layer or cannot be measured.

    Re-queries with geometry rather than asking for it on every check: only the
    dozen or so layers that hit need adjudicating, and returning rings for all
    40 would multiply the payload for no gain.
    """
    rings = geometry["rings"]
    lon0, lat0 = rings[0][0][0], rings[0][0][1]
    services = service if isinstance(service, (list, tuple)) else [service]
    total, measured = 0.0, False
    for one in services:
        params = _geom_params(geometry)
        params["returnGeometry"] = "true"
        params["outSR"] = 4326
        data = _post(L.url_for(one) + "/query", params)
        for feat in data.get("features", []):
            fr = (feat.get("geometry") or {}).get("rings")
            if not fr:
                return None            # lines or points: not an area overlay
            a = overlap_m2(rings, fr, lon0, lat0)
            if a is None:
                return None
            total += a
            measured = True
    return total if measured else None


def _check_one(spec, geometry):
    """Return a finding dict for one layer. Never raises."""
    out = dict(spec)
    try:
        # Buried services carry a tolerance. Council's asset geometry and
        # LINZ's parcel geometry come from different survey lineages and
        # disagree by a metre or so, so a main laid along a boundary reads as
        # on or off the property depending on whose line you believe. For a
        # planning overlay that does not matter; for something you might put a
        # digger through, "just outside" is not a distinction to rely on.
        hits = query_layer(spec["service"], geometry,
                           distance_m=spec.get("tolerance_m", 0))
        if hits:
            out["status"] = "on_site"
            # Boundary-sliver test. Only for area overlays hit at zero
            # tolerance: a service with a tolerance is meant to flag on
            # proximity, and a line has no area to measure. Anything that
            # cannot be measured stays on_site.
            if geometry["type"] == "polygon" and not spec.get("tolerance_m"):
                area = _sliver_area(spec["service"], geometry)
                if area is not None and area <= MIN_OVERLAP_M2:
                    out["status"] = "abuts"
                    out["overlap_m2"] = area
            return out
        # A layer whose published coverage is known to be incomplete cannot
        # produce a clear result, and a nearby result is no better: finding a
        # trunk main 150 m away is not actionable, and its absence from the
        # parcel says nothing about what is actually buried there. So anything
        # short of a direct hit reports as "partial", which every output
        # renders as not confirmed with the layer's own `absent` wording
        # telling the reader what to do about it.
        if spec.get("partial"):
            out["status"] = "partial"
            return out
        if spec.get("nearby") and query_layer(spec["service"], geometry,
                                              distance_m=NEARBY_M):
            out["status"] = "nearby"
            return out
        out["status"] = "clear"
        return out
    except Exception as exc:                      # noqa: BLE001
        out["status"] = "error"
        out["error"] = str(exc)
        return out


# ----------------------------------------------------------------- assembly

def run(address, workers=8):
    site = geocode(address)
    lon, lat = site["lon"], site["lat"]

    result = dict(address=address, site=site, parcel=None, findings=[],
                  zone=None, soil=None, errors=[], warnings=[],
                  generated=datetime.now().strftime("%d %B %Y at %I:%M %p")
                  .lstrip("0"))

    parcel = parcel_at(lon, lat)
    result["parcel"] = parcel
    if parcel and parcel.get("rings"):
        geometry = dict(type="polygon", rings=parcel["rings"])
    else:
        geometry = dict(type="point", lon=lon, lat=lat)
        result["warnings"].append(
            "No LINZ parcel found for this location, so checks were run against "
            "a single point rather than the whole property. Overlays that cover "
            "part of the site may be missed. Verify manually before issuing.")

    # Primary zone from a point inside the property, secondary zones from the
    # full polygon so a genuinely split site is still caught.
    if geometry["type"] == "polygon":
        cx, cy = ring_centroid(geometry["rings"])
        zone_point = dict(type="point", lon=cx, lat=cy)
    else:
        zone_point = geometry

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_check_one, spec, geometry) for spec in L.LAYERS]
        zone_f = pool.submit(query_layer, L.ZONE_LAYER["service"], zone_point)
        overlap_f = pool.submit(query_layer, L.ZONE_LAYER["service"], geometry,
                                0, True)
        domain_f = pool.submit(zone_domain)
        # Soil is descriptive context rather than a constraint, so it rides in
        # the same pool and costs no extra wall time. It is deliberately kept
        # out of result["findings"], because a soil classification is not a
        # pass or fail and must not move the "40 checked, 9 flagged" counts.
        soil_f = pool.submit(SOIL.lookup, zone_point["lon"], zone_point["lat"])
        result["findings"] = [f.result() for f in futures]

    try:
        result["soil"] = soil_f.result()
    except Exception as exc:                      # noqa: BLE001
        result["soil"] = dict(status="error", source="FSL",
                              error=str(exc)[:200])
    if (result["soil"] or {}).get("status") == "error":
        result["errors"].append("Soil classification: %s"
                                % result["soil"].get("error", "lookup failed"))

    try:
        feats, domain = zone_f.result(), domain_f.result()
        if feats:
            code = feats[0]["attributes"].get("ZONE")
            name = domain.get(code, "Zone code %s" % code)
            std, status = S.lookup(name)
            result["zone"] = dict(code=code, name=name, standards=std,
                                  standards_status=status)

            prings = geometry["rings"] if geometry["type"] == "polygon" else None
            lon0, lat0 = ((prings[0][0][0], prings[0][0][1]) if prings
                          else (None, None))
            others = []
            for feat in overlap_f.result():
                n = domain.get(feat["attributes"].get("ZONE"), "")
                if not n or n == name or n in others:
                    continue
                if prings and not zone_is_on_the_land(feat, prings, lon0, lat0):
                    continue          # shares only a boundary with the parcel
                others.append(n)
            result["zone"]["other_zones"] = others

            # Nobody's garden is in the road reserve. A base zone of Road means
            # the address resolved to the carriageway and every check above ran
            # against the wrong parcel. This used to surface by accident, as a
            # warning that the real residential zone was a "second zone" on the
            # property; the boundary test above correctly suppresses that, so
            # the condition has to be stated directly or the report presents a
            # confidently wrong zone with nothing to contradict it.
            if name == "Road":
                result["warnings"].append(
                    "This check ran against a parcel zoned Road, so the address "
                    "has resolved to the road reserve rather than the property. "
                    "Every finding in this report is for the wrong parcel. "
                    "Confirm the address and re-run before issuing.")

            if others:
                result["warnings"].append(
                    "Part of this property may also fall in: %s. The standards "
                    "shown are for %s. Confirm which applies where before design "
                    "is finalised." % (", ".join(others), name))
        else:
            result["zone"] = dict(code=None, name=None, standards=None,
                                  standards_status="no_zone", other_zones=[])
    except Exception as exc:                      # noqa: BLE001
        result["errors"].append("Base zone lookup failed: %s" % exc)

    result["errors"] += ["%s: %s" % (f["name"], f["error"])
                         for f in result["findings"] if f["status"] == "error"]
    return result
