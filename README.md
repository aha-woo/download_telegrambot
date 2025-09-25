# Telegram Media Forward Bot

一个用于自动从源频道下载媒体文件并转发到目标频道的Telegram机器人。

## 功能特性

- 🤖 自动监听源频道的消息
- 📥 下载图片、视频、文档等媒体文件
- 📤 转发消息到目标频道
- 🔄 支持多种媒体格式
- 📝 完整的日志记录
- 🛡️ 错误处理和重试机制
- 🚀 支持VPS部署和系统服务
- 🌐 **SOCKS5/HTTP代理支持**
- ⏱️ **随机延迟模拟人工操作**
- 🎭 **反检测机制，减少被识别为机器人的风险**
- 🕐 **可控轮询功能，支持手动启停**
- ⏰ **时间段控制，指定运行时间**
- ⚡ **可配置轮询间隔，灵活调整频率**

## 支持的媒体类型

- 图片 (Photo)
- 视频 (Video)
- 文档 (Document)
- 音频 (Audio)
- 语音 (Voice)
- 视频笔记 (Video Note)
- 动画 (Animation/GIF)
- 贴纸 (Sticker)

## 安装和配置

### 1. 获取Bot Token

1. 在Telegram中找到 [@BotFather](https://t.me/botfather)
2. 发送 `/newbot` 创建新机器人
3. 按提示设置机器人名称和用户名
4. 获取Bot Token

### 2. 获取频道信息

#### 源频道（要监听的频道）
- 将机器人添加到源频道
- 给机器人管理员权限（至少需要读取消息权限）
- 获取频道ID（格式：`@channel_username` 或 `-1001234567890`）

#### 目标频道（要转发到的频道）
- 将机器人添加到目标频道
- 给机器人管理员权限（需要发送消息权限）
- 获取频道ID（格式：`@channel_username` 或 `-1001234567890`）

### 3. 部署到VPS

#### 方法一：使用部署脚本（推荐）

```bash
# 克隆项目
git clone <your-repo-url> download_bot
cd download_bot

# 运行带轮询控制的部署脚本（推荐）
chmod +x deploy_polling_control.sh
./deploy_polling_control.sh

# 或运行带代理支持的部署脚本
chmod +x deploy_with_proxy.sh
./deploy_with_proxy.sh

# 或使用基础部署脚本
chmod +x deploy.sh
./deploy.sh
```

#### 方法二：手动部署

```bash
# 1. 安装依赖
sudo apt update
sudo apt install -y python3 python3-pip python3-venv

# 2. 创建项目目录
mkdir -p ~/download_bot
cd ~/download_bot

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装Python依赖
pip install -r requirements.txt

# 5. 配置环境变量
cp config.env.example .env
nano .env  # 编辑配置文件

# 6. 安装系统服务
sudo cp systemd/telegram-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable telegram-bot
sudo systemctl start telegram-bot
```

### 4. 配置环境变量

编辑 `.env` 文件：

```env
# Telegram Bot Configuration
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
SOURCE_CHANNEL_ID=@source_channel_username
TARGET_CHANNEL_ID=@target_channel_username

# 下载设置
DOWNLOAD_PATH=./downloads
MAX_FILE_SIZE=50MB

# 代理设置 (SOCKS5代理)
PROXY_ENABLED=true
PROXY_TYPE=socks5
PROXY_HOST=your_proxy_host
PROXY_PORT=your_proxy_port
PROXY_USERNAME=your_proxy_username
PROXY_PASSWORD=your_proxy_password

# 随机延迟设置 (模拟人工操作)
DELAY_ENABLED=true
MIN_DELAY=1.0
MAX_DELAY=5.0
DOWNLOAD_DELAY_MIN=2.0
DOWNLOAD_DELAY_MAX=8.0
FORWARD_DELAY_MIN=1.0
FORWARD_DELAY_MAX=4.0
```

## 使用方法

### 启动机器人

```bash
# 启动服务
sudo systemctl start telegram-bot

# 查看状态
sudo systemctl status telegram-bot

# 查看日志
sudo journalctl -u telegram-bot -f
```

### 机器人命令

- `/start` - 显示机器人状态信息
- `/status` - 查看详细状态和统计信息

## 配置说明

### 环境变量

| 变量名 | 必需 | 说明 | 示例 |
|--------|------|------|------|
| `BOT_TOKEN` | ✅ | Bot Token | `1234567890:ABCdef...` |
| `SOURCE_CHANNEL_ID` | ✅ | 源频道ID | `@source_channel` |
| `TARGET_CHANNEL_ID` | ✅ | 目标频道ID | `@target_channel` |
| `DOWNLOAD_PATH` | ❌ | 下载目录 | `./downloads` |
| `MAX_FILE_SIZE` | ❌ | 最大文件大小 | `50MB` |
| `PROXY_ENABLED` | ❌ | 启用代理 | `true/false` |
| `PROXY_TYPE` | ❌ | 代理类型 | `socks5/http` |
| `PROXY_HOST` | ❌ | 代理主机 | `proxy.example.com` |
| `PROXY_PORT` | ❌ | 代理端口 | `1080` |
| `PROXY_USERNAME` | ❌ | 代理用户名 | `username` |
| `PROXY_PASSWORD` | ❌ | 代理密码 | `password` |
| `DELAY_ENABLED` | ❌ | 启用随机延迟 | `true/false` |
| `DOWNLOAD_DELAY_MIN` | ❌ | 下载最小延迟(秒) | `2.0` |
| `DOWNLOAD_DELAY_MAX` | ❌ | 下载最大延迟(秒) | `8.0` |
| `FORWARD_DELAY_MIN` | ❌ | 转发最小延迟(秒) | `1.0` |
| `FORWARD_DELAY_MAX` | ❌ | 转发最大延迟(秒) | `4.0` |
| `POLLING_ENABLED` | ❌ | 启用轮询功能 | `true/false` |
| `POLLING_INTERVAL` | ❌ | 轮询间隔(秒) | `60.0` |
| `AUTO_POLLING` | ❌ | 启动时自动轮询 | `true/false` |
| `TIME_CONTROL_ENABLED` | ❌ | 启用时间段控制 | `true/false` |
| `START_TIME` | ❌ | 开始时间 | `10:00` |
| `END_TIME` | ❌ | 结束时间 | `12:00` |
| `TIMEZONE` | ❌ | 时区 | `Asia/Shanghai` |

### 文件大小限制

支持的文件大小单位：
- `KB` - 千字节
- `MB` - 兆字节  
- `GB` - 千兆字节

示例：`10MB`, `1GB`, `500KB`

## 代理配置

### 支持的代理类型

- **SOCKS5** (推荐) - 支持TCP和UDP代理，更安全
- **HTTP** - 仅支持HTTP流量代理

### 代理配置示例

```env
# 启用SOCKS5代理
PROXY_ENABLED=true
PROXY_TYPE=socks5
PROXY_HOST=185.241.228.116
PROXY_PORT=12324
PROXY_USERNAME=14a7615c70476
PROXY_PASSWORD=2c83188abb
```

### 代理测试

机器人提供内置的代理测试工具：

```bash
# 测试代理连接
python test_proxy.py
```

测试内容包括：
- 代理连接状态
- Telegram API连接
- 当前IP地址
- 频道访问权限

## 随机延迟配置

为了模拟人工操作，减少被Telegram识别为机器人的风险，系统支持多种随机延迟：

### 延迟类型

1. **消息处理延迟** (`MIN_DELAY` - `MAX_DELAY`)
   - 收到新消息后的等待时间
   - 默认：1-5秒

2. **下载延迟** (`DOWNLOAD_DELAY_MIN` - `DOWNLOAD_DELAY_MAX`)
   - 开始下载媒体前的等待时间
   - 默认：2-8秒

3. **转发延迟** (`FORWARD_DELAY_MIN` - `FORWARD_DELAY_MAX`)
   - 下载完成后开始转发前的等待时间
   - 默认：1-4秒

### 延迟配置建议

```env
# 保守配置（更安全，但速度较慢）
DELAY_ENABLED=true
MIN_DELAY=2.0
MAX_DELAY=8.0
DOWNLOAD_DELAY_MIN=3.0
DOWNLOAD_DELAY_MAX=12.0
FORWARD_DELAY_MIN=2.0
FORWARD_DELAY_MAX=6.0

# 平衡配置（推荐）
DELAY_ENABLED=true
MIN_DELAY=1.0
MAX_DELAY=5.0
DOWNLOAD_DELAY_MIN=2.0
DOWNLOAD_DELAY_MAX=8.0
FORWARD_DELAY_MIN=1.0
FORWARD_DELAY_MAX=4.0

# 快速配置（速度优先，风险较高）
DELAY_ENABLED=true
MIN_DELAY=0.5
MAX_DELAY=2.0
DOWNLOAD_DELAY_MIN=1.0
DOWNLOAD_DELAY_MAX=3.0
FORWARD_DELAY_MIN=0.5
FORWARD_DELAY_MAX=2.0
```

### 命令行调整延迟

您可以通过修改 `.env` 文件并重启机器人来调整延迟设置：

```bash
# 编辑配置
nano .env

# 重启机器人（PM2方式）
pm2 restart mytestxiazai-bot

# 或重启系统服务
sudo systemctl restart telegram-bot
```

## 轮询控制功能

### 什么是轮询控制？

传统的Telegram机器人会持续不断地向Telegram服务器请求新消息（轮询）。轮询控制功能允许您：

- 🕐 **手动控制轮询**：按需启动/停止轮询
- ⏰ **时间段控制**：仅在指定时间段内运行（如工作时间）
- ⚡ **调整轮询频率**：从默认10秒改为1分钟或更长
- 📊 **监控轮询状态**：实时查看轮询统计信息

### 轮询控制命令

```bash
# 机器人命令（在Telegram中使用）
/start_polling          # 开始轮询
/stop_polling           # 停止轮询
/polling_status         # 查看轮询状态和统计
/set_interval 60        # 设置轮询间隔为60秒
/status                 # 查看完整机器人状态
```

### 配置示例

#### 基础配置
```env
# 启用轮询控制但不自动开始
POLLING_ENABLED=true
POLLING_INTERVAL=60.0
AUTO_POLLING=false
```

#### 时间段控制配置
```env
# 仅在上午10-12点自动运行
POLLING_ENABLED=true
POLLING_INTERVAL=60.0
AUTO_POLLING=true
TIME_CONTROL_ENABLED=true
START_TIME=10:00
END_TIME=12:00
TIMEZONE=Asia/Shanghai
```

#### 高频轮询配置
```env
# 每30秒轮询一次，启动时自动开始
POLLING_ENABLED=true
POLLING_INTERVAL=30.0
AUTO_POLLING=true
TIME_CONTROL_ENABLED=false
```

### 使用场景

1. **节省资源**：仅在需要时运行轮询
2. **避开高峰期**：在网络繁忙时停止轮询
3. **定时任务**：配合cron实现定时启停
4. **调试模式**：手动控制轮询便于调试
5. **合规要求**：在特定时间段内运行

### 轮询状态说明

```
📊 轮询状态报告

🔄 轮询状态: 🟢 运行中
⚡ 轮询间隔: 60.0秒
📅 ✅ 在允许时间段内
⏰ 时间控制: 10:00-12:00 (Asia/Shanghai)

📈 统计信息:
• 请求次数: 25
• 处理消息: 3
• 运行时长: 25分0秒
• 最后活动: 14:32:15

🎯 下次轮询: 14:33:00
```

## 日志和监控

### 查看日志

```bash
# 实时查看日志
sudo journalctl -u telegram-bot -f

# 查看最近的日志
sudo journalctl -u telegram-bot -n 100

# 查看今天的日志
sudo journalctl -u telegram-bot --since today
```

### 日志文件

机器人还会在项目目录下创建 `bot.log` 文件记录详细日志。

## 故障排除

### 常见问题

1. **机器人无法启动**
   - 检查Bot Token是否正确
   - 检查频道ID格式是否正确
   - 查看日志：`sudo journalctl -u telegram-bot -f`

2. **无法接收消息**
   - 确认机器人已添加到源频道
   - 确认机器人有读取消息的权限
   - 检查频道ID是否正确

3. **无法发送消息**
   - 确认机器人已添加到目标频道
   - 确认机器人有发送消息的权限
   - 检查目标频道ID是否正确

4. **文件下载失败**
   - 检查磁盘空间是否充足
   - 检查文件大小是否超过限制
   - 查看详细错误日志

### 权限检查

确保机器人在频道中有以下权限：

**源频道权限：**
- 读取消息
- 查看媒体

**目标频道权限：**
- 发送消息
- 发送媒体
- 嵌入链接

## 安全注意事项

1. **保护Bot Token**
   - 不要将Bot Token提交到代码仓库
   - 使用 `.env` 文件存储敏感信息
   - 设置适当的文件权限：`chmod 600 .env`

2. **网络安全**
   - 使用防火墙限制不必要的端口访问
   - 定期更新系统和依赖包
   - 监控异常活动

3. **数据安全**
   - 定期清理下载的临时文件
   - 备份重要配置
   - 监控磁盘使用情况

## 开发和贡献

### 项目结构

```
download_bot/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── bot_handler.py       # 消息处理
├── media_downloader.py  # 媒体下载
├── requirements.txt     # Python依赖
├── config.env.example   # 配置示例
├── deploy.sh           # 部署脚本
├── systemd/            # 系统服务配置
│   └── telegram-bot.service
└── README.md           # 说明文档
```

### 开发环境

```bash
# 克隆项目
git clone <repo-url>
cd download_bot

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp config.env.example .env
# 编辑 .env 文件

# 运行机器人
python main.py
```

## 许可证

MIT License

## 支持

如果遇到问题或有建议，请：

1. 查看日志文件排查问题
2. 检查配置是否正确
3. 提交Issue或Pull Request

---

**注意：** 使用此机器人时请遵守Telegram的使用条款和相关法律法规。
