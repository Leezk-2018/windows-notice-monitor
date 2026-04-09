# pc-wechat-bark 实现方案

## 目标

基于 `wechat-cli` 的 Python 能力实现一个独立项目，在 Windows 本机常驻运行，轮询微信新消息，并将好友/群聊的新消息通过 Bark 推送到手机。

## 实现原则

- 直接 `import wechat_cli`，不走 CLI 子进程
- 首次运行只建立基线，不推送当前未读
- 每个变更会话单独推送一条 Bark
- 默认排除公众号/订阅号/服务号
- 仅在推送成功后推进状态
- Bark 失败时做进程内有限重试并记录日志

## 模块划分

- `config`：加载 TOML 配置并生成默认配置
- `state`：读写独立状态文件
- `source`：复用 `wechat_cli` 读取 `session.db` 与联系人信息
- `classifier`：识别好友/群聊/公众号
- `bark`：发送 Bark 通知
- `poller`：比较快照、生成事件、推进状态
- `service`：常驻轮询
- `cli`：`init-config` / `doctor` / `check` / `run`

## 关键行为

1. 启动后读取配置与状态。
2. 通过 `wechat_cli` 获取当前会话快照。
3. 若状态为空，则写入基线并退出。
4. 若会话 `timestamp` 变大，则视为新消息。
5. 仅保留好友和群聊，过滤公众号/未知会话。
6. 构造 Bark 标题与正文并发送。
7. 发送成功后更新该会话状态。

## CLI 设计

- `pc-wechat-bark init-config`：生成默认配置文件
- `pc-wechat-bark doctor`：检查配置、`wechat_cli` 与 Bark 配置
- `pc-wechat-bark check`：单次检查并推送
- `pc-wechat-bark run`：常驻轮询

## 测试

- 首次运行只建基线
- 有新增好友/群聊时推送
- 公众号被过滤
- Bark 失败时不推进状态
- 正文拼装与截断正确
