"""
配置文件管理
"""

import os
import json
from pathlib import Path
from typing import Optional, List, Dict, Any


class Config:
    """配置类"""
    
    def __init__(self):
        self.bot_token = self._get_required_env('BOT_TOKEN')
        self.source_channel_id = self._get_required_env('SOURCE_CHANNEL_ID')
        self.target_channel_id = self._get_required_env('TARGET_CHANNEL_ID')
        
        # 可选配置
        self.api_id = self._get_optional_env('API_ID')
        self.api_hash = self._get_optional_env('API_HASH')
        
        # 下载设置
        self.download_path = os.getenv('DOWNLOAD_PATH', './downloads')
        self.max_file_size = self._parse_file_size(os.getenv('MAX_FILE_SIZE', '50MB'))
        
        # 代理设置
        self.proxy_enabled = os.getenv('PROXY_ENABLED', 'false').lower() == 'true'
        self.proxy_host = self._get_optional_env('PROXY_HOST')
        self.proxy_port = self._get_optional_env('PROXY_PORT')
        self.proxy_username = self._get_optional_env('PROXY_USERNAME')
        self.proxy_password = self._get_optional_env('PROXY_PASSWORD')
        self.proxy_type = os.getenv('PROXY_TYPE', 'socks5').lower()
        
        # 随机延迟设置
        self.delay_enabled = os.getenv('DELAY_ENABLED', 'true').lower() == 'true'
        self.min_delay = float(os.getenv('MIN_DELAY', '1.0'))
        self.max_delay = float(os.getenv('MAX_DELAY', '5.0'))
        self.download_delay_min = float(os.getenv('DOWNLOAD_DELAY_MIN', '2.0'))
        self.download_delay_max = float(os.getenv('DOWNLOAD_DELAY_MAX', '8.0'))
        self.forward_delay_min = float(os.getenv('FORWARD_DELAY_MIN', '1.0'))
        self.forward_delay_max = float(os.getenv('FORWARD_DELAY_MAX', '4.0'))
        
        # 轮询控制设置
        self.polling_enabled = os.getenv('POLLING_ENABLED', 'true').lower() == 'true'
        self.polling_interval = float(os.getenv('POLLING_INTERVAL', '10.0'))  # 轮询间隔（秒）
        self.auto_polling = os.getenv('AUTO_POLLING', 'true').lower() == 'true'  # 启动时自动开始轮询
        
        # 时间段控制
        self.time_control_enabled = os.getenv('TIME_CONTROL_ENABLED', 'false').lower() == 'true'
        self.start_time = os.getenv('START_TIME', '10:00')  # 开始时间 HH:MM
        self.end_time = os.getenv('END_TIME', '12:00')    # 结束时间 HH:MM
        self.timezone = os.getenv('TIMEZONE', 'Asia/Shanghai')  # 时区
        
        # 下载配置
        self.download_timeout = int(os.getenv('DOWNLOAD_TIMEOUT', '7200'))  # 秒 - 下载超时时间（默认2小时）
        self.media_group_timeout = int(os.getenv('MEDIA_GROUP_TIMEOUT', '3'))  # 秒 - 等待更多消息的时间
        self.media_group_max_wait = int(os.getenv('MEDIA_GROUP_MAX_WAIT', '60'))  # 秒 - 等待新消息的最大时间
        
        # 网络超时配置
        self.upload_connect_timeout = int(os.getenv('UPLOAD_CONNECT_TIMEOUT', '120'))  # 秒 - 连接超时（默认2分钟）
        self.upload_read_timeout = int(os.getenv('UPLOAD_READ_TIMEOUT', '1800'))  # 秒 - 读取超时（默认30分钟）
        self.upload_write_timeout = int(os.getenv('UPLOAD_WRITE_TIMEOUT', '1800'))  # 秒 - 写入超时（默认30分钟）
        
        # Caption管理配置 - 运行时设置，不从环境变量读取
        self.fixed_caption = None  # 固定caption内容，如果设置则替换所有消息的caption
        self.append_caption = None  # 追加到原caption后面的内容
        
        # 多频道配置
        self.multi_channel_enabled = os.getenv('MULTI_CHANNEL_ENABLED', 'false').lower() == 'true'
        self.channels_config_file = os.getenv('CHANNELS_CONFIG_FILE', 'channels.json')
        self.channel_mappings = []  # 存储频道映射列表
        self.global_channel_settings = {}  # 全局频道设置
        
        # 加载多频道配置
        self._load_channel_mappings()
        
        # 验证配置
        self._validate_config()
    
    def _get_required_env(self, key: str) -> str:
        """获取必需的环境变量"""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"必需的环境变量 {key} 未设置")
        return value
    
    def _get_optional_env(self, key: str) -> Optional[str]:
        """获取可选的环境变量"""
        return os.getenv(key)
    
    def _parse_file_size(self, size_str: str) -> int:
        """解析文件大小字符串为字节数"""
        size_str = size_str.upper().strip()
        
        if size_str.endswith('KB'):
            return int(size_str[:-2]) * 1024
        elif size_str.endswith('MB'):
            return int(size_str[:-2]) * 1024 * 1024
        elif size_str.endswith('GB'):
            return int(size_str[:-2]) * 1024 * 1024 * 1024
        else:
            # 假设是字节数
            return int(size_str)
    
    def _validate_config(self):
        """验证配置"""
        # 验证频道ID格式（仅在非多频道模式下验证）
        if not self.multi_channel_enabled:
            if not (self.source_channel_id.startswith('@') or self.source_channel_id.startswith('-')):
                raise ValueError("源频道ID必须以@或-开头")
            
            if not (self.target_channel_id.startswith('@') or self.target_channel_id.startswith('-')):
                raise ValueError("目标频道ID必须以@或-开头")
        else:
            # 多频道模式下，验证配置文件和频道映射
            if not self.channel_mappings:
                raise ValueError("多频道模式下至少需要一个频道映射")
        
        # 验证下载路径
        download_path = Path(self.download_path)
        if not download_path.exists():
            download_path.mkdir(parents=True, exist_ok=True)
        
        # 验证文件大小限制
        if self.max_file_size <= 0:
            raise ValueError("最大文件大小必须大于0")
        
        # 验证代理配置
        if self.proxy_enabled:
            if not self.proxy_host:
                raise ValueError("启用代理时必须设置 PROXY_HOST")
            if not self.proxy_port:
                raise ValueError("启用代理时必须设置 PROXY_PORT")
            try:
                self.proxy_port = int(self.proxy_port)
            except ValueError:
                raise ValueError("PROXY_PORT 必须是有效的数字")
            
            if self.proxy_type not in ['socks5', 'socks4', 'http']:
                raise ValueError("PROXY_TYPE 必须是 socks5, socks4 或 http")
        
        # 验证延迟配置
        if self.delay_enabled:
            if self.min_delay < 0 or self.max_delay < 0:
                raise ValueError("延迟时间不能为负数")
            if self.min_delay > self.max_delay:
                raise ValueError("最小延迟不能大于最大延迟")
            if self.download_delay_min > self.download_delay_max:
                raise ValueError("最小下载延迟不能大于最大下载延迟")
            if self.forward_delay_min > self.forward_delay_max:
                raise ValueError("最小转发延迟不能大于最大转发延迟")
        
        # 验证轮询配置
        if self.polling_interval < 1.0:
            raise ValueError("轮询间隔不能小于1秒")
        
        # 验证下载配置
        if self.download_timeout <= 0:
            raise ValueError("下载超时时间必须大于0")
        if self.media_group_timeout <= 0:
            raise ValueError("媒体组超时时间必须大于0")
        if self.media_group_max_wait <= 0:
            raise ValueError("媒体组最大等待时间必须大于0")
        if self.download_timeout < 60:
            raise ValueError("下载超时时间至少应为60秒")
        
        # 验证网络超时配置
        if self.upload_connect_timeout <= 0:
            raise ValueError("上传连接超时时间必须大于0")
        if self.upload_read_timeout <= 0:
            raise ValueError("上传读取超时时间必须大于0")
        if self.upload_write_timeout <= 0:
            raise ValueError("上传写入超时时间必须大于0")
        if self.upload_connect_timeout < 10:
            raise ValueError("连接超时时间至少应为10秒")
        if self.upload_read_timeout < 60:
            raise ValueError("读取超时时间至少应为60秒")
        if self.upload_write_timeout < 60:
            raise ValueError("写入超时时间至少应为60秒")
        
        # 验证时间格式
        if self.time_control_enabled:
            try:
                import datetime
                datetime.datetime.strptime(self.start_time, '%H:%M')
                datetime.datetime.strptime(self.end_time, '%H:%M')
            except ValueError:
                raise ValueError("时间格式必须为 HH:MM")
            
            # 验证时区
            try:
                import pytz
                pytz.timezone(self.timezone)
            except:
                # 如果pytz不可用或时区无效，使用默认时区
                self.timezone = 'Asia/Shanghai'
    
    def get_proxy_config(self):
        """获取代理配置字典"""
        if not self.proxy_enabled:
            return None
        
        proxy_config = {
            'proxy_type': self.proxy_type,
            'host': self.proxy_host,
            'port': self.proxy_port,
        }
        
        if self.proxy_username and self.proxy_password:
            proxy_config['username'] = self.proxy_username
            proxy_config['password'] = self.proxy_password
        
        return proxy_config
    
    def is_in_time_range(self):
        """检查当前时间是否在允许的时间范围内"""
        if not self.time_control_enabled:
            return True
        
        try:
            from datetime import datetime
            import pytz
            
            tz = pytz.timezone(self.timezone)
            now = datetime.now(tz)
            current_time = now.strftime('%H:%M')
            
            # 处理跨日情况
            if self.start_time <= self.end_time:
                # 同一天内的时间范围
                return self.start_time <= current_time <= self.end_time
            else:
                # 跨日的时间范围
                return current_time >= self.start_time or current_time <= self.end_time
        except Exception:
            # 如果时间检查失败，默认允许
            return True
    
    def __str__(self):
        """返回配置信息的字符串表示"""
        proxy_info = f"启用 ({self.proxy_type}://{self.proxy_host}:{self.proxy_port})" if self.proxy_enabled else "禁用"
        delay_info = f"启用 (转发:{self.forward_delay_min}-{self.forward_delay_max}s, 下载:{self.download_delay_min}-{self.download_delay_max}s)" if self.delay_enabled else "禁用"
        
        polling_info = f"启用 (间隔:{self.polling_interval}s)" if self.polling_enabled else "禁用"
        if self.time_control_enabled:
            polling_info += f" (时间段:{self.start_time}-{self.end_time} {self.timezone})"
        
        download_info = f"超时:{self.download_timeout//60}分钟, 媒体组等待:{self.media_group_max_wait}s"
        network_info = f"连接:{self.upload_connect_timeout}s, 读写:{self.upload_read_timeout//60}分钟"
        
        return f"""
配置信息:
- Bot Token: {self.bot_token[:10]}...
- 源频道: {self.source_channel_id}
- 目标频道: {self.target_channel_id}
- 下载路径: {self.download_path}
- 最大文件大小: {self.max_file_size / (1024*1024):.1f}MB
- 代理: {proxy_info}
- 随机延迟: {delay_info}
- 轮询控制: {polling_info}
- 下载配置: {download_info}
- 网络超时: {network_info}
- 多频道模式: {'启用' if self.multi_channel_enabled else '禁用'}
- 频道映射数量: {len(self.channel_mappings)}
"""
    
    def _load_channel_mappings(self):
        """加载频道映射配置"""
        if not self.multi_channel_enabled:
            # 如果未启用多频道模式，创建兼容的单频道映射
            self.channel_mappings = [{
                'id': 'default',
                'name': '默认频道映射',
                'source_channel': self.source_channel_id,
                'target_channel': self.target_channel_id,
                'enabled': True,
                'description': '兼容模式的单频道映射',
                'settings': {
                    'fixed_caption': None,
                    'append_caption': None,
                    'delay_enabled': self.delay_enabled,
                    'min_delay': self.min_delay,
                    'max_delay': self.max_delay
                }
            }]
            return
        
        # 多频道模式：从JSON文件加载配置
        config_file = Path(self.channels_config_file)
        
        if not config_file.exists():
            # 如果配置文件不存在，创建默认配置
            self._create_default_channels_config(config_file)
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.channel_mappings = config_data.get('channels', [])
            self.global_channel_settings = config_data.get('global_settings', {})
            
            # 验证频道映射配置
            self._validate_channel_mappings()
            
        except Exception as e:
            raise ValueError(f"加载频道配置文件失败 {config_file}: {e}")
    
    def _create_default_channels_config(self, config_file: Path):
        """创建默认的频道配置文件"""
        default_config = {
            "channels": [
                {
                    "id": "default",
                    "name": "默认频道映射",
                    "source_channel": self.source_channel_id,
                    "target_channel": self.target_channel_id,
                    "enabled": True,
                    "description": "从环境变量创建的默认映射",
                    "settings": {
                        "fixed_caption": None,
                        "append_caption": None,
                        "delay_enabled": self.delay_enabled,
                        "min_delay": self.min_delay,
                        "max_delay": self.max_delay
                    }
                }
            ],
            "global_settings": {
                "max_concurrent_channels": 5,
                "default_enabled": True,
                "auto_create_folders": True,
                "log_channel_activity": True,
                "fallback_to_single_channel": True
            }
        }
        
        try:
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
            print(f"✅ 已创建默认频道配置文件: {config_file}")
        except Exception as e:
            print(f"❌ 创建配置文件失败: {e}")
    
    def _validate_channel_mappings(self):
        """验证频道映射配置"""
        if not self.channel_mappings:
            raise ValueError("至少需要配置一个频道映射")
        
        channel_ids = set()
        source_channels = set()
        
        for mapping in self.channel_mappings:
            # 验证必需字段
            required_fields = ['id', 'name', 'source_channel', 'target_channel']
            for field in required_fields:
                if field not in mapping:
                    raise ValueError(f"频道映射缺少必需字段: {field}")
            
            # 验证ID唯一性
            mapping_id = mapping['id']
            if mapping_id in channel_ids:
                raise ValueError(f"频道映射ID重复: {mapping_id}")
            channel_ids.add(mapping_id)
            
            # 验证源频道格式
            source_channel = mapping['source_channel']
            if not (source_channel.startswith('@') or source_channel.startswith('-')):
                raise ValueError(f"源频道ID格式错误: {source_channel}")
            
            # 验证目标频道格式
            target_channel = mapping['target_channel']
            if not (target_channel.startswith('@') or target_channel.startswith('-')):
                raise ValueError(f"目标频道ID格式错误: {target_channel}")
            
            # 记录源频道（用于消息路由）
            source_channels.add(source_channel)
            
            # 设置默认值
            mapping.setdefault('enabled', True)
            mapping.setdefault('description', '')
            mapping.setdefault('settings', {})
    
    def get_enabled_channel_mappings(self) -> List[Dict[str, Any]]:
        """获取启用的频道映射列表"""
        return [mapping for mapping in self.channel_mappings if mapping.get('enabled', True)]
    
    def get_channel_mapping_by_source(self, source_channel: str) -> Optional[Dict[str, Any]]:
        """根据源频道ID获取频道映射（支持智能匹配）"""
        for mapping in self.get_enabled_channel_mappings():
            config_channel = mapping['source_channel']
            
            # 直接匹配
            if config_channel == source_channel:
                return mapping
            
            # 智能格式匹配：用户名(@xxx) vs 数字ID(-100xxx)
            if config_channel.startswith('@') and source_channel.startswith('-'):
                # 配置是用户名，消息是数字ID - 跳过（需要反向匹配）
                continue
            elif source_channel.startswith('@') and config_channel.startswith('-'):
                # 消息是用户名，配置是数字ID - 跳过（需要反向匹配）
                continue
            elif config_channel.startswith('@') and source_channel.startswith('@'):
                # 都是用户名格式 - 已通过直接匹配处理
                continue
            elif config_channel.startswith('-') and source_channel.startswith('-'):
                # 都是数字ID格式 - 可能是完整ID vs 短ID的差异
                # 处理Telegram频道ID的不同格式匹配（完整格式 vs 短格式）
                config_num = config_channel[1:]  # 去掉开头的 -
                source_num = source_channel[1:]  # 去掉开头的 -
                
                # 情况1：配置是完整格式(-1003...)，消息是短格式(-100...)
                if config_num.startswith('1003') and source_num.startswith('1003'):
                    # 比较除去前缀的数字部分
                    if len(config_num) == 13 and len(source_num) == 12:
                        # 完整格式：1003152172020，短格式：100315217020
                        # 取后面的数字部分比较：3152172020 vs 15217020
                        if config_num[4:] == source_num[4:]:
                            return mapping
                    elif len(source_num) == 13 and len(config_num) == 12:
                        # 反向：消息是完整格式，配置是短格式
                        if source_num[4:] == config_num[4:]:
                            return mapping
        
        return None
    
    def get_all_source_channels(self) -> List[str]:
        """获取所有启用的源频道ID列表"""
        return [mapping['source_channel'] for mapping in self.get_enabled_channel_mappings()]
    
    def save_channel_mappings(self) -> bool:
        """保存频道映射配置到文件"""
        if not self.multi_channel_enabled:
            return False
        
        try:
            config_data = {
                'channels': self.channel_mappings,
                'global_settings': self.global_channel_settings
            }
            
            config_file = Path(self.channels_config_file)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"❌ 保存频道配置失败: {e}")
            return False
    
    def add_channel_mapping(self, mapping: Dict[str, Any]) -> bool:
        """添加新的频道映射"""
        try:
            # 验证映射数据
            required_fields = ['id', 'name', 'source_channel', 'target_channel']
            for field in required_fields:
                if field not in mapping:
                    raise ValueError(f"缺少必需字段: {field}")
            
            # 检查ID是否已存在
            for existing in self.channel_mappings:
                if existing['id'] == mapping['id']:
                    raise ValueError(f"频道映射ID已存在: {mapping['id']}")
            
            # 设置默认值
            mapping.setdefault('enabled', True)
            mapping.setdefault('description', '')
            mapping.setdefault('settings', {})
            
            # 添加到列表
            self.channel_mappings.append(mapping)
            
            # 保存到文件
            return self.save_channel_mappings()
            
        except Exception as e:
            print(f"❌ 添加频道映射失败: {e}")
            return False
    
    def remove_channel_mapping(self, mapping_id: str) -> bool:
        """删除频道映射"""
        try:
            # 查找并删除映射
            for i, mapping in enumerate(self.channel_mappings):
                if mapping['id'] == mapping_id:
                    del self.channel_mappings[i]
                    return self.save_channel_mappings()
            
            raise ValueError(f"找不到ID为 {mapping_id} 的频道映射")
            
        except Exception as e:
            print(f"❌ 删除频道映射失败: {e}")
            return False