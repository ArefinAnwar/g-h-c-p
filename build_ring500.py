"""Build 500 Ring PNGs (web size) + 2-choice items for the human ring500 pilot.

Reads ../scale500_pilot20 (gold graphs + strict-ring positions + VERIFY crossings).
Writes into this folder: images/r{idx:03d}_circular.png, items.json, assignments.json,
gold.json, Code.gs, manifest.csv.

Order: interleaved gitqa / generated so each reviewer's 100-set is 50/50.
Five disjoint reviewer sets, same opaque codes as the 70-pilot (40190..40590).
"""
from __future__ import annotations

import csv
import json
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent / "pilot"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx

from replication_v2.ring_layout import _draw_ring_ax

PACK = ROOT.parent / "scale500_pilot20"
OUT_IMG = ROOT / "images"
FIGSIZE = (9.0, 9.0)
DPI = 110
CODES = ["40190", "40290", "40390", "40490", "40590"]
PER_REVIEWER = 100


def adj_to_graph(adj: dict) -> nx.Graph:
    G = nx.Graph()
    for u, vs in adj.items():
        u = int(u)
        G.add_node(u)
        for v in vs:
            G.add_edge(u, int(v))
    return G


def norm_cyc(nodes: list[int]) -> tuple[int, ...]:
    n = [int(x) for x in nodes]
    if len(n) >= 2 and n[0] == n[-1]:
        n = n[:-1]
    if len(n) < 3:
        return tuple()
    best = None
    for seq in (n, list(reversed(n))):
        i = seq.index(min(seq))
        rot = tuple(seq[i:] + seq[:i])
        if best is None or rot < best:
            best = rot
    return best or tuple()


def fmt_cyc(nodes: list[int]) -> str:
    n = [int(x) for x in nodes]
    if n and n[0] == n[-1]:
        n = n[:-1]
    return " – ".join(str(x) for x in n)


def shortest_cycle(G: nx.Graph) -> list[int]:
    best: list[int] | None = None
    for u, v in G.edges():
        H = G.copy()
        H.remove_edge(u, v)
        try:
            p = nx.shortest_path(H, u, v)
        except nx.NetworkXNoPath:
            continue
        if best is None or len(p) < len(best):
            best = [int(x) for x in p]
    return best or []


def other_gold_cycle(G: nx.Graph, gold: list[int]) -> list[int] | None:
    gset = set(norm_cyc(gold))
    cands: list[list[int]] = []
    for cyc in nx.cycle_basis(G):
        c = [int(x) for x in cyc]
        if len(c) >= 3 and set(norm_cyc(c)) != gset:
            cands.append(c)
    if not cands:
        return None
    cands.sort(key=lambda c: (len(c), norm_cyc(c)))
    return cands[0]


def premature_close(gold: list[int], G: nx.Graph) -> list[int] | None:
    n = [int(x) for x in gold]
    if len(n) < 4:
        return None
    fake = n[:-1]
    a, b = fake[0], fake[-1]
    if G.has_edge(a, b):
        return None
    if len(fake) < 3:
        return None
    return fake


def ring_order_from_pos(pos: dict[int, tuple[float, float]]) -> list[int]:
    def ang(n: int) -> float:
        x, y = pos[n]
        return math.atan2(y, x)

    return sorted(pos.keys(), key=ang)


def adjacent_fake(G: nx.Graph, order: list[int], gold: list[int]) -> list[int] | None:
    gset = set(norm_cyc(gold))
    for i, a in enumerate(order):
        b = order[(i + 1) % len(order)]
        if G.has_edge(a, b):
            continue
        for w in G.neighbors(a):
            w = int(w)
            if w == b:
                continue
            if G.has_edge(w, b):
                cyc = [int(a), w, int(b)]
                if set(norm_cyc(cyc)) != gset:
                    return cyc
        for w in order:
            if w in (a, b):
                continue
            if G.has_edge(a, w) and G.has_edge(w, b):
                cyc = [int(a), int(w), int(b)]
                if set(norm_cyc(cyc)) != gset:
                    return cyc
        nbrs = [int(x) for x in G.neighbors(a) if int(x) != b]
        if nbrs:
            cyc = [int(a), nbrs[0], int(b)]
            if set(norm_cyc(cyc)) != gset and len(set(cyc)) == 3:
                return cyc
    return None


def two_options(G: nx.Graph, order: list[int], rng: random.Random) -> tuple[list[int], list[dict]]:
    gold = shortest_cycle(G)
    if len(gold) < 3:
        raise RuntimeError("no cycle")
    seen = {norm_cyc(gold)}
    pool: list[tuple[str, list[int]]] = [("gold", gold)]
    for kind, cyc in (
        ("premature", premature_close(gold, G)),
        ("adjacent", adjacent_fake(G, order, gold)),
        ("other", other_gold_cycle(G, gold)),
    ):
        if cyc and len(cyc) >= 3 and norm_cyc(cyc) not in seen:
            seen.add(norm_cyc(cyc))
            pool.append((kind, cyc))
            break
    if len(pool) < 2:
        for cyc in nx.cycle_basis(G):
            c = [int(x) for x in cyc]
            if len(c) >= 3 and norm_cyc(c) not in seen:
                seen.add(norm_cyc(c))
                pool.append(("other", c))
                break
    if len(pool) < 2:
        nodes = list(G.nodes())
        for _ in range(20):
            a, b, c = rng.sample(nodes, 3)
            if norm_cyc([a, b, c]) not in seen:
                pool.append(("filler", [a, b, c]))
                break
    pool = pool[:2]
    rng.shuffle(pool)
    opts = [{"id": i, "kind": k, "nodes": cyc, "label": fmt_cyc(cyc)} for i, (k, cyc) in enumerate(pool)]
    return gold, opts


