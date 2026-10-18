# -*- coding: utf-8 -*-
"""pytest 路径引导：把 src 加入 sys.path，测试可直接 import dmverify。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))
