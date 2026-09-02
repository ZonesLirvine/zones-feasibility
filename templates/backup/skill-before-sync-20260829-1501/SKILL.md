---
name: zones-feasibility
description: Zones Landscaping Auckland site feasibility check and S&F Report generator. Give it an address and it checks 40 Council and LINZ planning, hazard and buried-service records against the real property boundary, then builds either a standalone council feasibility report or the whole Scoping and Feasibility client binder around the result, covering the cover page, personal note, the client's own drawing sheets, the site findings, scope, timeline and budget. Always ask which of the two is wanted before building anything. Use this skill whenever the user mentions a site check, a feasibility check, an S&F report or binder, what is on this site, consent triggers, planning overlays, zone standards, buried services, wastewater or water mains, or gives an Auckland address for a landscaping job, even when they do not name the tool. Also use it for questions about what a site is zoned, what they are allowed to build on, how much hard surface is allowed, or whether something is likely to need consent.
---

# Zones Site Feasibility

Auckland-only site feasibility check for Zones Landscaping, and the generator
for the whole S&F Report client binder. Python, no API keys, all data is
Auckland Council open data, Council's GeoMaps asset server, and LINZ.

The code is in `scripts/`. Run everything from there.

## What it produces

Two deliverables, and **which one is always Lee's call, never an assumption**.
See step 3 of the workflow: ask before building either.

**The full presentation**, the whole S&F client binder:

```bash
python run.py "<address>" --report "<job>.pptx" --client "<Client Name>"
```

A4 landscape, one slide per ring-binder page: how to use (internal), cover,
personal note from Lee, contents, the design section, the YOUR SITE divider,
four site feasibility pages generated in place, scope of work, timeline, budget
range, how we work, what happens next. Note that scope, timeline and budget are
placeholders Lee fills in, so this is the start of a client pack rather than a
finished one.

**Just the council feasibility**, the site read on its own:

```bash
python run.py "<address>" --pdf "<job>.pdf"
```

A4 portrait, site map, property and zone standards, every finding and the full
notice. Nothing to fill in, so it is complete the moment it is built.

Other outputs, all optional and independent:

| Flag | Gives |
|---|---|
| `--report PATH` | the whole S&F binder (the main deliverable) |
| `--client "Name"` | fills the client name into the binder's merge fields |
| `--plans PATH` | the job's drawing set, PDF or image, into the design section |
| `--pdf PATH` | client-facing A4 portrait report, site map included |
| `--page a3` | with `--pdf`, A3 landscape presentation sheets instead |
| `--pptx PATH` | just the four site pages, as editable slides |
| `--docx PATH` | just the four site pages, as Word |
| `--map PATH` | the site map on its own, as a PNG |
| `--json PATH` | the raw findings, useful for rebuilding without re-querying |
| `--note "..."` | your plain-English read of the site, printed on A3 sheet 1 |
| `--flags-only` | hide the clear results. Internal only, never for a client |
| `--skip-verify` | skip the layer health check. Never for client work |

Roughly 9 to 12 seconds per address, nearly all of it waiting on Council.

## Before you touch the outputs, understand what the tool is for

This document goes to a homeowner who is about to spend money, and it gets read
as a statement of fact about their property. Almost every rule below exists
because the alternative is a client digging into a live main, or budgeting for a
build that needs a consent nobody mentioned.

The single worst failure is a **false all-clear**: the report saying nothing was
found when something is there, or when nothing was actually checked. Several
guards exist specifically to prevent that, and they are easy to undo by
accident. If you are changing behaviour, read `references/safeguards.md` first.

## The workflow

1. **Get the address.** Auckland only. If the user gives a job folder or a
   project name instead, find the address before running anything.
2. **Run the check.** Start with the address alone to see the findings in the
   terminal, so you can talk about them before committing to a document.
3. **Always ask which deliverable Lee wants. Every run, before building
   anything.** Two options, and do not assume from context which one it is:

   - **the full presentation** — the whole S&F client binder (`--report`),
     cover through budget, with the site pages generated inside it
   - **just the council feasibility** — the A4 PDF on its own (`--pdf`), site
     map and findings, no cover, scope, timeline or budget

   Ask even when the request mentions a client, an owner name or a job folder.
   None of those settle it: the binder is a full client pack that needs scope
   and budget written into it before it can go anywhere, and most of the time
   what is actually wanted is the feasibility read on the site. Building the
   binder unasked produces seventeen pages of placeholders Lee did not want.

   The A3 sheets (`--pdf --page a3`) are a third option, but only offer them if
   he asks or mentions a presentation: they are for spreading on a table, not
   for reading. `--pptx` and `--docx` are for when he wants to edit the site
   pages, not a deliverable in their own right.
