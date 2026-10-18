# -*- coding: utf-8 -*-
"""命题逻辑核验器（基于 SymPy）。

功能：公式解析（兼容 LaTeX 与多种记法）、真值表生成、等价判定
（含反例赋值）、永真/永假/可满足分类、主析取范式与主合取范式。
"""
from __future__ import annotations

import itertools
import re

import sympy as sp
from sympy.logic.boolalg import (And, BooleanFalse, BooleanTrue, Equivalent,
                                 Implies, Not, Or)


class ParseError(ValueError):
    """公式解析失败。"""


# ---------- 记法归一 ----------

def normalize(src: str) -> str:
    """把 LaTeX / ASCII 多种写法归一到内部符号 ¬ ∧ ∨ → ↔。"""
    s = src or ""
    s = s.replace("$", "").replace("\\left", "").replace("\\right", "")
    s = re.sub(r"\\(?:boldsymbol|mathbf|mathrm|mathit|mathcal|text|bm)\s*\{",
               "(", s)
    s = (s.replace("\\lnot", "¬").replace("\\neg", "¬")
          .replace("\\land", "∧").replace("\\wedge", "∧").replace("\\bigwedge", "∧")
          .replace("\\lor", "∨").replace("\\vee", "∨").replace("\\bigvee", "∨")
          .replace("\\rightarrow", "→").replace("\\to", "→")
          .replace("\\Rightarrow", "→").replace("\\implies", "→")
          .replace("\\leftrightarrow", "↔").replace("\\Leftrightarrow", "↔")
          .replace("\\iff", "↔").replace("\\equiv", "↔")
          .replace("≡", "↔"))
    s = re.sub(r"\\quad|\\qquad", " ", s)
    s = re.sub(r"\\[,;:]", " ", s)
    for a, b in (("<=>", "↔"), ("<->", "↔"), ("->", "→"), ("=>", "→"),
                 ("/\\", "∧"), ("\\/", "∨"), ("&&", "∧"), ("||", "∨"),
                 ("~", "¬"), ("!", "¬")):
        s = s.replace(a, b)
    s = s.replace("}", ")")
    return s


_TOKEN_RE = re.compile(r"[¬∧∨→↔()]|[A-Za-z][A-Za-z0-9_]*")


def _tokenize(s: str):
    toks, i = [], 0
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        m = _TOKEN_RE.match(s, i)
        if not m:
            raise ParseError(
                f"第 {i + 1} 个字符「{s[i]}」无法识别"
                f"（只支持连词 ¬ ∧ ∨ → ↔、括号和变量字母）")
        toks.append(m.group(0))
        i = m.end()
    return toks


class _Parser:
    """递归下降解析器。优先级：¬ > ∧ > ∨ > →（右结合）> ↔。"""

    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _eat(self, want=None):
        t = self.peek()
        if t is None:
            raise ParseError("公式不完整（意外结尾）")
        if want is not None and t != want:
            raise ParseError(f"此处应为「{want}」，却遇到「{t}」")
        self.i += 1
        return t

    def parse(self):
        e = self._iff()
        if self.peek() is not None:
            raise ParseError(f"多余的符号「{self.peek()}」（连词缺失或括号不匹配）")
        return e

    def _atom(self):
        t = self.peek()
        if t == "(":
            self._eat()
            e = self._iff()
            self._eat(")")
            return e
        if t is None:
            raise ParseError("公式不完整（意外结尾）")
        if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", t):
            self._eat()
            if t == "T":
                return BooleanTrue()
            if t == "F":
                return BooleanFalse()
            return sp.Symbol(t)
        raise ParseError(f"「{t}」不是合法的命题变量或左括号")

    def _unary(self):
        if self.peek() == "¬":
            self._eat()
            return Not(self._unary())
        return self._atom()

    def _and(self):
        e = self._unary()
        while self.peek() == "∧":
            self._eat()
            e = And(e, self._unary())
        return e

    def _or(self):
        e = self._and()
        while self.peek() == "∨":
            self._eat()
            e = Or(e, self._and())
        return e

    def _imp(self):
        e = self._or()
        if self.peek() == "→":
            self._eat()
            return Implies(e, self._imp())
        return e

    def _iff(self):
        e = self._imp()
        while self.peek() == "↔":
            self._eat()
            e = Equivalent(e, self._imp())
        return e


def parse(src: str):
    """解析命题公式，返回 SymPy 表达式；失败抛 ParseError（中文提示）。"""
    s = normalize(src)
    if not s.strip():
        raise ParseError("公式为空")
    return _Parser(_tokenize(s)).parse()


