# scripts/stop.sh (Linux/macOS)
#!/bin/bash
# 停止程序脚本

echo "正在停止服务..."

# 检查PID文件是否存在
if [ -f "sbot.pid" ]; then
    PID=$(cat sbot.pid)
    
    # 检查进程是否正在运行
    if ps -p $PID > /dev/null; then
        echo "找到运行中的进程，PID: $PID"
        echo "正在终止进程..."
        kill -9 $PID
        
        # 等待一段时间确认进程已停止
        sleep 2
        
        if ps -p $PID > /dev/null; then
            echo "警告: 进程未成功终止，请手动终止: kill -9 $PID"
        else
            echo "进程已成功终止"
            rm sbot.pid
            echo "PID文件已删除"
        fi
    else
        echo "错误: 未找到运行中的进程，PID文件可能已过时"
        echo "请检查是否有其他实例在运行: ps aux | grep sbot.py"
    fi
else
    echo "错误: 未找到PID文件，请确保程序已通过start.sh启动"
    echo "请检查是否有其他实例在运行: ps aux | grep sbot.py"
fi