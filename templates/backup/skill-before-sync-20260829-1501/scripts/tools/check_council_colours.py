"""
Compare our map colours against Auckland Council's published symbology.

    python tools/check_council_colours.py

Council publish a renderer with every layer, so their exact RGB is readable
rather than guessable. Where a layer is marked "Council" in mapper.STYLES we
use their colour so anyone familiar with GeoMaps reads our map the same way.
This checks those are still in step, and reports what Council uses for the
layers where we deliberately differ.

It reads only, changes nothing. If a "Council" layer has drifted, update
mapper.STYLES by hand: some of Council's colours are unusable over an aerial
and that judgement should not be automated.
"""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layers as L      # noqa: E402
import mapper           # noqa: E402

# Layers where mapper.STYLES deliberately departs from Council, and why.
DELIBERATE = {
    "stormwater_watercourse": "Council uses the same green as stormwater pipe",
    "overland_flow": "GeoMaps cyan 0,197,255 adopted; open data uses 0,112,255",
    "gas_pipeline": "Council's red is the wastewater red; both can appear here",
    "fuel_pipeline": "Council's brown vanishes over a dark aerial",
    "landslide_shallow": "Council's browns vanish over aerial photography",
    "landslide_large": "Council's olives vanish over aerial photography",
    "special_character": "Council has no fill, outline only",
    "sea": "Council's mid green is weak over dark bush",
    "onf": "classed renderer, no single colour",
    "onl": "classed renderer, no single colour",
    "notable_trees": "picture marker, no colour to read",
    "notable_tree_group": "picture marker, no colour to read",
    "mana_whenua": "kept distinct from the heritage purple",
    "natural_stream": "kept distinct from the flood blues",
    "septic_tank": "Council publishes no colour for this layer",
    "vehicle_access": "Council's 78,78,78 grey vanishes over an aerial",
    "designation": "Council publishes no fill for this layer",
    "height_variation": "Council publishes no fill for this layer",
}


def council_colours(service):
    """
    Every distinct fill colour in a layer's renderer, most common first.

    Resolves through layers.url_for, so it reads whichever server the layer
    actually lives on: the open data portal for planning overlays, the GeoMaps
    asset server for buried services. A grouped layer is checked on its first
    service, which is the one whose colour we adopt.
    """
    if isinstance(service, (list, tuple)):
        service = service[0]
    url = L.url_for(service)
    url = url + "?f=json" if "?" not in url else url
    try:
        with urllib.request.urlopen(url, timeout=45) as fh:
            info = json.load(fh)
    except Exception as exc:                          # noqa: BLE001
        return None, str(exc)
    renderer = (info.get("drawingInfo") or {}).get("renderer") or {}
    found = []

    def take(symbol):
        if not symbol:
            return
        colour = symbol.get("color")
        if not colour:
            outline = symbol.get("outline") or {}
            colour = outline.get("color")
        if colour and len(colour) >= 3 and colour[3:4] != [0]:
            rgb = tuple(colour[:3])
            if rgb not in found:
                found.append(rgb)

    take(renderer.get("symbol"))
    for key in ("uniqueValueInfos", "classBreakInfos"):
        for entry in renderer.get(key) or []:
            take(entry.get("symbol"))
    return found, None


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    services = {spec["key"]: spec["service"] for spec in L.LAYERS}
    drift = 0

    print("%-24s %-16s %s" % ("LAYER", "OURS", "COUNCIL"))
    print("-" * 78)
    for key, (ours, label, _pattern, _w) in sorted(mapper.STYLES.items()):
        service = services.get(key)
        if not service:
            continue
        theirs, error = council_colours(service)
        if error:
            print("%-24s %-16s could not read: %s" % (key, ours, error[:30]))
            continue
        note = DELIBERATE.get(key)
        if note:
            print("%-24s %-16s %s   [by design: %s]"
                  % (key, ours, theirs or "none", note))
        elif ours in (theirs or []):
            print("%-24s %-16s matches" % (key, ours))
        else:
            drift += 1
            print("%-24s %-16s DRIFTED, Council now %s" % (key, ours, theirs))

    print()
    if drift:
        print("%d layer(s) marked Council in mapper.STYLES no longer match. "
              "Council has restyled them; update mapper.STYLES by hand, "
              "checking each is still legible over an aerial." % drift)
        return 1
    print("Every layer we match Council on is still in step.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
