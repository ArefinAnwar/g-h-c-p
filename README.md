# Human cycle check (GITQA 70, pilot)

Four people. Each gets a link. One drawing, two loops, pick the one you can trace.

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

- r1: `...?who=r1`
- r2: `...?who=r2`
- r3: `...?who=r3`
- r4: `...?who=r4`

Each person: 20 shared graphs (all four see these) plus their own slice (~12–13). About 32–33 graphs each.

## Sheet columns
`ts, who, graph_id, gitqa_id, choice_nodes, readable, correct, ms`

`correct` is 1 if they picked a rotation/reversal of the gold shortest cycle.
