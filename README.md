# Human cycle check (GITQA 70, pilot)

Four people. Each gets a link. One drawing, four loops, pick the one you can trace.

## What you do (once)

### 1. Google Sheet
1. Open [Google Sheets](https://sheets.google.com) and make a blank spreadsheet. Name it `gitqa-human-pilot`.
2. **Extensions → Apps Script**. Delete any starter code.
3. Paste the whole contents of `Code.gs` from this repo. Save.
4. **Deploy → New deployment → Web app**.
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Authorize (Google asks you, once).
6. Copy the URL that ends with `/exec`.
7. Open `config.js` in this repo. Put that URL in `scriptUrl`. Commit and push.

Until step 7 is done, answers still save in the reviewer’s browser. After step 7 they also land in the Sheet.

### 2. GitHub Pages
Repo **Settings → Pages → Deploy from a branch → `main` / `/ (root)`**.  
Site: `https://<you>.github.io/gitqa-human-cycle-pilot/`

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
