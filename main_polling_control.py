#!/usr/bin/env python3
"""
Telegram Bot with Advanced Polling Control
支持手动控制轮询、时间段控制、可配置轮询间隔
"""

import asyncio
import logging
import os
import signal
import sys
import random
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta

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


class TelegramMediaBotWithPollingControl:
    def __init__(self):
        self.config = Config()
        self.application = None
        self.bot_handler = None
        self.media_downloader = None
        self.running = False
        self.shutdown_flag = False
        
        # 轮询控制状态
        self.polling_active = False
        self.polling_task = None
        self.last_update_id = None
        self.polling_stats = {
            'start_time': None,
            'requests_count': 0,
            'messages_processed': 0,
            'last_activity': None
        }

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /start 命令"""
        user = update.effective_user
        polling_status = "🟢 运行中" if self.polling_active else "🔴 已停止"
        in_time_range = "✅ 是" if self.config.is_in_time_range() else "❌ 否"
        
        welcome_message = (
            f"🤖 欢迎使用Telegram媒体转发机器人！\n\n"
            f"👋 你好 {user.mention_html()}！\n\n"
            f"📊 当前状态:\n"
            f"• 轮询状态: {polling_status}\n"
            f"• 轮询间隔: {self.config.polling_interval}秒\n"
            f"• 在允许时间段: {in_time_range}\n\n"
            f"🔧 轮询控制命令:\n"
            f"/start_polling - 开始轮询\n"
            f"/stop_polling - 停止轮询\n"
            f"/polling_status - 查看轮询状态\n"
            f"/set_interval <秒数> - 设置轮询间隔\n\n"
            f"📝 其他命令:\n"
            f"/status - 查看机器人状态\n"
            f"/random_download - 随机下载媒体文件\n\n"
            f"📱 源频道: {self.config.source_channel_id}\n"
            f"🎯 目标频道: {self.config.target_channel_id}\n"
            f"📁 下载路径: {self.config.download_path}"
        )
        
        await update.message.reply_html(welcome_message)

    async def start_polling_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """手动开始轮询"""
        if self.polling_active:
            await update.message.reply_text("⚠️ 轮询已经在运行中！")
            return
        
        if not self.config.polling_enabled:
            await update.message.reply_text("❌ 轮询功能已在配置中禁用！")
            return
        
        await self.start_custom_polling()
        await update.message.reply_text(
            f"✅ 轮询已启动！\n"
            f"🔄 轮询间隔: {self.config.polling_interval}秒\n"
            f"⏰ 启动时间: {datetime.now().strftime('%H:%M:%S')}"
        )

    async def stop_polling_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """手动停止轮询"""
        if not self.polling_active:
            await update.message.reply_text("⚠️ 轮询未在运行！")
            return
        
        await self.stop_custom_polling()
        await update.message.reply_text(
            f"🛑 轮询已停止！\n"
            f"📊 运行统计:\n"
            f"• 处理请求: {self.polling_stats['requests_count']}次\n"
            f"• 处理消息: {self.polling_stats['messages_processed']}条\n"
            f"• 运行时长: {self._get_running_duration()}"
        )

    async def polling_status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """查看轮询状态"""
        status = "🟢 运行中" if self.polling_active else "🔴 已停止"
        in_time_range = self.config.is_in_time_range()
        time_status = "✅ 在允许时间段内" if in_time_range else "❌ 不在允许时间段内"
        
        if self.config.time_control_enabled:
            time_info = f"\n⏰ 时间控制: {self.config.start_time}-{self.config.end_time} ({self.config.timezone})"
        else:
            time_info = "\n⏰ 时间控制: 禁用"
        
        status_message = (
            f"📊 轮询状态报告\n\n"
            f"🔄 轮询状态: {status}\n"
            f"⚡ 轮询间隔: {self.config.polling_interval}秒\n"
            f"📅 {time_status}{time_info}\n\n"
            f"📈 统计信息:\n"
            f"• 请求次数: {self.polling_stats['requests_count']}\n"
            f"• 处理消息: {self.polling_stats['messages_processed']}\n"
            f"• 运行时长: {self._get_running_duration()}\n"
            f"• 最后活动: {self._get_last_activity()}\n\n"
            f"🎯 下次轮询: {self._get_next_poll_time()}"
        )
        
        await update.message.reply_text(status_message)

    async def set_interval_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """设置轮询间隔"""
        try:
            if not context.args or len(context.args) != 1:
                await update.message.reply_text(
                    "❌ 使用方法: /set_interval <秒数>\n"
                    "例如: /set_interval 30"
                )
                return
            
            new_interval = float(context.args[0])
            if new_interval < 1.0:
                await update.message.reply_text("❌ 轮询间隔不能小于1秒！")
                return
            
            old_interval = self.config.polling_interval
            self.config.polling_interval = new_interval
            
            # 如果轮询正在运行，重启以应用新间隔
            if self.polling_active:
                await self.stop_custom_polling()
                await self.start_custom_polling()
                restart_msg = "（轮询已重启以应用新间隔）"
            else:
                restart_msg = ""
            
            await update.message.reply_text(
                f"✅ 轮询间隔已更新！\n"
                f"🔄 原间隔: {old_interval}秒\n"
                f"🔄 新间隔: {new_interval}秒\n"
                f"{restart_msg}"
            )
            
        except ValueError:
            await update.message.reply_text("❌ 请输入有效的数字！")
        except Exception as e:
            await update.message.reply_text(f"❌ 设置失败: {str(e)}")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /status 命令"""
        try:
            # 获取机器人信息
            bot_info = await update.get_bot().get_me()
            
            # 检查源频道
            try:
                source_chat = await update.get_bot().get_chat(self.config.source_channel_id)
                source_status = f"✅ 已连接: {source_chat.title}"
            except Exception as e:
                source_status = f"❌ 连接失败: {str(e)}"
            
            # 检查目标频道
            try:
                target_chat = await update.get_bot().get_chat(self.config.target_channel_id)
                target_status = f"✅ 已连接: {target_chat.title}"
            except Exception as e:
                target_status = f"❌ 连接失败: {str(e)}"
            
            # 检查下载目录
            download_path = Path(self.config.download_path)
            if download_path.exists():
                download_status = f"✅ 目录存在: {download_path.absolute()}"
            else:
                download_status = f"❌ 目录不存在: {download_path.absolute()}"
            
            polling_status = "🟢 运行中" if self.polling_active else "🔴 已停止"
            
            status_message = (
                f"🤖 机器人状态报告\n\n"
                f"🔹 机器人: {bot_info.first_name} (@{bot_info.username})\n"
                f"🔹 运行状态: {'✅ 正常运行' if self.running else '❌ 未运行'}\n"
                f"🔹 轮询状态: {polling_status}\n\n"
                f"📱 源频道: {source_status}\n"
                f"🎯 目标频道: {target_status}\n"
                f"📁 下载目录: {download_status}\n\n"
                f"⚙️ 配置信息:\n"
                f"• 代理: {'启用' if self.config.proxy_enabled else '禁用'}\n"
                f"• 延迟: {'启用' if self.config.delay_enabled else '禁用'}\n"
                f"• 时间控制: {'启用' if self.config.time_control_enabled else '禁用'}\n\n"
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

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理消息（只有在轮询激活时才处理）"""
        if not self.polling_active:
            return
        
        try:
            # 检查消息是否来自源频道
            if update.effective_chat.id != int(self.config.source_channel_id.replace('@', '').replace('-100', '')):
                return
            
            # 检查时间控制
            if not self.config.is_in_time_range():
                logger.info(f"⏰ 当前时间不在允许范围内，跳过消息处理")
                return
            
            # 添加随机延迟模拟人工操作
            if self.config.delay_enabled:
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                logger.info(f"⏱️ 等待 {delay:.1f}s 后处理消息（模拟人工操作）")
                await asyncio.sleep(delay)
            
            if not self.bot_handler:
                self.bot_handler = TelegramBotHandler(self.config)
            
            # 处理消息
            await self.bot_handler.handle_channel_message(update, context)
            
            # 更新统计
            self.polling_stats['messages_processed'] += 1
            self.polling_stats['last_activity'] = datetime.now()
            
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
        self.application.add_handler(CommandHandler("start_polling", self.start_polling_command))
        self.application.add_handler(CommandHandler("stop_polling", self.stop_polling_command))
        self.application.add_handler(CommandHandler("polling_status", self.polling_status_command))
        self.application.add_handler(CommandHandler("set_interval", self.set_interval_command))
        self.application.add_handler(CommandHandler("random_download", self.random_download_command))
        
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
            logger.info("机器人启动完成，准备开始轮询控制模式...")
            self.running = True

        except Exception as e:
            logger.error(f"启动时获取机器人信息失败: {e}")
    
    async def shutdown_callback(self, application):
        """关闭回调函数"""
        logger.info("机器人正在关闭...")
        await self.stop_custom_polling()
        self.running = False
        self.shutdown_flag = True

    def signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"收到信号 {signum}，设置关闭标志...")
        self.shutdown_flag = True

    async def start_custom_polling(self):
        """启动自定义轮询"""
        if self.polling_active:
            return
        
        self.polling_active = True
        self.polling_stats['start_time'] = datetime.now()
        self.polling_stats['requests_count'] = 0
        self.polling_stats['messages_processed'] = 0
        
        logger.info(f"🔄 开始自定义轮询 (间隔: {self.config.polling_interval}秒)")
        
        # 创建轮询任务
        self.polling_task = asyncio.create_task(self._polling_loop())

    async def stop_custom_polling(self):
        """停止自定义轮询"""
        if not self.polling_active:
            return
        
        self.polling_active = False
        
        if self.polling_task and not self.polling_task.done():
            self.polling_task.cancel()
            try:
                await self.polling_task
            except asyncio.CancelledError:
                pass
        
        logger.info("🛑 自定义轮询已停止")

    async def _polling_loop(self):
        """轮询循环"""
        try:
            while self.polling_active and not self.shutdown_flag:
                # 检查时间控制
                if not self.config.is_in_time_range():
                    logger.info(f"⏰ 当前时间不在允许范围内，跳过本次轮询")
                    await asyncio.sleep(self.config.polling_interval)
                    continue
                
                try:
                    # 获取更新
                    offset = self.last_update_id + 1 if self.last_update_id else None
                    updates = await self.application.bot.get_updates(
                        offset=offset,
                        limit=100,
                        timeout=int(self.config.polling_interval / 2)
                    )
                    
                    self.polling_stats['requests_count'] += 1
                    
                    if updates:
                        logger.info(f"📥 收到 {len(updates)} 个更新")
                        
                        for update in updates:
                            self.last_update_id = update.update_id
                            
                            # 处理更新
                            await self.application.process_update(update)
                    
                    # 等待下次轮询
                    await asyncio.sleep(self.config.polling_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"轮询过程中出错: {e}")
                    await asyncio.sleep(self.config.polling_interval)
                    
        except asyncio.CancelledError:
            logger.info("轮询循环被取消")

    def _get_running_duration(self):
        """获取运行时长"""
        if not self.polling_stats['start_time']:
            return "未运行"
        
        duration = datetime.now() - self.polling_stats['start_time']
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}小时{minutes}分{seconds}秒"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"

    def _get_last_activity(self):
        """获取最后活动时间"""
        if not self.polling_stats['last_activity']:
            return "无"
        
        return self.polling_stats['last_activity'].strftime('%H:%M:%S')

    def _get_next_poll_time(self):
        """获取下次轮询时间"""
        if not self.polling_active:
            return "轮询未运行"
        
        next_time = datetime.now() + timedelta(seconds=self.config.polling_interval)
        return next_time.strftime('%H:%M:%S')

    async def run(self):
        """运行机器人"""
        # 设置信号处理器
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        try:
            # 创建应用构建器
            app_builder = Application.builder().token(self.config.bot_token)
            
            # 配置代理
            proxy_config = self.config.get_proxy_config()
            if proxy_config:
                logger.info(f"🌐 配置代理: {proxy_config['proxy_type']}://{proxy_config['host']}:{proxy_config['port']}")
                try:
                    # 为 httpx 配置代理
                    if proxy_config['proxy_type'] == 'socks5':
                        proxy_url = f"socks5://{proxy_config.get('username', '')}:{proxy_config.get('password', '')}@{proxy_config['host']}:{proxy_config['port']}"
                        if not proxy_config.get('username'):
                            proxy_url = f"socks5://{proxy_config['host']}:{proxy_config['port']}"
                    elif proxy_config['proxy_type'] == 'http':
                        proxy_url = f"http://{proxy_config.get('username', '')}:{proxy_config.get('password', '')}@{proxy_config['host']}:{proxy_config['port']}"
                        if not proxy_config.get('username'):
                            proxy_url = f"http://{proxy_config['host']}:{proxy_config['port']}"
                    
                    # 设置代理
                    app_builder = app_builder.proxy(proxy_url)
                    logger.info(f"✅ 代理配置成功: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
                    
                except Exception as e:
                    logger.error(f"❌ 代理配置失败: {e}")
                    logger.warning("⚠️ 将使用直连模式")
            else:
                logger.info("🔗 使用直连模式（未配置代理）")
            
            # 创建应用
            self.application = app_builder.build()
            
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
            logger.info(f"⚙️ 轮询配置: 间隔={self.config.polling_interval}秒, 自动启动={self.config.auto_polling}")
            
            if self.config.time_control_enabled:
                logger.info(f"⏰ 时间控制: {self.config.start_time}-{self.config.end_time} ({self.config.timezone})")
            
            # 启动应用
            async with self.application:
                await self.application.start()
                
                # 根据配置决定是否自动开始轮询
                if self.config.auto_polling and self.config.polling_enabled:
                    await self.start_custom_polling()
                    logger.info("🔄 自动轮询已启动")
                else:
                    logger.info("⏸️ 轮询未自动启动，使用 /start_polling 命令手动启动")
                
                # 等待关闭信号
                while not self.shutdown_flag:
                    await asyncio.sleep(1)
                
                # 停止轮询和应用
                await self.stop_custom_polling()
                await self.application.stop()
            
            logger.info("机器人已正常关闭")
            
        except Exception as e:
            logger.error(f"机器人运行出错: {e}")


async def main():
    """主函数"""
    bot = TelegramMediaBotWithPollingControl()
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
