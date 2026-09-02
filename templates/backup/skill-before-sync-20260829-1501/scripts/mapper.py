"""
Renders a site map: Council aerial photography with the parcel boundary and
any flagged overlays drawn on top.

Everything is done in NZTM 2193, the projection Council's aerial basemap is
published in. Overlay geometries are requested from ArcGIS with outSR=2193 so
the server handles the reprojection, which avoids a pyproj dependency and any
chance of us getting the maths wrong.
"""

import io
import math
import os

from PIL import Image, ImageChops, ImageDraw, ImageFont

import engine
import layers as L

NZTM = 2193
AERIAL = ("https://mapspublic.aucklandcouncil.govt.nz/arcgis/rest/services/"
          "Basemap/AerialBasemap/MapServer/export")

MAP_PX = 1100          # aerial height in px; width = MAP_PX * aspect
MARGIN = 28
MIN_SPAN_M = 90        # stops a small section being zoomed in absurdly far
PAD_FRAC = 0.35        # padding around the parcel, as a fraction of its size

PARCEL_COLOUR = (255, 232, 0)

# colour, label, hatch pattern, outline width.
#
# Area overlays are drawn as a hatch rather than a solid fill. Solid fills
# stack: three overlapping overlays turn the photo into mud and you cannot
# tell which is which. A hatch lets the aerial read through, and giving each
# layer its own pattern and angle means overlapping areas stay separable.
#
# Pattern is None for line and point layers, which carry no fill.
#
# COLOUR POLICY. Where Council's own published symbology is legible over an
# aerial and unambiguous, we use their exact RGB, so anyone who knows GeoMaps
# reads our map the same way. Those are marked "Council" below and were read
# from each layer's drawingInfo renderer on 31 Jul 2026; re-check with
# tools/check_council_colours.py if Council restyles.
#
# Services come from the GeoMaps UndergroundServices renderers, which is the
# view Lee actually works from, rather than the open data portal. The two
# servers symbolise the same assets differently, and the open data one is not
# what anyone looks at.
#
# Five cases deliberately do NOT match, because copying Council literally makes
# this map worse rather than more familiar:
#   - stormwater pipe and watercourse are both 116,212,0 in Council's renderer,
#     so matching would make two different things identical in our legend. The
#     pipe takes the green; the watercourse keeps cyan
#   - high-pressure gas is the same red as wastewater in GeoMaps, which works
#     there because you choose which layer to switch on and cannot here, so gas
#     takes Council's gas-transmission magenta
#   - fuel pipelines are 115,38,0, a brown that disappears against a dark
#     aerial. It is the most dangerous thing that can cross a site, so it gets
#     a colour that survives the photo
#   - both landslide layers are dark browns and olives (61,33,8 / 82,75,22),
#     drawn by Council over a pale basemap; over dark aerial photography they
#     disappear
#   - Special Character has no fill at all in Council's renderer, just an
#     outline, which cannot carry a hatch
STYLES = {
    "landslide_large":      ((255, 105, 45),  "Large scale landslide susceptibility", "bdiag", 0),
    "landslide_shallow":    ((255, 200, 40),  "Shallow landslide susceptibility", "fdiag", 0),
    "flood_plain":          ((158, 187, 215), "Flood plain", "horiz", 3),          # Council
    "flood_prone":          ((0, 38, 115),    "Flood prone area", "fdiag", 2),     # Council
    "flood_sensitive":      ((115, 223, 255), "Flood sensitive area", "vert", 2),  # Council
    "coastal_inundation":   ((190, 232, 255), "Coastal inundation control", "bdiag", 3),  # Council
    # Small crosses, not a line hatch. The SEA is usually the biggest area on
    # the map and the flood layers routinely sit over it; a diagonal mesh over
    # an orthogonal one just reads as mesh.
    "sea":                  ((30, 230, 80),   "Significant Ecological Area", "crosslet", 5),
    "onf":                  ((130, 255, 130), "Outstanding Natural Feature", "horiz", 3),
    "onl":                  ((130, 255, 130), "Outstanding Natural Landscape", "vert", 3),
    "special_character":    ((200, 110, 255), "Special Character Area", "cross", 4),
    "heritage":             ((112, 68, 137),  "Historic Heritage", "fdiag", 3),    # Council
    "mana_whenua":          ((255, 75, 195),  "Site of Significance to Mana Whenua", "bdiag", 3),
    "natural_stream":       ((60, 195, 255),  "Natural Stream Management Area", "vert", 3),
    # Buried services follow GeoMaps' own utility convention, read from the
    # UndergroundServices renderers: wastewater red, potable water blue,
    # stormwater green, other owners' pipework light purple. This is the set
    # Lee and anyone else who uses GeoMaps already reads without a legend.
    "stormwater_pipe":      ((116, 212, 0),  "Stormwater pipe", None, 2),   # Council
    "wastewater_pipe":      ((230, 0, 0),    "Wastewater pipe", None, 3),   # Council
    "wastewater_transmission": ((230, 0, 0), "Wastewater transmission main", None, 6),  # Council
    "water_pipe":           ((0, 77, 168),   "Water main", None, 3),        # Council
    "water_transmission":   ((0, 77, 168),   "Water transmission main", None, 6),  # Council
    "other_utility_pipe":   ((223, 115, 255), "Other utility pipework", None, 2),  # Council
    # GeoMaps draws high-pressure gas in the same red as wastewater and tells
    # them apart by which layer you switched on. Both can appear here at once,
    # so gas takes Council's gas-transmission magenta instead.
    "gas_pipeline":         ((230, 0, 169),  "Gas pipeline", None, 5),
    # Council's fuel brown is 115,38,0, which vanishes against a dark aerial.
    # A fuel line is the single most dangerous thing that can cross a site, so
    # legibility wins over the match here.
    "fuel_pipeline":        ((255, 90, 0),   "Fuel pipeline", None, 6),
    "septic_tank":          ((160, 120, 60), "Septic tank", None, 3),
    "notable_tree_group":   ((0, 220, 140),  "Notable group of trees", "cross", 3),
    "vehicle_access":       ((255, 130, 60), "Vehicle access restriction", None, 4),
    "designation":          ((190, 130, 255), "Designation", "bdiag", 3),
    "wetland":              ((76, 129, 205), "Natural inland wetland", "horiz", 3),  # Council
    "height_variation":     ((215, 160, 255), "Height variation control", "vert", 3),
    # Teal, because GeoMaps draws watercourses in the same green as stormwater
    # pipes and both can be on this map at once.
    "stormwater_watercourse": ((0, 150, 136), "Watercourse", None, 4),
    # GeoMaps' own cyan for overland flow, from the stormwater service. The
    # open data portal uses 0,112,255 for the same thing, which sat too close
    # to the water main's dark blue to tell apart on an aerial.
    "overland_flow":        ((0, 197, 255),   "Overland flow path", None, 3),  # Council
    "notable_trees":        ((0, 255, 120),   "Notable tree", None, 2),
}

