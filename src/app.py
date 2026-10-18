# -*- coding: utf-8 -*-
"""离散数学智能问答与答案核验平台 —— Streamlit 前端。

运行：streamlit run app.py
"""
from __future__ import annotations

import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from dmverify import autodissect, graphs, llm, prop, rels, runner, sets_engine
from dmverify import config
from dmverify.cases import CASES

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei",
                                   "Noto Sans CJK SC", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(page_title="离散数学核验平台", page_icon="🎓", layout="wide")

st.markdown("""
<style>
  .main .block-container {padding-top: 1.4rem; max-width: 1240px;}
  h1 {background: linear-gradient(90deg,#4338ca,#7c3aed,#db2777);
      -webkit-background-clip: text !important; -webkit-text-fill-color: transparent;}
  div[data-testid="stMetric"] {background:#f8fafc;border:1px solid #e2e8f0;
      border-radius:12px;padding:10px 14px;}
</style>""", unsafe_allow_html=True)

KIND_NAME = {"prop": "命题逻辑", "set": "集合", "rel": "关系", "graph": "图论"}
VERDICT_COLOR = {"必真": "#16a34a", "必假": "#dc2626",
                 "无法确定": "#d97706", "约束矛盾": "#7c3aed"}


# ---------------- 侧边栏 ----------------

def sidebar():
    st.sidebar.markdown("## 🎓 离散数学核验台")
    st.sidebar.caption("实验二 · 选题 1 · Python + SymPy + NetworkX")
    page = st.sidebar.radio(
        "功能导航",
        ["📝 录入与自动拆解", "🔢 命题逻辑", "📦 集合", "🔗 关系",
         "🕸 图论", "🧪 案例回归", "🤖 AI 记录", "📖 说明"],
        label_visibility="collapsed")
    with st.sidebar.expander("⚙️ 大模型接口（火山方舟）"):
        st.session_state["api_key"] = st.text_input(
            "API Key", value=config.ARK_API_KEY, type="password")
        st.session_state["model_id"] = st.text_input(
            "模型 ID", value=config.ARK_MODEL)
    st.sidebar.caption("核验器全部为确定性程序，不依赖大模型。")
    return page


# ---------------- 录入与自动拆解 ----------------

def page_dissect():
    st.title("📝 录入与自动拆解")
    st.caption("系统自动完成：提取约束 → 登记原子命题 → 符号化 → 真值表 → 判定 → 核验 AI 断言")
    left, right = st.columns(2, gap="medium")
    with left:
        preset = st.selectbox("内置示例", ["（选择示例）"] + list(autodissect.PRESETS))
        if st.button("载入示例", disabled=preset == "（选择示例）"):
            p = autodissect.PRESETS[preset]
            st.session_state["q_in"] = p["question"]
            st.session_state["ai_in"] = p["ai_answer"]
            st.rerun()
        st.text_area("① 题目原文（约束条件可写在题目里）", height=175, key="q_in")
        st.text_area("补充约束（可选；留空则自动从题目全文提取）",
                     height=80, key="extra_in")
    with right:
        st.text_area("② AI 原话（手填，或让大模型现场作答）", height=175, key="ai_in")
        col1, col2 = st.columns([1, 2])
        if col1.button("🤖 让大模型作答", use_container_width=True):
            q = st.session_state.get("q_in", "").strip()
            if not q:
                st.error("请先录入题目")
            else:
                with st.spinner("模型思考中…"):
                    try:
                        ans = llm.ask_llm(q, api_key=st.session_state["api_key"],
                                          model=st.session_state["model_id"])
                        st.session_state["ai_in"] = ans
                        st.session_state.setdefault("ai_log", []).append(
                            {"题目": q[:40] + ("…" if len(q) > 40 else ""),
                             "AI 回答": ans, "来源": st.session_state["model_id"]})
                        st.rerun()
                    except llm.LLMError as e:
                        st.error(str(e))
        col2.caption(f"当前模型：`{st.session_state['model_id']}`")

    if not st.button("▶ 开始自动拆解与核验", type="primary",
                     use_container_width=True):
        return
    q = st.session_state.get("q_in", "").strip()
    extra = st.session_state.get("extra_in", "").strip()
    if not (q or extra):
        st.error("请先录入题目或约束条件")
        return
    r = autodissect.analyze(q, ai_text=st.session_state.get("ai_in", ""),
                            extra_constraints=extra)
    st.session_state["last_dissect"] = r

    if not st.session_state.get("last_dissect"):
        return
    render_dissect(st.session_state["last_dissect"])


