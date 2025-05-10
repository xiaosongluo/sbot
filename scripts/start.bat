:: scripts/start.bat (Windows)
@echo off
echo 启动服务...

:: 配置环境变量
if exist .env (
    for /f "tokens=*" %%a in (.env) do (
        set "%%a"
    )
)

:: 激活虚拟环境（如果有）
if exist venv\Scripts\activate.bat (
    echo 激活虚拟环境...
    call venv\Scripts\activate.bat
)

:: 创建日志目录
if not exist logs mkdir logs

:: 启动程序
echo 启动程序...
start "SBot Monitor" cmd /c "python sbot.py > logs\sbot.log 2>&1"

echo 程序已启动
echo 日志文件: logs\sbot.log