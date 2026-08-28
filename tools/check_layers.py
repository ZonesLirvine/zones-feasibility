"""
Health check for every layer the tool depends on.

Run this before trusting a report on a job that matters, and any time results
look unexpectedly clean. It catches the specific failure mode that motivated
it: Auckland Council retired an old endpoint that still answered HTTP 200 with
a blank IIS placeholder page, so anything built against it would have looked
healthy while returning nothing.

    python tools/check_layers.py
"""

import os
import sys
import urllib.parse
import urllib.request
import json
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import layers as L                                # noqa: E402
import engine                                     # noqa: E402


# The probe itself lives in engine.probe_layer, which is what the pre-flight
# gate in run.py uses. This tool used to carry its own copy, and the copy went
# stale the moment engine learned about grouped layers: it crashed on the first
# layer whose service is a list. One implementation, so the standalone check
# and the gate can never disagree about what "healthy" means.
probe = engine.probe_layer


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    specs = ([dict(name=s["name"], service=s["service"]) for s in L.LAYERS]
             + [L.ZONE_LAYER, L.COASTLINE_LAYER, L.WIND_LAYER])

    print("Checking %d Auckland Council layers\n" % len(specs))
    bad = 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda s: (s, probe(s["service"])), specs))

    for spec, (status, detail) in results:
        if status != "OK":
            bad += 1
        print("  %-9s %-52s %s" % (status, spec["name"][:51], detail))

    # The parcel service is not a Council layer but everything depends on it.
    print()
    try:
        p = engine.parcel_at(174.76953, -36.6269)
        print("  %-9s %-52s %s" % (
            "OK" if p else "DOWN", "LINZ NZ Primary Parcels",
            p.get("legal_description") if p else "no parcel returned"))
        if not p:
            bad += 1
    except Exception as exc:                      # noqa: BLE001
        bad += 1
        print("  %-9s %-52s %s" % ("DOWN", "LINZ NZ Primary Parcels", exc))

    # Soil is a different host and a different protocol (Manaaki Whenua WMS,
    # not ArcGIS), so it cannot go through probe(). Its own probe queries a
    # point with a known answer, because MapServer returns HTTP 200 with an
    # XML exception body when it fails: reachable is not the same as working.
    print()
    try:
        import soil as SOIL                       # noqa: PLC0415
        status, detail = SOIL.probe()
        if status != "OK":
            bad += 1
        print("  %-9s %-52s %s" % (
            status, "Manaaki Whenua FSL soil classification", detail))
    except Exception as exc:                      # noqa: BLE001
        bad += 1
        print("  %-9s %-52s %s" % (
            "DOWN", "Manaaki Whenua FSL soil classification", exc))

    # Guard against the zone names in standards.py drifting from what the
    # Council layer actually returns. A mismatch is silent: the zone just
    # reports as unknown and nobody notices the standards stopped appearing.
    print()
    try:
        import standards as S                     # noqa: PLC0415
        names = set(engine.zone_domain().values())
        if not names:
            print("  %-9s %s" % ("SUSPECT", "zone domain returned no values"))
            bad += 1
        else:
            aliases = getattr(S, "ALIASES", set())
            stale = [k for k in list(S.ZONE_STANDARDS) + list(S.PENDING)
                     if k not in names and k not in aliases]
            if stale:
                bad += 1
                for k in stale:
                    print("  %-9s zone name not in Council's domain: %s"
                          % ("STALE", k))
            else:
                print("  %-9s %-52s %d zones mapped" % (
                    "OK", "standards.py zone names", len(S.ZONE_STANDARDS)))
    except Exception as exc:                      # noqa: BLE001
        bad += 1
        print("  %-9s %-52s %s" % ("DOWN", "zone name check", exc))

    print("\n%d checks, %d problem(s)." % (len(specs) + 3, bad))
    if bad:
        print("Do not issue a report to a client until these are resolved. A "
              "layer that cannot answer is not the same as a clear result.")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
