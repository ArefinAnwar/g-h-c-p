# Human cycle check (Ring500: 250 GITQA + 250 generated, ring only)

Five people. Each gets a link. One ring drawing, two loops, pick the one you
can trace. A one-screen tutorial with worked examples shows first.

Dataset source: `scale500_pilot20` in the research workspace
(500 strict-ring layouts, verify 500/500).
Only `*_circular.png` ring drawings are used here — no base/circo/spring.
Graph order is interleaved GITQA/generated, so every reviewer's 100-set is
50 GITQA + 50 generated. Each graph is seen by exactly one reviewer.

The original 70-graph pilot is archived in [`pilot70/`](pilot70/) (own sheet,
own links, untouched).

## What you do (once)

### 1. Google Sheet (make a NEW one, not the 70-pilot sheet)
1. Open [Google Sheets](https://sheets.google.com) and make a blank spreadsheet. Name it `ring500-human`.
2. **Extensions → Apps Script**. Delete any starter code.
3. Paste the whole contents of `Code.gs` from this repo. Save.
4. At the top, choose function **`bindSheet`**, click **Run**, authorize if asked.
5. **Deploy → Manage deployments → pencil**.
   - Version: **New version**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy** (the dropdown alone does nothing).
6. Paste the `/exec` URL into `config.js` (`scriptUrl`), commit it.
7. In an incognito window open the `/exec?ping=1` URL. You must see `{"ok":true,"ping":true}`. If Google Drive says you need access, the deploy did not take.

Until ping shows JSON, answers stay only in the reviewer's browser.

### 2. GitHub Pages (required for the public links)
Repo **Settings → Pages → Deploy from a branch → `main` / `/ (root)`** → Save.
Until that is on, the github.io URL is 404. You can still test by opening `index.html` from this folder.

### 3. Send these links
Replace the host with your Pages URL:

- 40190: `...?who=40190` (graphs r000–r099: 50 GITQA + 50 generated)
- 40290: `...?who=40290` (graphs r100–r199: 50 GITQA + 50 generated)
- 40390: `...?who=40390` (graphs r200–r299: 50 GITQA + 50 generated)
- 40490: `...?who=40490` (graphs r300–r399: 50 GITQA + 50 generated)
- 40590: `...?who=40590` (graphs r400–r499: 50 GITQA + 50 generated)

Each person: 100 graphs, no overlap between reviewers.

## Sheet columns
`ts, who, graph_id, gitqa_id, choice_nodes, readable, correct, ms`

`correct` is 1 if they picked a rotation/reversal of the gold shortest cycle.
`gitqa_id` holds the GITQA numeric id (1070–1319) or `gen-<stem>` for generated
graphs. `graph_id` 0–499 matches `manifest.csv` and `items.json`.

## Trace files (all committed)
- `manifest.csv` — one row per graph: graph_id, image, source, pack_id,
  gitqa_ref, n, m, girth, cycles, longest_cycle, crossings, ring_order,
  gold_cycle, foil_kind, reviewer. Foils are `premature` (345) or `adjacent`
  (155); no filler triples were needed.
- `assignments.json` — hardcoded disjoint 100-sets per reviewer code.
- `items.json` / `gold.json` — site payload and gold shortest cycles.
- `build_ring500.py` — rebuilds everything from the workspace `scale500_pilot20`.

> After pulling `Code.gs` changes, paste it into Apps Script again and
> **Deploy → New version**, or `?stats=1` will 404.
