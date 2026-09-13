# Human cycle check (GITQA 70, pilot)

Five people. Each gets a link. One drawing, two loops, pick the one you can trace. A one-screen tutorial with a worked example shows first.

## What you do (once)

### 1. Google Sheet
1. Open [Google Sheets](https://sheets.google.com) and make a blank spreadsheet. Name it `gitqa-human-pilot`.
2. **Extensions → Apps Script**. Delete any starter code.
3. Paste the whole contents of `Code.gs` from this repo. Save.
4. At the top, choose function **`bindSheet`**, click **Run**, authorize if asked.
5. **Deploy → Manage deployments → pencil**.
   - Version: **New version**
   - Execute as: **Me**
   - Who has access: **Anyone**
   - Click **Deploy** (the dropdown alone does nothing).
6. In an incognito window open the `/exec?ping=1` URL. You must see `{"ok":true,"ping":true}`. If Google Drive says you need access, the deploy did not take.

Until ping shows JSON, answers stay only in the reviewer’s browser.

### 2. GitHub Pages (required for the public links)
Repo **Settings → Pages → Deploy from a branch → `main` / `/ (root)`** → Save.  
Until that is on, the github.io URL is 404. You can still test by opening `index.html` from this folder.

### 3. Send these links
Replace the host with your Pages URL:

- 40190: `...?who=40190`
- 40290: `...?who=40290`
- 40390: `...?who=40390`
- 40490: `...?who=40490`
- 40590: `...?who=40590`

Each person: 14 graphs, no overlap between reviewers.

## Sheet columns
`ts, who, graph_id, gitqa_id, choice_nodes, readable, correct, ms`

`correct` is 1 if they picked a rotation/reversal of the gold shortest cycle.

## Stats page
Open `stats.html` (same Pages site). It reads the Sheet live via
`?stats=1` and shows answered / 70, accuracy, per-reviewer progress,
and readability. If the Sheet is unreachable, upload the exported
Excel/CSV instead (File → Download → .xlsx, then choose it on the page).

> After pulling `Code.gs` changes, paste it into Apps Script again and
> **Deploy → New version**, or `?stats=1` will 404.
