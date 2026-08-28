"""
Zones site feasibility check.

    python run.py "12 Example Road, Devonport"
    python run.py "12 Example Road, Devonport" --json out.json
    python run.py "12 Example Road, Devonport" --flags-only

Or the whole client binder, site check included:

    python run.py "12 Example Road, Devonport" --report sf-report.pptx \\
                  --client "Sarah Thompson"
"""

import argparse
import json
import os
import sys

import engine
import render

_WORKDIR = None


def _workdir():
    """
    Scratch space for intermediates: site maps and rasterised drawing sheets.

    These are embedded in the finished document and are of no use on their own,
    so they must not be written beside the output. The output usually lands in
    the client's job folder on Drive, where 20 MB of stray PNGs would sync and
    sit there looking like deliverables.
    """
    global _WORKDIR
    if _WORKDIR is None:
        import tempfile
        _WORKDIR = tempfile.mkdtemp(prefix="zones-feasibility-")
    return _WORKDIR


def main():
    # NZ place names carry macrons (Whangaparāoa, Ōrākei). The Windows console
    # defaults to cp1252 and will crash on them, so force UTF-8 output.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    p = argparse.ArgumentParser(description="Auckland site feasibility check")
    p.add_argument("address", help="Site address, Auckland only")
    p.add_argument("--json", metavar="PATH", help="also write raw results as JSON")
    p.add_argument("--flags-only", action="store_true",
                   help="hide the clear results (internal use, not for clients)")
    p.add_argument("--map", metavar="PATH", nargs="?", const="site-map.png",
                   help="also render a site map PNG (aerial with overlays)")
    p.add_argument("--pdf", metavar="PATH", nargs="?", const="site-report.pdf",
                   help="render the client-facing PDF (A4 portrait). Includes "
                        "the site map automatically.")
    p.add_argument("--page", choices=("a4", "a3"), default="a4",
                   help="a4 = A4 portrait report (default). a3 = A3 landscape "
                        "presentation sheets, designed for the folder.")
    p.add_argument("--pptx", metavar="PATH", nargs="?", const="site-report.pptx",
                   help="also export editable PowerPoint slides")
    p.add_argument("--docx", metavar="PATH", nargs="?", const="site-report.docx",
                   help="also export an editable Word document")
    p.add_argument("--report", metavar="PATH", nargs="?", const="sf-report.pptx",
                   help="build the whole S&F Report binder (16 slides, A4 "
                        "landscape), with the site feasibility pages generated "
                        "in place. Never gated on the site lookup: if the "
                        "address fails or the layer check fails, the site "
                        "pages fall back to a placeholder and the rest of the "
                        "binder still builds.")
    p.add_argument("--plans", metavar="PATH",
                   help="your drawing set for this job, to go in the design "
                        "section of --report. A PDF (every page becomes one "
                        "binder page, in order) or a single image. Replaces "
                        "the 2D plan, 3D render and selections placeholders.")
    p.add_argument("--client", metavar="NAME",
                   help="client name for the report's merge fields, e.g. "
                        "\"Sarah Thompson\"")
    p.add_argument("--note", metavar="TEXT",
                   help="your read on the site, in plain words. Appears near "
                        "the top of the A3 sheets as the headline finding.")
    p.add_argument("--skip-verify", action="store_true",
                   help="skip the layer health check before building documents "
                        "(not recommended for anything a client sees)")
    p.add_argument("--a3", action="store_true",
                   help="with --page a4, also write an A3 landscape version "
                        "with two A4 pages per sheet")
    args = p.parse_args()

    site_ok = True
    site_reason = None
    result = None
    try:
        result = engine.run(args.address)
    except engine.LookupError_ as exc:
        if not args.report:
            print("Lookup failed: %s" % exc, file=sys.stderr)
            return 2
        # The binder is never gated on the site lookup: fall back to the
        # placeholder site pages and still build the rest of the deck. The
        # address itself is not in doubt, only what Council could tell us
        # about it, so the cover and the merge fields still carry it.
        print("Lookup failed: %s (site pages will be a placeholder)"
              % exc, file=sys.stderr)
        site_ok = False
        site_reason = str(exc)

    if result:
        print(render.render(result, show_clear=not args.flags_only))

    # Health-check the layers before producing anything a client will read.
    # A layer that has been renamed or emptied upstream fails silently, and a
    # silent failure prints a clean page that says "clear".
    wants_doc = bool(args.pdf or args.pptx or args.docx)
    wants_site_data = wants_doc or (args.report and result)
    if wants_site_data and not args.skip_verify:
        problems = engine.verify_layers()
        if problems:
            print("\nLayer health check FAILED.", file=sys.stderr)
            for name, status, detail in problems:
                print("  %-9s %-48s %s" % (status, name[:47], detail),
                      file=sys.stderr)
            if wants_doc:
                print("\nRefusing to build a client document. A layer that "
                      "cannot answer is not the same as a clear result. "
                      "Resolve these, or re-run with --skip-verify if you "
                      "understand the risk.", file=sys.stderr)
                return 1
            # --report only: degrade the site pages, still build the binder.
            site_ok = False
            site_reason = ("The layer health check failed for this address; "
                           "see the log above.")
        else:
            result["verified"] = True

    site_for_docs = result if site_ok else None

    map_path = args.map
    if (args.pdf or args.pptx or args.docx or (args.report and site_for_docs)) \
            and not map_path:
        # The PDF always wants a map, so render one alongside it. It goes to
        # the working directory, not next to the output: the output often
        # lands in the client's job folder on Drive, and the maps and
        # rasterised drawing sheets are intermediates that get embedded in the
        # document anyway. Ask for --map if you want the PNG itself.
        base = args.pdf or args.pptx or args.docx or args.report
        map_path = os.path.join(_workdir(),
                                os.path.basename(os.path.splitext(base)[0])
                                + "-map.png")

    deck_map = None
    if map_path and site_for_docs:
        try:
            import mapper
            path = mapper.render_map(
                site_for_docs, map_path,
                chrome=not ((args.pdf or args.pptx or args.docx)
                            and not args.map),
                layout="wide" if args.page == "a3" else "stack")
            if not path:
                map_path = None
                print("\nSite map skipped: no parcel geometry for this "
                      "location.", file=sys.stderr)
            elif args.map:
                print("\nSite map written to %s" % path, file=sys.stderr)
        except Exception as exc:                  # noqa: BLE001
            map_path = None
            print("\nSite map could not be rendered: %s" % exc, file=sys.stderr)
    elif not site_for_docs:
        map_path = None

    # Slides need their own map. The shared one above carries the title band
    # whenever --map was asked for as a standalone file, which duplicates the
    # slide's own heading, and it is square whenever the page size is A4, which
    # leaves a landscape slide half empty. Both page sizes give landscape
    # slides, so the deck always wants a wide, chrome-free map.
    if map_path and (args.pptx or args.report):
        try:
            import mapper
            base = os.path.basename(
                os.path.splitext(args.pptx or args.report)[0])
            deck_map = os.path.join(_workdir(), base + "-slide-map.png")
            if not mapper.render_map(site_for_docs, deck_map, chrome=False,
                                     layout="wide"):
                deck_map = None
        except Exception as exc:                  # noqa: BLE001
            deck_map = None
            print("\nSlide map could not be rendered, falling back to the "
                  "report map: %s" % exc, file=sys.stderr)

    if args.pdf and not result:
        print("\nPDF skipped: no lookup result for this address.",
              file=sys.stderr)
    elif args.pdf:
        try:
            import report_pdf
            if args.page == "a3":
                import presentation_a3
                presentation_a3.build(result, args.pdf, map_path,
                                      note=args.note)
            else:
                report_pdf.build(result, args.pdf, map_path, size="a4")
            print("\nPDF written to %s (%s)" % (args.pdf, args.page.upper()),
                  file=sys.stderr)
            if args.a3 and args.page == "a4":
                a3 = os.path.splitext(args.pdf)[0] + "-A3.pdf"
                report_pdf.impose_a3(args.pdf, a3)
                print("A3 folder version written to %s" % a3, file=sys.stderr)
            elif args.a3:
                print("--a3 ignored: pages are already A3.", file=sys.stderr)
        except Exception as exc:                  # noqa: BLE001
            print("\nPDF could not be built: %s" % exc, file=sys.stderr)
            return 1

    for kind, path in (("pptx", args.pptx), ("docx", args.docx)):
        if not path:
            continue
        if not result:
            print("\n%s skipped: no lookup result for this address."
                  % kind.upper(), file=sys.stderr)
            continue
        try:
            import deck_export
            if kind == "pptx":
                deck_export.build_pptx(result, path, deck_map or map_path,
                                       size=args.page)
            else:
                deck_export.build_docx(result, path, map_path)
            print("\n%s written to %s" % (kind.upper(), path),
                  file=sys.stderr)
        except Exception as exc:                  # noqa: BLE001
            print("\n%s export failed: %s" % (kind.upper(), exc),
                  file=sys.stderr)

    # Drawing sheets for the design section. A PDF is rasterised a page at a
    # time: the sheets are vector A3 landscape, so 200 dpi keeps the 1:100
    # annotations legible once they land on an A4 binder page.
    design_sheets = None
    if args.plans:
        if not os.path.exists(args.plans):
            print("\nPlans not found: %s" % args.plans, file=sys.stderr)
            return 2
        if args.plans.lower().endswith(".pdf"):
            try:
                import fitz
                base = os.path.basename(
                    os.path.splitext(args.report or args.plans)[0])
                doc = fitz.open(args.plans)
                design_sheets = []
                for i, page in enumerate(doc, 1):
                    out = os.path.join(_workdir(),
                                       "%s-sheet%02d.png" % (base, i))
                    page.get_pixmap(dpi=200).save(out)
                    design_sheets.append(out)
                print("\n%d drawing sheet(s) read from %s"
                      % (len(design_sheets), args.plans), file=sys.stderr)
            except Exception as exc:              # noqa: BLE001
                print("\nPlans could not be read: %s" % exc, file=sys.stderr)
                return 1
        else:
            design_sheets = [args.plans]

    report_incomplete = False
    if args.report:
        report_path = args.report
        if not site_ok:
            # The rest of the binder (design, photos, materials, timeline) is
            # fine to keep building, but this file must not read as a
            # finished, sendable report. Mark it in the filename itself, so
            # it is obviously not-ready from the folder listing alone, before
            # anyone opens it or reaches the placeholder page.
            base, ext = os.path.splitext(args.report)
            report_path = base + "-DRAFT-SITE-INCOMPLETE" + ext
            report_incomplete = True
        try:
            import sf_report
            sf_report.build(site_for_docs, report_path, client=args.client,
                            map_path=deck_map or map_path,
                            site_reason=site_reason, address=args.address,
                            design_sheets=design_sheets)
            print("\nS&F Report written to %s" % report_path, file=sys.stderr)
            if not site_ok:
                print("SITE CHECK INCOMPLETE (%s). The YOUR SITE section is "
                      "a placeholder. Do not send this to the client until "
                      "you have re-run the check and rebuilt the report."
                      % site_reason, file=sys.stderr)
        except Exception as exc:                  # noqa: BLE001
            print("\nS&F Report could not be built: %s" % exc,
                  file=sys.stderr)
            return 1

    if args.json:
        if result:
            with open(args.json, "w", encoding="utf-8") as fh:
                json.dump(result, fh, indent=2)
            print("\nRaw results written to %s" % args.json, file=sys.stderr)
        else:
            print("\nJSON skipped: no lookup result for this address.",
                  file=sys.stderr)

    if result and result["errors"]:
        print("\n%d layer(s) could not be checked, see report."
              % len(result["errors"]), file=sys.stderr)
        return 1
    if report_incomplete:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