# ---------- 展示 ----------

def _prec(e) -> int:
    if isinstance(e, (BooleanTrue, BooleanFalse, sp.Symbol)):
        return 9
    if isinstance(e, Not):
        return 4
    if isinstance(e, And):
        return 3
    if isinstance(e, Or):
        return 2
    if isinstance(e, Implies):
        return 1
    return 0


def to_str(e) -> str:
    """把 SymPy 布尔表达式打印成 ¬ ∧ ∨ → ↔ 形式。"""
    return _to_str(e, 0)


def _to_str(e, mp: int) -> str:
    p = _prec(e)
    if isinstance(e, sp.Symbol):
        s = e.name
    elif isinstance(e, BooleanTrue):
        s = "T"
    elif isinstance(e, BooleanFalse):
        s = "F"
    elif isinstance(e, Not):
        s = "¬" + _to_str(e.args[0], 4)
    elif isinstance(e, And):
        s = "∧".join(_to_str(a, 3) for a in e.args)
    elif isinstance(e, Or):
        s = "∨".join(_to_str(a, 2) for a in e.args)
    elif isinstance(e, Implies):
        s = _to_str(e.args[0], 2) + "→" + _to_str(e.args[1], 1)
    elif isinstance(e, Equivalent):
        s = _to_str(e.args[0], 1) + "↔" + _to_str(e.args[1], 1)
    else:
        s = str(e)
    if p < mp:
        s = "(" + s + ")"
    return s


# ---------- 真值表 / 判定 ----------

def free_symbols(expr):
    return sorted(expr.free_symbols, key=lambda s: s.name)


def truth_table(expr):
    """返回 (变量列表, 行列表)；每行为 (赋值 dict, 真值)。

    变量按名称排序，第一个变量视为二进制最高位（极小项编号约定）。
    """
    syms = free_symbols(expr)
    rows = []
    for bits in itertools.product([False, True], repeat=len(syms)):
        env = dict(zip(syms, bits))
        rows.append((env, bool(expr.subs(env))))
    return syms, rows


def row_index(env, syms) -> int:
    idx = 0
    for s in syms:
        idx = idx * 2 + (1 if env[s] else 0)
    return idx


def classify(expr) -> str:
    """返回「永真」「永假」「可满足」之一。"""
    _, rows = truth_table(expr)
    vals = [v for _, v in rows]
    if all(vals):
        return "永真"
    if not any(vals):
        return "永假"
    return "可满足"


def check_equivalence(a, b):
    """返回 (是否等价, 反例赋值 dict 或 None, 中文说明)。"""
    syms = sorted(a.free_symbols | b.free_symbols, key=lambda s: s.name)
    for bits in itertools.product([False, True], repeat=len(syms)):
        env = dict(zip(syms, bits))
        if bool(a.subs(env)) != bool(b.subs(env)):
            ce = {s.name: ("真" if v else "假") for s, v in env.items()}
            return False, ce, f"反例：取 {ce} 时两式一真一假，不等价"
    return True, None, "两式在所有赋值下取值完全相同，等价成立"


def principal_dnf(expr):
    """主析取范式：返回 (极小项编号列表, 可读字符串)。"""
    syms, rows = truth_table(expr)
    idxs, terms = [], []
    for env, v in rows:
        if v:
            idxs.append(row_index(env, syms))
            lits = [(s.name if env[s] else "¬" + s.name) for s in syms]
            terms.append("∧".join(lits))
    if not syms:
        return ([0] if idxs else []), ("T" if idxs else "F")
    if not idxs:
        return [], "矛盾式：无成真赋值，主析取范式为 0"
    return idxs, f"m{tuple(idxs)} = " + "∨".join("(" + t + ")" for t in terms)


def principal_cnf(expr):
    """主合取范式：返回 (极大项编号列表, 可读字符串)。"""
    syms, rows = truth_table(expr)
    idxs, terms = [], []
    for env, v in rows:
        if not v:
            idxs.append(row_index(env, syms))
            lits = [(s.name if not env[s] else "¬" + s.name) for s in syms]
            terms.append("∨".join(lits))
    if not syms:
        return ([] if idxs else [0]), ("F" if idxs else "T")
    if not idxs:
        return [], "永真式：无成假赋值，主合取范式为 1"
    return idxs, f"M{tuple(idxs)} = " + "∧".join("(" + t + ")" for t in terms)
