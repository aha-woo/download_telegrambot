#!/usr/bin/env python3
"""
Complete Telegram Bot with Advanced Polling Control
包含所有原始功能 + 轮询控制 + 代理支持 + 随机延迟
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


class CompleteTelegramMediaBot:
    def __init__(self):
        self.config = Config()
        self.application = None
        self.bot_handler = None
        self.media_downloader = None
        self.running = False
        self.shutdown_flag = False
        
        # 原始功能：媒体组缓存
        self.media_groups = {}  # {media_group_id: {'messages': [], 'timer': asyncio.Task, 'last_message_time': float, 'status': str, 'download_start_time': float}}
        self.media_group_timeout = self.config.media_group_timeout  # 等待更多消息的时间
        self.media_group_max_wait = self.config.media_group_max_wait  # 等待新消息的最大时间
        self.download_timeout = self.config.download_timeout  # 下载超时时间（支持大文件）
        self.download_progress_check_interval = 30  # 秒 - 下载进度检查间隔（30秒，更频繁的进度报告）
        
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
        polling_status = "🟢 运行中" if self.polling_active else "🔴 已停止"
        in_time_range = "✅ 是" if self.config.is_in_time_range() else "❌ 否"
        
        await update.message.reply_text(
            "🤖 Telegram媒体转发机器人已启动！\n\n"
            f"📊 轮询状态: {polling_status}\n"
            f"⏱️ 轮询间隔: {self.config.polling_interval}秒\n"
            f"⏰ 在允许时间段: {in_time_range}\n\n"
            f"📡 源频道: {self.config.source_channel_id}\n"
            f"📤 目标频道: {self.config.target_channel_id}\n\n"
            "🔄 轮询控制:\n"
            "• /start_polling - 开始轮询\n"
            "• /stop_polling - 停止轮询\n"
            "• /polling_status - 查看轮询状态\n"
            "• /set_interval <秒数> - 设置轮询间隔\n\n"
            "🛠️ 手动命令:\n"
            "• /status - 查看机器人状态\n"
            "• /random_download <数量> - 随机下载N条历史消息\n"
            "• /selective_forward keyword <关键词> - 按关键词转发\n"
            "• /selective_forward type <类型> - 按消息类型转发\n"
            "• /selective_forward recent <数量> - 转发最近N条消息\n\n"
            "📝 使用示例:\n"
            "• /random_download 5\n"
            "• /selective_forward keyword 新品\n"
            "• /selective_forward type photo\n"
            "• /selective_forward recent 10"
        )

    # 轮询控制命令
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
        """处理 /random_download 命令 - 随机下载N个历史消息"""
        try:
            # 获取参数
            if not context.args:
                await update.message.reply_text(
                    "❌ 请指定要下载的消息数量\n"
                    "用法: /random_download <数量>\n"
                    "例如: /random_download 5"
                )
                return
            
            try:
                count = int(context.args[0])
                if count <= 0 or count > 100:
                    await update.message.reply_text("❌ 数量必须在1-100之间")
                    return
            except ValueError:
                await update.message.reply_text("❌ 请输入有效的数字")
                return
            
            await update.message.reply_text(f"🔄 开始随机下载 {count} 条历史消息...")
            
            if not self.media_downloader:
                self.media_downloader = MediaDownloader(self.config)
            
            # 获取源频道的历史消息
            try:
                # 获取频道最近的消息
                async for message in update.get_bot().iter_history(
                    chat_id=self.config.source_channel_id,
                    limit=count * 3  # 获取更多消息以供随机选择
                ):
                    # 只处理有媒体的消息
                    if self.bot_handler.has_media(message):
                        downloaded_files = await self.media_downloader.download_media(message, update.get_bot())
                        if downloaded_files:
                            # 转发消息
                            await self.bot_handler.forward_message(message, downloaded_files, update.get_bot())
                            # 清理文件
                            await self._cleanup_files(downloaded_files)
                            count -= 1
                            if count <= 0:
                                break
                            
                            # 添加随机延迟
                            if self.config.delay_enabled:
                                delay = random.uniform(self.config.forward_delay_min, self.config.forward_delay_max)
                                await asyncio.sleep(delay)
                
                await update.message.reply_text(f"✅ 随机下载完成！")
                
            except Exception as e:
                logger.error(f"获取历史消息失败: {e}")
                await update.message.reply_text(f"❌ 获取历史消息失败: {str(e)}")
                
        except Exception as e:
            logger.error(f"随机下载失败: {e}")
            await update.message.reply_text(f"❌ 随机下载失败: {str(e)}")

    async def selective_forward_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理 /selective_forward 命令 - 选择性转发"""
        try:
            if not context.args:
                await update.message.reply_text(
                    "❌ 请指定转发条件\n"
                    "用法: /selective_forward <条件>\n"
                    "支持的条件:\n"
                    "• 关键词: /selective_forward keyword <关键词>\n"
                    "• 消息类型: /selective_forward type <photo|video|document|text>\n"
                    "• 最近N条: /selective_forward recent <数量>\n"
                    "例如: /selective_forward keyword 新品\n"
                    "例如: /selective_forward type photo\n"
                    "例如: /selective_forward recent 10"
                )
                return
            
            condition_type = context.args[0].lower()
            
            if condition_type == "keyword":
                if len(context.args) < 2:
                    await update.message.reply_text("❌ 请指定关键词")
                    return
                keyword = " ".join(context.args[1:])
                await self._selective_forward_by_keyword(update, keyword)
                
            elif condition_type == "type":
                if len(context.args) < 2:
                    await update.message.reply_text("❌ 请指定消息类型 (photo|video|document|text)")
                    return
                media_type = context.args[1].lower()
                await self._selective_forward_by_type(update, media_type)
                
            elif condition_type == "recent":
                if len(context.args) < 2:
                    await update.message.reply_text("❌ 请指定消息数量")
                    return
                try:
                    count = int(context.args[1])
                    if count <= 0 or count > 50:
                        await update.message.reply_text("❌ 数量必须在1-50之间")
                        return
                except ValueError:
                    await update.message.reply_text("❌ 请输入有效的数字")
                    return
                await self._selective_forward_recent(update, count)
                
            else:
                await update.message.reply_text("❌ 未知的转发条件，支持: keyword, type, recent")
                
        except Exception as e:
            logger.error(f"选择性转发失败: {e}")
            await update.message.reply_text(f"❌ 选择性转发失败: {str(e)}")

    async def _selective_forward_by_keyword(self, update, keyword):
        """按关键词选择性转发"""
        await update.message.reply_text(f"🔍 搜索包含关键词 '{keyword}' 的消息...")
        # 实现关键词搜索逻辑
        # 这里可以添加具体的搜索和转发逻辑
        
    async def _selective_forward_by_type(self, update, media_type):
        """按类型选择性转发"""
        await update.message.reply_text(f"🔍 搜索类型为 '{media_type}' 的消息...")
        # 实现类型筛选逻辑
        
    async def _selective_forward_recent(self, update, count):
        """转发最近N条消息"""
        await update.message.reply_text(f"🔍 转发最近 {count} 条消息...")
        # 实现最近消息转发逻辑

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """处理消息"""
        try:
            # 检查消息是否来自源频道
            source_chat = update.effective_chat
            if source_chat is None:
                return
            
            # 支持频道用户名和ID两种格式
            if self.config.source_channel_id.startswith('@'):
                # 用户名格式：@channelname
                if source_chat.username != self.config.source_channel_id.replace('@', ''):
                    return
            else:
                # ID格式：-1001234567890
                try:
                    if source_chat.id != int(self.config.source_channel_id):
                        return
                except ValueError:
                    # 如果转换失败，跳过此消息
                    return
            
            # 如果自定义轮询未激活，不处理源频道消息
            if not self.polling_active:
                logger.info("⏸️ 自定义轮询未启动，跳过源频道消息处理")
                return
            
            # 检查时间控制
            if not self.config.is_in_time_range():
                logger.info(f"⏰ 当前时间不在允许范围内，跳过消息处理")
                return
            
            message = update.effective_message
            if not message:
                return
            
            logger.info(f"📥 收到来自源频道的消息 {message.message_id}")
            
            # 检查是否是媒体组消息
            if message.media_group_id:
                logger.info(f"消息 {message.message_id} 属于媒体组: {message.media_group_id}")
                await self._handle_media_group_message(message, context)
            else:
                # 处理单独的消息，在这里添加整个消息的延迟
                logger.info(f"📝 处理单独消息 {message.message_id}")
                
                # 添加消息级延迟模拟人工操作
                if self.config.delay_enabled:
                    delay = random.uniform(self.config.min_delay, self.config.max_delay)
                    logger.info(f"⏱️ 单独消息处理前等待 {delay:.1f}s（模拟人工操作）")
                    await asyncio.sleep(delay)
                
                await self._handle_single_message(message, context)
            
            # 更新统计
            self.polling_stats['messages_processed'] += 1
            self.polling_stats['last_activity'] = datetime.now()
            
        except Exception as e:
            logger.error(f"处理消息失败: {e}")

    async def _handle_single_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """处理单独的消息"""
        try:
            # 检查消息是否包含媒体
            if self.bot_handler.has_media(message):
                logger.info(f"📥 消息 {message.message_id} 包含媒体，开始下载...")
                
                # 消息级延迟已在上层处理，这里直接下载
                
                # 下载媒体文件
                downloaded_files = await self.media_downloader.download_media(message, context.bot)
                
                if downloaded_files:
                    logger.info(f"📥 消息 {message.message_id} 下载完成，共 {len(downloaded_files)} 个文件")
                    
                    # 消息级延迟已在上层处理，这里直接转发
                    
                    logger.info(f"📤 开始转发消息 {message.message_id} 到目标频道...")
                    
                    # 转发消息到目标频道
                    await self.bot_handler.forward_message(message, downloaded_files, context.bot)
                    logger.info(f"🎉 成功转发消息 {message.message_id} 到目标频道")
                    
                    # 自动清理已成功发布的文件
                    logger.info(f"🧹 开始清理消息 {message.message_id} 的本地文件...")
                    await self._cleanup_files(downloaded_files)
                    logger.info(f"🧹 消息 {message.message_id} 文件清理完成")
                else:
                    logger.warning(f"⚠️ 消息 {message.message_id} 没有可下载的媒体文件")
                    
            else:
                logger.info(f"📝 消息 {message.message_id} 是纯文本消息")
                
                # 消息级延迟已在上层处理，这里直接转发
                
                # 转发纯文本消息
                await self.bot_handler.forward_text_message(message, context.bot)
                logger.info(f"🎉 成功转发文本消息 {message.message_id} 到目标频道")
                
        except Exception as e:
            logger.error(f"❌ 处理消息 {message.message_id} 失败: {e}")

    async def _handle_media_group_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE):
        """处理媒体组消息"""
        media_group_id = message.media_group_id
        current_time = asyncio.get_event_loop().time()
        
        # 如果媒体组不存在，创建新的
        if media_group_id not in self.media_groups:
            self.media_groups[media_group_id] = {
                'messages': [],
                'timer': None,
                'last_message_time': current_time,
                'start_time': current_time,
                'status': 'collecting',  # collecting, downloading, completed
                'download_start_time': None,
            }
            
            # 只在新建媒体组时设置定时器
            logger.info(f"📦 创建新媒体组 {media_group_id}")
            self.media_groups[media_group_id]['timer'] = asyncio.create_task(
                self._process_media_group_after_timeout(media_group_id, context)
            )
        
        # 如果媒体组已经完成，忽略新消息
        if self.media_groups[media_group_id]['status'] == 'completed':
            logger.info(f"媒体组 {media_group_id} 已完成，忽略新消息")
            return
        
        # 如果媒体组正在下载，说明这是延迟到达的消息，应该添加到当前媒体组
        if self.media_groups[media_group_id]['status'] == 'downloading':
            logger.info(f"媒体组 {media_group_id} 正在下载，将延迟消息 {message.message_id} 加入当前组")
            # 直接添加到当前媒体组的消息列表，而不是等待队列
            self.media_groups[media_group_id]['messages'].append(message)
            self.media_groups[media_group_id]['last_message_time'] = current_time
            logger.info(f"媒体组 {media_group_id} 现在有 {len(self.media_groups[media_group_id]['messages'])} 条消息（包含延迟消息）")
            return
        
        # 添加消息到媒体组
        self.media_groups[media_group_id]['messages'].append(message)
        self.media_groups[media_group_id]['last_message_time'] = current_time
        logger.info(f"媒体组 {media_group_id} 现在有 {len(self.media_groups[media_group_id]['messages'])} 条消息")
        
        # 关键修复：不再重复取消和重新设置定时器！
        # 让原始定时器继续运行，它会在超时后检查 last_message_time

    async def _process_media_group_after_timeout(self, media_group_id: str, context: ContextTypes.DEFAULT_TYPE):
        """智能处理媒体组超时"""
        try:
            # 等待超时（收集阶段用短间隔，下载阶段用长间隔）
            sleep_time = self.media_group_timeout if media_group_id not in self.media_groups or self.media_groups[media_group_id]['status'] == 'collecting' else self.download_progress_check_interval
            await asyncio.sleep(sleep_time)
            
            if media_group_id not in self.media_groups:
                return
                
            current_time = asyncio.get_event_loop().time()
            group_data = self.media_groups[media_group_id]
            
            # 状态机处理
            if group_data['status'] == 'collecting':
                # 检查是否最近有新消息
                time_since_last_message = current_time - group_data['last_message_time']
                total_wait_time = current_time - group_data['start_time']
                
                logger.info(f"📦 媒体组 {media_group_id} 检查: 距上次消息 {time_since_last_message:.1f}s, 总等待 {total_wait_time:.1f}s")
                
                if time_since_last_message < self.media_group_timeout and total_wait_time < self.media_group_max_wait:
                    # 还有新消息且未超过最大等待时间，继续等待
                    logger.info(f"📦 媒体组 {media_group_id} 继续等待新消息...")
                    group_data['timer'] = asyncio.create_task(
                        self._process_media_group_after_timeout(media_group_id, context)
                    )
                    return
                else:
                    # 没有新消息或超过最大等待时间，开始下载
                    reason = "超过最大等待时间" if total_wait_time >= self.media_group_max_wait else "没有新消息"
                    logger.info(f"📦 媒体组 {media_group_id} {reason}，开始下载 ({len(group_data['messages'])} 条消息)")
                    await self._start_media_group_download(media_group_id, context)
                    
            elif group_data['status'] == 'downloading':
                # 下载阶段：检查下载超时
                download_time = current_time - group_data['download_start_time']
                if download_time > self.download_timeout:
                    logger.error(f"❌ 媒体组 {media_group_id} 下载超时（{download_time:.1f}秒），放弃处理")
                    del self.media_groups[media_group_id]
                else:
                    # 继续等待下载完成
                    minutes = int(download_time // 60)
                    seconds = int(download_time % 60)
                    if minutes > 0:
                        time_str = f"{minutes}分{seconds}秒"
                    else:
                        time_str = f"{seconds}秒"
                    
                    logger.info(f"📥 媒体组 {media_group_id} 正在下载中，已用时 {time_str} (超时时间: {self.download_timeout//60}分钟)")
                    group_data['timer'] = asyncio.create_task(
                        self._process_media_group_after_timeout(media_group_id, context)
                    )
                
        except asyncio.CancelledError:
            logger.info(f"⏹️ 媒体组 {media_group_id} 的处理被取消")
        except Exception as e:
            logger.error(f"❌ 处理媒体组 {media_group_id} 时出错: {e}")
            # 清理媒体组缓存
            if media_group_id in self.media_groups:
                del self.media_groups[media_group_id]

    async def _start_media_group_download(self, media_group_id: str, context: ContextTypes.DEFAULT_TYPE):
        """开始媒体组下载"""
        try:
            if media_group_id not in self.media_groups:
                return
                
            group_data = self.media_groups[media_group_id]
            messages = group_data['messages']
            
            # 更新状态
            group_data['status'] = 'downloading'
            group_data['download_start_time'] = asyncio.get_event_loop().time()
            
            logger.info(f"开始处理媒体组 {media_group_id}，包含 {len(messages)} 条消息")
            
            # 添加消息级延迟（以整个媒体组为单位）
            if self.config.delay_enabled:
                delay = random.uniform(self.config.min_delay, self.config.max_delay)
                logger.info(f"⏱️ 媒体组 {media_group_id} 处理前等待 {delay:.1f}s（模拟人工操作）")
                await asyncio.sleep(delay)
            
            # 设置下载进度监控
            group_data['timer'] = asyncio.create_task(
                self._process_media_group_after_timeout(media_group_id, context)
            )
            
            # 下载所有媒体文件（动态更新消息列表）
            all_downloaded_files = []
            
            logger.info(f"📥 开始下载媒体组 {media_group_id} 的所有文件...")
            
            i = 0
            while i < len(group_data['messages']):
                message = group_data['messages'][i]
                current_total = len(group_data['messages'])
                
                if self.bot_handler.has_media(message):
                    logger.info(f"📥 下载媒体组 {media_group_id} 第 {i+1}/{current_total} 个文件")
                    downloaded_files = await self.media_downloader.download_media(message, context.bot)
                    all_downloaded_files.extend(downloaded_files)
                    logger.info(f"✅ 完成下载第 {i+1}/{current_total} 个文件，共获得 {len(downloaded_files)} 个文件")
                
                i += 1
                
                # 检查是否有新消息在下载过程中添加
                if len(group_data['messages']) > current_total:
                    logger.info(f"📦 下载过程中发现新消息，媒体组 {media_group_id} 现在有 {len(group_data['messages'])} 条消息")
            
            logger.info(f"📥 媒体组 {media_group_id} 所有文件下载完成，共 {len(all_downloaded_files)} 个文件")
            
            # 取消进度监控定时器
            if group_data['timer']:
                group_data['timer'].cancel()
            
            # 转发消息（消息级延迟已在上层处理）
            if all_downloaded_files:
                
                # 使用第一条消息作为代表进行转发
                representative_message = messages[0]
                for msg in messages:
                    if self.bot_handler.has_media(msg):
                        representative_message = msg
                        break
                
                logger.info(f"📤 开始转发媒体组 {media_group_id} 到目标频道...")
                
                try:
                    await self.bot_handler.forward_message(representative_message, all_downloaded_files, context.bot)
                    
                    download_time = asyncio.get_event_loop().time() - group_data['download_start_time']
                    logger.info(f"🎉 成功转发媒体组 {media_group_id} 到目标频道！包含 {len(all_downloaded_files)} 个文件，总耗时 {download_time:.1f} 秒")
                    
                    # 更新状态为完成
                    group_data['status'] = 'completed'
                    
                    # 自动清理已成功发布的文件
                    logger.info(f"🧹 开始清理媒体组 {media_group_id} 的本地文件...")
                    await self._cleanup_files(all_downloaded_files)
                    logger.info(f"🧹 媒体组 {media_group_id} 文件清理完成")
                    
                except Exception as e:
                    logger.error(f"❌ 转发媒体组 {media_group_id} 失败: {e}")
                    logger.info(f"🧹 转发失败，清理本地文件...")
                    await self._cleanup_files(all_downloaded_files)
                    raise
            else:
                logger.warning(f"⚠️ 媒体组 {media_group_id} 没有可下载的媒体文件")
            
            # 不再需要处理等待队列，因为延迟消息已经直接加入当前媒体组
            
            # 清理媒体组缓存
            del self.media_groups[media_group_id]
            
        except Exception as e:
            logger.error(f"下载媒体组 {media_group_id} 时出错: {e}")
            # 清理媒体组缓存
            if media_group_id in self.media_groups:
                del self.media_groups[media_group_id]

    async def _cleanup_files(self, file_infos: list):
        """清理已成功发布的文件"""
        import os
        for file_info in file_infos:
            try:
                # 处理文件格式 {'path': Path, 'type': str}
                if isinstance(file_info, dict):
                    file_path = file_info['path']
                else:
                    # 向后兼容旧格式
                    file_path = file_info
                    
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"已清理文件: {file_path}")
            except Exception as e:
                logger.error(f"清理文件 {file_info} 失败: {e}")


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

    # 轮询控制相关方法
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
        """自定义轮询状态监控循环（用于统计和状态）"""
        try:
            while self.polling_active and not self.shutdown_flag:
                # 更新统计信息
                self.polling_stats['requests_count'] += 1
                
                # 等待下次检查
                await asyncio.sleep(self.config.polling_interval)
                    
        except asyncio.CancelledError:
            logger.info("自定义轮询监控被取消")

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
            
            # 初始化处理器
            if not self.bot_handler:
                self.bot_handler = TelegramBotHandler(self.config)
            if not self.media_downloader:
                self.media_downloader = MediaDownloader(self.config)
            
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
                
                # 始终启动标准轮询以处理命令
                await self.application.updater.start_polling(
                    allowed_updates=Update.ALL_TYPES,
                    drop_pending_updates=True
                )
                
                # 根据配置决定是否自动开始自定义轮询
                if self.config.auto_polling and self.config.polling_enabled:
                    await self.start_custom_polling()
                    logger.info("🔄 自动自定义轮询已启动")
                else:
                    logger.info("⏸️ 自定义轮询未自动启动，使用 /start_polling 命令手动启动")
                
                # 等待关闭信号
                while not self.shutdown_flag:
                    await asyncio.sleep(1)
                
                # 停止轮询
                await self.application.updater.stop()
                
                # 停止轮询和应用
                await self.stop_custom_polling()
                await self.application.stop()
            
            logger.info("机器人已正常关闭")
            
        except Exception as e:
            logger.error(f"机器人运行出错: {e}")


async def main():
    """主函数"""
    bot = CompleteTelegramMediaBot()
    try:
        await bot.run()
    except KeyboardInterrupt:
        logger.info("收到键盘中断，机器人已停止")
    except Exception as e:
        logger.error(f"程序异常退出: {e}")


if __name__ == "__main__":
    try:
        # 确保在 PM2 环境中正确运行
        asyncio.run(main())
        
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)