def main() -> None:
    gold_payload = json.loads((PACK / "gold" / "graphs.json").read_text(encoding="utf-8"))
    pos_raw = json.loads((PACK / "layouts" / "positions_circular.json").read_text(encoding="utf-8"))
    verify = {r["id"]: r for r in json.loads((PACK / "VERIFY.json").read_text(encoding="utf-8"))["rows"]}
    recs = gold_payload["graphs"]
    gitqa = [g for g in recs if g.get("source") == "gitqa"]
    gen = [g for g in recs if g.get("source") == "generated"]
    assert len(gitqa) == 250 and len(gen) == 250, (len(gitqa), len(gen))

    # Interleave: gitqa, gen, gitqa, gen ... -> each 100-chunk is 50/50.
    ordered: list[dict] = []
    for i in range(250):
        ordered.append(gitqa[i])
        ordered.append(gen[i])
    assert len(ordered) == 500

    OUT_IMG.mkdir(parents=True, exist_ok=True)
    items = []
    gold_map: dict[str, list[int]] = {}
    manifest: list[dict] = []
    for idx, g in enumerate(ordered):
        G = adj_to_graph(g["gold_adjacency"])
        raw = pos_raw[g["id"]]["circular"]
        pos = {int(k): (float(v[0]), float(v[1])) for k, v in raw.items()}
        meta = g.get("ring_meta") or {}
        png = f"r{idx:03d}_circular.png"
        fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
        fig.patch.set_facecolor("white")
        fig.subplots_adjust(left=0.03, right=0.97, bottom=0.03, top=0.97)
        _draw_ring_ax(ax, G, pos, float(meta.get("node_size", 300.0)), int(meta.get("font_size", 12)))
        fig.savefig(OUT_IMG / png, dpi=DPI, facecolor="white")
        plt.close(fig)
        order = ring_order_from_pos(pos)
        rng = random.Random(500 + idx)
        gold_cyc, opts = two_options(G, order, rng)
        gold_map[str(idx)] = list(norm_cyc(gold_cyc))
        ref = str(g.get("gitqa_id")) if g.get("source") == "gitqa" else f"gen-{g['id']}"
        items.append(
            {
                "graph_id": idx,
                "gitqa_id": ref,
                "image": "images/" + png,
                "options": [{"id": o["id"], "label": o["label"], "nodes": o["nodes"]} for o in opts],
                "kinds": [o["kind"] for o in opts],
            }
        )
        v = verify.get(g["id"], {})
        manifest.append(
            {
                "graph_id": idx,
                "image": png,
                "source": g.get("source"),
                "pack_id": g["id"],
                "gitqa_ref": ref,
                "n": g.get("num_nodes"),
                "m": g.get("num_edges"),
                "girth": g.get("girth"),
                "cycles": g.get("n_cycles") if g.get("n_cycles") is not None else len(nx.cycle_basis(G)),
                "longest_cycle": g.get("longest_cycle") or "",
                "crossings": v.get("crossings", ""),
                "ring_order": meta.get("order", ""),
                "gold_cycle": fmt_cyc(gold_cyc),
                "foil_kind": next((o["kind"] for o in opts if o["kind"] != "gold"), ""),
                "reviewer": CODES[idx // PER_REVIEWER],
            }
        )
        if idx % 100 == 0:
            print(f"r{idx:03d} {g['id']} gold={fmt_cyc(gold_cyc)} kinds={[o['kind'] for o in opts]}")

    ids = list(range(500))
    assign = {CODES[i]: {"shared": [], "own": ids[i * PER_REVIEWER:(i + 1) * PER_REVIEWER]} for i in range(5)}
    # Disjointness guard: every graph in exactly one reviewer's set.
    seen: dict[int, str] = {}
    for code, a in assign.items():
        for gid in a["own"]:
            assert gid not in seen, f"graph {gid} in two sets"
            seen[gid] = code
    assert len(seen) == 500

    (ROOT / "gold.json").write_text(json.dumps(gold_map, indent=2), encoding="utf-8")
    (ROOT / "assignments.json").write_text(json.dumps(assign, indent=2), encoding="utf-8")
    public = [{k: v for k, v in it.items() if k != "kinds"} for it in items]
    (ROOT / "items.json").write_text(json.dumps({"items": public}, indent=2), encoding="utf-8")
    gs = (ROOT / "Code.gs.template").read_text(encoding="utf-8")
    gs = gs.replace("/*GOLD*/", json.dumps(gold_map, separators=(",", ":")))
    (ROOT / "Code.gs").write_text(gs, encoding="utf-8")
    with (ROOT / "manifest.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    print(f"wrote {len(items)} items, {len(list(OUT_IMG.glob('*.png')))} pngs, manifest {len(manifest)} rows")


if __name__ == "__main__":
    main()