# The hatch has to stay sparse. The whole point is that the aerial reads
# through it, so err on the side of too light: wide spacing, thin strokes.
# Cross-hatch draws in two directions, so it gets extra spacing to compensate.
HATCH_SPACING = 26        # px between hatch lines
HATCH_SPACING_CROSS = 34
# Discrete marks cover far less ink per cell than a continuous line, so they
# sit closer together to read as a texture rather than as scattered specks.
HATCH_SPACING_CROSSLET = 19
HATCH_WIDTH = 2           # px line thickness
HATCH_ALPHA = 190         # opacity of the hatch strokes themselves
TINT_ALPHA = 10           # barely-there solid tint under the hatch
BLANKET_FRAC = 0.9        # coverage above which a layer is noted, not drawn

# Landslide susceptibility is a regional wash surface, not a boundary. It is
# only worth drawing when it actually distinguishes part of the view, so it
# gets a much stricter threshold. Above it, the legend says the layer covers
# the view and the map stays readable for the layers that do have edges.
WASH_LAYERS = {"landslide_large", "landslide_shallow"}
WASH_BLANKET_FRAC = 0.5

MIN_DIM_M = 4.0           # shorter boundary edges are not labelled
DIM_OFFSET_M = 4.5        # how far outside the boundary labels sit

