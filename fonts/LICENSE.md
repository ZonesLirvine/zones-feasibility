# Bundled fonts

These are bundled deliberately so the tool renders identically on a machine that
is not Lee's Windows desktop. Before 28 August 2026 the code looked only in
`%LOCALAPPDATA%\Microsoft\Windows\Fonts` and `C:\Windows\Fonts`, so on Linux it
silently fell back to base-14 Helvetica, which has no macron glyphs. Every
Orakei, Mangere or Pukekohe address would have lost characters, and "Toitu Te
Whenua" would have printed with a gap.

| Family | Files | Licence |
|---|---|---|
| Montserrat | `montserrat-v31-*` | SIL Open Font License 1.1 |
| Open Sans | `open-sans-v44-*` | SIL Open Font License 1.1 |

Both licences permit redistribution, including bundled inside another work, so
long as the fonts are not sold on their own and the licence travels with them.
That is what this file is for.

## What is deliberately NOT here

**Arial and Segoe UI.** `mapper.py` used to fall back to `segoeui.ttf` and
`arial.ttf` for map labels. Both are Microsoft proprietary fonts, licensed with
Windows, and **must never be committed to this repository**. The map labels now
use bundled Open Sans instead. Do not reintroduce them.

## Subsets

`latin-ext` files come first in every lookup and the plain `latin` files are the
fallback. Only the ext subsets carry macrons. Keep both: the plain ones let the
tool still run somewhere only they exist, just without macrons.
