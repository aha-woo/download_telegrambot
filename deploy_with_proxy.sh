#!/bin/bash

echo "🚀 部署带代理和延迟功能的Telegram Bot..."

# 停止当前的PM2进程
echo "停止当前进程..."
pm2 stop mytestxiazai-bot 2>/dev/null || echo "进程未运行"
pm2 delete mytestxiazai-bot 2>/dev/null || echo "进程不存在"

# 创建虚拟环境（如果不存在）
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境并安装依赖
echo "激活虚拟环境并安装依赖..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 检查依赖安装
echo "验证依赖安装..."
python -c "
import sys
try:
    from dotenv import load_dotenv
    print('✅ python-dotenv OK')
    
    from telegram import Update
    print('✅ python-telegram-bot OK')
    
    import httpx
    print('✅ httpx OK')
    
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
echo "检查环境配置..."
if [ ! -f ".env" ]; then
    echo "⚠️ .env 文件不存在，请根据 config.env.example 创建"
    echo "📝 示例配置："
    echo "PROXY_ENABLED=true"
    echo "PROXY_HOST=185.241.228.116"
    echo "PROXY_PORT=12324"
    echo "PROXY_USERNAME=14a7615c70476"
    echo "PROXY_PASSWORD=2c83188abb"
    echo "DELAY_ENABLED=true"
    echo ""
    echo "❓ 是否使用示例配置创建 .env 文件？(y/n)"
    read -r create_env
    if [ "$create_env" = "y" ] || [ "$create_env" = "Y" ]; then
        cp config.env.example .env
        echo "✅ 已创建 .env 文件，请检查并修改配置"
    else
        echo "❌ 请手动创建 .env 文件"
        exit 1
    fi
fi

# 备份原文件
echo "备份原文件..."
if [ -f main.py ]; then
    cp main.py main_backup_proxy_$(date +%Y%m%d_%H%M%S).py
    echo "原文件已备份"
fi

# 使用带代理功能的版本
echo "使用带代理功能的版本..."
if [ -f main_final_fix.py ]; then
    cp main_final_fix.py main.py
    echo "✅ 已更新为支持代理的版本"
else
    echo "❌ main_final_fix.py 文件不存在！"
    exit 1
fi

# 测试代理连接
echo "测试代理连接..."
python test_proxy.py

if [ $? -ne 0 ]; then
    echo "⚠️ 代理测试失败，但继续部署..."
else
    echo "✅ 代理测试成功"
fi

# 确保日志目录存在
echo "创建日志目录..."
mkdir -p logs

# 清理旧日志
echo "清理旧日志..."
> logs/error.log 2>/dev/null || true
> logs/out.log 2>/dev/null || true
> logs/combined.log 2>/dev/null || true

# 重新启动
echo "重新启动机器人..."
pm2 start ecosystem.config.js

# 等待启动
echo "等待机器人启动..."
sleep 10

# 检查状态
echo "检查机器人状态..."
pm2 status mytestxiazai-bot

echo ""
echo "🔍 检查最近的日志..."
pm2 logs mytestxiazai-bot --lines 20

echo ""
echo "✅ 部署完成！"
echo ""
echo "📋 功能说明："
echo "  🌐 代理: SOCKS5代理已配置"
echo "  ⏱️ 延迟: 随机延迟已启用，模拟人工操作"
echo "  🎯 转发延迟: 1-4秒"
echo "  📥 下载延迟: 2-8秒"
echo ""
echo "🔧 管理命令："
echo "  查看日志: pm2 logs mytestxiazai-bot"
echo "  查看状态: pm2 status"
echo "  重启机器人: pm2 restart mytestxiazai-bot"
echo "  测试代理: python test_proxy.py"
echo ""
echo "⚙️ 延迟配置（在 .env 文件中修改）："
echo "  DELAY_ENABLED=true/false"
echo "  FORWARD_DELAY_MIN=1.0"
echo "  FORWARD_DELAY_MAX=4.0"
echo "  DOWNLOAD_DELAY_MIN=2.0"
echo "  DOWNLOAD_DELAY_MAX=8.0"
