#!/bin/bash

echo "🔧 快速修复依赖问题..."

# 停止当前进程
echo "停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 检查并安装缺失的依赖
echo "安装 python-dotenv..."
pip3 install python-dotenv==1.0.0

echo "安装 python-telegram-bot..."
pip3 install python-telegram-bot==20.7

echo "安装其他依赖..."
pip3 install aiofiles==23.2.1
pip3 install aiohttp==3.9.1
pip3 install Pillow==10.1.0

# 验证安装
echo "验证依赖安装..."
python3 -c "
import sys
try:
    from dotenv import load_dotenv
    print('✅ python-dotenv OK')
    
    from telegram import Update
    print('✅ python-telegram-bot OK')
    
    from pathlib import Path
    print('✅ pathlib OK')
    
    import logging
    print('✅ logging OK')
    
    print('✅ 所有核心依赖正常')
except Exception as e:
    print(f'❌ 依赖检查失败: {e}')
    sys.exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ 依赖验证失败"
    exit 1
fi

# 创建日志目录
mkdir -p logs

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
sleep 5

# 检查状态
echo "检查状态..."
pm2 status mytestxiazai-bot

echo ""
echo "🔍 检查日志..."
pm2 logs mytestxiazai-bot --lines 10