def render_dissect(r):
    st.divider()
    st.subheader("③ 系统自动拆解")

    letters = {v["name"]: v["var"] for v in r["var_table"]}
    c1, c2 = st.columns([2, 3])
    with c1:
        st.markdown("**原子命题（系统自动登记）**")
        if r["var_table"]:
            st.dataframe(pd.DataFrame(r["var_table"]).rename(
                columns={"var": "命题变元", "name": "对象",
                         "meaning": "含义"}),
                hide_index=True, use_container_width=True)
        else:
            st.info("未识别出对象名。可在『补充约束』中用「X和Y不可能都是真话」句式。")
        st.markdown("**约束符号化**")
        if r["conditions"]:
            for i, c in enumerate(r["conditions"]):
                st.markdown(f"- 约束{i + 1}：{c['sent']} → `{c['fstr']}`")
        else:
            st.warning("未提取到任何约束。")
    with c2:
        if r["unsupported"]:
            st.warning("**暂不支持自动符号化的句子（已跳过）**\n\n" +
                       "\n".join(f"- {s}" for s in r["unsupported"]))
        st.markdown(f"**真值表**（绿色 = 满足全部约束，共 **{len(r['rows'])}** 行）")
        if r["table"]:
            df = pd.DataFrame(r["table"])
            ren = {n: f"{letters.get(n, '?')}·{n}" for n in r["order"]}
            for i, c in enumerate(r["conditions"]):
                ren[f"c{i}"] = f"约束{i + 1}"
            ren["all"] = "全部满足"
            df = df.rename(columns=ren)

            def _hl(row):
                if bool(row["全部满足"]):
                    return ["background-color:#dcfce7"] * len(row)
                return [""] * len(row)

            st.dataframe(df.style.apply(_hl, axis=1),
                         hide_index=True, use_container_height=True)

    st.markdown("**各原子命题判定**（在全部满足约束的情形上归纳）")
    if r["order"]:
        cols = st.columns(len(r["order"]))
        for col, n in zip(cols, r["order"]):
            v = r["verdict"][n]
            color = VERDICT_COLOR.get(v, "#334155")
            col.markdown(
                f"<div style='border:1px solid #e2e8f0;border-radius:10px;"
                f"padding:8px;text-align:center'>"
                f"<span style='color:#64748b'>{letters.get(n, '')}·{n}</span><br>"
                f"<b style='color:{color};font-size:17px'>{v}</b></div>",
                unsafe_allow_html=True)

    st.subheader("④ AI 断言逐条核验")
    if not r["claims"]:
        st.info("AI 原话中未提取到可判真假的断言（如「X和Y都在说谎」）。")
    for c in r["claims"]:
        icon = {True: "✅", False: "❌", None: "❓"}[c["ok"]]
        with st.container(border=True):
            head = f"{icon} **{c['raw']}** → `{c.get('formula', '')}`　**{c['status']}**"
            st.markdown(head)
            tail = c["why"] or ""
            if c.get("counter"):
                tail += f"　　**反例情形**：{c['counter']}"
            st.caption(tail)

    st.subheader("⑤ 核验报告")
    if r["errors"]:
        st.error(f"发现 {len(r['errors'])} 处 AI 错误")
        for e in r["errors"]:
            st.markdown(f"- 「{e['raw']}」{e['why']}"
                        + (f"（反例：{e['counter']}）" if e.get("counter") else ""))
    elif r["claims"]:
        st.success("本次 AI 回答未发现可证伪的错误。")
    if r["verdict"] and any(v == "约束矛盾" for v in r["verdict"].values()):
        st.error("约束条件自身矛盾：不存在同时满足全部约束的情形。")


