#!/bin/bash

echo "🔄 快速重启机器人（配置化网络超时设置）..."

# 停止当前进程
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理日志
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true

echo "✅ 已配置化网络超时设置:"
echo "  - 超时时间可通过环境变量调整"
echo "  - UPLOAD_CONNECT_TIMEOUT（连接超时）"
echo "  - UPLOAD_READ_TIMEOUT（读取超时）"
echo "  - UPLOAD_WRITE_TIMEOUT（写入超时）"
echo "  - 默认支持1GB文件（30分钟超时）"

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
echo "📋 现在可以根据网络情况调整超时："
echo ""
echo "🌐 常见网络速度建议："
echo "  1-5 Mbps:   设置 UPLOAD_WRITE_TIMEOUT=3600 (1小时)"
echo "  5-20 Mbps:  默认设置 1800秒 (30分钟) ✅"
echo "  20+ Mbps:   可减少到 UPLOAD_WRITE_TIMEOUT=900 (15分钟)"
echo ""
echo "💡 在 config.env 中修改这些值！"
