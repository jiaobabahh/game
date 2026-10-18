# -*- coding: utf-8 -*-
"""预注册测试：60 条回归案例 + 自动拆解引擎专项 + 关键单元测试。"""
import pytest

from dmverify import autodissect, graphs, prop, rels, runner, sets_engine
from dmverify.cases import CASES


@pytest.mark.parametrize("c", CASES, ids=[c["id"] for c in CASES])
def test_regression_cases(c):
    ok, got = runner.run_case(c)
    assert ok, f"{c['id']} {c['title']}: {got}"


DETECTIVE = (
    "某写字楼深夜失窃，保安锁定了男管家、厨师、园丁、杂役四人，"
    "警察分别讯问，四人各说了一句话。已知：如果男管家说的是真话，"
    "那么厨师说的也是真话；厨师和园丁说的不可能都是真话；"
    "园丁和杂役不可能都在说谎；如果杂役说真话，那么厨师在说谎。"
    "请问谁说的是真话？小偷最可能是谁？"
)


def test_detective_auto_dissect():
    r = autodissect.analyze(
        DETECTIVE,
        ai_text="根据条件推理：男管家和厨师说的应该也都是真话，园丁和杂役都在说谎。所以作案的是园丁。")
    assert len(r["conditions"]) == 4, r["conditions"]
    assert len(r["unsupported"]) >= 1
    assert len(r["rows"]) == 3, r["rows"]
    v = r["verdict"]
    assert v["男管家"] == "必假"
    assert v["厨师"] == "必假"
    assert v["园丁"] == "无法确定"
    assert v["杂役"] == "无法确定"
    # AI 两条断言都错
    assert len(r["errors"]) == 2, r["claims"]
    assert all(c["status"] == "AI 错误" for c in r["errors"])
    assert r["errors"][0]["counter"]  # 有反例情形


LIAR = "A说B在说谎，B说C在说谎，C说A和B都在说谎。"


def test_liar_auto_dissect():
    r = autodissect.analyze(LIAR, ai_text="结论：B说的是真话，A和C在说谎。")
    assert len(r["conditions"]) == 3, r["conditions"]
    assert len(r["rows"]) == 1, r["rows"]
    row = r["rows"][0]
    assert row["A"] is False and row["B"] is True and row["C"] is False
    assert r["verdict"]["A"] == "必假"
    assert r["verdict"]["B"] == "必真"
    assert r["verdict"]["C"] == "必假"
    assert r["ok_all"], r["claims"]


def test_triple_one_truth():
    q = ("甲、乙、丙三人中只有一人说真话。"
         "如果甲说的是真话，那么乙说的也是真话；"
         "甲和乙不可能都是真话；乙和丙至少有一个说真话。"
         "问：谁说真话？")
    r = autodissect.analyze(q, ai_text="我认为甲说的是真话，乙和丙都在说谎。")
    assert len(r["conditions"]) == 3, r["conditions"]
    # 手工验证：约束为 P→Q, ¬(P∧Q), Q∨R，满足行应恰有一行
    # P→Q 且 P∧Q 为假 => P 假；Q∨R 需真；乙丙至少一人真话
    # 枚举：P=F 时 Q 任意，Q∨R 真
    assert len(r["rows"]) == 3
    assert all(row["甲"] is False for row in r["rows"])
    assert r["verdict"]["甲"] == "必假"


def test_normalize_and_parse_latex():
    e = prop.parse("$\\boldsymbol{\\neg(C \\land G)}$")
    assert prop.to_str(e) == "¬(C∧G)"
    ok, _, _ = prop.check_equivalence(e, prop.parse("¬C∨¬G"))
    assert ok


def test_prop_parse_error_message():
    with pytest.raises(prop.ParseError):
        prop.parse("P∧")


def test_set_counterexample_search():
    res = sets_engine.check_claim_full("A∪B", "⊆", "A", universe=[1, 2])
    assert res["ok"] is False
    assert res["counterexample"], res


def test_set_distributive_law_universal():
    res = sets_engine.check_claim_full(
        "A∪(B∩C)", "=", "(A∪B)∩(A∪C)", universe=[1, 2, 3])
    assert res["ok"] is True


def test_relation_counterexample_text():
    got = rels.rel_props([1, 2, 3], [(1, 2), (2, 3)])
    assert got["传递"][0] is False
    assert "(1, 3)" in got["传递"][1] or "(1,3)" in got["传递"][1]


def test_graph_euler_k5():
    G, _ = graphs.parse_edges("1-2, 1-3, 1-4, 1-5, 2-3, 2-4, 2-5, 3-4, 3-5, 4-5")
    r = graphs.check_graph(G)
    assert r["连通"] and r["欧拉回路"] and r["欧拉通路"]
    assert r["奇度顶点"] == []


def test_graph_star_not_eulerian():
    G, _ = graphs.parse_edges("1-2, 1-3, 1-4")
    r = graphs.check_graph(G)
    assert not r["欧拉回路"] and not r["欧拉通路"]
    assert len(r["奇度顶点"]) == 4
