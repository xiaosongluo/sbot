:: scripts/stop.bat (Windows)
@echo off
echo 正在停止服务...

:: 查找并终止进程
tasklist /FI "WINDOWTITLE eq SBot Price Monitor" | find "cmd.exe" > nul
if %errorlevel% equ 0 (
    echo 找到运行中的进程，正在终止...
    taskkill /FI "WINDOWTITLE eq SBot Price Monitor" /F
    echo 进程已终止
) else (
    echo 未找到运行中的进程
    echo 请检查是否有其他实例在运行: tasklist | find "python"
)