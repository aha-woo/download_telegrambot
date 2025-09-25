#!/bin/bash

echo "🔄 快速重启机器人..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

# 重启
pm2 start ecosystem.config.js

# 等待启动
sleep 3

# 检查状态
pm2 status mytestxiazai-bot

echo ""
echo "最新日志:"
pm2 logs mytestxiazai-bot --lines 8

echo ""
echo "✅ 重启完成！现在测试 /start 命令"