# Broad hazard washes first so the named overlays and linear features stay
# legible on top of them.
# Back to front: area overlays first, then lines, then points, so the buried
# services draw over the washes rather than under them.
#
# This list is the gate, not STYLES. A layer missing from here is silently
# never drawn even when it is flagged and styled, which is how the wastewater
# mains came to be reported as NEEDS ATTENTION in the table while being absent
# from the map beside it. If you add a layer, add it in both places.
DRAW_ORDER = [
    "landslide_large", "landslide_shallow",
    "flood_plain", "flood_prone", "flood_sensitive", "coastal_inundation",
    "sea", "onf", "onl", "special_character", "heritage", "mana_whenua",
    "natural_stream",
    "stormwater_pipe", "stormwater_watercourse", "overland_flow",
    "wastewater_pipe", "wastewater_transmission",
    "notable_trees",
]


def _font(size, bold=False):
    names = (["segoeuib.ttf", "arialbd.ttf"] if bold
             else ["segoeui.ttf", "arial.ttf"])
    for n in names:
        for path in (n, os.path.join(r"C:\Windows\Fonts", n)):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def parcel_nztm(lon, lat):
    """Parcel rings in NZTM, or None."""
    d = engine._get(engine.PARCEL_URL + "/query", {
        "geometry": "%f,%f" % (lon, lat), "geometryType": "esriGeometryPoint",
        "inSR": 4326, "outSR": NZTM, "spatialRel": "esriSpatialRelIntersects",
        "outFields": "appellation", "returnGeometry": "true", "f": "json"})
    feats = d.get("features") or []
    return feats[0]["geometry"]["rings"] if feats else None


