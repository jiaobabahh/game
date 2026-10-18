# 命题逻辑与规则核验平台（离散数学实验二）

## 在线使用

**[打开离散数学核验台](https://jiaobabahh.github.io/game/)**

网页无需安装 Python 或登录。支持命题逻辑、集合、关系、图论、受限句式推理题拆解与 60 条案例回归。
首次访问需下载约 18 MB 的计算引擎；题目与核验计算留在浏览器中。
可将上方链接直接添加到 PPT 的超链接中，放映时点击打开。

浏览器版使用 Pyodide 运行原项目的 Python 核验引擎，界面位于 `docs/`。
更新引擎后运行 `python sync-web.py` 同步浏览器副本，再提交。
GitHub Pages 的发布源设置为 `main` 分支的 `/docs` 目录。
浏览器版支持粘贴 AI 答案核验，不包含在线调用模型的密钥。
集合全称检验仅覆盖输入的有限宇宙；自然语言拆解仅覆盖明确支持的句式。

让大模型（火山方舟）对离散数学题作答，再用本平台的确定性核验器逐条检查 AI 的答案：
对就放行，错就给出可复现的反例。代码分 `data / src / tests` 三层，拉下来就能跑。

## 目录结构

```
源代码/
├── data/                      数据文件（题目案例库、AI 实验记录、数据说明）
│   ├── cases.json             60 条预注册回归案例
│   ├── ai_experiment_record.txt  AI 原话与核验记录（完整留存）
│   └── 数据说明.md
├── src/                       源代码
│   ├── dmverify/              核验引擎包
│   │   ├── prop.py            命题逻辑：解析/真值表/等价判定(含反例)/范式
│   │   ├── sets_engine.py     集合：∪∩−⊕/幂集/基数/全称断言自动反例
│   │   ├── rels.py            关系：自反对称传递等性质判定 + 等价类
│   │   ├── graphs.py          图论：连通/度序列/欧拉回路与通路
│   │   ├── autodissect.py     自动拆解引擎：说谎推理题符号化 + AI 结论核验
│   │   ├── llm.py             大模型接口（火山方舟 OpenAI 兼容协议）
│   │   ├── cases.py           案例库（与 data/cases.json 同源）
│   │   ├── runner.py          案例执行器
│   │   └── config.py          接口配置
│   ├── app.py                 Streamlit 界面（8 页）
│   └── launch.py              端口启动器
├── tests/                     测试
│   └── test_dmverify.py       预注册回归 + 拆解引擎专项 + 单元测试
├── conftest.py                pytest 路径引导
├── run_platform.py            本地启动入口
├── requirements.txt           依赖清单
└── 启动平台.bat                Windows 双击启动
```

## 怎么装依赖

需要 Python 3.10 及以上。在 `源代码/` 目录下执行：

```bash
pip install -r requirements.txt
```

依赖一共五项：streamlit、sympy、networkx、requests、pytest。

## 怎么运行

```bash
# 方式一：图形界面（Streamlit）
python run_platform.py            # 或在 Windows 下双击 启动平台.bat
# 浏览器打开 http://localhost:8501（可用环境变量 PORT 改端口）

# 方式二：跑全部测试
pytest -q                         # 在 源代码/ 目录下执行
```

大模型接口：通过环境变量 `ARK_API_KEY` 设置自己的火山方舟 Key，
`ARK_MODEL` 填模型名（本实验用的是 deepseek-v4-1-flash-260910）。
不填 Key 时，除「AI 作答」页外的核验功能都照常可用。

## 数据放哪里

所有数据在 `data/` 下，来源、版本、隐私情况见 `data/数据说明.md`。
案例库在代码里是 `src/dmverify/cases.py`，`data/cases.json` 是它的 JSON 导出，
两者内容一致；改案例时先改 cases.py，再重新导出。
