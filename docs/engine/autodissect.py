# -*- coding: utf-8 -*-
"""自动拆解引擎（本实验的核心创新点）。

流程（对齐教材例题的规范过程，全部由系统自动完成）：
1. 从题目原文 / 约束条件中自动提取「谁说真话 / 谁说谎」类约束；
2. 自动登记原子命题（P=男管家说真话 …），把每条约束符号化为命题公式；
3. 对全部原子命题列真值表，筛出满足所有约束的行；
4. 归纳每个原子命题在满足行中是否恒真 / 恒假 / 不定（必真 / 必假 / 无法确定）；
5. 从 AI 原话中自动提取可判真假的断言并逐条核验，输出错误与反例。

符号化基于受限句式（确定性文法），不依赖 NLP 猜测，保证可解释。
"""
from __future__ import annotations

import itertools
import re

import sympy as sp
from sympy.logic.boolalg import And, Equivalent, Implies, Not, Or

from .prop import to_str

VAR_LETTERS = "PQRSTUVW"

_SENT_SPLIT = re.compile(r"[。；;！？\n]+")
_FRAG_SPLIT = re.compile(r"[，,]+")

_QUESTION_WORDS = {"谁", "何人", "哪些人", "什么人", "几人", "哪些"}

# 名字不能包含「说」、标点或空白；单条断言里名字还不能包含「和/或」
_N = r"([^说，。；！？\s]{1,6}?)"
_N1 = r"([^说和或，。；！？\s]{1,6}?)"


def split_sentences(t: str):
    return [x.strip() for x in _SENT_SPLIT.split(t or "") if x.strip()]


_LEAD = ("另外|而且|同时|并且|其中|如果|那么|所以|因此|可见|因而|但是|但|而|"
         "据|据说|根据条件|由此|综上|综述|结论|问|答|答：|解")
_TRAIL = r"(?:说的?|都是|也|都|是|应该|可能|肯定|一定|话|的)+"


def clean_name(s: str) -> str:
    s = (s or "").strip()
    prev = None
    while prev != s:
        prev = s
        s = re.sub(rf"^({_LEAD})", "", s)
        s = re.sub(f"{_TRAIL}$", "", s)
        s = s.strip("，,。．.:：;；「」『』“”‘’\"'()（）？！?!")
    return s.strip()


class VarBox:
    """原子命题登记表：对象名 → P/Q/R/…"""

    def __init__(self):
        self.reg = {}
        self.names = []

    def has(self, name: str) -> bool:
        return clean_name(name) in self.reg

    def V(self, name):
        name = clean_name(name)
        if not name or len(self.names) >= len(VAR_LETTERS):
            return None
        if name not in self.reg:
            self.reg[name] = sp.Symbol(VAR_LETTERS[len(self.names)])
            self.names.append(name)
        return self.reg[name]

    def letter(self, name: str):
        name = clean_name(name)
        return str(self.reg[name]) if name in self.reg else name


# ---------- 条件句式 ----------

_COND_PATTERNS = [
    # 如果X说的是真话，那么Y说的也是真话
    ("^如果" + _N + "说(?:的)?是?真话[，,]?(?:那么|那)?" + _N +
     "说(?:的)?(?:也|同样|一样)?是?真话$",
     lambda vb, a, b: Implies(vb.V(a), vb.V(b))),
    # 如果X说真话，那么Y在说谎
    ("^如果" + _N + "说(?:的)?是?真话[，,]?(?:那么|那)?" + _N + "(?:在)?说谎$",
     lambda vb, a, b: Implies(vb.V(a), Not(vb.V(b)))),
    # X和Y不可能都是真话
    ("^" + _N + "和" + _N + "说?的?不可能都是?真话$",
     lambda vb, a, b: Not(And(vb.V(a), vb.V(b)))),
    # X和Y不可能都在说谎  <=>  X、Y至少一人说真话
    ("^" + _N + "和" + _N + "说?的?不可能都在说谎$",
     lambda vb, a, b: Or(vb.V(a), vb.V(b))),
    # X和Y至少有一个说真话
    ("^" + _N + "和" + _N + "至少有一个(?:说真话|说的是?真话)$",
     lambda vb, a, b: Or(vb.V(a), vb.V(b))),
    # X和Y至少有一个说谎
    ("^" + _N + "和" + _N + "至少有一个(?:说谎|在说谎|说的是?假话|说的是?谎话)$",
     lambda vb, a, b: Or(Not(vb.V(a)), Not(vb.V(b)))),
    # X说Y和Z都在说谎
    ("^" + _N + "说" + _N + "和" + _N + "都在说谎$",
     lambda vb, a, b, c: Equivalent(vb.V(a), And(Not(vb.V(b)), Not(vb.V(c))))),
    # X说Y在说谎
    ("^" + _N + "说" + _N + "(?:在)?说谎$",
     lambda vb, a, b: Equivalent(vb.V(a), Not(vb.V(b)))),
    # X说Y说的是真话
    ("^" + _N + "说" + _N + "说(?:的)?是?真话$",
     lambda vb, a, b: Equivalent(vb.V(a), vb.V(b))),
]

