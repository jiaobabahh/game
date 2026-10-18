"""Browser adapter. Original dmverify engines are copied unchanged by sync-web.py."""
import json
import re
from dmverify import prop, sets_engine, rels, graphs, autodissect, runner
from dmverify.cases import CASES


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [clean(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def verify(p):
    mode = p['mode']
    if any(len(str(v)) > 4000 for v in p.values()):
        raise ValueError('单个输入最多 4000 个字符。')
    if mode == 'prop':
        a = prop.parse(p['a'])
        b = prop.parse(p['b']) if p.get('b', '').strip() else None
        if len(a.free_symbols | (b.free_symbols if b is not None else set())) > 7:
            raise ValueError('网页版每次最多支持 7 个命题变量，请缩小题目。')
        syms, rows = prop.truth_table(a)
        result = {'title': prop.classify(a), 'formula': prop.to_str(a),
                  'table': [{**{str(k): v for k, v in env.items()}, '公式值': val}
                            for env, val in rows],
                  'dnf': prop.principal_dnf(a)[1], 'cnf': prop.principal_cnf(a)[1]}
        if b is not None:
            ok, counter, detail = prop.check_equivalence(a, b)
            result.update(title='两式等价' if ok else '两式不等价', ok=ok,
                          detail=detail, counterexample=counter)
        return result
    if mode == 'set':
        lhs, op, rhs = sets_engine.split_claim(p['claim'])
        env = dict(sets_engine.parse_env_line(line) for line in p.get('env', '').splitlines() if line.strip())
        universe = p.get('universe', '').strip()
        if universe and len(re.split(r'[,，;；\s{}]+', universe.strip('{} '))) > 4:
            raise ValueError('网页版穷举宇宙最多 4 个元素。')
        return sets_engine.check_claim_full(lhs, op, rhs, env, universe or None)
    if mode == 'rel':
        base, pairs = rels.parse_base(p['base']), rels.parse_pairs(p['pairs'])
        if not base:
            raise ValueError('请输入非空基本集。')
        # The source parser is forgiving. Reject leftover text instead of silently dropping it.
        pattern = r'\([^,，;；()\[\]\s]+\s*[,，]\s*[^,，;；()\[\]\s]+\)'
        leftovers = re.sub(pattern, '', p['pairs'])
        if leftovers.strip(' ,，;；{}\n\t'):
            raise ValueError('序偶请写成 (1,2),(2,3)，不能包含未识别内容。')
        if len(base) > 60 or len(pairs) > 300:
            raise ValueError('基本集最多 60 个元素，关系最多 300 个序偶。')
        if any(a not in base or b not in base for a, b in pairs):
            raise ValueError('序偶中的元素必须都属于基本集。')
        props = rels.rel_props(base, pairs)
        return {'title': '关系性质核验完成', 'properties': props,
                'classes': rels.equivalence_classes(base, pairs) if props['等价关系'][0] else [],
                'nodes': base, 'edges': pairs, 'directed': True}
    if mode == 'graph':
        edge_pattern = r'[^\s,，;；\-–—>]+\s*(?:-|–|—|~)\s*[^\s,，;；\-–—>]+'
        if re.sub(edge_pattern, '', p['edges']).strip(' ,，;；\n\t'):
            raise ValueError('边列表中有未识别内容，请写成 1-2, 2-3。')
        graph, _ = graphs.parse_edges(p['edges'])
        if len(graph) > 60 or graph.number_of_edges() > 300:
            raise ValueError('图最多 60 个顶点、300 条边。')
        return {'title': '图论核验完成', 'properties': graphs.check_graph(graph),
                'nodes': list(graph), 'edges': list(graph.edges), 'directed': False}
    if mode == 'dissect':
        r = autodissect.analyze(p.get('question', ''), p.get('answer', ''), p.get('extra', ''))
        if not r['conditions']:
            raise ValueError('未识别到支持的约束句式。请载入示例，或在补充约束中写“如果甲说真话，那么乙说真话”等条件。')
        # An unsupported clause may change the solution; never certify a partial interpretation.
        return {'title': '约束解析与断言核验', **r}
    if mode == 'regression':
        rows = []
        for case in CASES:
            ok, detail = runner.run_case(case)
            rows.append({'编号': case['id'], '案例': case['title'], '通过': ok, '说明': detail})
        return {'title': f"{sum(r['通过'] for r in rows)} / {len(rows)} 条案例通过", 'table': rows}
    raise ValueError('未知核验类型。')


def handle(payload):
    try:
        return json.dumps(clean(verify(json.loads(payload))), ensure_ascii=False)
    except (ValueError, KeyError, TypeError, RecursionError) as error:
        return json.dumps({'_error': str(error)}, ensure_ascii=False)
