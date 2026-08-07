# Scio — Design tokens & visual reference

Direction: **drafting table / blueprint** (see ADR-0003). Quiet, precise, engineered.
These tokens are the single source of truth. In Phase 1.2 / 2.1 they are consumed as CSS
variables + a Tailwind config shared by the app and the website.

## Colour — light (default)
- ink            #14181C   (text, structure)
- muted          #586268   (secondary text)
- paper          #E7EBEA   (page background — cool draft paper, deliberately not cream)
- surface        #F5F7F6   (cards, panels)
- line           #C6CFD1   (hairlines)
- line-strong    #93A1A6   (construction lines, stronger dividers)
- teal           #0B5563   (primary — deepwater)
- teal-hover     #094650
- teal-tint      #DCE8E9   (ghost hover, subtle fills)
- verified       #2F7A57   (semantic: works)
- attention      #B07D2B   (semantic: needs a look — also the honest-status colour)
- error          #A5432E   (semantic: error)

## Colour — dark (first-class)
- ink            #EAEEEF
- muted          #8C989E
- paper          #121619
- surface        #1A2024
- line           #2C353A
- line-strong    #3C474D
- teal           #3FA8B8
- teal-hover     #57BAC9
- teal-tint      #16323A
- verified       #5FB088
- attention      #D4A44E
- error          #D6725C

## Typography
- Display: **Space Grotesk** (500 / 600) — headings, wordmark. Technical character, used with restraint.
- Body / UI: **IBM Plex Sans** (400 / 500 / 600).
- Utility / data: **IBM Plex Mono** (400 / 500) — labels, version hashes, "your code". Brand signal.
- Scale (starting): display 34 / subhead 22 / body 15-16 / utility 11-13. Tight letter-spacing on display.

## Shape, spacing, motion
- Radius: 7px (cards), 5px (buttons, number tiles). Precise, not pill, not sharp-cold.
- Structure via thin 1px lines and dividers (drafting feel) rather than heavy shadows.
- 4px spacing grid; generous whitespace.
- Motion minimal: things land, they don't bounce. Respect prefers-reduced-motion.

## Components (notes)
- Buttons: primary (teal fill), secondary (ink outline), ghost (teal text, tint hover). Visible focus ring.
- Inputs: paper fill, teal focus border, mono "Ex: ..." helper under wizard fields.
- Honest-status chips: works (verified) / needs a look (attention) / error — muted, never candy.
- Wholeness panel: a calm blueprint surface; assumptions marked with a small mono "assumed" tag.
- Number-annotation tiles: small mono squares (radius 5), teal — the signature, used on design + running app.
- Construction-line motif: faint corner ticks + a coordinate ruler on the design surface (the one aesthetic risk).

## Signature
Mark -> number -> describe -> update: the product's own editing mechanic, rendered as the brand.
