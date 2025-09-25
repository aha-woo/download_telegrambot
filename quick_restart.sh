#!/bin/bash

echo "🔄 快速重启机器人（修复频道ID错误）..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

echo "✅ 已修复频道ID比较逻辑"
echo "  - 支持 @username 格式的频道"
echo "  - 支持 -1001234567890 格式的频道ID"

# 重启
pm2 start ecosystem.config.js

# 等待启动
sleep 5

# 检查状态
pm2 status mytestxiazai-bot

echo ""
echo "最新日志:"
pm2 logs mytestxiazai-bot --lines 10

echo ""
echo "✅ 重启完成！"
echo "📋 现在应该："
echo "  1. 没有频道ID转换错误"
echo "  2. /start 命令显示完整菜单"
echo "  3. 所有命令正常工作"
