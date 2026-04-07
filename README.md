# pc-wechat-monitor

> Windows WeChat notification bridge for Bark and WxPusher.
> 基于 Windows 系统通知的微信消息提醒桥接器。

## Overview | 项目简介

**pc-wechat-monitor** is a lightweight bridge that reads WeChat notifications from Windows system toasts, parses basic message info, deduplicates repeated alerts, and forwards them to mobile push channels.

`pc-wechat-monitor` 是一个轻量级桥接器，用来读取 Windows 系统通知中的微信提醒，解析发送人和消息摘要，进行短时去重，再转发到手机推送通道。

### What it does | 已实现功能

- Read WeChat-related Windows toast notifications  
  读取 Windows 中与微信相关的系统通知
- Parse sender / preview / timestamp into a unified event model  
  将发送人 / 摘要 / 时间解析为统一事件结构
- Deduplicate repeated notifications with TTL  
  通过 TTL 去重避免重复提醒
- Forward notifications to Bark  
  转发到 Bark
- Optionally forward notifications to WxPusher  
  可选转发到 WxPusher
- Support mock mode for local development and testing  
  支持 mock 模式，便于本地开发和测试

### What it does not do | 当前不做的事

- Full chat history capture  
  抓取完整聊天记录
- Auto reply / remote messaging  
  自动回复 / 远程发消息
- Image, file, or voice extraction  
  提取图片、文件、语音内容
- WeChat process injection, hook, or DLL patching  
  微信进程注入、Hook、DLL 改造

## Architecture | 架构

```text
Windows WeChat
   ↓
Windows Toast Notification
   ↓
Notification Listener
   ↓
WeChat Notification Parser
   ↓
Deduper
   ↓
Dispatcher
   ├── Bark Notifier
   └── WxPusher Notifier
```

## Features | 功能特性

- Windows toast based listener
- Unified raw notification and parsed event model
- In-memory TTL dedupe
- Bark notifier
- WxPusher notifier
- Graceful fallback when real Windows notification access is unavailable
- `--once` and `--loop` run modes
- Basic local state persistence

## Project Structure | 项目结构

```text
src/
  app.py
  config.py
  models.py
  listener/
    windows_notifications.py
  parser/
    wechat_notification_parser.py
  dedupe/
    memory_dedupe.py
  notifiers/
    bark_notifier.py
    wxpusher_notifier.py
  store/
    state_store.py

tests/
  test_parser.py
  test_dedupe.py
  test_windows_listener.py
```

## Requirements | 环境要求

- Windows 10 / 11
- Python 3.11+
- Desktop WeChat installed and logged in
- WeChat system notifications enabled
- Windows notification access available

## Installation | 安装

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration | 配置

Create your local config from the example:

```bash
cp config.example.yaml config.yaml
```

Example config:

```yaml
source:
  app_names:
    - 微信
    - WeChat

push:
  bark:
    enabled: true
    server: https://api.day.app
    key: your_bark_key
    group: wechat-notify
  wxpusher:
    enabled: false
    app_token: your_app_token
    uids:
      - your_uid

dedupe:
  ttl_seconds: 10

runtime:
  log_level: INFO
  poll_interval_seconds: 2
  use_mock_listener: true
```

### Config notes | 配置说明

- `runtime.use_mock_listener: true` → use built-in mock notification for local testing  
  使用内置 mock 通知，适合本地联调
- `runtime.use_mock_listener: false` → use real Windows notification listener  
  使用真实 Windows 通知监听
- Placeholder Bark / WxPusher credentials are skipped automatically  
  占位 Bark / WxPusher 配置会被自动跳过，不会直接报错

## Usage | 使用方式

### Mock mode | mock 模式

```bash
python -m src.app --config config.example.yaml --once
```

### Real Windows notification mode | 真实监听模式

Set:

```yaml
runtime:
  use_mock_listener: false
```

Then run once:

```bash
python -m src.app --config config.yaml --once
```

Or run continuously:

```bash
python -m src.app --config config.yaml --loop
```

## Push Channels | 推送通道

### Bark

- Title: sender
- Subtitle: 微信新消息
- Body: preview

### WxPusher

- Title: `微信新消息 - sender`
- Body: sender, preview, timestamp

## Internal Event Model | 内部事件结构

```json
{
  "source": "wechat_windows_notification",
  "app_name": "微信",
  "sender": "张三",
  "preview": "晚上一起吃饭吗",
  "chat_type": "unknown",
  "raw_text": "张三\n晚上一起吃饭吗",
  "timestamp": "2026-04-07T20:31:00+08:00"
}
```

## Limitations | 限制说明

- The project depends on WeChat actually producing Windows notifications  
  依赖微信确实产生 Windows 系统通知
- Notifications may contain only message previews, not full content  
  通知通常只有摘要，不保证完整消息
- Group chat parsing may not always be precise  
  群聊解析未必始终精确
- Real listener support depends on local PowerShell / WinRT availability and permission  
  真实监听依赖本机 PowerShell / WinRT 能力和通知权限

## Safety and Compliance | 安全与合规

This project is intentionally designed to avoid intrusive techniques:

- No WeChat process injection
- No protocol cracking
- No DLL patching
- No account bypass
- Only reads notification content already exposed by the OS

本项目刻意避免高侵入方式：

- 不注入微信进程
- 不破解微信协议
- 不修改 DLL
- 不绕过账号鉴权
- 只读取操作系统已暴露给用户的通知内容

## Testing | 测试

```bash
python -m pytest
```

## Roadmap | 路线图

- More stable Windows notification integration
- Better group-chat parsing
- Enhanced persistent state storage
- Startup scripts and auto-start support
- Better logging and recovery behavior

## Open Source Notes | 开源说明

Recommended repository extras:

- `LICENSE`
- `.gitignore`
- keep `config.yaml` out of git
- mention that this is still a V1 project

## Disclaimer | 免责声明

This project is provided as a personal notification bridge and may behave differently across Windows and WeChat versions. Test in your own environment before relying on it.

本项目是个人提醒桥接工具，不同 Windows / 微信版本组合下可能表现不同，请在自己的环境中先完成测试再投入长期使用。
