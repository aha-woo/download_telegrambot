#!/usr/bin/env python3
"""
代理连接测试脚本
"""

import asyncio
import sys
from telegram import Bot
from telegram.error import TelegramError
from config import Config
from dotenv import load_dotenv

async def test_proxy():
    """测试代理连接"""
    print("🔧 开始测试代理连接...")
    
    try:
        # 加载环境变量
        load_dotenv()
        
        # 创建配置
        config = Config()
        print(f"📋 配置信息:\n{config}")
        
        # 创建Bot实例
        proxy_config = config.get_proxy_config()
        if proxy_config:
            print(f"🌐 使用代理: {proxy_config['proxy_type']}://{proxy_config['host']}:{proxy_config['port']}")
            
            # 构建代理URL
            if proxy_config['proxy_type'] == 'socks5':
                proxy_url = f"socks5://{proxy_config.get('username', '')}:{proxy_config.get('password', '')}@{proxy_config['host']}:{proxy_config['port']}"
                if not proxy_config.get('username'):
                    proxy_url = f"socks5://{proxy_config['host']}:{proxy_config['port']}"
            elif proxy_config['proxy_type'] == 'http':
                proxy_url = f"http://{proxy_config.get('username', '')}:{proxy_config.get('password', '')}@{proxy_config['host']}:{proxy_config['port']}"
                if not proxy_config.get('username'):
                    proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
            
            print(f"🔗 代理URL: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
        else:
            print("🔗 使用直连模式")
            proxy_url = None
        
        # 创建Bot（使用代理）
        if proxy_url:
            from telegram.ext import Application
            app = Application.builder().token(config.bot_token).proxy(proxy_url).build()
            bot = app.bot
        else:
            bot = Bot(token=config.bot_token)
        
        # 测试连接
        print("📡 测试Telegram API连接...")
        
        async with bot:
            # 获取机器人信息
            bot_info = await bot.get_me()
            print(f"✅ 连接成功！")
            print(f"🤖 机器人信息:")
            print(f"   - 名称: {bot_info.first_name}")
            print(f"   - 用户名: @{bot_info.username}")
            print(f"   - ID: {bot_info.id}")
            
            # 测试获取更新
            print("📥 测试获取更新...")
            try:
                updates = await bot.get_updates(limit=1)
                print(f"✅ 获取更新成功！收到 {len(updates)} 个更新")
            except Exception as e:
                print(f"⚠️ 获取更新失败: {e}")
            
            # 测试获取频道信息
            print("🔍 测试频道访问...")
            try:
                source_chat = await bot.get_chat(config.source_channel_id)
                print(f"✅ 源频道访问成功: {source_chat.title}")
            except Exception as e:
                print(f"❌ 源频道访问失败: {e}")
            
            try:
                target_chat = await bot.get_chat(config.target_channel_id)
                print(f"✅ 目标频道访问成功: {target_chat.title}")
            except Exception as e:
                print(f"❌ 目标频道访问失败: {e}")
        
        print("\n🎉 代理测试完成！")
        
        # 测试IP地址（如果使用代理）
        if proxy_url:
            print("🌍 检查当前IP地址...")
            try:
                import httpx
                async with httpx.AsyncClient(proxy=proxy_url) as client:
                    response = await client.get("https://httpbin.org/ip", timeout=10.0)
                    ip_info = response.json()
                    print(f"✅ 当前IP: {ip_info.get('origin', 'Unknown')}")
            except Exception as e:
                print(f"⚠️ 无法检查IP: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ 代理测试失败: {e}")
        return False

async def main():
    """主函数"""
    success = await test_proxy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
