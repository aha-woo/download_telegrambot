#!/bin/bash

echo "🚀 部署带轮询控制功能的Telegram Bot..."

# 停止当前的PM2进程
echo "停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 激活虚拟环境并安装依赖
echo "激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 检查依赖安装
echo "验证依赖安装..."
python -c "
import sys
try:
    from dotenv import load_dotenv
    print('✅ python-dotenv OK')
    
    from telegram import Update
    print('✅ python-telegram-bot OK')
    
    import httpx
    print('✅ httpx OK')
    
    import pytz
    print('✅ pytz OK')
    
    print('✅ 所有依赖正常')
except Exception as e:
    print(f'❌ 依赖检查失败: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖验证失败"
    exit 1
fi

# 检查环境配置
echo "检查环境配置..."
if [ ! -f ".env" ]; then
    echo "⚠️ .env 文件不存在，请根据 config.env.example 创建"
    echo "📝 轮询控制配置示例："
    echo "POLLING_ENABLED=true"
    echo "POLLING_INTERVAL=60.0"
    echo "AUTO_POLLING=false"
    echo "TIME_CONTROL_ENABLED=true"
    echo "START_TIME=10:00"
    echo "END_TIME=12:00"
    echo "TIMEZONE=Asia/Shanghai"
    echo ""
    echo "❓ 是否使用示例配置创建 .env 文件？(y/n)"
    read -r create_env
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        cp config.env.example .env
        echo "✅ 已创建 .env 文件，请检查并修改配置"
    else
        echo "❌ 请手动创建 .env 文件"
        exit 1
    fi
fi

# 备份原文件
echo "备份原文件..."
if [ -f main.py ]; then
    cp main.py main_backup_polling_$(date +%Y%m%d_%H%M%S).py
    echo "原文件已备份"
fi

# 使用轮询控制版本
echo "使用轮询控制版本..."
if [ -f main_polling_control.py ]; then
    cp main_polling_control.py main.py
    echo "✅ 已更新为轮询控制版本"
else
    echo "❌ main_polling_control.py 文件不存在！"
    exit 1
fi

# 确保日志目录存在
echo "创建日志目录..."
mkdir -p logs

# 清理旧日志
echo "清理旧日志..."
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true
> logs/combined.log 2>/dev/null || true

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
echo "等待机器人启动..."
sleep 10

# 检查状态
echo "检查机器人状态..."
pm2 status mytestxiazai-bot

echo ""
echo "🔍 检查最近的日志..."
pm2 logs mytestxiazai-bot --lines 20

echo ""
echo "✅ 轮询控制版本部署完成！"
echo ""
echo "📋 新功能说明："
echo "  🕐 轮询控制: 可手动启动/停止轮询"
echo "  ⏰ 时间段控制: 支持指定时间段运行（如10:00-12:00）"
echo "  ⚡ 可配置轮询间隔: 默认60秒，可动态调整"
echo "  📊 实时状态监控: 查看轮询统计和状态"
echo ""
echo "🎯 轮询控制命令："
echo "  /start_polling - 开始轮询"
echo "  /stop_polling - 停止轮询"
echo "  /polling_status - 查看轮询状态"
echo "  /set_interval <秒数> - 设置轮询间隔"
echo "  /status - 查看机器人完整状态"
echo ""
echo "⚙️ 配置说明（在 .env 文件中）："
echo "  POLLING_ENABLED=true          # 启用轮询功能"
echo "  POLLING_INTERVAL=60.0         # 轮询间隔（秒）"
echo "  AUTO_POLLING=false            # 启动时自动开始轮询"
echo "  TIME_CONTROL_ENABLED=true     # 启用时间段控制"
echo "  START_TIME=10:00              # 开始时间"
echo "  END_TIME=12:00                # 结束时间"
echo "  TIMEZONE=Asia/Shanghai        # 时区"
echo ""
echo "📱 使用方法："
echo "1. 机器人启动后默认不会自动轮询（AUTO_POLLING=false）"
echo "2. 在Telegram中向机器人发送 /start_polling 开始轮询"
echo "3. 使用 /polling_status 监控轮询状态"
echo "4. 使用 /set_interval 60 设置轮询间隔为60秒"
echo "5. 时间控制功能会在指定时间段外自动暂停轮询"
