#!/bin/bash

echo "🔄 快速重启机器人（修复Caption长度限制）..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

echo "✅ 已修复关键问题:"
echo "  - 媒体组处理逻辑优化"
echo "  - 增加下载超时到2小时（支持大文件）"
echo "  - 修复Caption长度限制问题"
echo "  - 智能截断过长文本（在句子边界）"
echo "  - 支持频道用户名和ID格式"

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
echo "  1. 媒体组能正常下载和转发"
echo "  2. 过长的Caption自动截断"
echo "  3. 不再出现'Message caption is too long'错误"
echo "  4. 所有功能正常工作"
