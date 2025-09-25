"""
Telegram Bot 消息处理模块
"""

import asyncio
import logging
import random
from typing import List, Optional
from pathlib import Path

from telegram import Update, Message, InputMediaPhoto, InputMediaVideo, InputMediaDocument
from telegram.error import TelegramError

from config import Config

logger = logging.getLogger(__name__)


class TelegramBotHandler:
    """Telegram Bot 消息处理器"""
    
    def __init__(self, config: Config):
        self.config = config
    
    def has_media(self, message: Message) -> bool:
        """检查消息是否包含媒体文件"""
        return any([
            message.photo,
            message.video,
            message.document,
            message.audio,
            message.voice,
            message.video_note,
            message.animation,
            message.sticker
        ])
    
    def get_media_type(self, message: Message) -> Optional[str]:
        """获取媒体类型"""
        if message.photo:
            return 'photo'
        elif message.video:
            return 'video'
        elif message.document:
            return 'document'
        elif message.audio:
            return 'audio'
        elif message.voice:
            return 'voice'
        elif message.video_note:
            return 'video_note'
        elif message.animation:
            return 'animation'
        elif message.sticker:
            return 'sticker'
        return None
    
    async def handle_channel_message(self, update, context):
        """处理来自源频道的消息"""
        message = update.effective_message
        if not message:
            return
        
        logger.info(f"📥 收到来自源频道的消息 {message.message_id}")
        
        try:
            # 检查消息是否包含媒体
            if self.has_media(message):
                logger.info(f"📥 消息 {message.message_id} 包含媒体，开始下载...")
                
                # 添加下载前的随机延迟
                if self.config.delay_enabled:
                    delay = random.uniform(self.config.download_delay_min, self.config.download_delay_max)
                    logger.info(f"⏱️ 下载前等待 {delay:.1f}s（模拟人工操作）")
                    await asyncio.sleep(delay)
                
                # 下载媒体文件
                from media_downloader import MediaDownloader
                downloader = MediaDownloader(self.config)
                downloaded_files = await downloader.download_media(message, context.bot)
                
                if downloaded_files:
                    logger.info(f"📥 消息 {message.message_id} 下载完成，共 {len(downloaded_files)} 个文件")
                    
                    # 添加转发前的随机延迟
                    if self.config.delay_enabled:
                        delay = random.uniform(self.config.forward_delay_min, self.config.forward_delay_max)
                        logger.info(f"⏱️ 转发前等待 {delay:.1f}s（模拟人工操作）")
                        await asyncio.sleep(delay)
                    
                    logger.info(f"📤 开始转发消息 {message.message_id} 到目标频道...")
                    
                    # 转发消息到目标频道
                    await self.forward_message(message, downloaded_files, context.bot)
                    logger.info(f"🎉 成功转发消息 {message.message_id} 到目标频道")
                    
                    # 自动清理已成功发布的文件
                    logger.info(f"🧹 开始清理消息 {message.message_id} 的本地文件...")
                    await self._cleanup_files(downloaded_files)
                    logger.info(f"🧹 消息 {message.message_id} 文件清理完成")
                else:
                    logger.warning(f"⚠️ 消息 {message.message_id} 没有可下载的媒体文件")
                    
            else:
                logger.info(f"📝 消息 {message.message_id} 是纯文本消息")
                
                # 添加转发前的随机延迟
                if self.config.delay_enabled:
                    delay = random.uniform(self.config.forward_delay_min, self.config.forward_delay_max)
                    logger.info(f"⏱️ 转发前等待 {delay:.1f}s（模拟人工操作）")
                    await asyncio.sleep(delay)
                
                # 转发纯文本消息
                await self.forward_text_message(message, context.bot)
                logger.info(f"🎉 成功转发文本消息 {message.message_id} 到目标频道")
                
        except Exception as e:
            logger.error(f"❌ 处理消息 {message.message_id} 失败: {e}")
            raise
    
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
    
    async def forward_text_message(self, message: Message, bot=None):
        """发送纯文本消息（作为原创内容）"""
        try:
            # 获取bot实例
            bot_instance = bot or getattr(message, 'bot', None)
            if not bot_instance:
                raise ValueError("无法获取bot实例")
            
            # 构建消息文本
            forward_text = self._build_forward_text(message)
            
            # 发送到目标频道
            await bot_instance.send_message(
                chat_id=self.config.target_channel_id,
                text=forward_text,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            
            logger.info(f"成功转发文本消息到目标频道")
            
        except TelegramError as e:
            logger.error(f"转发文本消息失败: {e}")
            raise
    
    async def forward_message(self, message: Message, downloaded_files: List[dict], bot=None):
        """发送包含媒体的消息（作为原创内容）"""
        try:
            # 获取bot实例
            bot_instance = bot or getattr(message, 'bot', None)
            if not bot_instance:
                raise ValueError("无法获取bot实例")
            
            # 构建消息文本
            forward_text = self._build_forward_text(message)
            
            # 根据媒体类型和数量选择转发方式
            media_type = self.get_media_type(message)
            
            if len(downloaded_files) == 1:
                # 单个媒体文件
                await self._send_single_media(message, downloaded_files[0], forward_text, bot_instance)
            else:
                # 多个媒体文件
                await self._send_media_group(message, downloaded_files, forward_text, bot_instance)
            
            logger.info(f"成功转发媒体消息到目标频道")
            
        except TelegramError as e:
            logger.error(f"转发媒体消息失败: {e}")
            raise
    
    async def _send_single_media(self, message: Message, file_info: dict, caption: str, bot):
        """发送单个媒体文件"""
        file_path = file_info['path']
        media_type = file_info['type']
        
        # 通用超时设置（从配置读取，支持大文件）
        timeout_kwargs = {
            'read_timeout': self.config.upload_read_timeout,
            'write_timeout': self.config.upload_write_timeout,
            'connect_timeout': self.config.upload_connect_timeout
        }
        
        with open(file_path, 'rb') as file:
            if media_type == 'photo':
                await bot.send_photo(
                    chat_id=self.config.target_channel_id,
                    photo=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'video':
                await bot.send_video(
                    chat_id=self.config.target_channel_id,
                    video=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'document':
                await bot.send_document(
                    chat_id=self.config.target_channel_id,
                    document=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'audio':
                await bot.send_audio(
                    chat_id=self.config.target_channel_id,
                    audio=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'voice':
                await bot.send_voice(
                    chat_id=self.config.target_channel_id,
                    voice=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'video_note':
                await bot.send_video_note(
                    chat_id=self.config.target_channel_id,
                    video_note=file,
                    **timeout_kwargs
                )
            elif media_type == 'animation':
                await bot.send_animation(
                    chat_id=self.config.target_channel_id,
                    animation=file,
                    caption=caption,
                    parse_mode='HTML',
                    **timeout_kwargs
                )
            elif media_type == 'sticker':
                await bot.send_sticker(
                    chat_id=self.config.target_channel_id,
                    sticker=file,
                    **timeout_kwargs
                )
    
    async def _send_media_group(self, message: Message, file_infos: List[dict], caption: str, bot):
        """发送媒体组"""
        media_list = []
        
        # 读取所有文件内容到内存，避免文件句柄关闭问题
        file_contents = []
        for file_info in file_infos:
            with open(file_info['path'], 'rb') as f:
                file_contents.append(f.read())
        
        for i, (file_info, file_content) in enumerate(zip(file_infos, file_contents)):
            media_type = file_info['type']
            
            # 只在第一个媒体上添加说明文字
            if i == 0 and caption:
                if media_type == 'photo':
                    media = InputMediaPhoto(media=file_content, caption=caption, parse_mode='HTML')
                elif media_type == 'video':
                    media = InputMediaVideo(media=file_content, caption=caption, parse_mode='HTML')
                else:
                    media = InputMediaDocument(media=file_content, caption=caption, parse_mode='HTML')
            else:
                if media_type == 'photo':
                    media = InputMediaPhoto(media=file_content)
                elif media_type == 'video':
                    media = InputMediaVideo(media=file_content)
                else:
                    media = InputMediaDocument(media=file_content)
            
            media_list.append(media)
        
        logger.info(f"📤 准备发送媒体组，包含 {len(media_list)} 个媒体文件")
        
        # 发送媒体组（使用配置的超时时间，支持大文件如1GB视频）
        await bot.send_media_group(
            chat_id=self.config.target_channel_id,
            media=media_list,
            read_timeout=self.config.upload_read_timeout,
            write_timeout=self.config.upload_write_timeout,
            connect_timeout=self.config.upload_connect_timeout
        )
        
        logger.info(f"✅ 成功发送媒体组，包含 {len(media_list)} 个媒体文件")
    
    def _build_forward_text(self, message: Message) -> str:
        """构建消息文本（不显示转发信息）"""
        text_parts = []
        
        # 添加原始消息文本
        if message.text:
            text_parts.append(message.text)
        elif message.caption:
            text_parts.append(message.caption)
        
        # 不再添加转发信息，让消息看起来像原创内容
        result_text = '\n'.join(text_parts) if text_parts else ""
        
        # 限制caption长度（Telegram限制为1024字符）
        return self._truncate_caption(result_text)
    
    def _truncate_caption(self, text: str, max_length: int = 1024) -> str:
        """截断caption文本以符合Telegram长度限制"""
        if not text:
            return ""
        
        if len(text) <= max_length:
            return text
        
        # 如果超长，尝试在句子边界截断
        truncated_length = max_length - 4  # 为 "..." 预留空间
        
        # 尝试在最近的句号、换行符或空格处截断
        for delimiter in ['\n', '. ', '。', ' ']:
            last_pos = text.rfind(delimiter, 0, truncated_length)
            if last_pos > truncated_length * 0.8:  # 如果找到的位置不会丢失太多内容
                truncated = text[:last_pos + (1 if delimiter in ['. ', '。'] else 0)] + "..."
                logger.warning(f"Caption过长({len(text)}字符)，已在'{delimiter}'处截断至{len(truncated)}字符")
                return truncated
        
        # 如果找不到合适的截断点，直接截断
        truncated = text[:truncated_length] + "..."
        logger.warning(f"Caption过长({len(text)}字符)，已强制截断至{len(truncated)}字符")
        return truncated
    
    def _escape_html(self, text: str) -> str:
        """转义HTML特殊字符"""
        if not text:
            return ""
        
        escape_chars = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#x27;'
        }
        
        for char, escaped in escape_chars.items():
            text = text.replace(char, escaped)
        
        return text
