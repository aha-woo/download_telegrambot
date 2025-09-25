#!/bin/bash

echo "🔧 修复Telegram Bot..."

# 停止当前的PM2进程
echo "停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 备份原文件
echo "备份原文件..."
if [ -f main.py ]; then
    cp main.py main_backup_$(date +%Y%m%d_%H%M%S).py
    echo "原文件已备份"
fi

# 确保日志目录存在
echo "创建日志目录..."
mkdir -p logs

# 检查固定版本是否存在
if [ ! -f main_fixed.py ]; then
    echo "❌ main_fixed.py 文件不存在！"
    exit 1
fi

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待几秒让机器人启动
sleep 3

# 检查状态
echo "检查机器人状态..."
pm2 status mytestxiazai-bot

echo "✅ 修复完成！"
echo "查看日志: pm2 logs mytestxiazai-bot"
echo "查看状态: pm2 status"
echo "实时日志: pm2 logs mytestxiazai-bot --lines 50"
