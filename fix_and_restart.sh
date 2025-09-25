#!/bin/bash

echo "🔧 修复并重启机器人..."

# 停止当前进程
echo "1. 停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 激活虚拟环境并确保依赖完整
echo "2. 检查虚拟环境和依赖..."
source venv/bin/activate

# 安装缺失的依赖
pip install python-dotenv==1.0.0 pytz==2023.3 --quiet

# 验证关键依赖
python -c "
try:
    from dotenv import load_dotenv
    from telegram import Update
    import pytz
    print('✅ 所有依赖正常')
except Exception as e:
    print(f'❌ 依赖问题: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖验证失败"
    exit 1
fi

# 确保配置文件存在
echo "3. 检查配置文件..."
if [ ! -f ".env" ]; then
    cp config.env.example .env
    echo "✅ 已创建 .env 配置文件"
fi

# 清理旧日志
echo "4. 清理日志..."
mkdir -p logs
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

# 重启机器人
echo "5. 重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
sleep 5

# 检查状态
echo "6. 检查状态..."
pm2 status mytestxiazai-bot

echo ""
echo "7. 最新日志..."
pm2 logs mytestxiazai-bot --lines 10

echo ""
echo "✅ 修复完成！"
echo ""
echo "如果看到启动成功，在Telegram中测试："
echo "  /start_polling - 开始轮询"
echo "  /polling_status - 查看状态"
