# PROJECT PLAN — AI Companion Pro Demo

> **权威开发计划。所有开发活动必须严格按照本文档的阶段顺序执行。**
> **协作规范：参见 `docs/rules/multi_agent_workflow.md`**

---

## 总览

| Phase | 模块 | 天数 | 状态 |
|-------|------|:----:|:----:|
| 0 | 项目骨架 + 文档 | 已完成 | ✅ |
| 1 | Persona System | Day 1 | ✅ |
| 2 | Chat API + Prompt Builder | Day 2 | ✅ |
| 3 | Emotion System | Day 3 | ✅ |
| 4 | Long-term Memory | Day 4 | ✅ |
| 5 | Lightweight RAG | Day 5 | ✅ |
| 6 | Conversation Summary | Day 6 | ✅ |
| 7 | Product Chat UI | Day 7 | ✅ |
| 8 | 集成调试 + Demo 打磨 | Day 8 | ✅ |

---

## 执行规则（不可违反）

### 1. 严格按 Phase 顺序
- 必须完成 Phase N 的所有验收标准后，才能进入 Phase N+1
- 禁止"顺便把下一个 Phase 的模型也建了"
- 禁止"这个功能很简单我先写了"

### 2. 一次只做一个 Phase
- 每个 Phase 的文件范围在下方明确列出
- 不允许改动当前 Phase 文件范围之外的代码
- 发现 bug 或改进点？记下来，当前 Phase 结束后再评估

### 3. 每个 Phase 的流程（含多 Agent 协作）

```
Phase N 开始
  │
  ├─→ STEP 1: Claude 拆分 Phase 为 N 个 TASK
  │     └─→ 每个 TASK 有唯一 ID + 文件范围 + 验收标准
  │
  ├─→ STEP 2: Claude 分配 TASK → DeepSeek 实现
  │     └─→ DeepSeek 按 TASK 精确编码，不越界
  │
  ├─→ STEP 3: DeepSeek Review 代码
  │     └─→ 输出 REVIEW REPORT
  │
  ├─→ STEP 4: Claude Merge Decision
  │     ├─→ 通过 → 标记 TASK 完成
  │     └─→ 不通过 → 返工或拆分新 TASK
  │
  └─→ 所有 TASK 完成 → Phase 完成 → 用户确认 → 进入下一 Phase
```

### 4. 禁止跳阶段
- 不管后面多简单，不管前面做得多好
- Phase 顺序是设计好的依赖链
- Persona → Chat → Emotion → Memory → RAG → Summary → UI → Polish
- 前一个没做完，后一个的基础不牢

---

## Phase 0：项目骨架 + 文档 ✅

**状态：已完成**

产出：
- 项目目录结构
- 15 个文档文件
- CLAUDE.md、PROJECT_PLAN.md
- backend 代码骨架 (main.py, config.py, database.py)
- .gitignore、GitHub 仓库

---

## Phase 1：Persona System ⬜

**目标：** FastAPI 跑通，3 个预设角色可查询

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/models/persona.py` | 新建 |
| `backend/schemas/chat.py` | 新建（Persona 相关 schema） |
| `backend/services/persona_service.py` | 新建 |
| `backend/api/chat.py` | 新建（persona routes） |
| `backend/main.py` | 修改（注册路由、lifespan 初始化） |

### 验收标准
- [ ] `uvicorn main:app` 启动成功
- [ ] `GET /api/v1/personas` 返回 3 个预设角色
- [ ] `GET /api/v1/personas/{id}` 返回单个角色详情
- [ ] 3 个角色（小暖/小锐/小默）人格定义完整
- [ ] 数据库自动建表

### 依赖
无（Phase 0 已完成）

---

## Phase 2：Chat API + Prompt Builder ⬜

**目标：** SSE 流式聊天跑通，Prompt Pipeline 输出有角色感的回复

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/schemas/chat.py` | 修改（加 Chat 相关 schema） |
| `backend/services/prompt_builder.py` | 新建 |
| `backend/api/chat.py` | 修改（加 chat routes） |

### 验收标准
- [ ] `POST /api/v1/chat/session` 创建会话
- [ ] `POST /api/v1/chat/send` SSE 流式返回
- [ ] system_prompt 包含 Persona Block
- [ ] 不同角色回复风格明显不同
- [ ] 流式输出不卡顿

### 依赖
Phase 1（Persona 数据可查询）

---

## Phase 3：Emotion System ⬜

