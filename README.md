# pc-wechat-bark

一个基于 `wechat-cli` 的微信新消息 Bark 推送服务。

它会在本机轮询微信会话变化，并把**好友**和**群聊**的新消息推送到你的 Bark 设备；默认**不推送公众号/订阅号/服务号**。

---

## 项目用途

这个项目适合下面这些场景：

- 在 Windows 电脑上长期挂着微信，希望手机及时收到本机微信的新消息提醒
- 希望把本地微信的“好友/群聊”新消息做二次通知
- 想基于 `wechat-cli` 搭一个轻量、可控、可二次开发的消息通知服务
- 想后续扩展到更多通知渠道，例如 Telegram、企业微信、钉钉、邮件等

---

## 功能特性

- 直接复用 `wechat_cli` 的 Python 能力读取本地微信会话
- 首次运行只建立基线，不推送历史未读，避免首次刷屏
- 仅推送好友 / 群聊
- 默认过滤公众号 / 订阅号 / 服务号
- 每个变更会话单独推送一条 Bark
- Bark 发送失败自动重试
- 独立状态文件，不污染 `wechat-cli` 自身状态
- 提供 `doctor / check / run / init-config` 命令

---

## 工作原理

本项目并不是 Hook 微信，也不是实时监听系统通知。

它的核心思路是：

1. 通过 `wechat-cli` 解密并读取本地微信 `session.db`
2. 获取每个会话的最新时间戳、摘要、发送者等信息
3. 与本项目自己的状态文件进行对比
4. 识别新增消息会话
5. 过滤出好友和群聊
6. 通过 Bark 发送到手机

因此它具备：

- **优点**：实现简单、稳定、完全本地、易扩展
- **限制**：当前主要基于会话摘要，不是逐条还原所有消息正文

---

## 依赖说明

### 运行环境

- Python `>= 3.10`
- 已可正常使用的 `wechat-cli`
- 已完成 `wechat-cli init`
- 可用的 Bark 设备 Key

### Python 依赖

本项目当前依赖：

- `click >= 8.1, < 9`
- `tomli >= 2.0`（仅 Python < 3.11 时使用）

### 上游依赖

本项目依赖 `wechat-cli` 提供以下能力：

- 微信数据目录发现
- 密钥提取与数据库解密
- 联系人与会话信息读取
- 消息摘要解压与类型格式化

如果 `wechat-cli` 无法正常工作，本项目也无法正常读取微信会话。

---

## 安装

```powershell
cd D:\lee\github\wechat-cli\pc-wechat-bark
pip install -e .
```

请先确保你的环境已经能正常执行：

```powershell
wechat-cli init
```

---

## 快速开始

### 1）生成配置文件

```powershell
pc-wechat-bark init-config
```

默认会在当前目录生成：

- `config.toml`

### 2）填写 Bark 配置

至少修改：

```toml
[bark]
device_key = "YOUR_DEVICE_KEY"
```

如果你使用官方 Bark 服务，一般保持：

```toml
server = "https://api.day.app"
```

### 3）检查环境

```powershell
pc-wechat-bark doctor
```

### 4）首次建立基线

```powershell
pc-wechat-bark check
```

第一次执行时：

- 只建立基线
- 不推送历史未读消息

### 5）常驻运行

```powershell
pc-wechat-bark run
```

---

## 配置示例

```toml
[wechat]
config_path = ""

[poll]
interval_seconds = 15
first_run_mode = "baseline_only"

[filters]
include_groups = true
include_friends = true
exclude_official_accounts = true
include_unknown = false

[bark]
server = "https://api.day.app"
device_key = "YOUR_DEVICE_KEY"
group = "wechat"
sound = ""
icon = ""
url = ""

[notify]
show_sender = true
show_msg_type = true
show_summary = true
max_body_length = 160

[retry]
max_attempts = 3
backoff_seconds = [1, 3, 10]

[logging]
level = "INFO"
file = ""

[state]
path = "~/.pc-wechat-bark/state.json"
```

---

## 命令说明

### `pc-wechat-bark init-config`

生成默认配置文件。

### `pc-wechat-bark doctor`

检查：

- 配置文件是否可读取
- Bark 配置是否完整
- `wechat_cli` 数据源是否可用

### `pc-wechat-bark check`

执行一次检查：

- 首次运行：建立基线
- 后续运行：发现新消息并推送

### `pc-wechat-bark run`

常驻运行，按配置周期轮询。

---

## 当前行为说明

当前版本默认行为：

- 只推送好友和群聊
- 默认不推送公众号
- 首次运行不推送历史未读
- Bark 推送成功后才推进状态
- Bark 推送失败会重试，失败后本轮不推进该会话状态

---

## 测试

运行测试：

```powershell
python -m unittest discover -s tests
```

---

## 目录结构

```text
pc-wechat-bark/
├─ pc_wechat_bark/
│  ├─ bark.py
│  ├─ classifier.py
│  ├─ cli.py
│  ├─ config.py
│  ├─ models.py
│  ├─ poller.py
│  ├─ service.py
│  ├─ source.py
│  └─ state.py
├─ tests/
├─ config.toml.example
├─ plan.md
├─ pyproject.toml
└─ README.md
```

---

## 开源说明

本项目适合以开源项目方式发布到 GitHub。

建议你发布时补充：

- 仓库描述
- License 文件
- Release / Tag
- 使用截图或运行示例
- 免责声明

当前项目代码本身没有引入闭源组件；但它依赖用户本机已经安装并初始化好的 `wechat-cli` 与微信本地数据环境。

如果你准备公开发布，建议增加一个正式的 `LICENSE` 文件。  
若你想与上游 `wechat-cli` 风格保持一致，可以优先考虑：

- `Apache-2.0`

---

## 致谢

感谢以下项目与服务：

- [`wechat-cli`](https://github.com/freestylefly/wechat-cli)  
  本项目的核心基础能力来源，包括微信数据库解密、联系人读取、会话读取等。

- [Bark](https://github.com/Finb/Bark)  
  提供简洁好用的 iPhone 推送能力。

- Python 社区与 `click` 项目  
  为命令行工具开发提供了稳定基础。

---

## 免责声明

本项目仅用于：

- 个人本机消息提醒
- 本地自动化
- 学习和研究 `wechat-cli` 的扩展方式

请勿将其用于任何非法用途。  
使用本项目时，请自行确保符合你所在地区的法律法规、平台协议以及个人隐私要求。

---

## 后续可扩展方向

- 支持只推送指定好友 / 指定群
- 支持防抖 / 合并通知
- 支持更多通知渠道
- 支持开机自启 / Windows 计划任务
- 支持更丰富的消息正文提取
- 支持更细粒度的过滤规则

