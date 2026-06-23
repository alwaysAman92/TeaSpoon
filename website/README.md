# TeaSpoon Landing Page

A single static page (PRD Section 8) in the TeaSpoon design language: one blunt
headline, three oversized stat callouts, four one-line steps, blunt
differentiator blocks, CSS phone mockups of the real screens, a credibility
note, and store badges. No backend, no email capture, no pricing.

## Run locally

```bash
python3 -m http.server 5173
# open http://localhost:5173
```

## Deploy (free, per the PRD)

- **GitHub Pages**: push `website/` to a repo and enable Pages.
- **Domain**: free `.me` (Namecheap) or `.tech` via the GitHub Student Pack.

## Files

```
index.html   # structure + content
styles.css   # design system (shares the app palette)
script.js    # count-up stats + scroll reveal (no dependencies)
```
