# -*- coding: utf-8 -*-
"""本地启动入口：python run_platform.py
把 src 加入 sys.path 后调起 Streamlit 应用（端口默认 8501，可用 PORT 环境变量改）。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT, "src"))
os.chdir(os.path.join(ROOT, "src"))

from launch import main  # noqa: E402

if __name__ == "__main__":
    main()
