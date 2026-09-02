# Verifying a document before you hand it over

The outputs are client-facing and printed. Never tell the user a document is
right without having looked at it.

## Rendering on Windows without LibreOffice

Lee's machine has no `soffice`, no `pdftoppm` and no LibreOffice, so the usual
PDF and pptx rendering instructions fail. Do not reach for them. Use the real
Office apps over COM, which is more faithful anyway, then rasterise with
PyMuPDF, which is already a dependency.

PowerPoint to PDF:

```powershell
$ppt = New-Object -ComObject PowerPoint.Application
$p = $ppt.Presentations.Open("$env:TEMP\out.pptx", $true, $false, $false)
$p.SaveAs("$env:TEMP\out.pdf", 32); $p.Close(); $ppt.Quit()
```

PDF to PNG:

```python
import fitz
for i, page in enumerate(fitz.open("out.pdf")):
    page.get_pixmap(dpi=110).save("p%02d.png" % (i + 1))
```

`Read` the PNGs and actually look at them. Note that the `Read` tool renders
PDFs through `pdftoppm`, which is not installed here, so go through PyMuPDF
rather than pointing `Read` at a PDF.

## What to look for

Check every page, not a sample. Layout bugs cluster on the pages with the most
content, which are exactly the ones a sampling pass skips.

- **Text overflowing its box.** Most of this deck is fixed-position, so a
  string that grew (a longer address, a job with more findings, a list that
  gained an item when a layer was added) silently runs into whatever is below.
- **Anything inside the 25 mm left margin.** That is the ring binder punch. A
  quick programmatic check:

  ```python
  from pptx import Presentation
  from pptx.util import Mm
  for i, s in enumerate(Presentation(path).slides, 1):
      for sh in s.shapes:
          if sh.left is not None and sh.left < Mm(25) and sh.width < Mm(290):
              print(i, sh.shape_type, sh.left / 36000)
  ```

  Full-bleed furniture (banners, caption bars) is allowed to cross it.
- **Placeholder text that should have been filled**, and merge tokens like
  `{{Name}}` left in when a value was available.
- **The map.** Every layer flagged in the findings table should appear on the
  map and in its legend. A findings row saying NEEDS ATTENTION with nothing on
  the map beside it is a real bug and has happened.
- **Counts that should agree.** The figure strip on A3 sheet 3 sums to the
  records checked. If it does not, a status is being counted in the wrong
  bucket.

## Iterate without hammering Council

Write the findings once, then rebuild documents from that file:

```bash
python run.py "<address>" --json findings.json --report out.pptx
```

```python
import json, sf_report
r = json.load(open("findings.json", encoding="utf-8"))
sf_report.build(r, "out.pptx", client="...", map_path="...", address="...")
```

That saves the 9 to 12 second wait per iteration and keeps you off Council's API
while you are only changing layout.

## Fonts

Montserrat and Open Sans are installed to Lee's user font store. They render
from the web in Google Docs, but Office needs them present locally. If a fresh
machine renders the deck in Calibri, that is why, and it is a machine setup
issue rather than a bug in the tool.

**Use the latin-ext builds, not latin.** The PDF renderers embed the font file
rather than asking the OS for a substitute, so a glyph the file does not carry
is dropped without a warning. The latin subsets have no macrons: "Toitū Te
Whenua" printed as "Toit  Te Whenua" in every PDF this tool has produced, and
an Ōrākei, Māngere or Pukekōhe address would have lost characters from the
header of every page. The pptx never showed it because PowerPoint substitutes a
font of its own, so the binder looked fine while the PDF was wrong.

`FONT_FILES` in `report_pdf.py` and `presentation_a3.py` lists latin-ext first
and latin second, so a machine with only the old files still runs, just without
macrons. Check a machine before trusting its PDFs:

```python
import fitz, report_pdf as P
f = fitz.Font(fontfile=P._font_path(P.FONT_FILES["body"]))
print(all(f.has_glyph(c) for c in (0x0101, 0x0113, 0x012B, 0x014D, 0x016B)))
```

False means the latin-ext files are missing. Re-fetch them from the Google
Fonts CSS API with a normal user agent and `&subset=latin-ext`; an old IE agent
returns an extensionless kit URL instead of a `.ttf` and is no use.

## Test addresses

Each exercises a different shape of job. Use more than one when changing
anything that affects layout.

| Address | Exercises |
|---|---|
| `66 Rhinevale Close` | Henderson, H3, three buried services on site, a second zone warning, backs onto bush |
| `15e Balmain Road, Birkenhead` | H3, bush gully, many flagged, so both the flagged and clear paths |
| `33 Marine Parade, Herne Bay` | 9 on-property findings, fills and overflows the card grid |
| `75 Karekare Road, Karekare` | H2 zone, exercises the `n/a` standards tiles |
| `985 Whangaparaoa Road, Tindalls Beach` | the validation case against the feasibility.co.nz sample report |

## Validated against

The feasibility.co.nz sample report for 985 Whangaparaoa Road (7 Jul 2026).
Every field this tool covers matches: zone, site area, legal description, title
number, the SEA overlay, coastal inundation, all four coastal erosion scenarios,
both landslide layers, and all four flood layers reading clear. Boundary
dimensions cross-check to within 0.2 m.

Note LINZ's own surveyed area and the area calculated from their boundary
geometry disagree (1,416 m² against 1,477 m² on that property). That gap is in
LINZ's data. The report shows the surveyed figure and labels its source.