# ---------------- 命题逻辑 ----------------

def verify_prop_conclusion(text, ea, eb):
    t = re.sub(r"\s+", "", text)
    if "主析取" in t:
        m = re.search(r"m[\(（]?([0-9,，、]*)[\)）]?", t)
        if not m:
            return None, "未找到极小项编号"
        want = sorted(int(x) for x in re.split(r"[,，、]", m.group(1)) if x)
        idxs, s = prop.principal_dnf(ea)
        return (idxs == want), f"AI 断言 m{tuple(want)}；实际：{s}"
    if "主合取" in t:
        m = re.search(r"M[\(（]?([0-9,，、]*)[\)）]?", t)
        if not m:
            return None, "未找到极大项编号"
        want = sorted(int(x) for x in re.split(r"[,，、]", m.group(1)) if x)
        idxs, s = prop.principal_cnf(ea)
        return (idxs == want), f"AI 断言 M{tuple(want)}；实际：{s}"
    if "等价" in t or "≡" in t:
        if eb is None:
            return None, "判断等价需要提供公式 B"
        ok, ce, note = prop.check_equivalence(ea, eb)
        return ok, note + (f"（反例赋值 {ce}）" if ce else "")
    if "永真" in t or "重言" in t:
        got = prop.classify(ea)
        return (got == "永真"), f"AI 断言永真；实际判定「{got}」"
    if "永假" in t or "矛盾" in t:
        got = prop.classify(ea)
        return (got == "永假"), f"AI 断言永假；实际判定「{got}」"
    if "可满足" in t:
        got = prop.classify(ea)
        return (got != "永假"), f"AI 断言可满足；实际判定「{got}」"
    return None, ("未能识别断言类型（支持：等价 / 永真 / 永假 / 可满足 / "
                  "主析取范式 m(…) / 主合取范式 M(…)）")


def page_prop():
    st.title("🔢 命题逻辑核验器（SymPy）")
    c1, c2 = st.columns(2)
    a = c1.text_input("公式 A", "¬(P∧Q)")
    b = c2.text_input("公式 B（等价判断用）", "¬P∨¬Q")
    conc = st.text_input("AI 结论核验（可选）", "A 与 B 等价")
    if st.button("核验", type="primary"):
        try:
            ea = prop.parse(a)
            eb = prop.parse(b) if b.strip() else None
        except prop.ParseError as e:
            st.error(f"解析失败：{e}")
            return
        st.markdown(f"**A** = `{prop.to_str(ea)}`"
                    + (f"　　**B** = `{prop.to_str(eb)}`" if eb is not None else ""))

        got = prop.classify(ea)
        color = {"永真": "#16a34a", "永假": "#dc2626", "可满足": "#d97706"}[got]
        m1, m2, m3 = st.columns(3)
        m1.metric("公式类型", got)
        idxs_d, s_d = prop.principal_dnf(ea)
        idxs_c, s_c = prop.principal_cnf(ea)
        m2.metric("主析取范式极小项", str(idxs_d) or "—")
        m3.metric("主合取范式极大项", str(idxs_c) or "—")
        st.caption(f"主析取范式：{s_d}")
        st.caption(f"主合取范式：{s_c}")

        syms, rows = prop.truth_table(ea)
        data = []
        for env, val in rows:
            row = {f"{s.name}": "真" if env[s] else "假" for s in syms}
            row["A 的值"] = "真" if val else "假"
            if eb is not None:
                row["B 的值"] = "真" if bool(eb.subs(env)) else "假"
            data.append(row)
        st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)

        if eb is not None:
            ok, ce, note = prop.check_equivalence(ea, eb)
            (st.success if ok else st.error)(f"等价判定：{note}")

        if conc.strip():
            ok, msg = verify_prop_conclusion(conc, ea, eb)
            if ok is True:
                st.success(f"AI 结论核验：✅ {msg}")
            elif ok is False:
                st.error(f"AI 结论核验：❌ {msg}")
            else:
                st.warning(f"AI 结论核验：❓ {msg}")


