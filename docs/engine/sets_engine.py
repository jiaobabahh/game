# -*- coding: utf-8 -*-
"""集合运算核验器。

支持：∪ ∩ − ⊕（对称差）、幂集 P(X)、基数 |X|、子集判断（⊆ ⊇ ∈ ∉），
以及「全称断言」的自动反例搜索（遍历给定宇宙的所有子集组合）。
"""
from __future__ import annotations

import itertools
import re

import sympy as sp


class SetParseError(ValueError):
    pass


class SetEvalError(ValueError):
    pass


_OPS = ("≠", "⊆", "⊇", "∈", "∉", "≤", "≥", "=", "<", ">")


def normalize_set(s: str) -> str:
    s = s or ""
    repl = [("U", "∪"), ("\\cup", "∪"), ("\\cap", "∩"), ("\\setminus", "−"),
            ("\\oplus", "⊕"), ("\\Delta", "⊕"), ("\\\\", "−"),
            ("^", "⊕"), ("Δ", "⊕"), ("∆", "⊕")]
    for a, b in repl:
        s = s.replace(a, b)
    return s


_TOK_RE = re.compile(
    r"\s*(?:(?P<num>\d+)|"
    r"(?P<var>[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff]*)|"
    r"(?P<op>∪|∩|⊕|−|-|－|\\|\^|Δ|\(|\)|\{|\}|,|，|\|))"
)


def _tokenize(s: str):
    toks, i = [], 0
    while i < len(s):
        if s[i].isspace():
            i += 1
            continue
        m = _TOK_RE.match(s, i)
        if not m:
            raise SetParseError(f"无法识别的字符「{s[i]}」")
        toks.append(m.group(0))
        i = m.end()
    return toks


class _SP:
    def __init__(self, toks):
        self.toks = toks
        self.i = 0

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else None

    def _eat(self, want=None):
        t = self.peek()
        if t is None:
            raise SetParseError("集合表达式不完整")
        if want is not None and t != want:
            raise SetParseError(f"此处应为「{want}」，却遇到「{t}」")
        self.i += 1
        return t

    def parse(self):
        e = self.expr()
        if self.peek() is not None:
            raise SetParseError(f"多余的符号「{self.peek()}」")
        return e

    def expr(self):
        e = self.term()
        while self.peek() in ("∪", "⊕", "−", "-", "－", "\\"):
            self._eat()
            e = (self.peek() if False else self.toks[self.i - 1], e, self.term())
        return e

    def term(self):
        e = self.factor()
        while self.peek() == "∩":
            self._eat()
            e = ("∩", e, self.factor())
        return e

    def factor(self):
        if self.peek() == "P" and self.toks[self.i + 1:self.i + 2] == ["("]:
            self._eat()
            self._eat("(")
            e = self.expr()
            self._eat(")")
            return ("pow", e)
        if self.peek() == "|":
            self._eat("|")
            e = self.expr()
            self._eat("|")
            return ("card", e)
        return self.atom()

    def atom(self):
        t = self.peek()
        if t == "(":
            self._eat()
            e = self.expr()
            self._eat(")")
            return e
        if t == "{":
            self._eat("{")
            els = []
            if self.peek() != "}":
                els.append(self._element())
                while self.peek() in (",", "，"):
                    self._eat()
                    els.append(self._element())
            self._eat("}")
            return ("set", frozenset(els))
        if t is not None and re.fullmatch(r"\d+", t):
            self._eat()
            return ("num", int(t))
        if t is not None and re.fullmatch(r"[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff]*", t):
            self._eat()
            return ("var", t)
        raise SetParseError(f"意外的符号「{t}」")

    def _element(self):
        t = self.peek()
        if t is None:
            raise SetParseError("集合字面量缺少元素")
        if re.fullmatch(r"\d+", t):
            self._eat()
            return int(t)
        if re.fullmatch(r"[A-Za-z\u4e00-\u9fff][A-Za-z0-9\u4e00-\u9fff]*", t):
            self._eat()
            return t
        raise SetParseError(f"集合元素不合法「{t}」（仅支持数字或字母名）")


def parse_setexpr(src: str):
    return _SP(_tokenize(normalize_set(src))).parse()


def _all_subsets(s):
    elems = list(s)
    return [frozenset(c) for k in range(len(elems) + 1)
            for c in itertools.combinations(elems, k)]


def eval_expr(ast, env):
    t = ast[0]
    if t == "set":
        return ast[1]
    if t == "num":
        return ast[1]
    if t == "var":
        if ast[1] not in env:
            raise SetEvalError(f"集合变量 {ast[1]} 未定义")
        return env[ast[1]]
    if t == "pow":
        e = eval_expr(ast[1], env)
        if not isinstance(e, (frozenset, set)):
            raise SetEvalError("幂集 P(X) 的 X 必须是集合")
        return frozenset(frozenset(s) for s in _all_subsets(e))
    if t == "card":
        return len(eval_expr(ast[1], env))
    if t in ("∪", "∩", "−", "-", "－", "\\", "⊕"):
        a = eval_expr(ast[1], env)
        b = eval_expr(ast[2], env)
        if t == "∪":
            return a | b
        if t == "∩":
            return a & b
        if t in ("−", "-", "－", "\\"):
            return a - b
        return a ^ b
    raise SetEvalError(f"未知的集合运算节点 {t}")