**目标：** 情绪状态随对话动态变化，影响 Prompt

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/models/emotion.py` | 新建 |
| `backend/services/emotion_service.py` | 新建 |
| `backend/services/prompt_builder.py` | 修改（加 Emotion Block） |
| `backend/api/chat.py` | 修改（加 emotion route） |

### 验收标准
- [ ] 情绪四维度（favorability/trust/mood/dependency）正确更新
- [ ] 情绪变化历史可追溯
- [ ] 不同情绪状态下 AI 回复语气不同
- [ ] `GET /api/v1/emotion/{session_id}` 返回当前状态

### 依赖
Phase 2（Chat 已跑通）

---

## Phase 4：Long-term Memory ⬜

**目标：** 用户信息/偏好/事件持久化存储，跨会话保留

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/models/memory.py` | 新建 |
| `backend/services/memory_service.py` | 新建 |
| `backend/api/chat.py` | 修改（加 memory route） |

### 验收标准
- [ ] 对话中提取的用户信息正确存储
- [ ] 记忆按类型分类（user_info/preference/event/emotion）
- [ ] 退出重进后记忆保留
- [ ] `GET /api/v1/memories/{session_id}` 返回记忆列表

### 依赖
Phase 2（Chat 已跑通）+ Phase 3（Emotion 可标记情绪事件）

---

## Phase 5：Lightweight RAG ⬜

**目标：** 用户消息 → embedding → 相似度召回 → 注入 Prompt

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/services/rag_service.py` | 新建 |
| `backend/services/prompt_builder.py` | 修改（加 Memory Block） |
| `backend/services/memory_service.py` | 修改（加 embedding 生成） |

### 验收标准
- [ ] sentence-transformers 加载成功
- [ ] 新记忆自动生成 embedding 并存储
- [ ] 用户消息触发相似记忆召回
- [ ] 召回记忆出现在 AI 回复中（自然融入，不刻意列举）
- [ ] Top-K=5, threshold=0.3 生效

### 依赖
Phase 4（Memory 存储已就位）

---

## Phase 6：Conversation Summary ⬜

**目标：** 长对话自动压缩，上下文不爆炸

### 文件范围

| 文件 | 操作 |
|------|------|
| `backend/services/summary_service.py` | 新建 |
| `backend/api/chat.py` | 修改（send route 加入 summary 触发） |

### 验收标准
- [ ] 对话超过 20 轮自动触发摘要
- [ ] 摘要内容覆盖：用户近况、情绪变化、关系变化
- [ ] 摘要存入 memory
- [ ] 摘要后对话仍保持连贯

### 依赖
Phase 4（Memory 可存储摘要）+ Phase 5（RAG 可召回摘要）

---

## Phase 7：Product Chat UI ⬜

**目标：** 前端像真正的 AI 陪伴产品

### 文件范围

| 文件 | 操作 |
|------|------|
| `frontend/chat/` — Next.js 项目 | 新建（npx create-next-app） |
| 角色选择页 | 新建 |
| 聊天气泡组件 | 新建 |
| 情绪状态面板 | 新建 |
| SSE 接收逻辑 | 新建 |

### 验收标准
- [ ] 角色选择页，3 个角色卡片可选
- [ ] 聊天气泡（左AI右用户）+ typing 动画
- [ ] 情绪状态实时展示
- [ ] SSE 流式接收逐字显示
- [ ] 响应式布局
- [ ] shadcn/ui 组件 + TailwindCSS 样式
- [ ] 温暖柔和配色

### 依赖
Phase 1-6（后端全部 API 就位）

---

## Phase 8：集成调试 + Demo 打磨 ⬜

**目标：** 全链路跑通，演示就绪

### 验收标准
- [ ] Persona 切换后回复风格明显不同
- [ ] 情绪状态随对话动态变化
- [ ] 退出重进后记忆保留
- [ ] RAG 召回历史记忆并体现在回复中
- [ ] 长对话自动摘要
- [ ] 流式输出不卡顿
- [ ] UI 覆盖 loading/empty/error 状态
- [ ] 边界情况处理（空消息、超长消息、断网）

### 依赖
Phase 1-7 全部完成

---

## 禁止事项

- 禁止在 Phase N 中改动 Phase N+1 及之后的文件
- 禁止一次实现多个 Phase 的模块
- 禁止"顺便把模型建好以后用"
- 禁止跳过验收标准直接标记完成
- 禁止在未完成当前 Phase 时讨论后续 Phase 的实现细节
