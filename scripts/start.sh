# scripts/start.sh (Linux/macOS)
#!/bin/bash
# 启动程序脚本

# 配置环境变量
source .env 2>/dev/null

# 检查环境
OS=$(uname)
echo "检测到操作系统: $OS"

# 激活虚拟环境（如果有）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
fi

# 创建日志目录
mkdir -p logs

# 启动程序
echo "启动服务..."
nohup python sbot.py > logs/sbot.log 2>&1 &

# 保存进程ID
echo $! > sbot.pid

echo "程序已启动，进程ID: $(cat sbot.pid)"
echo "日志文件: logs/sbot.log"