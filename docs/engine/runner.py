# -*- coding: utf-8 -*-
"""案例统一执行器：run_case(case) -> (是否通过, 结果描述)。"""
from __future__ import annotations

from . import graphs, prop, rels, sets_engine


def run_case(c):
    kind = c["kind"]
    try:
        if kind == "prop":
            return _run_prop(c)
        if kind == "set":
            return _run_set(c)
        if kind == "rel":
            return _run_rel(c)
        if kind == "graph":
            return _run_graph(c)
        return False, f"未知案例类别 {kind}"
    except Exception as e:  # noqa: BLE001
        if c.get("check") == "parse_err":
            return True, f"解析失败（符合预期）：{e}"
        return False, f"执行异常：{type(e).__name__}: {e}"


def _run_prop(c):
    chk = c.get("check")
    try:
        e = prop.parse(c["a"])
    except prop.ParseError as ex:
        if chk == "parse_err":
            return True, f"解析失败（符合预期）：{ex}"
        return False, f"解析失败：{ex}"
    except Exception as ex:  # noqa: BLE001
        if chk == "parse_err":
            return True, f"解析失败（符合预期）：{ex}"
        return False, f"解析异常：{ex}"
    if chk == "parse_err":
        return False, "公式竟然解析成功了"
    if chk == "parse_ok":
        return True, "解析成功：" + prop.to_str(e)
    if chk == "equiv":
        b = prop.parse(c["b"])
        ok, ce, note = prop.check_equivalence(e, b)
        extra = f"；反例赋值 {ce}" if ce else ""
        return (ok == c["want"]), note + extra
    if chk == "class":
        got = prop.classify(e)
        return (got == c["want"]), f"判定「{got}」，预期「{c['want']}」"
    if chk == "pdnf":
        idxs, s = prop.principal_dnf(e)
        return (idxs == c["want"]), f"{s}（预期极小项 {c['want']}）"
    if chk == "pcnf":
        idxs, s = prop.principal_cnf(e)
        return (idxs == c["want"]), f"{s}（预期极大项 {c['want']}）"
    return False, f"未知检查类型 {chk}"


def _run_set(c):
    res = sets_engine.check_claim_full(
        c["lhs"], c["op"], c["rhs"],
        env=c.get("env"), universe=c.get("universe"))
    ok = res["ok"]
    desc = f"[{res['mode']}] {res['detail']}"
    if res.get("counterexample"):
        desc += f"；反例：{res['counterexample']}"
    return (ok == c["want"]), desc


def _run_rel(c):
    base = rels.parse_base(c["base"])
    pairs = rels.parse_pairs(c["pairs"])
    got = rels.rel_props(base, pairs)
    bad = []
    for k, wv in c["want"].items():
        gv = got[k][0]
        if gv != wv:
            bad.append(f"{k}: 预期 {'成立' if wv else '不成立'}，实得 "
                       f"{'成立' if gv else '不成立'}（{got[k][1]}）")
    if bad:
        return False, "；".join(bad)
    good = "、".join(f"{k}={'成立' if v else '不成立'}"
                     for k, v in c["want"].items())
    return True, f"全部符合预期：{good}"


def _run_graph(c):
    G, _ = graphs.parse_edges(c["edges"])
    got = graphs.check_graph(G)
    bad = []
    for k, wv in c["want"].items():
        gv = got.get(k)
        if gv != wv:
            bad.append(f"{k}: 预期 {'是' if wv else '否'}，实得 "
                       f"{'是' if gv else '否'}")
    if bad:
        return False, "；".join(bad) + f"；系统分析：{got.get('反例', '')}"
    return True, f"全部符合预期；{got.get('反例', '')}"
