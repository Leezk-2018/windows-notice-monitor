# WeChat Notify Bridge V1 产品需求与方案

## 1. 背景
你有一台长期登录个人微信的 Windows 电脑，希望在不依赖微信内部 Hook/注入的前提下，把微信新消息提醒同步到手机。

V1 不追求完整聊天消息抓取，也不做远程回消息，只做：
- 监听 Windows 上微信的新消息通知
- 提取谁发来的、粗略消息内容、时间
- 转发到 Bark
- 可选同时转发到 WxPusher

这个版本的目标是先做出一个稳定、低侵入、可长期运行的提醒桥接器。

## 2. V1 目标
### 2.1 核心目标
当 Windows 微信产生系统通知时，程序能：
1. 捕获该通知
2. 识别为微信来源
3. 解析出联系人/群名与消息摘要
4. 去重后推送到 Bark / WxPusher

### 2.2 非目标
V1 不包含：
- 完整聊天记录抓取
- 图片/文件/语音内容提取
- 自动回复
- 远程发消息
- 微信客户端 UI 自动化读取聊天窗口
- 微信 Hook / DLL 注入

## 3. 用户场景
### 场景 1：同步微信提醒到 iPhone
- Windows 微信上收到新消息
- 程序监听到系统通知
- Bark 收到一条推送，显示谁发的和消息摘要

### 场景 2：双通道提醒
- 同时发 Bark 和 WxPusher
- 你在 iPhone 或微信内都能看到提醒

### 场景 3：避免重复提醒
- Windows 通知中心/系统重复触发同一条提醒
- 程序根据短时去重策略只推送一次

## 4. 需求范围
### 4.1 输入
- Windows 系统通知（Toast）
- 仅处理来源为微信的通知

### 4.2 输出
- Bark 推送（默认）
- WxPusher 推送（可选）

### 4.3 消息结构
统一内部事件结构：

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

字段说明：
- `sender`：联系人名或群名
- `preview`：粗略消息摘要
- `chat_type`：V1 可为 `unknown` / `private` / `group`
- `raw_text`：原始通知文本，便于调试

## 5. 技术方案
## 5.1 总体架构

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

## 5.2 模块划分
### `src/listener/windows_notifications.py`
负责监听 Windows 通知，并把原始通知转换为统一原始输入。

### `src/parser/wechat_notification_parser.py`
负责：
- 判断是否来自微信
- 解析 sender / preview / raw_text
- 生成内部消息事件

### `src/dedupe/memory_dedupe.py`
负责：
- 生成消息指纹
- TTL 去重
- 清理过期缓存

### `src/notifiers/bark_notifier.py`
负责 Bark HTTP 推送。

### `src/notifiers/wxpusher_notifier.py`
负责 WxPusher HTTP 推送。

### `src/store/state_store.py`
负责本地持久化：
- 最近指纹
- 失败日志（后续可扩展）

### `src/app.py`
主流程编排：
- 加载配置
- 启动监听
- 解析消息
- 去重
- 调用通知通道

## 5.3 配置设计
建议使用 YAML：

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
```

## 5.4 去重策略
V1 使用短时 TTL 去重：
- 指纹组成：`sender + preview + time_bucket`
- 时间桶粒度：10 秒内视作同一条提醒
- 同内容重复通知只发一次

## 5.5 推送格式
### Bark
- 标题：`sender`
- 副标题：`微信新消息`
- 正文：`preview`
- group：`wechat-notify`

### WxPusher
- 标题：`微信新消息 - sender`
- 内容：包含摘要与时间

## 5.6 依赖策略
V1 先保持基础依赖可直接安装运行：
- `requests`
- `PyYAML`
- `pytest`

Windows 通知实时监听所需的 WinRT / winsdk 能力先作为**后续可选集成**，避免在未安装 Visual Studio C/C++ Build Tools 的机器上卡住初始化。第一阶段先用 mock/适配层把解析、去重、推送、运行框架跑通，再补系统通知接入。

## 6. 风险与限制
1. 依赖微信确实产生 Windows 系统通知。
2. 如果某会话在微信中被免打扰，可能收不到系统通知。
3. Windows 专注助手/静默模式可能影响通知捕获。
4. 通知内容可能只有摘要，不一定是完整消息。
5. 群聊场景下未必总能精确拆出“群名 + 发送人”。

## 7. 验收标准
满足以下条件视为 V1 成功：
1. Windows 微信上收到新消息时，程序能捕获通知。
2. 能提取联系人/群名与消息摘要。
3. 能推送到 Bark。
4. 开启 WxPusher 后，能同时推送到 WxPusher。
5. 同一条通知在短时间内不会重复推送。
6. 本地日志可定位失败原因。

## 8. 实现步骤
### Step 1：文档与项目骨架
- 写根目录 Markdown 文档
- 初始化 `src/`、`tests/`、`scripts/`
- 增加 `requirements.txt`
- 增加 `config.example.yaml`

### Step 2：通知解析与推送闭环
- 实现内部数据模型
- 实现微信通知解析器
- 实现去重器
- 实现 Bark / WxPusher 推送器
- 增加模拟输入模式，先不依赖真实系统通知完成闭环验证

### Step 3：接入 Windows 通知监听
- 实现 Windows 通知监听器
- 将原始通知接入解析管道
- 只保留微信通知

### Step 4：增强可用性
- 增加 SQLite 状态存储
- 增加日志与错误处理
- 增加 PowerShell 启动脚本
- 增加开机自启脚本

### Step 5：验证
- 本地模拟测试
- 真实微信通知测试
- Bark 推送测试
- WxPusher 推送测试

## 9. 当前推荐实现路线
V1 推荐优先级：
1. **先做模拟闭环**，确保解析 + 去重 + 推送稳定
2. **再接 Windows 通知监听**
3. **最后补部署脚本和开机自启**

这样可以先把核心链路做稳，再接入系统侧能力。