_CLAIM_PATTERNS = [
    # X和Y(说的)(应该)也都是真话
    ("^" + _N1 + "和" + _N1 + "说?的?(?:应该|可能|肯定|一定)?[也就的都]{0,4}(?:是)?真话$",
     lambda a, b: ("both_true", [a, b])),
    # X和Y都在说谎
    ("^" + _N1 + "和" + _N1 + "说?的?(?:应该|可能|肯定|一定)?[也就的都]{0,4}(?:是)?(?:在)?(?:说谎|假话|谎话)$",
     lambda a, b: ("both_lie", [a, b])),
    # X说(的)是真话
    ("^" + _N1 + "(?:说(?:的)?是?真话|说真话)$",
     lambda a: ("truth", [a])),
    # X在说谎
    ("^" + _N1 + "(?:在?说谎|说的是?假话|说的是?谎话)$",
     lambda a: ("lie", [a])),
    ("^(无解|互相矛盾|不存在满足)", lambda a: ("none", [])),
    ("^无法确定", lambda a: ("unsure", [])),
]


def _candidates(sent: str):
    """一句话本身 + 冒号后的部分（处理「已知：…」「结论：…」）。"""
    cands = [sent]
    if "：" in sent:
        cands.append(sent.split("：")[-1])
    if ":" in sent:
        cands.append(sent.split(":")[-1])
    return cands


def parse_condition(sent: str, vb: VarBox):
    """返回 (SymPy 公式, 可读串) 或 (None, None)。"""
    return _parse_cond(sent, vb)


def _parse_cond(sent: str, vb: VarBox):
    s = re.sub(r"[「」『』“”‘’\"'\s]", "", sent)
    for cand in _candidates(s):
        for pat, fn in _COND_PATTERNS:
            m = re.match(pat, cand)
            if m:
                try:
                    e = fn(vb, *m.groups())
                except TypeError:
                    continue
                if e is not None:
                    return e, to_str(e)
    return None, None


def parse_claim(sent: str, vb: VarBox):
    """从一句 AI 原话中提取断言；不是断言则返回 None。

    返回 dict(kind, vars, raw)；kind ∈ truth/lie/both_true/both_lie/
    maybe_true/maybe_lie/none/unsure。只读登记表，不新增变量。
    """
    for cand in _candidates(sent.strip()):
        s = re.sub(r"[「」『』“”‘’\"'\s]", "", cand)
        for pat, fn in _CLAIM_PATTERNS:
            m = re.match(pat, s)
            if not m:
                continue
            try:
                kind, names = fn(*m.groups())
            except TypeError:
                continue
            names = [clean_name(n) for n in names]
            if any(n in _QUESTION_WORDS or not n for n in names):
                continue
            if "可能" in s and kind in ("both_true", "truth"):
                kind = "maybe_" + ("true" if kind == "both_true" else "true")
            elif "可能" in s and kind in ("both_lie", "lie"):
                kind = "maybe_lie"
            return {"kind": kind, "vars": names, "raw": sent.strip()}
    return None


def _fmt_row(row: dict, order) -> str:
    return "、".join(f"{n}={'真话' if row[n] else '谎话'}" for n in order)


def analyze(question_text: str, ai_text: str = "",
            extra_constraints: str = "") -> dict:
    """对一道「说真话/说谎」型推理题做全自动拆解与核验。"""
    vb = VarBox()
    src = (extra_constraints or "").strip() or question_text or ""

    conds, unsupported = [], []
    for sent in split_sentences(src):
        e, fs = _parse_cond(sent, vb)
        if e is None and _FRAG_SPLIT.search(sent):
            for frag in _FRAG_SPLIT.split(sent):
                frag = frag.strip()
                if not frag:
                    continue
                e, fs = _parse_cond(frag, vb)
                if e is not None:
                    conds.append({"sent": frag, "expr": e, "fstr": fs})
        elif e is not None:
            conds.append({"sent": sent, "expr": e, "fstr": fs})
        else:
            unsupported.append(sent)

    claims = []
    for sent in split_sentences(ai_text):
        c = parse_claim(sent, vb)
        if c:
            claims.append(c)
        elif _FRAG_SPLIT.search(sent):
            for frag in _FRAG_SPLIT.split(sent):
                c = parse_claim(frag.strip(), vb)
                if c:
                    claims.append(c)

    var_table = [{"var": str(vb.reg[n]), "name": n,
                  "meaning": f"{n} 说的是真话"} for n in vb.names]
    order = list(vb.names)
    syms = [vb.reg[n] for n in order]

    table, cond_keys = [], [f"c{i}" for i in range(len(conds))]
    for bits in itertools.product([False, True], repeat=len(order)):
        env = dict(zip(syms, bits))
        row = {n: b for n, b in zip(order, bits)}
        for i, c in enumerate(conds):
            row[cond_keys[i]] = bool(c["expr"].subs(env))
        row["all"] = all(row[k] for k in cond_keys)
        table.append(row)

    rows = [t for t in table if t["all"]]

    verdict = {}
    for n in order:
        if not rows:
            verdict[n] = "约束矛盾"
            continue
        vals = {r[n] for r in rows}
        verdict[n] = ("必真" if vals == {True}
                      else "必假" if vals == {False} else "无法确定")

    checked = [_verify_claim(c, vb, rows, verdict, order) for c in claims]
    errors = [c for c in checked if c["ok"] is False]

    return {
        "var_table": var_table,
        "conditions": [{"sent": c["sent"], "fstr": c["fstr"]} for c in conds],
        "unsupported": unsupported,
        "rows": rows,
        "table": table,
        "cond_keys": cond_keys,
        "verdict": verdict,
        "claims": checked,
        "errors": errors,
        "ok_all": (len(errors) == 0),
        "order": order,
    }


