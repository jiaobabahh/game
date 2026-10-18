# -*- coding: utf-8 -*-
"""dmverify —— 离散数学智能问答与答案核验平台（Python 后端核心包）

模块划分（对应指导书「核心技术」）：
- prop          命题逻辑：SymPy 解析 / 真值表 / 判等价 / 主析取·主合取范式
- sets_engine   集合：∪ ∩ − ⊕、幂集 P(X)、基数 |X|、全称断言自动反例搜索
- rels          关系：自反/对称/传递/反对称/等价 + NetworkX 构图
- graphs        图论：连通性、度序列、欧拉回路/通路（NetworkX）
- autodissect   自动拆解引擎：自然语言约束 → 原子命题 → 符号化 → 真值表判定
- llm           大模型接口：火山方舟（Ark）OpenAI 兼容协议
- cases/runner  60 条预注册回归案例与统一执行器
"""

__version__ = "2.0.0"
