# Roadmap

## v0.1.0 — AI Companion Core (当前 8-Day Sprint)

**目标**：可演示的 AI 陪伴 Demo，具备记忆+情绪+人格

| # | 模块 | 状态 |
|---|------|:----:|
| 1 | Persona System (3预设角色) | [ ] |
| 2 | Chat API + SSE Stream | [ ] |
| 3 | Emotion System | [ ] |
| 4 | Long-term Memory (SQLite) | [ ] |
| 5 | Lightweight RAG | [ ] |
| 6 | Prompt Builder Pipeline | [ ] |
| 7 | Conversation Summary | [ ] |
| 8 | Product Chat UI (Next.js) | [ ] |

---

## v0.2.0 — Voice & Interaction

**目标**：加入语音交互能力

- Whisper ASR 语音转文字
- EdgeTTS / CosyVoice 文字转语音
- WebSocket 实时语音流
- 前端语音按钮 + 音量动画

---

## v0.3.0 — Avatar & Visual

**目标**：数字人形象

- Live2D Cubism SDK 集成
- 嘴型同步 (lip-sync)
- 情绪表情映射
- 动态待机动画

---

## v0.4.0 — Mobile & PWA

**目标**：移动端覆盖

- PWA 离线支持
- 响应式移动 UI 优化
- Android WebView 封装
- Push Notification (主动关心)

---

## v0.5.0 — Advanced AI

**目标**：更深度的 AI 能力

- 混合检索 (BM25 + Dense)
- 记忆重要性评分 + 时间衰减
- 向量数据库替换 (ChromaDB/Qdrant)
- Multi-Agent 架构 (LangGraph)
- 主动交互引擎

---

## v1.0.0 — Product Release

**目标**：完整产品体验

- 用户注册/登录
- 多会话管理
- 角色市场 (自定义 Persona)
- 数据导出/隐私控制
- 性能优化 + 安全审计