4. **Include the drawing set** with `--plans` if the job has one. Each sheet
   becomes its own binder page in the design section, in order.
5. **Write the output into the job folder**, not a temp directory, so the
   client's file lives with the rest of the job. The Drive layout is
   `G:\My Drive\_Zones\Projects\<year>\<Suburb>_<street> <number>\01_Scoping & Design\`.
6. **Check the result before handing it over.** See `references/verifying.md`.
   Do not tell the user a document is right without having looked at it.

## Reading the findings back to a client

Findings carry one of six statuses. What they mean matters more than the word:

- **on_site** — it is on or right beside the property. This is what shapes the
  design and the budget.
- **abuts** — the boundary runs along it, but none of the land is inside it.
  Reads as ADJOINS. It does not control what can be built, and it never reaches
  the consent draft, but it is still flagged and still drawn on the map: it
  usually means the adjoining owner is a school, a reserve or the Crown, which
  matters for anything built on that boundary. See the overlap threshold in
  `references/safeguards.md`.
- **nearby** — within 200 m but not on the property. Worth knowing, rarely
  controls anything.
- **clear** — checked, nothing there. Always shown, never hidden. "We checked
  40 things and 28 are clear" is a large part of what the S&F fee buys, and
  hiding it makes the report look thin.
- **partial** — nothing found, but the published data does not cover this
  fully, so it cannot be called clear. Wastewater and water are the cases:
  public mains are complete, private laterals are in no public record at all.
  Reads as NOT CONFIRMED and points at beforeUdig.
- **error** — the layer could not answer. Never the same as clear.

When summarising for a user, lead with what is on the property and what it does
to the design or the cost. A list of overlay names is not useful to anyone; a
sentence about needing a geotech assessment for the retaining is.

## The soil section

Separate from the findings and deliberately so: a soil classification is not a
pass or a fail, so it never enters the counts. It sits after the zone
standards, in the terminal and in the A4 PDF.

The source is Manaaki Whenua's Fundamental Soil Layer, **not S-map**, because
S-map has no keyless API. Never call it S-map to a client. It does not map
built-up land, so established Auckland Central suburbs report as not mapped
while fringe and greenfield jobs answer. Both the reason and the measured
coverage are in `references/data-sources.md`.

Where it does answer it is worth leading with, because it speaks directly to
drainage: at 6E Crows Road it returned Impeded Allophanic Soil, "a hard layer
that impedes roots and water", which is the mud the client is complaining
about.

## Things that will bite you

**Never send a file named `-DRAFT-SITE-INCOMPLETE`.** The tool adds that suffix
and exits 3 when the site check could not complete. The rest of the binder is
still fine to work on, but the YOUR SITE section is a placeholder, not a result.
Re-run once the address resolves or Council's data is back.

**The binder is never gated on the site lookup.** If the address fails or
Council is down, everything else still builds. That is deliberate: Lee still
needs his binder. Do not "fix" this by making it refuse.

**A failed lookup does not make the address unknown.** Lee typed it and has been
to the site. The address still prints on the cover, letter, divider and closing
page. What changes is that claims about the *check* drop to what we do rather
than what we found.

**Never use the open data portal for buried services.** Council publishes model
subsets prefixed `wm_` that look like the real network and are about a tenth of
it. Details and the full layer registry in `references/data-sources.md`.

**Non-residential zones are not loaded.** Business, Open Space and Rural report
"standards not held" rather than guessing. Do not invent figures for them.

## Reference files

Read these when the task calls for them, not upfront:

- `references/data-sources.md` — where every layer comes from, the `wm_` trap,
  how to add a layer, the position tolerance on buried services, and what is
  deliberately not covered (contaminated land, covenants, power and fibre).
- `references/safeguards.md` — the guards that stop a false all-clear, and why
  each exists. Read before changing engine or layer behaviour.
- `references/verifying.md` — how to render and check a document on a machine
  with no LibreOffice, plus the test addresses that exercise different paths.
- `references/the-binder.md` — the binder's page order, what is placeholder
  versus generated, the merge fields, and how `--plans` slots the drawing set in.

## Dependencies

Python 3.9+. `PyMuPDF` and `Pillow` for the PDF and the map; `python-pptx` and
`python-docx` for the editable exports; `shapely` to measure how much of an
overlay actually lands on the parcel. No API keys, no account, nothing to
configure.

```bash
pip install pymupdf pillow python-pptx python-docx shapely
```

Without `shapely` everything still runs, but the boundary-sliver test cannot be
measured and every intersecting overlay reports as `on_site`, which is the old
behaviour and errs toward over-flagging.

Health-check the data sources any time something looks wrong:

```bash
python tools/check_layers.py
```

44 probes, and it fails loudly rather than letting a renamed layer quietly
report "clear".
