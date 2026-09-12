"""Build 70 Ring PNGs + 4-choice items for the human cycle pilot."""
from __future__ import annotations

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

PACK = ROOT.parent / "gitqa_hard_ring70"
OUT_IMG = ROOT / "images"
FIGSIZE = (9.0, 9.0)
DPI = 110


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
    # Drop last vertex of the gold cycle; fake-close the remaining path.
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
    n = len(order)
    gset = set(norm_cyc(gold))
    for i, a in enumerate(order):
        b = order[(i + 1) % n]
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
        # path of length 2 via any node
        for w in order:
            if w in (a, b):
                continue
            if G.has_edge(a, w) and G.has_edge(w, b):
                cyc = [int(a), int(w), int(b)]
                if set(norm_cyc(cyc)) != gset:
                    return cyc
        # last resort: a, neighbor, b even if b-neighbor missing
        nbrs = [int(x) for x in G.neighbors(a) if int(x) != b]
        if nbrs:
            cyc = [int(a), nbrs[0], int(b)]
            if set(norm_cyc(cyc)) != gset and len(set(cyc)) == 3:
                return cyc
    return None


def four_options(G: nx.Graph, order: list[int], rng: random.Random) -> tuple[list[int], list[dict]]:
    gold = shortest_cycle(G)
    if len(gold) < 3:
        raise RuntimeError("no cycle")
    seen = {norm_cyc(gold)}
    pool: list[tuple[str, list[int]]] = [("gold", gold)]

    def add(kind: str, cyc: list[int] | None) -> None:
        if not cyc or len(cyc) < 3:
            return
        key = norm_cyc(cyc)
        if not key or key in seen:
            return
        seen.add(key)
        pool.append((kind, cyc))

    add("premature", premature_close(gold, G))
    add("adjacent", adjacent_fake(G, order, gold))
    add("other", other_gold_cycle(G, gold))
    # pad with other simple cycles if needed
    if len(pool) < 4:
        for cyc in nx.cycle_basis(G):
            add("other", [int(x) for x in cyc])
            if len(pool) >= 4:
                break
    if len(pool) < 4:
        nodes = list(G.nodes())
        for _ in range(20):
            a, b, c = rng.sample(nodes, 3)
            add("filler", [a, b, c])
            if len(pool) >= 4:
                break
    pool = pool[:4]
    rng.shuffle(pool)
    opts = [{"id": i, "kind": k, "nodes": cyc, "label": fmt_cyc(cyc)} for i, (k, cyc) in enumerate(pool)]
    return gold, opts


def main() -> None:
    gold_payload = json.loads((PACK / "gold" / "graphs.json").read_text(encoding="utf-8"))
    pos_raw = json.loads((PACK / "layouts" / "positions_circular.json").read_text(encoding="utf-8"))
    qc = {int(r["graph_id"]): r for r in json.loads((PACK / "layouts" / "qc_circular.json").read_text(encoding="utf-8"))}
    OUT_IMG.mkdir(parents=True, exist_ok=True)
    items = []
    gold_map = {}
    for g in gold_payload["graphs"]:
        gid = int(g["graph_id"])
        G = adj_to_graph(g["gold_adjacency"])
        raw = pos_raw[str(gid)]["circular"]
        pos = {int(k): (float(v[0]), float(v[1])) for k, v in raw.items()}
        meta = qc[gid]["circular"]
        png = f"g{gid:02d}_circular.png"
        fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
        fig.patch.set_facecolor("white")
        fig.subplots_adjust(left=0.03, right=0.97, bottom=0.03, top=0.97)
        _draw_ring_ax(ax, G, pos, float(meta["node_size"]), int(meta["font_size"]))
        fig.savefig(OUT_IMG / png, dpi=DPI, facecolor="white")
        plt.close(fig)
        order = ring_order_from_pos(pos)
        rng = random.Random(70 + gid)
        gold_cyc, opts = four_options(G, order, rng)
        gold_key = list(norm_cyc(gold_cyc))
        gold_map[str(gid)] = gold_key
        items.append(
            {
                "graph_id": gid,
                "gitqa_id": int(g["gitqa_id"]),
                "image": "images/" + png,
                "options": [{"id": o["id"], "label": o["label"], "nodes": o["nodes"]} for o in opts],
                "kinds": [o["kind"] for o in opts],
            }
        )
        print(f"g{gid:02d} gitqa={g['gitqa_id']} gold={fmt_cyc(gold_cyc)} kinds={[o['kind'] for o in opts]}")

    ids = [it["graph_id"] for it in items]
    shared = ids[:20]
    rest = ids[20:]
    assign = {
        "r1": {"shared": shared, "own": rest[0:13]},
        "r2": {"shared": shared, "own": rest[13:26]},
        "r3": {"shared": shared, "own": rest[26:38]},
        "r4": {"shared": shared, "own": rest[38:50]},
    }
    (ROOT / "gold.json").write_text(json.dumps(gold_map, indent=2), encoding="utf-8")
    (ROOT / "assignments.json").write_text(json.dumps(assign, indent=2), encoding="utf-8")
    public = [{k: v for k, v in it.items() if k != "kinds"} for it in items]
    (ROOT / "items.json").write_text(json.dumps({"items": public}, indent=2), encoding="utf-8")
    gs = (ROOT / "Code.gs.template").read_text(encoding="utf-8")
    gs = gs.replace("/*GOLD*/", json.dumps(gold_map, separators=(",", ":")))
    (ROOT / "Code.gs").write_text(gs, encoding="utf-8")
    print(f"wrote {len(items)} items, {len(list(OUT_IMG.glob('*.png')))} pngs")


if __name__ == "__main__":
    main()
