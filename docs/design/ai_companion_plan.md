# AI Companion Pro Demo — 完整开发计划

## 项目定位

**AI Companion Pro Demo** 是一个 8 天内完成的中型 AI 应用 Demo。

目标用户：面试官 / 招聘方 / 作品集浏览者
核心体验：**"有陪伴感的 AI"**

不是：商业化产品、SaaS 平台、Agent 框架、微服务系统

---

# 一、Current Scope（8天内完成）

## 模块全景

```
用户消息
  → Emotion 情绪分析
  → RAG 记忆召回
  → Prompt Builder 拼装 system_prompt
  → LLM 生成回复
  → Memory 存储新记忆
  → Conversation Summary (when needed)
  → 流式返回前端
```

---

## Day 1：项目搭建 + Persona System

### 目标
FastAPI 骨架跑通，Persona 数据模型和 3 个预设角色就位。

### 交付物
- `backend/main.py` — FastAPI app 启动
- `backend/config.py` — 配置管理（DB路径、API key、模型参数）
- `backend/models/persona.py` — Persona SQLAlchemy 模型
- `backend/schemas/chat.py` — Pydantic 请求/响应 schema
- `backend/services/persona_service.py` — 角色 CRUD
- `backend/api/chat.py` — GET /api/v1/personas 路由

### Persona 数据模型

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 唯一标识 |
| name | str | 角色名 |
| personality | str | 性格描述 |
| speaking_style | str | 说话风格 |
| background_story | str | 背景故事 |
| emotional_traits | JSON | 情绪特质列表 |
| avatar_url | str? | 头像URL（可选） |

### 3 个预设角色

1. **小暖** — 温柔体贴、擅长倾听、语气软糯
2. **小锐** — 理性毒舌、一针见血、但不冷漠
3. **小默** — 安静沉稳、话少但每句有分量

---

## Day 2：Chat API + Prompt Builder

### 目标
聊天接口跑通，Prompt Pipeline 拼装出有角色感的 system_prompt。

### 交付物
- `backend/api/chat.py` — POST /api/v1/chat (SSE 流式)
- `backend/services/prompt_builder.py` — Prompt 管线
- `backend/api/chat.py` — POST /api/v1/chat/session (创建会话)

### Prompt Pipeline

```
┌─────────────────────────────────────┐
│           System Prompt              │
│  ┌─────────────────────────────┐    │
│  │ 1. Persona Block            │    │
│  │    - 性格 / 说话风格 / 背景  │    │
│  ├─────────────────────────────┤    │
│  │ 2. Emotion Block            │    │
│  │    - 当前情绪状态            │    │
│  ├─────────────────────────────┤    │
│  │ 3. Memory Block             │    │
│  │    - 召回的用户记忆          │    │
│  ├─────────────────────────────┤    │
│  │ 4. Response Rules           │    │
│  │    - 回复格式/字数/限制      │    │
│  └─────────────────────────────┘    │
│                                      │
│  Recent Chat History (最近N轮)        │
│  User Message                        │
└─────────────────────────────────────┘
```

### 流式输出
- SSE (Server-Sent Events)，不是 WebSocket
- 逐 token 返回

---

## Day 3：Emotion System

### 目标
情绪状态模型运行，LLM 分类用户情绪，情绪影响 Prompt 生成。

### 交付物
- `backend/models/emotion.py` — 情绪状态 SQLAlchemy 模型
- `backend/services/emotion_service.py` — 情绪识别 + 状态更新

### 情绪维度

| 维度 | 范围 | 说明 |
|------|------|------|
| favorability | 0-100 | 好感度 |
| trust | 0-100 | 信任度 |
| mood | -1.0 ~ 1.0 | 当前情绪（负=低落，正=开心） |
| dependency | 0-100 | 依赖度（AI对用户的依赖感） |

### 情绪识别流程

用户消息 → LLM 情绪分类 → 更新 emotion_state → 注入 Prompt Builder → 影响回复风格

---

## Day 4：Long-term Memory

### 目标
记忆存取跑通，用户信息/偏好/事件可持续存储。

### 交付物
- `backend/models/memory.py` — Memory SQLAlchemy 模型
- `backend/services/memory_service.py` — 记忆 CRUD + 提取

### 记忆类型

| 类型 | 示例 |
|------|------|
| user_info | "名字叫小王"、"职业是设计师" |
| user_preference | "喜欢猫"、"不喜欢下雨天" |
| relationship_event | "第一次聊天是在3月"、"昨天一起聊到凌晨" |
| emotional_event | "今天心情不好"、"上周升职了很开心" |

### 记忆提取流程

每轮对话后 → LLM 判断是否有新记忆 → 如果是，提取并存储

---

## Day 5：Lightweight RAG

### 目标
sentence-transformers 嵌入 + SQLite 向量存储 + 余弦相似度召回。

### 交付物
- `backend/services/rag_service.py` — embedding 生成 + 相似度检索

### 技术方案

