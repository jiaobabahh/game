# -*- coding: utf-8 -*-
"""大模型接口：火山方舟（Ark）OpenAI 兼容协议。

实验定位：让大模型对离散数学题目作答，再由本平台的确定性核验器
检查 AI 答案是否出错——因此这里的提示词刻意"朴素"，不给任何提示。
"""
from __future__ import annotations

import os

import requests

from . import config

ARK_URL = config.ARK_URL
DEFAULT_MODEL = config.ARK_MODEL

SYSTEM_PROMPT = (
    "你是一个离散数学答题器。请直接回答用户给出的离散数学题目："
    "先用一两句话给出明确结论，再给出简要理由。不要联网，不要反问。"
)


class LLMError(RuntimeError):
    """调用大模型失败（网络 / 鉴权 / 返回格式）。"""


def ask_llm(question: str, api_key: str | None = None,
            model: str | None = None, timeout: int = 60) -> str:
    """调用方舟 chat/completions，返回模型回答文本。"""
    key = api_key or os.environ.get("ARK_API_KEY") or config.ARK_API_KEY
    mdl = model or config.ARK_MODEL
    if not key:
        raise LLMError("未配置 API Key：请在侧边栏填入，或设置环境变量 ARK_API_KEY")
    payload = {
        "model": mdl,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    }
    try:
        r = requests.post(
            ARK_URL,
            json=payload,
            headers={
                "Authorization": "Bearer " + key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise LLMError(f"网络错误：{e}") from e
    if r.status_code != 200:
        raise LLMError(f"接口返回 HTTP {r.status_code}：{r.text[:200]}")
    try:
        data = r.json()
        return data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError) as e:
        raise LLMError(f"返回格式异常：{e}") from e
