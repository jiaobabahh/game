# -*- coding: utf-8 -*-
"""60 条预注册回归案例（期望结果在运行前写定）。

三层设计：功能（基本正确性）/ 边界（特殊输入）/ 杀手（AI 常犯错误）。
覆盖四类核验器：命题逻辑 35 + 集合 9 + 关系 9 + 图论 7。
"""


def _p(i, level, title, **kw):
    return {"id": f"P{i:02d}", "kind": "prop", "level": level,
            "title": title, **kw}


def _s(i, level, title, **kw):
    return {"id": f"S{i:02d}", "kind": "set", "level": level,
            "title": title, **kw}


def _r(i, level, title, **kw):
    return {"id": f"R{i:02d}", "kind": "rel", "level": level,
            "title": title, **kw}


def _g(i, level, title, **kw):
    return {"id": f"G{i:02d}", "kind": "graph", "level": level,
            "title": title, **kw}


CASES = [
    # ---------- 命题逻辑（35） ----------
    _p(1, "功能", "德摩根定律", check="equiv", a="¬(P∧Q)", b="¬P∨¬Q", want=True),
    _p(2, "功能", "LaTeX 输入兼容（boldsymbol/neg/land）",
       check="equiv", a="$\\boldsymbol{\\neg(C \\land G)}$", b="¬C∨¬G", want=True),
    _p(3, "功能", "蕴含展开", check="equiv", a="P→Q", b="¬P∨Q", want=True),
    _p(4, "功能", "逆否命题", check="equiv", a="P→Q", b="¬Q→¬P", want=True),
    _p(5, "杀手", "AI 常把蕴当当可交换：P→Q 与 Q→P",
       check="equiv", a="P→Q", b="Q→P", want=False),
    _p(6, "功能", "吸收律", check="equiv", a="P∨(P∧Q)", b="P", want=True),
    _p(7, "功能", "分配律", check="equiv", a="P∧(Q∨R)", b="(P∧Q)∨(P∧R)", want=True),
    _p(8, "功能", "假言三段论是永真式",
       check="class", a="(P→Q)∧(Q→R)→(P→R)", want="永真"),
    _p(9, "功能", "矛盾联言", check="class", a="(P∨Q)∧¬P∧¬Q", want="永假"),
    _p(10, "功能", "偶然式", check="class", a="P∧Q", want="可满足"),
    _p(11, "功能", "主析取范式 P∧Q", check="pdnf", a="P∧Q", want=[3]),
    _p(12, "功能", "主析取范式 P∨Q", check="pdnf", a="P∨Q", want=[1, 2, 3]),
    _p(13, "功能", "主析取范式 P→Q", check="pdnf", a="P→Q", want=[0, 1, 3]),
    _p(14, "功能", "主合取范式 P∨Q", check="pcnf", a="P∨Q", want=[0]),
    _p(15, "功能", "排中律", check="class", a="P∨¬P", want="永真"),
    _p(16, "边界", "残缺公式一", check="parse_err", a="P∧"),
    _p(17, "边界", "括号不配对", check="parse_err", a="P∨(Q"),
    _p(18, "功能", "德摩根蕴含形式永真",
       check="class", a="¬(P∧Q)→(¬P∨¬Q)", want="永真"),
    _p(19, "功能", "双条件展开", check="equiv", a="P↔Q", b="(P→Q)∧(Q→P)", want=True),
    _p(20, "边界", "两个矛盾式在扩域意义下等价",
       check="equiv", a="P∧¬P", b="Q∧¬Q", want=True),
    _p(21, "杀手", "德摩根错记为 ¬P∨¬Q",
       check="equiv", a="¬(P∨Q)", b="¬P∨¬Q", want=False),
    _p(22, "功能", "双重否定", check="equiv", a="¬¬P", b="P", want=True),
    _p(23, "杀手", "前件与后件混淆",
       check="equiv", a="(P→Q)∧P", b="Q", want=False),
    _p(24, "功能", "蕴含与其展开等价（整体永真）",
       check="class", a="(P→Q)↔(¬P∨Q)", want="永真"),
    _p(25, "功能", "主合取范式 P∧Q", check="pcnf", a="P∧Q", want=[0, 1, 2]),
    _p(26, "功能", "前提自相矛盾", check="class", a="(P→Q)∧P∧¬Q", want="永假"),
    _p(27, "功能", "析取交换律", check="equiv", a="P∨Q", b="Q∨P", want=True),
    _p(28, "边界", "蕴当环取永真式", check="class", a="(P→Q)∨(Q→P)", want="永真"),
    _p(29, "杀手", "蕴含右结合陷阱", check="equiv", a="((P→Q)→R)",
       b="(P→(Q→R))", want=False),
    _p(30, "边界", "联言自毁", check="class", a="P∧Q∧(¬P∨¬Q)", want="永假"),
    _p(31, "杀手", "AI 把德摩根写成合取",
       check="equiv", a="¬(P∧Q)", b="¬P∧¬Q", want=False),
    _p(32, "杀手", "AI 称 P→Q 永真（实为偶然式）",
       check="class", a="P→Q", want="可满足"),
    _p(33, "功能", "双条件的主析取范式", check="pdnf", a="P↔Q", want=[0, 3]),
    _p(34, "杀手", "AI 声称 P→Q 与 ¬P∨Q 不等价",
       check="equiv", a="P→Q", b="¬P∨Q", want=True),
    _p(35, "杀手", "AI 判双条件展开正确（本条 AI 是对的）",
       check="equiv", a="(P→Q)∧(Q→P)", b="P↔Q", want=True),

    # ---------- 集合（9） ----------
    _s(1, "功能", "并集", lhs="{1,2}∪{2,3}", op="=", rhs="{1,2,3}", want=True),
    _s(2, "功能", "交集", lhs="{1,2}∩{2,3}", op="=", rhs="{2}", want=True),
    _s(3, "功能", "差集", lhs="{1,2,3}−{2}", op="=", rhs="{1,3}", want=True),
    _s(4, "功能", "对称差", lhs="{1,2}⊕{2,3}", op="=", rhs="{1,3}", want=True),
    _s(5, "边界", "幂集基数 2^n", lhs="|P({1,2})|", op="=", rhs="4", want=True),
    _s(6, "边界", "基数", lhs="|{a,b,c}|", op="=", rhs="3", want=True),
    _s(7, "杀手", "AI 常错：A∪B ⊆ A",
       lhs="A∪B", op="⊆", rhs="A", env={"A": "{1}", "B": "{2}"}, want=False),
    _s(8, "功能", "分配律全称验证（自动反例搜索）",
       lhs="A∪(B∩C)", op="=", rhs="(A∪B)∩(A∪C)", universe="1,2,3", want=True),
    _s(9, "杀手", "AI 常错：对称差等于交",
       lhs="A⊕B", op="=", rhs="A∩B", universe="1,2", want=False),

    # ---------- 关系（9） ----------
    _r(1, "功能", "恒等关系",
       base="{1,2,3}", pairs="(1,1),(2,2),(3,3)",
       want={"自反": True, "反自反": False, "对称": True, "反对称": True,
             "传递": True, "等价关系": True}),
    _r(2, "功能", "小于等于关系",
       base="{1,2,3}", pairs="(1,1),(1,2),(1,3),(2,2),(2,3),(3,3)",
       want={"自反": True, "对称": False, "反对称": True, "传递": True,
             "等价关系": False}),
    _r(3, "功能", "小于关系",
       base="{1,2,3}", pairs="(1,2),(1,3),(2,3)",
       want={"自反": False, "反自反": True, "对称": False, "反对称": True,
             "传递": True, "等价关系": False}),
    _r(4, "杀手", "AI 常漏传递验证",
       base="{1,2}", pairs="(1,2),(2,1),(1,1)",
       want={"自反": False, "对称": True, "反对称": False, "传递": False}),
    _r(5, "边界", "空关系", base="{1,2}", pairs="",
       want={"自反": False, "反自反": True, "对称": True, "反对称": True,
             "传递": True, "等价关系": False}),
    _r(6, "功能", "模 2 同余（等价关系）",
       base="{1,2,3,4}",
       pairs="(1,1),(2,2),(3,3),(4,4),(1,3),(3,1),(2,4),(4,2)",
       want={"自反": True, "对称": True, "传递": True, "等价关系": True}),
    _r(7, "杀手", "AI 常错：链式关系忘闭包",
       base="{1,2,3}", pairs="(1,2),(2,3)", want={"传递": False}),
    _r(8, "边界", "全关系（是等价关系）",
       base="{1,2}", pairs="(1,1),(1,2),(2,1),(2,2)",
       want={"自反": True, "对称": True, "反对称": False, "传递": True,
             "等价关系": True}),
    _r(9, "杀手", "AI 全判对（实为四性质全不成立）",
       base="{1,2,3}", pairs="(1,1),(1,2),(2,1),(2,2),(3,1)",
       want={"自反": False, "对称": False, "反对称": False, "传递": False,
             "等价关系": False}),

    # ---------- 图论（7） ----------
    _g(1, "功能", "三角形：有欧拉回路",
       edges="1-2, 2-3, 3-1", want={"连通": True, "欧拉回路": True, "欧拉通路": True}),
    _g(2, "功能", "链路：恰两个奇度顶点",
       edges="1-2, 2-3, 3-4", want={"连通": True, "欧拉回路": False, "欧拉通路": True}),
    _g(3, "杀手", "AI 常错：完全图 K4 四顶点全为奇度",
       edges="1-2, 1-3, 1-4, 2-3, 2-4, 3-4",
       want={"连通": True, "欧拉回路": False, "欧拉通路": False}),
    _g(4, "边界", "非连通图", edges="1-2, 3-4",
       want={"连通": False, "欧拉回路": False, "欧拉通路": False}),
    _g(5, "杀手", "星形：四个奇度顶点",
       edges="1-2, 1-3, 1-4", want={"连通": True, "欧拉回路": False, "欧拉通路": False}),
    _g(6, "边界", "完全图 K5（全偶度）",
       edges="1-2, 1-3, 1-4, 1-5, 2-3, 2-4, 2-5, 3-4, 3-5, 4-5",
       want={"连通": True, "欧拉回路": True, "欧拉通路": True}),
    _g(7, "杀手", "AI 常错：有对角的四边形",
       edges="1-2, 2-3, 3-4, 4-1, 1-3",
       want={"连通": True, "欧拉回路": False, "欧拉通路": True}),
]