- Embedding 模型：`all-MiniLM-L6-v2`（384维，轻量）
- 存储：SQLite 表直接存向量（BLOB）
- 检索：numpy 余弦相似度，top_k=5
- 每次对话时检索相关历史记忆

```python
# RAG Pipeline
user_message
  → embedding(user_message)
  → cosine_similarity(embedding, memory_embeddings)
  → top_k relevant memories
  → inject into Prompt Builder
```

### [FUTURE] 扩展点
- 替换为向量数据库 (ChromaDB / Qdrant / pgvector)
- 混合检索 (BM25 + Dense)
- 记忆重要性评分与衰减
- 多级缓存

---

## Day 6：Conversation Summary

### 目标
对话过长时自动触发摘要，压缩上下文。

### 交付物
- `backend/services/summary_service.py` — 摘要生成

### 触发条件

- 对话轮次 > 20 轮 → 触发摘要
- 摘要内容：用户近况、情绪变化、关系变化
- 摘要存入 memory，后续对话替代完整历史

### [FUTURE] 扩展点
- 分层摘要（即时/短期/长期）
- 结构化摘要（JSON格式）
- 增量摘要而非全量重算

---

## Day 7：Product Chat UI

### 目标
前端像真正的 AI 陪伴产品，不是课程作业。

### 交付物
- Next.js 项目 (`frontend/chat/`)
- 角色选择页
- 聊天气泡（左AI右用户）
- typing 动画（三个点跳动）
- 情绪状态展示（顶部小面板）
- SSE 流式接收

### UI 要求

- 温暖柔和配色
- 圆角气泡
- 呼吸感动画
- shadcn/ui 组件
- 响应式布局

### [FUTURE] 扩展点
- 语音输入按钮（UI 占位，disabled）
- 数字人头像区域（预留位置）
- PWA 移动端适配

---

## Day 8：集成调试 + Demo 打磨

### 目标
全链路跑通，边界处理，演示准备。

### 检查清单
- [ ] Persona 切换后回复风格明显不同
- [ ] 情绪状态随对话动态变化
- [ ] 退出重进后记忆保留
- [ ] RAG 召回历史记忆并体现在回复中
- [ ] 长对话自动摘要
- [ ] 流式输出不卡顿
- [ ] UI 各状态覆盖（加载/空/错误）

---

# 二、Future Scope（保留设计，不实现）

## 1. Voice System

### 规划
- ASR: Whisper 语音转文字
- TTS: EdgeTTS / CosyVoice 文字转语音
- WebSocket 实时语音流
- 降噪 + VAD (Voice Activity Detection)

### 当前保留
- `backend/services/voice_service.py` — class VoiceService interface stub
- API: `POST /api/v1/voice/asr`, `POST /api/v1/voice/tts` (占位)
- 前端语音按钮 UI（disabled 状态）

---

## 2. Avatar / Live2D 数字人

### 规划
- Live2D Cubism SDK 集成
- 嘴型同步 (lip-sync)
- 情绪表情切换
- 动态待机动画

### 当前保留
- `frontend/avatar/` 目录 + README
- Persona.avatar_url 字段
- 架构设计笔记

---

## 3. Mobile / Android

### 规划
- 响应式前端 → PWA → Android WebView
- 或 Flutter 重写移动端

### 当前保留
- TailwindCSS 响应式已覆盖
- Roadmap 条目

---

## 4. Multi-Agent 架构

### 规划
- Memory Agent / Emotion Agent / Conversation Agent
- LangGraph State Graph 编排
- Agent 间消息传递

### 当前保留
- `docs/architecture/agent_system.md` 概念设计
- 不建代码目录

---

## 5. Advanced Memory

### 规划
- ChromaDB / Qdrant 向量数据库
- 混合检索 (BM25 + Dense)
- 记忆重要性评分
- 时间衰减算法
- 分层记忆 (working / short / long / core)

### 当前保留
- 代码中 TODO 注释标记扩展点
- `docs/architecture/memory_system.md` Future 章节

---

# 三、API 设计概览

| Method | Path | Scope | 说明 |
|--------|------|-------|------|
| GET | /api/v1/personas | Current | 获取角色列表 |
| GET | /api/v1/personas/{id} | Current | 角色详情 |
| POST | /api/v1/chat/session | Current | 创建会话 |
| POST | /api/v1/chat/send | Current | 发送消息(SSE) |
| GET | /api/v1/chat/{session_id}/history | Current | 获取历史 |
| GET | /api/v1/emotion/{session_id} | Current | 当前情绪状态 |
| GET | /api/v1/memories/{session_id} | Current | 用户记忆列表 |
| POST | /api/v1/voice/asr | Future | 语音转文字 |
| POST | /api/v1/voice/tts | Future | 文字转语音 |

---

# 四、面试价值

| 技术方向 | 覆盖 |
|----------|:----:|
| LLM Application | Yes |
| Prompt Engineering | Yes |
| RAG / Memory System | Yes |
| Emotion AI | Yes |
| FastAPI 后端 | Yes |
| Next.js 前端 | Yes |
| AI Product Thinking | Yes |
| System Design | Yes |
