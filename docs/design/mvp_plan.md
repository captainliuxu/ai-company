# MVP Plan

## MVP 定义

**8 天内可完成的最小的、可演示的 AI Companion。**

## MVP Scope

```
┌─────────────────────────────────────┐
│            MVP Boundary             │
│                                      │
│  Persona System          ✓          │
│  Chat API (SSE)          ✓          │
│  Emotion System          ✓          │
│  Long-term Memory        ✓          │
│  Lightweight RAG         ✓          │
│  Prompt Builder          ✓          │
│  Conversation Summary    ✓          │
│  Product Chat UI         ✓          │
│                                      │
│  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ │
│  Voice System            (future)   │
│  Avatar/Live2D           (future)   │
│  Mobile App              (future)   │
│  Multi-Agent             (future)   │
└─────────────────────────────────────┘
```

## MVP 验收标准

- [ ] 3 个预设角色可切换，回复风格明显不同
- [ ] 情绪状态随对话动态变化，变化可追溯
- [ ] 用户信息/偏好/事件被持久化存储
- [ ] RAG 召回历史记忆并体现在 AI 回复中
- [ ] 对话超过 20 轮自动触发摘要
- [ ] SSE 流式输出不卡顿
- [ ] 前端有角色选择页 + 聊天气泡 + typing 动画 + 情绪展示
- [ ] 退出重进后记忆不丢失

## 不做的

- 语音输入/输出
- 数字人渲染
- 移动端 App
- 用户注册/登录系统（单用户 Demo）
- 多 Agent 协作
- 实时推送/通知
