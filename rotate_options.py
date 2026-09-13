"""Regenerate Ring500 options deterministically, then display-rotate them with
counterbalanced constraints (code-only; drawings/labels/gold untouched).

Step 1 (reproduction): rebuild each item's ORIGINAL options exactly as
build_ring500.py did (same helpers, same seed 500+gid) and assert the gold
norm-matches gold.json. This recovers the pre-rotation sequences.
Step 2 (constrained rotation, seed 7000+gid): random flip + rotation per
option, rejection-sampled so that
  (R1) no displayed option starts with 0 and ends with 1, and
  (R2) both options in a trial share start-with-0 status (both or neither),
so no first-node rule can beat chance. A/B positions are NOT reshuffled,
Code.gs grading (rotation/reversal invariant) is untouched, and rows already
collected stay valid.
Writes: items.json, manifest.csv (gold_cycle display text + display_note).
"""
from __future__ import annotations

import csv
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT.parent
sys.path.insert(0, str(WORK / "pilot"))
from replication_v2.ring_layout import _draw_ring_ax  # noqa: F401 (same env as build)
import build_ring500 as B


def norm(nodes: list[int]) -> tuple[int, ...]:
    n = [int(x) for x in nodes]
    if len(n) >= 2 and n[0] == n[-1]:
        n = n[:-1]
    best = None
    for seq in (n, list(reversed(n))):
        i = seq.index(min(seq))
        rot = tuple(seq[i:] + seq[:i])
        if best is None or rot < best:
            best = rot
    return best or tuple()


def fmt(nodes: list[int]) -> str:
    return " \u2013 ".join(str(x) for x in nodes)


def rotated(nodes: list[int], rng: random.Random) -> list[int]:
    seq = list(nodes) if rng.random() < 0.5 else list(reversed(nodes))
    k = rng.randrange(len(seq))
    return seq[k:] + seq[:k]


def ok(seq: list[int]) -> bool:
    return not (seq[0] == 0 and seq[-1] == 1)


def main() -> None:
    pack = json.load((ROOT / "items.json").open(encoding="utf-8"))
    gold = json.load((ROOT / "gold.json").open(encoding="utf-8"))
    recs = {g["id"]: g for g in json.load((WORK / "scale500_pilot20" / "gold" / "graphs.json").open(encoding="utf-8"))["graphs"]}
    pos_raw = json.load((WORK / "scale500_pilot20" / "layouts" / "positions_circular.json").open(encoding="utf-8"))
    rows = list(csv.DictReader((ROOT / "manifest.csv").open(encoding="utf-8")))
    man = {int(r["graph_id"]): r for r in rows}

    for e in pack["items"]:
        gid = e["graph_id"]
        g = norm(gold[str(gid)])
        rec = recs[man[gid]["pack_id"]]
        G = B.adj_to_graph(rec["gold_adjacency"])
        raw = pos_raw[rec["id"]]["circular"]
        pos = {int(k): (float(v[0]), float(v[1])) for k, v in raw.items()}
        order = B.ring_order_from_pos(pos)
        _, opts = B.two_options(G, order, random.Random(500 + gid))
        # Identify gold/foil in reproduced options; keep original A/B ids.
        seqs = {}
        for o in opts:
            seqs["gold" if norm(o["nodes"]) == g else o["kind"]] = (o["id"], [int(x) for x in o["nodes"]])
        assert "gold" in seqs and len(seqs) == 2, f"repro failed on {gid}"
        foil_key = next(k for k in seqs if k != "gold")
        rng = random.Random(7000 + gid)
        for _ in range(10000):
            gs = rotated(seqs["gold"][1], rng)
            fs = rotated(seqs[foil_key][1], rng)
            if ok(gs) and ok(fs) and (gs[0] == 0) == (fs[0] == 0):
                break
        else:
            raise RuntimeError(f"no counterbalanced rotation for {gid}")
        assert norm(gs) == g and norm(fs) != g
        for o in e["options"]:
            seq = gs if o["id"] == seqs["gold"][0] else fs
            o["nodes"] = seq
            o["label"] = fmt(seq)
        man[gid]["gold_cycle"] = fmt(gs)
        man[gid]["display_note"] = "options randomly rotated/flipped with counterbalance (seed 7000+gid); drawing+gold unchanged"

    (ROOT / "items.json").write_text(json.dumps({"items": pack["items"]}, indent=2), encoding="utf-8")
    with (ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"rewrote {len(pack['items'])} items with counterbalanced rotations")


if __name__ == "__main__":
    main()
