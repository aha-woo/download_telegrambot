#!/bin/bash

echo "🔄 快速重启机器人（优化延迟策略为消息级）..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

echo "✅ 已优化延迟策略为消息级:"
echo "  - 延迟以完整消息为单位（不是单个媒体）"
echo "  - 单个媒体消息：1次延迟处理"
echo "  - 媒体组消息：1次延迟处理整组"
echo "  - 避免媒体组内部时间差异"
echo "  - 保持消息完整性和时序"

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
echo "📋 关键修复说明："
echo ""
echo "🔧 之前问题：媒体级延迟导致时序混乱"
echo "  - 媒体组中每个媒体单独延迟"
echo "  - 同组消息到达时间不一致"
echo "  - 部分消息被误判为新媒体组"
echo ""
echo "✅ 现在方案：消息级延迟统一处理"
echo "  - 媒体组作为整体延迟处理"
echo "  - 单个消息延迟后一次性处理"
echo "  - 保持时序一致性"
echo "  - 符合人工操作习惯"