# ---------------- 集合 ----------------

def page_set():
    st.title("📦 集合核验器")
    st.caption("支持 ∪ ∩ − ⊕、幂集 P(X)、基数 |X|；给出宇宙 U 时自动做全称验证与反例搜索")
    c1, c2, c3 = st.columns(3)
    va = c1.text_input("集合 A", "{1,2}")
    vb_ = c2.text_input("集合 B", "{2,3}")
    vc = c3.text_input("集合 C", "{3}")
    c1, c2, c3 = st.columns([2, 1, 2])
    lhs = c1.text_input("断言左边", "A∪B")
    op = c2.selectbox("运算符", ["=", "≠", "⊆", "⊇", "∈", "∉"])
    rhs = c3.text_input("断言右边", "A")
    universe = st.text_input("宇宙 U（可选，触发全称验证 / 自动反例搜索）", "1,2,3,4")
    if st.button("核验", type="primary"):
        env = {}
        for nm, box in (("A", va), ("B", vb_), ("C", vc)):
            if box.strip():
                try:
                    env[nm] = sets_engine.eval_expr(
                        sets_engine.parse_setexpr(box), {})
                except (sets_engine.SetParseError, sets_engine.SetEvalError) as e:
                    st.error(f"集合 {nm} 赋值错误：{e}")
                    return
        try:
            res = sets_engine.check_claim_full(
                lhs, op, rhs, env=env or None, universe=universe or None)
        except (sets_engine.SetParseError, sets_engine.SetEvalError) as e:
            st.error(str(e))
            return
        if res["ok"] is True:
            st.success(f"成立（{res['mode']}）：{res['detail']}")
        elif res["ok"] is False:
            st.error(f"不成立（{res['mode']}）：{res['detail']}")
            if res.get("counterexample"):
                st.markdown("**自动生成的反例：**")
                st.dataframe(pd.DataFrame(
                    [{"变量": k, "取值": v}
                     for k, v in res["counterexample"].items()]),
                    hide_index=True, use_container_width=True)
        else:
            st.warning(res["detail"])


# ---------------- 关系 ----------------

def page_rel():
    st.title("🔗 关系性质核验器（NetworkX 构图）")
    c1, c2 = st.columns([1, 2])
    base = c1.text_input("基本集", "{1,2,3,4}")
    pairs = c2.text_input("序偶集合", "(1,1),(1,2),(2,1),(2,2),(3,4),(4,3),"
                                     "(1,3),(3,1),(2,4),(4,2)")
    if st.button("核验", type="primary"):
        b = rels.parse_base(base)
        ps = rels.parse_pairs(pairs)
        got = rels.rel_props(b, ps)
        rows = [{"性质": k, "结论": "✅ 成立" if v[0] else "❌ 不成立",
                 "说明": v[1]} for k, v in got.items()]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        if got["等价关系"][0]:
            classes = rels.equivalence_classes(b, ps)
            st.success("等价类：" + "　".join(
                "{" + ",".join(str(x) for x in g) + "}" for g in classes))
        try:
            st.pyplot(rels.draw_relation(b, ps))
        except Exception as e:  # noqa: BLE001
            st.caption(f"绘图失败：{e}")


# ---------------- 图论 ----------------

def page_graph():
    st.title("🕸 图论核验器（NetworkX）")
    edges = st.text_input("边列表（用 - 连接两端点）",
                          "1-2, 2-3, 3-4, 4-1, 1-3")
    directed = st.checkbox("有向图（欧拉判定暂只支持无向图）")
    if st.button("核验", type="primary"):
        try:
            G, ne = graphs.parse_edges(edges, directed)
        except ValueError as e:
            st.error(str(e))
            return
        r = graphs.check_graph(G, directed)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("顶点数 / 边数", f"{r['order']} / {r['size']}")
        m2.metric("连通性", "连通" if r["连通"] else "不连通")
        m3.metric("奇度顶点数", len(r["奇度顶点"]))
        m4.metric("欧拉回路 / 通路",
                  f"{'有' if r['欧拉回路'] else '无'} / {'有' if r['欧拉通路'] else '无'}")
        st.markdown(f"**度序列**：{r['度序列']}　　"
                    f"**奇度顶点**：{r['奇度顶点'] or '无'}")
        st.info(r["反例"])
        active = [v for v in G.nodes if G.degree(v) > 0]
        if active:
            start = sorted(active, key=str)[0]
            st.caption(f"从顶点 {start} 出发的 BFS 序："
                       f"{graphs.bfs_order(G, start)}")
        try:
            st.pyplot(graphs.draw_graph(G, directed))
        except Exception as e:  # noqa: BLE001
            st.caption(f"绘图失败：{e}")


