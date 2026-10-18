# -*- coding: utf-8 -*-
"""部署启动器：读取 PORT 环境变量并调起 Streamlit（沙箱/本地通用）。"""
import os
import sys

from streamlit.web import cli as stcli


def main():
    port = os.environ.get("PORT", "8501")
    sys.argv = [
        "streamlit", "run", "app.py",
        "--server.port", port,
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
        "--server.fileWatcherType", "none",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
