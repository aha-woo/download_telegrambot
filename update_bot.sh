#!/bin/bash

echo "🔄 更新Telegram Bot到最新修复版本..."

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

# 替换为修复版本
echo "使用修复版本..."
if [ -f main_fixed.py ]; then
    cp main_fixed.py main.py
    echo "✅ 已更新为修复版本"
else
    echo "❌ main_fixed.py 文件不存在！"
    exit 1
fi

# 确保日志目录存在
echo "创建日志目录..."
mkdir -p logs

# 设置执行权限
chmod +x main.py

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
sleep 5

# 检查状态
echo "检查机器人状态..."
pm2 status mytestxiazai-bot

echo ""
echo "✅ 更新完成！"
echo "查看日志: pm2 logs mytestxiazai-bot"
echo "查看状态: pm2 status"
echo "实时日志: pm2 logs mytestxiazai-bot --lines 50"
echo ""
echo "如果仍有问题，请运行: pm2 restart mytestxiazai-bot"