def vars_in(ast):
    out = set()
    if isinstance(ast, tuple):
        if ast[0] == "var":
            out.add(ast[1])
        for x in ast[1:]:
            out |= vars_in(x)
    return out


def split_claim(src: str):
    for op in _OPS:
        if op in src:
            i = src.index(op)
            return src[:i].strip(), op, src[i + 1:].strip()
    raise SetParseError("断言中未找到比较符（支持 = ≠ ⊆ ⊇ ∈ ∉ ≤ ≥ < >）")


def _holds(op, a, b) -> bool:
    if op == "=":
        return a == b
    if op == "≠":
        return a != b
    if op == "⊆":
        return a <= b
    if op == "⊇":
        return a >= b
    if op == "∈":
        return a in b
    if op == "∉":
        return a not in b
    if op == "<":
        return a < b
    if op == ">":
        return a > b
    if op == "≤":
        return a <= b
    if op == "≥":
        return a >= b
    raise SetParseError(f"未支持的运算符 {op}")


def _fmt_val(v) -> str:
    if isinstance(v, (frozenset, set)):
        return "{" + ",".join(str(x) for x in sorted(v, key=str)) + "}"
    return str(v)


def check_claim_full(lhs_src: str, op: str, rhs_src: str,
                     env: dict | None = None, universe=None):
    """核验一个集合断言。

    返回：{ok, detail, counterexample, mode}
    - 若 env 覆盖全部自由变量，直接按给定赋值判断（mode=具体赋值）；
    - 否则若给出 universe，遍历其所有子集组合做全称验证（mode=全称验证），
      返回自动找到的反例（即"自动反例生成器"）。
    """
    env = env or {}
    lhs = parse_setexpr(lhs_src)
    rhs = parse_setexpr(rhs_src)
    names = sorted(vars_in(lhs) | vars_in(rhs), key=str)

    if not names:
        a = eval_expr(lhs, {})
        b = eval_expr(rhs, {})
        ok = _holds(op, a, b)
        return {"ok": ok,
                "detail": f"{lhs_src} {op} {rhs_src}："
                          f"{_fmt_val(a)} {op} {_fmt_val(b)} -> {ok}",
                "counterexample": None, "mode": "直接计算"}

    if names and all(n in env for n in names):
        ev = {k: eval_expr(parse_setexpr(v), {}) if isinstance(v, str) else v
              for k, v in env.items()}
        a = eval_expr(lhs, ev)
        b = eval_expr(rhs, ev)
        ok = _holds(op, a, b)
        mode = "具体赋值"
        detail = f"{lhs_src} {op} {rhs_src}：{_fmt_val(a)} {op} {_fmt_val(b)} -> {ok}"
        return {"ok": ok, "detail": detail, "counterexample": (None if ok else ev), "mode": mode}

    if universe is not None and names:
        if isinstance(universe, str):
            univ = [int(x) if re.fullmatch(r"-?\d+", x) else x
                    for x in re.split(r"[,，;；\s{}]+", universe) if x]
            univ = sorted(set(univ), key=str)
        else:
            univ = sorted(set(universe), key=str)
        if len(univ) > 8:
            raise SetParseError("宇宙元素过多（≤8），无法穷举")
        subsets = [frozenset(c) for k in range(len(univ) + 1)
                   for c in itertools.combinations(univ, k)]
        count = 0
        for combo in itertools.product(subsets, repeat=len(names)):
            count += 1
            if count > 300000:
                return {"ok": None, "detail": "组合规模过大，已放弃穷举",
                        "counterexample": None, "mode": "全称验证"}
            ev = dict(zip(names, combo))
            if not _holds(op, eval_expr(lhs, ev), eval_expr(rhs, ev)):
                return {"ok": False,
                        "detail": f"全称断言不成立（在 {_fmt_val(univ)} 的所有子集组合下验证）",
                        "counterexample": {k: _fmt_val(v) for k, v in ev.items()},
                        "mode": "全称验证"}
        return {"ok": True,
                "detail": f"全称成立：遍历 {_fmt_val(univ)} 的所有子集组合均满足",
                "counterexample": None, "mode": "全称验证"}

    raise SetEvalError(
        f"自由变量 {names} 缺少赋值，且未给 universe；请填写集合赋值或提供宇宙")


def parse_env_line(line: str):
    """解析「A = {1,2}」形式的集合赋值，返回 (name, frozenset)。"""
    if "=" not in line:
        raise SetParseError("赋值缺少『=』")
    name, rhs = line.split("=", 1)
    name = name.strip()
    rhs = rhs.strip()
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise SetParseError(f"非法的集合名「{name}」")
    val = eval_expr(parse_setexpr(rhs), {})
    if not isinstance(val, (frozenset, set)):
        raise SetEvalError(f"{name} 的赋值必须是集合，得到 {type(val).__name__}")
    return name, val
