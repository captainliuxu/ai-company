# Agent System Design

> **[FUTURE] 概念设计 — 不在当前 8 天范围内实现**

## 概念概述

当前 Demo 是单体服务架构。如果未来需要更复杂的自主行为（主动关心、日程提醒、长期关系管理），可以引入 Agent 架构。

## 未来 Agent 设计

### Agent 类型

| Agent | 职责 | 触发方式 |
|-------|------|---------|
| **Conversation Agent** | 处理用户消息、生成回复 | 用户消息驱动 |
| **Memory Agent** | 记忆提取、整理、遗忘、定期归档 | 后台定时 + 事件驱动 |
| **Emotion Agent** | 情绪状态分析、长期情绪趋势、情感健康监测 | 每轮对话后 |
| **Scheduler Agent** | 主动关心、日程提醒、定期 check-in | Cron 定时触发 |

### 编排

推荐方案：LangGraph StateGraph（轻量使用，不过度抽象）

```
State Graph:
  [User Message]
       ↓
  [Emotion Agent] → update emotion_state
       ↓
  [Memory Agent] → recall relevant
       ↓
  [Conversation Agent] → generate reply
       ↓
  [Memory Agent] → extract & store
       ↓
  [Scheduler Agent] → check if proactive is needed
```

## 当前架构如何兼容未来

- 所有 Service 已经是独立类，可直接被 Agent 调用
- `voice_service.py` stub 为 Voice Agent 预留
- Memory 模型已包含 importance 字段（未来 Agent 评分用）

## 不做的事情

- 不建 Agent 框架
- 不引入 LangGraph 依赖
- 不实现 Agent 间消息通信
- 不写自主行为引擎

当前只需确保：**如果将来加 Agent，现有 Service 设计不需要重写。**