def _verify_claim(cl: dict, vb: VarBox, rows, verdict: dict, order) -> dict:
    names = cl["vars"]
    unknown = [n for n in names if n not in vb.reg]
    base = dict(cl)

    if unknown:
        return {**base, "ok": None, "status": "无法核验",
                "why": f"对象 {'、'.join(unknown)} 未在约束条件中出现",
                "counter": None}

    def letter_formula():
        ls = [vb.letter(n) for n in names]
        k = cl["kind"]
        if k in ("truth", "maybe_true"):
            return ls[0]
        if k in ("lie", "maybe_lie"):
            return "¬" + ls[0]
        if k == "both_true":
            return "∧".join(ls)
        if k == "both_lie":
            return "∧".join("¬" + x for x in ls)
        return ""

    formula = letter_formula()

    if cl["kind"] == "none":
        ok = len(rows) == 0
        return {**base, "formula": formula, "ok": ok,
                "status": "AI 正确" if ok else "AI 错误",
                "why": ("约束确实矛盾，无满足行" if ok
                        else f"存在 {len(rows)} 个满足全部约束的情形，并非无解"),
                "counter": None}

    if cl["kind"] == "unsure":
        forced = [n for n, v in verdict.items() if v in ("必真", "必假")]
        ok = not forced
        return {**base, "formula": formula, "ok": ok,
                "status": "AI 正确" if ok else "AI 错误",
                "why": ("确实存在无法确定的命题" if ok
                        else f"其实 {'、'.join(forced)} 是可以确定的"),
                "counter": None}

    if not rows:
        return {**base, "formula": formula, "ok": None, "status": "无法核验",
                "why": "约束条件自身矛盾（无满足行），无从核验断言",
                "counter": None}

    kind = cl["kind"]
    want = kind.endswith("lie") is False  # true 类断言要"都说真话"
    if kind in ("truth", "maybe_true", "both_true"):
        def sat(r):
            return all(r[n] for n in names)
    else:
        def sat(r):
            return all(not r[n] for n in names)

    sat_rows = [r for r in rows if sat(r)]
    maybe = kind.startswith("maybe")

    if len(sat_rows) == len(rows):
        return {**base, "formula": formula, "ok": True,
                "status": "AI 正确",
                "why": f"断言{'可能成立' if maybe else '必真'}："
                       f"在全部 {len(rows)} 个满足约束的情形下都成立",
                "counter": None}
    if not sat_rows:
        return {**base, "formula": formula, "ok": False, "status": "AI 错误",
                "why": f"断言必假：在所有 {len(rows)} 个满足约束的情形下都不成立",
                "counter": _fmt_row(rows[0], order)}
    if maybe:
        return {**base, "formula": formula, "ok": True, "status": "AI 正确",
                "why": "断言为『可能』型：确有满足约束且断言成立的情形",
                "counter": None}
    return {**base, "formula": formula, "ok": False, "status": "AI 错误",
            "why": "断言不必然成立：存在满足全部约束、但断言为假的情形",
            "counter": _fmt_row(next(r for r in rows if not sat(r)), order)}


# ---------- 内置示例 ----------

PRESETS = {
    "侦探四证人题（含 AI 典型错误）": {
        "question": (
            "某写字楼深夜失窃，保安锁定了男管家、厨师、园丁、杂役四人，"
            "警察分别讯问，四人各说了一句话。已知：如果男管家说的是真话，"
            "那么厨师说的也是真话；厨师和园丁说的不可能都是真话；"
            "园丁和杂役不可能都在说谎；如果杂役说真话，那么厨师在说谎。"
            "请问谁说的是真话？小偷最可能是谁？"
        ),
        "ai_answer": (
            "根据条件推理：男管家和厨师说的应该也都是真话，"
            "园丁和杂役都在说谎。所以作案的是园丁。"
        ),
    },
    "说谎者猜谜（唯一解）": {
        "question": (
            "A、B、C 三人，A说B在说谎，B说C在说谎，"
            "C说A和B都在说谎。问：谁说的是真话？"
        ),
        "ai_answer": "结论：B说的是真话，A和C在说谎。",
    },
    "真话假话双条件（AI 易错）": {
        "question": (
            "甲、乙、丙三人中只有一人说真话。"
            "如果甲说的是真话，那么乙说的也是真话；"
            "甲和乙不可能都是真话；乙和丙至少有一个说真话。"
            "问：谁说真话？"
        ),
        "ai_answer": "我认为甲说的是真话，乙和丙都在说谎。",
    },
}
