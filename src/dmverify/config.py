# -*- coding: utf-8 -*-
"""全局配置：火山方舟（Ark）大模型接口。

密钥优先级：侧边栏输入 > 环境变量 ARK_API_KEY > 本文件默认值。
"""
import os

ARK_API_KEY = os.environ.get(
    "ARK_API_KEY",
    "",
)
ARK_MODEL = os.environ.get("ARK_MODEL", "deepseek-v4-1-flash-260910")
ARK_URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
