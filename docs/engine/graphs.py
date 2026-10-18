# -*- coding: utf-8 -*-
"""图论核验器（NetworkX）。

判定：连通性、度序列、奇度顶点、欧拉回路 / 欧拉通路（无向图），
以及 BFS 遍历、最短路等辅助分析。
"""
from __future__ import annotations

import re

import networkx as nx


def parse_edges(s: str, directed: bool = False):
    G = nx.DiGraph() if directed else nx.Graph()
    n = 0
    for m in re.finditer(
            r"([^\s,，;；\-–—>]+)\s*(?:-|–|—|~)\s*([^\s,，;；\-–—>]+)", s or ""):
        a, b = m.group(1), m.group(2)

        def f(x):
            return int(x) if re.fullmatch(r"-?\d+", x) else x

        G.add_edge(f(a), f(b))
        n += 1
    if n == 0:
        raise ValueError("未解析到任何边；请用「1-2, 2-3」这样的写法")
    return G, n


def check_graph(G, directed: bool = False):
    res = {"order": G.number_of_nodes(), "size": G.number_of_edges()}
    deg = {v: G.degree(v) for v in G.nodes}
    res["度序列"] = sorted(deg.values(), reverse=True)

    active = [v for v in G.nodes if G.degree(v) > 0]
    H = G.subgraph(active).copy() if active else G

    if directed:
        res["连通"] = (nx.is_weakly_connected(H)
                       if H.number_of_nodes() > 1 else True)
        res["欧拉回路"] = False
        res["欧拉通路"] = False
        res["反例"] = "本实验的欧拉判定针对无向图"
        return res

    res["连通"] = (nx.is_connected(H) if H.number_of_nodes() > 1 else True)
    odd = sorted([v for v in G.nodes if deg[v] % 2 == 1], key=str)
    res["奇度顶点"] = odd

    if not active:
        res["欧拉回路"] = False
        res["欧拉通路"] = False
        res["反例"] = "图没有边"
        return res

    comp = nx.number_connected_components(H)
    if comp > 1:
        res["欧拉回路"] = False
        res["欧拉通路"] = False
        res["反例"] = f"含边部分分为 {comp} 个连通分量，不连通"
        return res

    res["欧拉回路"] = nx.is_eulerian(H)
    res["欧拉通路"] = nx.has_eulerian_path(H)
    if odd:
        if len(odd) == 2:
            res["反例"] = (f"顶点 {'、'.join(map(str, odd))} 度为奇数"
                           f"：存在欧拉通路，但无欧拉回路")
        else:
            res["反例"] = (f"顶点 {'、'.join(map(str, odd))} 度为奇数"
                           f"（恰需 0 或 2 个奇度顶点）")
    else:
        res["反例"] = "所有含边顶点度数均为偶数且连通"
    return res


def bfs_order(G, start):
    H = G.subgraph([v for v in G.nodes if G.degree(v) > 0]).copy()
    if start not in H:
        return []
    order = [start]
    for _, v in nx.bfs_edges(H, start):
        order.append(v)
    return order


def shortest_path(G, a, b):
    H = G.subgraph([v for v in G.nodes if G.degree(v) > 0]).copy()
    if a not in H or b not in H:
        return None
    try:
        return nx.shortest_path(H, a, b)
    except nx.NetworkXNoPath:
        return None


def draw_graph(G, directed: bool = False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    pos = nx.spring_layout(G, seed=7)
    fig, ax = plt.subplots(figsize=(5, 4.4))
    nx.draw_networkx_nodes(G, pos, ax=ax, node_color="#dcfce7",
                           node_size=900, edgecolors="#16a34a")
    nx.draw_networkx_labels(G, pos, ax=ax, font_color="#052e16")
    nx.draw_networkx_edges(G, pos, ax=ax, arrows=directed, arrowstyle="-|>",
                           edge_color="#475569")
    ax.set_title("图结构", color="#166534")
    ax.axis("off")
    return fig
