#!/usr/bin/env python3
"""
Telegram Bot for downloading media from source channel and forwarding to target channel
Final fix version for PM2 deployment - no event loop errors
"""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from telegram import Update, Message, ChatMember
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError

from bot_handler import TelegramBotHandler
from media_downloader import MediaDownloader
from config import Config

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class TelegramMediaBot:
    def __init__(self):
        self.config = Config()
        self.application = None
        self.bot_handler = None
        self.media_downloader = None
        self.running = False
        self.shutdown_flag = False

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        welcome_message = (
            f"🤖 欢迎使用Telegram媒体转发机器人！\n\n"
            f"👋 你好 {user.mention_html()}！\n\n"
            f"🔧 可用命令：\n"
            f"/start - 显示欢迎信息\n"
            f"/status - 查看机器人状态\n"
            f"/random_download - 随机下载媒体文件\n"
            f"/selective_forward - 选择性转发消息\n\n"
            f"📱 源频道: {self.config.source_channel_id}\n"
            f"🎯 目标频道: {self.config.target_channel_id}\n"
            f"📁 下载路径: {self.config.download_path}"
        )
        
        await update.message.reply_html(welcome_message)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        try:
            # 获取机器人信息
            bot_info = await context.bot.get_me()
            
            # 检查源频道
            try:
                source_chat = await context.bot.get_chat(self.config.source_channel_id)
                source_status = f"✅ 已连接: {source_chat.title}"
            except Exception as e:
                source_status = f"❌ 连接失败: {str(e)}"
            
            # 检查目标频道
            try:
                target_chat = await context.bot.get_chat(self.config.target_channel_id)
                target_status = f"✅ 已连接: {target_chat.title}"
            except Exception as e:
                target_status = f"❌ 连接失败: {str(e)}"
            
            # 检查下载目录
            download_path = Path(self.config.download_path)
            if download_path.exists():
                download_status = f"✅ 目录存在: {download_path.absolute()}"
            else:
                download_status = f"❌ 目录不存在: {download_path.absolute()}"
            
            status_message = (
                f"🤖 机器人状态报告\n\n"
                f"🔹 机器人: {bot_info.first_name} (@{bot_info.username})\n"
                f"🔹 运行状态: {'✅ 正常运行' if self.running else '❌ 未运行'}\n\n"
                f"📱 源频道: {source_status}\n"
                f"🎯 目标频道: {target_status}\n"
                f"📁 下载目录: {download_status}\n\n"
                f"⏰ 检查时间: {update.message.date}"
            )
            
            await update.message.reply_text(status_message)
            
        except Exception as e:
            await update.message.reply_text(f"❌ 获取状态失败: {str(e)}")

    async def random_download_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理随机下载命令"""
        try:
            await update.message.reply_text("🔄 开始随机下载...")
            
            if not self.media_downloader:
                self.media_downloader = MediaDownloader(self.config)
            
            result = await self.media_downloader.random_download_from_channel(
                self.config.source_channel_id
            )
            
            if result:
                await update.message.reply_text(f"✅ 下载成功: {result}")
            else:
                await update.message.reply_text("❌ 下载失败，请查看日志")
                
        except Exception as e:
            logger.error(f"随机下载失败: {e}")
            await update.message.reply_text(f"❌ 下载失败: {str(e)}")

    async def selective_forward_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理选择性转发命令"""
        try:
            await update.message.reply_text("🔄 开始选择性转发...")
            
            if not self.bot_handler:
                self.bot_handler = TelegramBotHandler(self.config)
            
            # 这里可以添加选择性转发的逻辑
            await update.message.reply_text("🔧 选择性转发功能开发中...")
            
        except Exception as e:
            logger.error(f"选择性转发失败: {e}")
            await update.message.reply_text(f"❌ 转发失败: {str(e)}")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理消息"""
        try:
            # 检查消息是否来自源频道
            if update.effective_chat.id != int(self.config.source_channel_id.replace('@', '').replace('-100', '')):
                return
            
            if not self.bot_handler:
                self.bot_handler = TelegramBotHandler(self.config)
            
            # 处理消息
            await self.bot_handler.handle_channel_message(update, context)
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """错误处理"""
        logger.error(f"更新 {update} 导致错误 {context.error}")
    
    def setup_handlers(self):
        """设置消息处理器"""
        # 命令处理器
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("status", self.status_command))
        self.application.add_handler(CommandHandler("random_download", self.random_download_command))
        self.application.add_handler(CommandHandler("selective_forward", self.selective_forward_command))
        
        # 消息处理器
        self.application.add_handler(MessageHandler(
            filters.ALL & ~filters.COMMAND, 
            self.handle_message
        ))
        
        # 错误处理器
        self.application.add_error_handler(self.error_handler)
    
    async def startup_callback(self, application):
        """启动回调函数"""
        try:
            # 获取机器人信息
            bot_info = await application.bot.get_me()
            logger.info(f"机器人信息: {bot_info.first_name} (@{bot_info.username})")
            logger.info("机器人启动完成，开始监听消息...")
            self.running = True

        except Exception as e:
            logger.error(f"启动时获取机器人信息失败: {e}")
    
    async def shutdown_callback(self, application):
        """关闭回调函数"""
        logger.info("机器人正在关闭...")
        self.running = False
        self.shutdown_flag = True
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，设置关闭标志...")
        self.shutdown_flag = True
        if self.application:
            self.application.stop_running()

    async def run(self):
        """运行机器人"""
        # 设置信号处理器
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # 创建应用
            self.application = Application.builder().token(self.config.bot_token).build()
            
            # 设置处理器
            self.setup_handlers()
            
            # 添加启动和关闭回调
            self.application.post_init = self.startup_callback
            self.application.post_shutdown = self.shutdown_callback
            
            # 创建下载目录
            download_path = Path(self.config.download_path)
            download_path.mkdir(exist_ok=True)
            
            logger.info("🤖 Telegram媒体转发机器人启动成功！")
            logger.info(f"源频道: {self.config.source_channel_id}")
            logger.info(f"目标频道: {self.config.target_channel_id}")
            logger.info(f"下载目录: {download_path.absolute()}")
            
            # 启动机器人 - 使用 start_polling 而不是 run_polling
            async with self.application:
                await self.application.start()
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                
                # 等待关闭信号
                while not self.shutdown_flag:
                    await asyncio.sleep(1)
                
                # 停止轮询
                await self.application.updater.stop()
                await self.application.stop()
            
            logger.info("机器人已正常关闭")
            
        except Exception as e:
            logger.error(f"机器人运行出错: {e}")


async def main():
    """主函数"""
    bot = TelegramMediaBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("收到键盘中断，机器人已停止")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")


if __name__ == "__main__":
    try:
        # 确保在 PM2 环境中正确运行
        if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        # 直接运行，让 PM2 管理进程
        asyncio.run(main())
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
