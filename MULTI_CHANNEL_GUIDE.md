# 🚀 多频道映射功能使用指南

## 📋 功能概述

新的多频道映射功能允许你的Bot同时监控多个源频道，并将内容转发到对应的目标频道。每个频道映射可以有独立的设置，包括caption处理、延迟配置等。

## 🎯 应用场景

- **新闻聚合**: 从多个新闻源转发到不同的分类频道
- **内容分发**: 一个机器人管理多个主题频道
- **备份系统**: 为每个重要频道创建备份
- **内容过滤**: 不同源频道使用不同的caption规则

## ⚙️ 配置方式

### 方法1: 环境变量启用

在 `.env` 文件中添加：

```env
# 启用多频道模式
MULTI_CHANNEL_ENABLED=true
CHANNELS_CONFIG_FILE=channels.json
```

### 方法2: 创建channels.json配置文件

```json
{
  "channels": [
    {
      "id": "tech_news",
      "name": "科技资讯转发",
      "source_channel": "@tech_source_channel", 
      "target_channel": "@my_tech_channel",
      "enabled": true,
      "description": "科技新闻从公共频道转发到我的频道",
      "settings": {
        "fixed_caption": null,
        "append_caption": "\n\n🔔 科技资讯 | 关注获取更多",
        "delay_enabled": true,
        "min_delay": 1.0,
        "max_delay": 5.0
      }
    },
    {
      "id": "entertainment",
      "name": "娱乐内容转发",
      "source_channel": "@entertainment_source",
      "target_channel": "-1001234567890",
      "enabled": true, 
      "description": "娱乐内容转发到私密群组",
      "settings": {
        "fixed_caption": "🎬 娱乐资讯",
        "append_caption": null,
        "delay_enabled": true,
        "min_delay": 2.0,
        "max_delay": 8.0
      }
    },
    {
      "id": "news_backup",
      "name": "新闻备份",
      "source_channel": "-1009876543210",
      "target_channel": "@my_news_backup", 
      "enabled": false,
      "description": "新闻频道备份（暂时禁用）",
      "settings": {
        "fixed_caption": null,
        "append_caption": "\n\n📰 新闻备份",
        "delay_enabled": false,
        "min_delay": 1.0,
        "max_delay": 3.0
      }
    }
  ],
  "global_settings": {
    "max_concurrent_channels": 5,
    "default_enabled": true,
    "auto_create_folders": true,
    "log_channel_activity": true,
    "fallback_to_single_channel": true
  }
}
```

## 🎮 管理命令

### 📋 查看频道列表
```
/list_channels
```
显示所有配置的频道映射，包括状态、源频道、目标频道等信息。

### ➕ 添加新频道映射
```
/add_channel <ID> <名称> <源频道> <目标频道> [描述]
```

**示例:**
```
/add_channel tech_news 科技资讯 @tech_source @my_tech 科技新闻转发
/add_channel ent_news 娱乐资讯 @ent_source -1001234567890 娱乐内容转发
```

### ❌ 删除频道映射
```
/remove_channel <ID>
```

**示例:**
```
/remove_channel tech_news
```

### 🔄 切换频道状态
```
/toggle_channel <ID>
```
在启用/禁用之间切换频道映射状态。

**示例:**
```
/toggle_channel tech_news
```

## 🔧 配置参数说明

### 频道映射字段

| 字段 | 必需 | 说明 | 示例 |
|------|------|------|------|
| `id` | ✅ | 唯一标识符 | `"tech_news"` |
| `name` | ✅ | 显示名称 | `"科技资讯转发"` |
| `source_channel` | ✅ | 源频道ID | `"@tech_source"` 或 `"-1001234567890"` |
| `target_channel` | ✅ | 目标频道ID | `"@my_tech"` 或 `"-1001234567890"` |
| `enabled` | ❌ | 是否启用 | `true` (默认) |
| `description` | ❌ | 描述信息 | `"科技新闻转发"` |
| `settings` | ❌ | 频道特定设置 | 见下方说明 |

### 频道特定设置 (settings)

| 字段 | 说明 | 示例 |
|------|------|------|
| `fixed_caption` | 固定caption（替换原内容） | `"🔥 热门资讯"` |
| `append_caption` | 追加caption（在原内容后） | `"\n\n📢 关注获取更多"` |
| `delay_enabled` | 是否启用延迟 | `true` |
| `min_delay` | 最小延迟(秒) | `1.0` |
| `max_delay` | 最大延迟(秒) | `5.0` |

## 🚦 工作流程

1. **消息接收**: Bot接收到源频道的新消息
2. **频道匹配**: 根据源频道ID查找对应的频道映射
3. **状态检查**: 确认频道映射已启用
4. **设置应用**: 应用频道特定的caption和延迟设置
5. **内容转发**: 将处理后的内容发送到目标频道

## 🎨 Caption处理优先级

1. **频道特定设置** (channels.json中的settings)
2. **全局设置** (通过命令设置的fixed_caption/append_caption)
3. **原始内容** (源消息的原始文本/caption)

## 📊 兼容性

### 向后兼容
- 当 `MULTI_CHANNEL_ENABLED=false` 时，Bot继续使用传统的单频道模式
- 现有的 `.env` 配置(SOURCE_CHANNEL_ID, TARGET_CHANNEL_ID)仍然有效

### 混合模式
- 如果启用多频道但没有找到 `channels.json`，会自动创建包含传统配置的默认文件

## 🐛 故障排除

### 常见问题

**1. Bot没有响应某个频道的消息**
- 检查频道映射是否启用: `/list_channels`
- 确认源频道ID格式正确 (以@或-开头)
- 验证Bot是否已添加到源频道

**2. 消息转发失败**
- 检查目标频道ID是否正确
- 确认Bot在目标频道有发送消息权限
- 查看Bot日志获取详细错误信息

**3. Caption设置不生效**
- 检查频道特定设置是否正确配置
- 确认设置优先级 (频道特定 > 全局 > 原始)

### 日志查看
```bash
pm2 logs mytestxiazai-bot --lines 50
```

## 📝 最佳实践

1. **ID命名**: 使用有意义的ID名称，如 `tech_news`, `ent_backup`
2. **描述信息**: 为每个映射添加清晰的描述
3. **延迟设置**: 根据频道类型调整延迟，避免被限制
4. **定期备份**: 定期备份 `channels.json` 配置文件
5. **权限管理**: 确保Bot在所有相关频道都有正确权限

## 🔄 从单频道迁移

如果你目前使用单频道模式，迁移到多频道很简单：

1. 在 `.env` 中设置 `MULTI_CHANNEL_ENABLED=true`
2. 重启Bot - 会自动创建包含现有配置的 `channels.json`
3. 使用管理命令添加更多频道映射

原有的单频道配置会自动转换为第一个频道映射，ID为 `"default"`。

## 🎯 高级用法

### 内容分类转发
```json
{
  "id": "news_classifier",
  "settings": {
    "append_caption": "\n\n📰 #新闻 #实时资讯"
  }
}
```

### 备份频道
```json
{
  "id": "backup_channel", 
  "settings": {
    "fixed_caption": "📁 备份内容",
    "delay_enabled": false
  }
}
```

### VIP频道 (快速转发)
```json
{
  "id": "vip_channel",
  "settings": {
    "append_caption": "\n\n⭐ VIP专享内容",
    "min_delay": 0.5,
    "max_delay": 1.0
  }
}
```

---

🎉 现在你可以使用强大的多频道映射功能来管理复杂的内容转发需求了！
