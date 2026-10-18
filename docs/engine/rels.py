# -*- coding: utf-8 -*-
"""关系性质核验器（NetworkX 辅助构图）。

判定：自反、反自反、对称、反对称、传递、等价关系，并给出等价类。
"""
from __future__ import annotations

import re
import networkx as nx


def parse_base(s: str):
    parts = re.split(r"[,，;；\s{}\[\]]+", (s or "").strip())
    out = []
    for e in parts:
        if not e:
            continue
        out.append(int(e) if re.fullmatch(r"-?\d+", e) else e)
    seen, res = set(), []
    for e in out:
        if e not in seen:
            seen.add(e)
            res.append(e)
    return res


def parse_pairs(s: str):
    ps = []
    for m in re.finditer(
            r"([^,，;；()\[\]\s]+)\s*[,，]\s*([^,，;；()\[\]\s]+)", s or ""):
        a, b = m.group(1), m.group(2)

        def f(x):
            return int(x) if re.fullmatch(r"-?\d+", x) else x

        ps.append((f(a), f(b)))
    # 保序去重（保留第一次出现）
    seen, res = set(), []
    for p in ps:
        if p not in seen:
            seen.add(p)
            res.append(p)
    return res


def rel_props(base, pairs):
    ps = list(pairs)
    pset = set(ps)
    res = {}

    missing = [a for a in base if (a, a) not in pset]
    res["自反"] = (not missing, ("每个元素都有 (a,a)" if not missing
                else f"缺少 {(missing[0], missing[0])}" + (" 等" if len(missing) > 1 else "")))

    diag = sorted({a for a, b in ps if a == b}, key=str)
    res["反自反"] = (not diag, ("没有 (a,a)" if not diag
                   else f"存在 {diag[:3]}" + (" 等" if len(diag) > 3 else "")))

    bad_sym = None
    for a, b in ps:
        if a != b and (b, a) not in pset:
            bad_sym = (a, b)
            break
    res["对称"] = (bad_sym is None, ("所有 (a,b) 都有 (b,a)" if bad_sym is None
                   else f"有 {(a, b)} 但无 {(b, a)}"))

    bad_anti = None
    for a, b in ps:
        if a != b and (b, a) in pset:
            bad_anti = (a, b)
            break
    res["反对称"] = (bad_anti is None, ("不存在 (a,b) 与 (b,a) 同时出现" if bad_anti is None
                   else f"{a} 与 {b} 互相成对出现"))

    bad_trans = None
    for a, b in ps:
        for c, d in ps:
            if b == c and (a, d) not in pset:
                bad_trans = ((a, b), (c, d), (a, d))
                break
        if bad_trans:
            break
    res["传递"] = (bad_trans is None, ("所有可传递链都闭合" if bad_trans is None
                   else f"有 {(a, b)} 与 {(c, d)}，却缺少 {(a, d)}"))

    equiv = (res["自反"][0] and res["对称"][0] and res["传递"][0])
    res["等价关系"] = (equiv, ("自反+对称+传递 同时成立" if equiv
                       else "自反/对称/传递 未同时成立"))

    return res


def equivalence_classes(base, pairs):
    parent = {e: e for e in base}

    def find(x):
        while parent[x] != x:
            parent[x], x = parent[parent[x]], parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for a, b in pairs:
        if a in parent and b in parent:
            union(a, b)
    groups = {}
    for e in base:
        groups.setdefault(find(e), []).append(e)
    return sorted(groups.values(), key=lambda g: str(g[0]))


def draw_relation(base, pairs):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    G = nx.DiGraph()
    G.add_nodes_from(base)
    G.add_edges_from(pairs)
    pos = nx.circular_layout(G)
    fig, ax = plt.subplots(figsize=(5, 4.4))
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#e0e7ff",
                            node_size=950, edgecolors="#6366f1")
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="#1e1b4b")
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=True, arrowstyle="-|>",
                           edge_color="#64748b", connectionstyle="arc3,rad=0.12")
    ax.set_title("关系有向图", color="#3730a3")
    ax.axis("off")
    return fig
