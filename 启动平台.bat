@echo off
chcp 65001 >nul
cd /d %~dp0
echo 正在启动 命题逻辑与规则核验平台 ...
python run_platform.py
pause
