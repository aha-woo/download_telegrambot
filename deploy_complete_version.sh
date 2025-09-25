#!/bin/bash

echo "🚀 部署完整版Telegram Bot（包含所有功能）..."

# 停止当前的PM2进程
echo "1. 停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 激活虚拟环境并安装依赖
echo "2. 激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 检查依赖安装
echo "3. 验证依赖安装..."
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
echo "4. 检查环境配置..."
if [ ! -f ".env" ]; then
    echo "⚠️ .env 文件不存在，创建默认配置..."
    cp config.env.example .env
    echo "✅ 已创建 .env 文件，请检查并修改配置"
fi

# 显示当前文件状态
echo "5. 当前文件状态:"
ls -la main*.py
echo ""

# 备份原文件
echo "6. 备份原文件..."
if [ -f main.py ]; then
    cp main.py main_backup_complete_$(date +%Y%m%d_%H%M%S).py
    echo "原文件已备份"
fi

# 使用完整版本
echo "7. 使用完整版本..."
if [ -f main_complete_with_polling.py ]; then
    cp main_complete_with_polling.py main.py
    echo "✅ 已更新为完整版本（$(wc -l < main_complete_with_polling.py) 行代码）"
    
    echo "📋 完整版本功能："
    echo "  ✅ 原始所有功能（媒体组、选择性转发、随机下载）"
    echo "  ✅ 轮询控制（手动启停、时间段控制）"
    echo "  ✅ 代理支持（SOCKS5/HTTP）"
    echo "  ✅ 随机延迟（模拟人工操作）"
    echo "  ✅ 智能媒体组处理"
    echo "  ✅ 下载进度监控"
else
    echo "❌ main_complete_with_polling.py 文件不存在！"
    echo "回退到修复版本..."
    if [ -f main_final_fix.py ]; then
        cp main_final_fix.py main.py
        echo "✅ 已更新为修复版本"
    else
        echo "❌ 没有找到任何修复版本！"
        exit 1
    fi
fi

# 确保日志目录存在
echo "8. 创建日志目录..."
mkdir -p logs

# 清理旧日志
echo "9. 清理旧日志..."
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true
> logs/combined.log 2>/dev/null || true

# 重新启动
echo "10. 重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
echo "11. 等待机器人启动..."
sleep 10

# 检查状态
echo "12. 检查机器人状态..."
pm2 status mytestxiazai-bot

echo ""
echo "13. 检查最近的日志..."
pm2 logs mytestxiazai-bot --lines 15

echo ""
echo "✅ 完整版本部署完成！"
echo ""
echo "📋 现在您拥有所有功能："
echo ""
echo "🔄 轮询控制命令："
echo "  /start_polling - 开始轮询"
echo "  /stop_polling - 停止轮询"
echo "  /polling_status - 查看轮询状态"
echo "  /set_interval <秒数> - 设置轮询间隔"
echo ""
echo "🛠️ 原始功能命令："
echo "  /status - 查看机器人状态"
echo "  /random_download <数量> - 随机下载N条历史消息"
echo "  /selective_forward keyword <关键词> - 按关键词转发"
echo "  /selective_forward type <类型> - 按消息类型转发"
echo "  /selective_forward recent <数量> - 转发最近N条消息"
echo ""
echo "🎯 智能功能："
echo "  • 自动处理媒体组（多张图片/视频）"
echo "  • 智能超时和重试机制"
echo "  • 代理支持和随机延迟"
echo "  • 时间段控制"
echo ""
echo "📱 测试建议："
echo "1. 先发送 /start 查看所有可用命令"
echo "2. 发送 /start_polling 开始轮询"
echo "3. 发送 /polling_status 监控状态"
echo "4. 在源频道发送消息测试转发功能"