# ---------------- 案例回归 / 记录 / 说明 ----------------

def page_regression():
    st.title("🧪 案例回归")
    st.caption(f"共 {len(CASES)} 条预注册案例（期望结果先于运行写定），与 pytest 测试同源")
    if st.button("运行全部案例", type="primary"):
        rows = []
        for c in CASES:
            ok, got = runner.run_case(c)
            rows.append({"编号": c["id"], "层级": c["level"],
                         "类别": KIND_NAME[c["kind"]], "案例": c["title"],
                         "结果": "✅ 通过" if ok else "❌ 失败", "详情": got})
        df = pd.DataFrame(rows)
        passed = (df["结果"] == "✅ 通过").sum()
        st.metric("通过率", f"{passed}/{len(df)}")
        st.dataframe(df, hide_index=True, use_container_width=True)


def page_log():
    st.title("🤖 AI 记录")
    log = st.session_state.get("ai_log", [])
    if not log:
        st.info("暂无记录；在『录入与自动拆解』页让大模型作答后自动记录。")
        return
    st.dataframe(pd.DataFrame(log[::-1]), hide_index=True,
                 use_container_width=True)


def page_about():
    st.title("📖 说明：与指导书『核心技术』对照")
    st.markdown("""
| 指导书要求 | 本平台实现 |
|---|---|
| Python | 全部核验器为 Python 包 `dmverify` |
| SymPy（真值表、判等价、主析取范式） | `dmverify/prop.py`：解析、真值表、等价（含反例赋值）、永真/永假/可满足、主析取/主合取范式 |
| NetworkX（关系与图算法） | `dmverify/rels.py`、`dmverify/graphs.py`：关系五性质 + 等价类、连通性、度序列、欧拉回路/通路、BFS |
| Streamlit / Gradio 界面 | 本页面（Streamlit） |
| pytest 做测试 | `tests/test_dmverify.py`：60 条预注册回归案例 + 自动拆解专项，`pytest` 一键运行 |
| 检索层 BM25 + 向量召回 | 可选扩展项，当前版本预留接口未实现 |

**核心流程（系统全自动，无需人工拆题）**

1. **录入**：题目原文 + AI 原话（可让大模型现场作答）；
2. **自动拆解**：系统从自然语言约束中登记原子命题（P/Q/R/S…）、符号化每条约束；
3. **真值表**：枚举全部赋值，筛出满足所有约束的行，归纳出每个原子命题必真 / 必假 / 无法确定；
4. **自动核验**：从 AI 原话中提取可判真假的断言，逐条与判定结果比对，输出错误与反例情形；
5. **多核验器**：命题逻辑 / 集合 / 关系 / 图论 各章一个确定性核验器，集合核验器支持在给定宇宙上自动搜索反例（自动反例生成器）。

**运行方式**

- 本机：`pip install -r requirements.txt` 后 `streamlit run app.py`；
- 测试：`pytest`（70 项断言）。
""")
    st.caption("AI 记录仅保存在当前会话中。核验器不依赖任何大模型接口。")


def main():
    page = sidebar()
    {"📝 录入与自动拆解": page_dissect,
     "🔢 命题逻辑": page_prop,
     "📦 集合": page_set,
     "🔗 关系": page_rel,
     "🕸 图论": page_graph,
     "🧪 案例回归": page_regression,
     "🤖 AI 记录": page_log,
     "📖 说明": page_about,
     }[page]()


if __name__ == "__main__":
    main()