def _bbox(rings):
    xs = [p[0] for r in rings for p in r]
    ys = [p[1] for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def view_box(rings, aspect=1.0):
    """
    NZTM extent around the parcel, with padding.

    aspect is width/height. The stacked layout uses a square view; the wide
    layout uses a landscape one so the map fills an A3 sheet instead of
    sitting in the middle with dead space either side.
    """
    x0, y0, x1, y1 = _bbox(rings)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    span = max((x1 - x0) / aspect, y1 - y0, MIN_SPAN_M)
    span *= (1 + 2 * PAD_FRAC)
    hx, hy = span * aspect / 2, span / 2
    return cx - hx, cy - hy, cx + hx, cy + hy


def fetch_aerial(box, size):
    q = {"bbox": "%f,%f,%f,%f" % box, "bboxSR": NZTM, "imageSR": NZTM,
         "size": "%d,%d" % size, "format": "png32",
         "transparent": "false", "f": "image"}
    import urllib.parse
    import urllib.request
    url = AERIAL + "?" + urllib.parse.urlencode(q)
    req = urllib.request.Request(url, headers={"User-Agent": engine.USER_AGENT})
    with urllib.request.urlopen(req, timeout=90) as r:
        return Image.open(io.BytesIO(r.read())).convert("RGBA")


def fetch_geometry(service, box):
    """Features of a layer inside the view, in NZTM."""
    env = {"xmin": box[0], "ymin": box[1], "xmax": box[2], "ymax": box[3],
           "spatialReference": {"wkid": NZTM}}
    try:
        d = engine._post(L.url_for(service) + "/query", {
            "geometry": __import__("json").dumps(env),
            "geometryType": "esriGeometryEnvelope", "inSR": NZTM, "outSR": NZTM,
            "spatialRel": "esriSpatialRelIntersects", "outFields": "",
            "returnGeometry": "true", "resultRecordCount": 400, "f": "json"})
        return d.get("features", []) if "error" not in d else []
    except Exception:                             # noqa: BLE001
        return []


def _projector(box, size):
    x0, y0, x1, y1 = box
    w, h = size
    sx, sy = x1 - x0, y1 - y0

    def to_px(x, y):
        return ((x - x0) / sx * w, h - (y - y0) / sy * h)   # north is up
    return to_px, sx / w                                    # metres per pixel


def hatch_tile(size, pattern, spacing=None, width=HATCH_WIDTH, offset=0):
    """A greyscale mask of hatch strokes covering the whole map area."""
    if spacing is None:
        spacing = {"cross": HATCH_SPACING_CROSS,
                   "crosslet": HATCH_SPACING_CROSSLET}.get(pattern,
                                                           HATCH_SPACING)
    spacing = max(3, spacing)
    w, h = size
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    o = offset % spacing
    if pattern in ("fdiag", "cross"):             # bottom-left to top-right
        for c in range(-h + o, w + h, spacing):
            d.line([(c, h), (c + h, 0)], fill=255, width=width)
    if pattern in ("bdiag", "cross"):             # top-left to bottom-right
        for c in range(-h + o, w + h, spacing):
            d.line([(c, 0), (c + h, h)], fill=255, width=width)
    if pattern == "horiz":
        for y in range(o, h, spacing):
            d.line([(0, y), (w, y)], fill=255, width=width)
    if pattern == "vert":
        for x in range(o, w, spacing):
            d.line([(x, 0), (x, h)], fill=255, width=width)
    if pattern == "crosslet":
        # A field of small crosses rather than continuous strokes. Every other
        # pattern here is made of lines, so two line hatches only ever differ
        # by angle and colour, and at a glance a diagonal mesh and an
        # orthogonal one read as the same texture. A discrete mark separates
        # instantly, which is why the SEA uses it: the SEA is usually the
        # largest area on the map and most likely to sit under the flood
        # layers. A cross also carries more ink than a dot of the same radius,
        # which matters because the SEA is normally over dark bush canopy.
        arm = max(3, width + 2)
        for row, y in enumerate(range(o, h + spacing, spacing)):
            stagger = spacing // 2 if row % 2 else 0
            for x in range(o + stagger, w + spacing, spacing):
                d.line([(x - arm, y), (x + arm, y)], fill=255, width=width)
                d.line([(x, y - arm), (x, y + arm)], fill=255, width=width)
    return m


def _draw_area(overlay, feats, to_px, colour, pattern, width, hatches,
               offset=0, blanket_frac=BLANKET_FRAC):
    """
    Hatch-fill and outline polygon features.

    The fill is built by masking a full-size hatch pattern with a mask of the
    polygons, so the strokes line up continuously across separate polygons of
    the same layer rather than restarting inside each one.
    """
    size = overlay.size
    mask = Image.new("L", size, 0)
    mdraw = ImageDraw.Draw(mask)
    any_poly = False

    for f in feats:
        for ring in (f.get("geometry") or {}).get("rings", []):
            pts = [to_px(p[0], p[1]) for p in ring]
            if len(pts) > 2:
                mdraw.polygon(pts, fill=255)
                any_poly = True
    if not any_poly:
        return False

    # A layer covering essentially the whole view tells you nothing about
    # where it is, and hatching it just wrecks legibility for every other
    # layer. The landslide susceptibility surfaces do this constantly. Say so
    # in the legend instead of drawing it.
    covered = sum(i * n for i, n in enumerate(mask.histogram())) / \
        (255.0 * size[0] * size[1])
    if covered >= blanket_frac:
        return "blanket"

    if pattern:
        cache_key = (pattern, offset)
        if cache_key not in hatches:
            hatches[cache_key] = hatch_tile(size, pattern, offset=offset)
        strokes = ImageChops.multiply(mask, hatches[cache_key])
        overlay.paste(Image.new("RGBA", size, colour + (255,)),
                      (0, 0), strokes.point(lambda v: v * HATCH_ALPHA // 255))
        overlay.paste(Image.new("RGBA", size, colour + (255,)),
                      (0, 0), mask.point(lambda v: v * TINT_ALPHA // 255))

    if width:
        d = ImageDraw.Draw(overlay)
        for f in feats:
            for ring in (f.get("geometry") or {}).get("rings", []):
                pts = [to_px(p[0], p[1]) for p in ring]
                if len(pts) > 2:
                    d.line(pts + [pts[0]], fill=colour + (240,), width=width)
    return True


def _draw_lines_points(overlay, feats, to_px, colour, width):
    d = ImageDraw.Draw(overlay)
    drew = False
    for f in feats:
        g = f.get("geometry") or {}
        for path in g.get("paths", []):
            pts = [to_px(p[0], p[1]) for p in path]
            if len(pts) > 1:
                d.line(pts, fill=(0, 0, 0, 90), width=width + 5)
                d.line(pts, fill=colour + (250,), width=width + 2)
                drew = True
        if g.get("x") is not None:
            px, py = to_px(g["x"], g["y"])
            d.ellipse([px - 7, py - 7, px + 7, py + 7], fill=colour + (230,),
                      outline=(255, 255, 255, 255), width=2)
            drew = True
    return drew


def _dimension_labels(overlay, rings, to_px):
    """
    Label each boundary edge with its length in metres.

    Lengths are straight from the NZTM coordinates, so they are true ground
    distances, not scaled off the image. Labels are rotated to run along their
    edge and pushed outward from the centre of the parcel so they sit outside
    the boundary rather than over the site.

    Short edges are skipped. Real parcels carry small jogs and corner splays,
    and labelling every one produces the stack of overlapping numbers visible
    in the reference report.
    """
    font = _font(19, True)

    # Build every candidate first, then place longest edge first and drop any
    # label that would collide with one already placed. A long thin accessway
    # puts its two sides within a few metres of each other, so without this the
    # numbers pile on top of each other and none of them can be read.
    cands = []
    for ring in rings:
        xs = [p[0] for p in ring]
        ys = [p[1] for p in ring]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)     # ring centre, NZTM

        for i in range(len(ring) - 1):
            (ax, ay), (bx, by) = ring[i][:2], ring[i + 1][:2]
            length = math.hypot(bx - ax, by - ay)
            if length < MIN_DIM_M:
                continue

            mx, my = (ax + bx) / 2, (ay + by) / 2
            ox, oy = mx - cx, my - cy
            norm = math.hypot(ox, oy) or 1
            px, py = to_px(mx + ox / norm * DIM_OFFSET_M,
                           my + oy / norm * DIM_OFFSET_M)

            p0, p1 = to_px(ax, ay), to_px(bx, by)
            rot = -math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
            if rot > 90 or rot < -90:              # never upside down
                rot += 180
            cands.append((length, px, py, rot))

    placed = []
    for length, px, py, rot in sorted(cands, key=lambda c: -c[0]):
        text = "%.1f m" % length
        pad = 6
        tw, th = int(font.getlength(text)) + pad * 2, 26
        chip = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        cd = ImageDraw.Draw(chip)
        cd.rounded_rectangle([0, 0, tw - 1, th - 1], radius=5,
                             fill=(0, 0, 0, 160))
        cd.text((pad, 3), text, font=font, fill=PARCEL_COLOUR + (255,))
        chip = chip.rotate(rot, expand=True, resample=Image.BICUBIC)

        x0, y0 = px - chip.width / 2, py - chip.height / 2
        box = (x0, y0, x0 + chip.width, y0 + chip.height)
        if any(box[0] < q[2] and box[2] > q[0]
               and box[1] < q[3] and box[3] > q[1] for q in placed):
            continue
        placed.append(box)
        overlay.alpha_composite(chip, (int(x0), int(y0)))


def _scale_bar(draw, m_per_px, x, y):
    """Draws the bar and returns the x where the next piece of furniture can go."""
    for target in (100, 50, 40, 30, 20, 10, 5):
        px = target / m_per_px
        if px <= 240:
            break
    px = int(px)
    draw.rectangle([x, y, x + px, y + 9], fill=(255, 255, 255, 235),
                   outline=(0, 0, 0, 235))
    draw.rectangle([x, y, x + px // 2, y + 9], fill=(0, 0, 0, 235))
    label = "%d m" % target
    draw.text((x + px + 9, y - 4), label, font=_font(15, True),
              fill=(255, 255, 255, 255))
    return x + px + 9 + draw.textlength(label, font=_font(15, True))


def _north_arrow(draw, x, y):
    """
    North point, sitting beside the scale bar.

    `_projector` maps NZTM straight to pixels with no rotation, so up the page
    is grid north. Drawn as a half-filled triangle over a stem, which is the
    convention on a survey plan and reads at a glance without a legend. Aerials
    run from near-white concrete to near-black shadow, so every stroke gets a
    dark outline under a light fill, same as the scale bar.
    """
    h, w = 46, 17                                  # head height, half-width
    dark, light = (0, 0, 0, 240), (255, 255, 255, 250)
    tip = (x, y - h)
    left, right = (x - w, y), (x + w, y)
    notch = (x, y - h * 0.30)                      # the waist of the arrowhead
    # Left half solid, right half hollow. The standard survey-plan north point,
    # and it survives being printed in greyscale because the two halves differ
    # in fill rather than in colour.
    draw.polygon([tip, left, notch], fill=dark)
    draw.polygon([tip, right, notch], fill=light)
    # Outline last, over both fills, so the shape holds against a busy aerial.
    draw.line([tip, left, notch, right, tip], fill=dark, width=3, joint="curve")
    draw.line([tip, notch], fill=dark, width=2)
    f = _font(19, True)
    n = draw.textlength("N", font=f)
    tx, ty = x - n / 2, y + 4
    # Same halo trick the dimension labels use: a dark pass under a light one
    # so it reads over both dark tarmac and pale concrete.
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        draw.text((tx + dx, ty + dy), "N", font=f, fill=dark)
    draw.text((tx, ty), "N", font=f, fill=light)


def render_map(result, out_path, chrome=True, layout="stack"):
    """
    Build the site map. Returns the path, or None if it could not be built.

    chrome=False drops the title band and the prepared-on line, for embedding
    in the PDF where the page already supplies both. The imagery attribution
    stays either way, since it is a licence condition.
    """
    site = result["site"]
    rings = parcel_nztm(site["lon"], site["lat"])
    if not rings:
        return None

    aspect = 1.32 if layout == "wide" else 1.0
    size = (int(MAP_PX * aspect), MAP_PX)
    box = view_box(rings, aspect)
    base = fetch_aerial(box, size)
    to_px, m_per_px = _projector(box, size)

    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    flagged = {f["key"]: f for f in result["findings"]
               if f["status"] in ("on_site", "abuts", "nearby")}

    # DRAW_ORDER sets the stacking, but anything styled and not listed still
    # gets drawn, on top. Otherwise forgetting to list a new layer silently
    # drops it from the map while the findings table beside it says NEEDS
    # ATTENTION, and a map that quietly omits a flagged item is worse than no
    # map at all.
    order = DRAW_ORDER + [k for k in STYLES if k not in DRAW_ORDER]

    legend, hatches = [], {}
    for key in order:
        if key not in flagged or key not in STYLES:
            continue
        spec = next((s for s in L.LAYERS if s["key"] == key), None)
        if not spec:
            continue
        feats = fetch_geometry(spec["service"], box)
        if not feats:
            continue
        colour, label, pattern, width = STYLES[key]
        if pattern:
            # Stagger layers sharing a pattern so their strokes interleave
            # rather than sitting exactly on top of each other.
            # Count against `order`, not DRAW_ORDER. A styled layer that is not
            # listed in DRAW_ORDER still draws (see above), and looking it up in
            # DRAW_ORDER raised ValueError and took the whole map down with it.
            offset = 9 * sum(1 for _, _, p, _ in
                             (STYLES[k] for k in order[:order.index(key)])
                             if p == pattern)
            frac = WASH_BLANKET_FRAC if key in WASH_LAYERS else BLANKET_FRAC
            drew = _draw_area(overlay, feats, to_px, colour, pattern, width,
                              hatches, offset, frac)
        else:
            drew = _draw_lines_points(overlay, feats, to_px, colour, width)
        # Only legend what actually made it onto the map.
        if drew == "blanket":
            legend.append((colour, label, "blanket", pattern))
        elif drew:
            legend.append((colour, label, flagged[key]["status"], pattern))

    # Parcel last so it is never buried under an overlay.
    for ring in rings:
        pts = [to_px(p[0], p[1]) for p in ring]
        draw.line(pts + [pts[0]], fill=(0, 0, 0, 200), width=8)
        draw.line(pts + [pts[0]], fill=PARCEL_COLOUR + (255,), width=4)

    _dimension_labels(overlay, rings, to_px)
    bar_y = size[1] - MARGIN - 10
    end = _scale_bar(draw, m_per_px, MARGIN, bar_y)
    # Sits on the scale bar's baseline so the two read as one piece of map
    # furniture rather than two things that happen to be near each other.
    _north_arrow(draw, end + 34, bar_y + 9)
    base = Image.alpha_composite(base, overlay)

    if layout == "wide":
        return _compose_wide(base, result, legend, out_path)
    return _compose(base, result, legend, out_path, chrome)


def _compose_wide(map_img, result, legend, out_path):
    """
    Legend in a column beside the map instead of underneath.

    Gives a landscape composition, which is what an A3 presentation sheet
    wants. The stacked version stays for on-screen and A4 use.
    """
    f_leg, f_small = _font(19), _font(15)
    f_lab = _font(17, True)

    leg_w = 430
    gap = 34
    mw, mh = map_img.size
    W = MARGIN * 2 + mw + gap + leg_w
    H = MARGIN * 2 + mh

    canvas = Image.new("RGB", (W, H), (255, 255, 255))
    canvas.paste(map_img.convert("RGB"), (MARGIN, MARGIN))
    d = ImageDraw.Draw(canvas)

    x = MARGIN + mw + gap
    y = MARGIN + 4
    d.text((x, y), "WHAT IS SHOWN", font=f_lab, fill=(1, 99, 47))
    y += 34

    items = [(PARCEL_COLOUR, "Your property boundary", None, "solid")] + legend
    for colour, label, status, pattern in items:
        _legend_swatch(canvas, d, x, y + 2, colour,
                       "blanket" if status == "blanket" else pattern,
                       w=34, h=19)
        suffix = {"nearby": "  (nearby)", "abuts": "  (adjoins)",
                  "blanket": "  (covers this whole view)"}.get(status, "")
        text = label + suffix
        # Wrap long legend labels inside the column.
        words, line, lines = text.split(), "", []
        for wd in words:
            trial = (line + " " + wd).strip()
            if f_leg.getlength(trial) > leg_w - 52 and line:
                lines.append(line)
                line = wd
            else:
                line = trial
        lines.append(line)
        for i, ln in enumerate(lines):
            d.text((x + 46, y + i * 22), ln, font=f_leg, fill=(35, 35, 35))
        y += max(30, len(lines) * 22 + 8)

    d.text((x, H - MARGIN - 34),
           "Aerial imagery and overlay data:", font=f_small,
           fill=(120, 120, 120))
    d.text((x, H - MARGIN - 16),
           "Auckland Council (CC BY 4.0). Parcel: LINZ.", font=f_small,
           fill=(120, 120, 120))

    canvas.save(out_path)
    return out_path


def _legend_swatch(canvas, d, x, y, colour, pattern, w=30, h=17):
    """
    Swatch matching how the layer is actually drawn, so the legend is
    readable against the map rather than just colour-coded.
    """
    if pattern == "solid":                        # the parcel boundary
        d.rectangle([x, y, x + w, y + h], fill=colour, outline=(70, 70, 70))
        return
    if pattern == "blanket":                      # not drawn on the map
        d.rectangle([x, y, x + w, y + h], fill=(248, 248, 248),
                    outline=(190, 190, 190))
        d.line([(x + 4, y + h - 4), (x + w - 4, y + 4)], fill=colour, width=3)
        return
    if pattern is None:                           # line or point layer
        d.line([(x, y + h // 2), (x + w, y + h // 2)], fill=colour, width=6)
        d.rectangle([x, y, x + w, y + h], outline=(190, 190, 190))
        return

    tile = hatch_tile((w, h), pattern, spacing=6, width=2)
    patch = Image.new("RGB", (w, h), (255, 255, 255))
    patch.paste(Image.new("RGB", (w, h), colour), (0, 0), tile)
    canvas.paste(patch, (x, y))
    d.rectangle([x, y, x + w, y + h], outline=colour)


def _compose(map_img, result, legend, out_path, chrome=True):
    """Title bar above the map, legend below."""
    f_title, f_sub = _font(30, True), _font(17)
    f_leg, f_small = _font(17), _font(14)

    head_h = 96 if chrome else 0
    rows = max(1, math.ceil(len(legend) / 2)) if legend else 1
    leg_h = 54 + rows * 30 + (74 if chrome else 40)

    mw, mh = map_img.size
    W = mw + MARGIN * 2
    canvas = Image.new("RGB", (W, head_h + mh + leg_h), (255, 255, 255))
    d = ImageDraw.Draw(canvas)

    if chrome:
        d.rectangle([0, 0, W, head_h], fill=(1, 99, 47))   # Zones green
        d.text((MARGIN, 20), "SITE MAP", font=f_title, fill=(255, 255, 255))
        addr = result["site"].get("display", result["address"])
        d.text((MARGIN, 58), addr[:88], font=f_sub, fill=(225, 240, 230))

    canvas.paste(map_img.convert("RGB"), (MARGIN, head_h))

    y = head_h + mh + 20
    d.text((MARGIN, y), "WHAT IS SHOWN", font=_font(16, True), fill=(1, 99, 47))
    y += 26

    items = [(PARCEL_COLOUR, "Your property boundary", None, "solid")] + legend
    col_w = (W - MARGIN * 2) // 2
    for i, (colour, label, status, pattern) in enumerate(items):
        cx = MARGIN + (i % 2) * col_w
        cy = y + (i // 2) * 30
        _legend_swatch(canvas, d, cx, cy + 2, colour,
                       "blanket" if status == "blanket" else pattern)
        suffix = {"nearby": " (nearby)", "abuts": " (adjoins)",
                  "blanket": " (covers this whole view)"}.get(status, "")
        d.text((cx + 40, cy), label + suffix, font=f_leg, fill=(35, 35, 35))

    fy = y + math.ceil(len(items) / 2) * 30 + 14
    d.text((MARGIN, fy),
           "Aerial imagery and overlay data: Auckland Council (CC BY 4.0). "
           "Parcel boundary: LINZ. Boundaries are indicative only.",
           font=f_small, fill=(110, 110, 110))
    if chrome:
        d.text((MARGIN, fy + 19),
               "Prepared %s. Not to be used for construction or consent "
               "purposes." % result.get("generated", ""),
               font=f_small, fill=(110, 110, 110))

    canvas.save(out_path)
    return out_path
