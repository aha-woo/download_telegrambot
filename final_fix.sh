#!/bin/bash

echo "🔧 应用最终修复 - 彻底解决事件循环错误..."

# 停止当前的PM2进程
echo "停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 清理PM2日志
echo "清理PM2日志..."
pm2 flush mytestxiazai-bot 2>/dev/null || true

# 备份原文件
echo "备份原文件..."
if [ -f main.py ]; then
    cp main.py main_backup_$(date +%Y%m%d_%H%M%S).py
    echo "原文件已备份"
fi

# 使用最终修复版本
echo "使用最终修复版本..."
if [ -f main_final_fix.py ]; then
    cp main_final_fix.py main.py
    echo "✅ 已更新为最终修复版本"
else
    echo "❌ main_final_fix.py 文件不存在！"
    exit 1
fi

# 确保日志目录存在
echo "创建日志目录..."
mkdir -p logs

# 设置执行权限
chmod +x main.py

# 清理旧的日志文件
echo "清理旧日志..."
> logs/error.log
> logs/out.log
> logs/combined.log
> bot.log

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
echo "等待机器人启动..."
sleep 8

# 检查状态
echo "检查机器人状态..."
pm2 status mytestxiazai-bot

echo ""
echo "🔍 检查最近的日志..."
pm2 logs mytestxiazai-bot --lines 10

echo ""
echo "✅ 最终修复完成！"
echo ""
echo "📋 监控命令："
echo "  查看日志: pm2 logs mytestxiazai-bot"
echo "  查看状态: pm2 status"
echo "  重启机器人: pm2 restart mytestxiazai-bot"
echo "  停止机器人: pm2 stop mytestxiazai-bot"
echo ""
echo "🎯 如果看到以下日志说明修复成功："
echo "  - 🤖 Telegram媒体转发机器人启动成功！"
echo "  - 机器人信息: [机器人名称]"
echo "  - 机器人启动完成，开始监听消息..."
echo "  - Application started"
echo ""
echo "❌ 如果仍有 'Cannot close a running event loop' 错误，"
echo "   请联系技术支持进行进一步诊断。"
