#!/bin/bash

echo "🔄 快速重启机器人（修复媒体组处理）..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

echo "✅ 已修复关键问题:"
echo "  - 媒体组处理逻辑优化"
echo "  - 停止重复取消/重设定时器"
echo "  - 改进状态管理和超时判断"
echo "  - 支持频道用户名和ID格式"
echo "  - 增加下载超时到2小时（支持大文件）"

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
echo "  1. 媒体组不再无限循环"
echo "  2. 媒体组能正常下载和转发"
echo "  3. /start 命令显示完整菜单"
echo "  4. 所有功能正常工作"
