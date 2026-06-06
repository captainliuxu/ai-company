# TASK BOARD

> **当前任务看板。Claude 负责维护，每个 TASK 生命周期在此追踪。**

---

## 状态生命周期

每个 TASK 必须经过 4 个状态，**Claude 是 TASK_BOARD 的唯一修改者**：

```
⬜ TODO        → Claude 创建 TASK 时设置
🔨 IN_PROGRESS → Claude 分配 TASK 给 DeepSeek 时设置
🔍 REVIEW      → Claude 收到 DeepSeek Dev 完成信号后设置（此时 DeepSeek Review 可领取审查）
✅ DONE        → Claude 收到 DeepSeek Review PASSED 后设置
❌ FAILED      → Claude 收到 DeepSeek Review FAILED 后设置
```

**关键规则：只有 `🔍 REVIEW` 状态的 TASK 才会被 DeepSeek Review Agent 领取审查。Claude 必须在 DeepSeek Dev 完成后立即更新状态，否则 Review Agent 无法开始工作。**

---

## Phase 1: Persona System

**目标：** FastAPI 跑通，3 个预设角色可查询

### 依赖图

```
Wave 1 (并行)    Wave 2 (串行)   Wave 3 (串行)   Wave 4 (串行)
PH1-001 ─┐
          ├──→ PH1-003 ──→ PH1-004 ──→ PH1-005
PH1-002 ─┘
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH1-001 | Persona 数据模型 | 1 | ✅ DONE | DeepSeek |
| PH1-002 | Persona Pydantic Schema | 1 | ✅ DONE | DeepSeek |
| PH1-003 | Persona Service | 2 | ✅ DONE | DeepSeek |
| PH1-004 | Persona API Routes | 3 | ✅ DONE | DeepSeek |
| PH1-005 | main.py 注册路由 | 4 | ✅ DONE | DeepSeek |
| PH1-FIX-001 | 修复 created_at 类型 (ISSUE-001) | FIX | ✅ DONE | DeepSeek |
| PH1-FIX-002 | 修复 404 状态码 (ISSUE-002) | FIX | ✅ DONE | DeepSeek |
| PH1-FIX-003 | 修复 utcnow 弃用 (ISSUE-003) | FIX | ✅ DONE | DeepSeek |

状态: ⬜ TODO → 🔨 IN_PROGRESS → 🔍 REVIEW → ✅ DONE / ❌ FAILED

---

## Wave 1（并行 — 2 Agent）

---

### TASK PH1-001：Persona 数据模型

```
TASK-ID: PH1-001
名称: Persona SQLAlchemy 数据模型
Wave: 1（与 PH1-002 并行）

目标: 定义 Persona ORM 模型，Base 注册，数据库自动建表
---

允许修改文件:
- backend/models/persona.py     (新建)
- backend/models/__init__.py    (修改)

禁止修改:
- backend/models/ 以外的任何文件
- backend/main.py
- backend/config.py
- backend/database.py
- backend/api/
- backend/services/
- backend/schemas/

输入条件:
- database.py 已存在 (Base, engine)
- config.py 已存在

输出要求:
1. Persona class 继承 Base
2. 字段:
   - id: UUID, primary_key, default=uuid4
   - name: str(50), unique, not null
   - personality: str(500)
   - speaking_style: str(500)
   - background_story: str(1000)
   - emotional_traits: JSON (存储 {"trait": "description", ...})
   - avatar_url: str(500), nullable
   - created_at: datetime, default=now
3. __init__.py 导出 Persona

完成标准:
- ✔ 文件创建成功，无语法错误
- ✔ Persona 正确继承 Base
- ✔ 字段类型正确（JSON 字段用 sqlalchemy.JSON）
- ✔ __init__.py 导出 Persona
```

---

### TASK PH1-002：Persona Pydantic Schema

```
TASK-ID: PH1-002
名称: Persona Pydantic Schema
Wave: 1（与 PH1-001 并行）

目标: 定义 Persona 的请求/响应 Pydantic schema
---

允许修改文件:
- backend/schemas/chat.py    (新建)
- backend/schemas/__init__.py (修改，如需)

禁止修改:
- backend/schemas/ 以外的任何文件
- backend/main.py
- backend/models/
- backend/api/
- backend/services/

输入条件:
- 无（独立，不依赖 PH1-001 的代码）

输出要求:
1. PersonaResponse(BaseModel):
   - id: str
   - name: str
   - personality: str
   - speaking_style: str
   - background_story: str
   - emotional_traits: dict
   - avatar_url: str | None
   - created_at: str (ISO format)
   - model_config = {"from_attributes": True}

2. PersonaListResponse(BaseModel):
   - personas: list[PersonaResponse]

完成标准:
- ✔ 文件创建成功，无语法错误
- ✔ PersonaResponse 有 from_attributes=True
- ✔ emotional_traits 为 dict 类型
- ✔ avatar_url 为 Optional[str]
```

---

## Wave 2（串行 — PH1-001 + PH1-002 完成后启动）

---

### TASK PH1-003：Persona Service

```
TASK-ID: PH1-003
名称: Persona Service (CRUD + 种子数据)
Wave: 2（依赖 PH1-001 + PH1-002）

目标: 实现 Persona 业务逻辑层：查询 + 种子数据初始化
---

允许修改文件:
- backend/services/persona_service.py    (新建)
- backend/services/__init__.py           (修改，如需)

禁止修改:
- backend/services/ 以外的任何文件
- backend/main.py
- backend/api/
- backend/models/
- backend/schemas/

输入条件:
- PH1-001 Persona model 已定义
- PH1-002 PersonaResponse schema 已定义

输出要求:
1. PersonaService class:
   - __init__(db_session)
   - async get_all() -> list[PersonaResponse]
   - async get_by_id(persona_id: str) -> PersonaResponse | None
   - async seed_default_personas() -> int  (返回创建数量)

2. 种子数据（3 个角色，仅在表为空时插入）:
   - 小暖: personality="温柔体贴、善解人意", speaking_style="软糯温和、多用语气词",
     background_story="来自江南小镇的治愈系少女...",
     emotional_traits={"warmth": "高", "patience": "高", "sharpness": "低"}
   - 小锐: personality="理性毒舌、一针见血但不冷漠",
     speaking_style="直接利落、偶尔带刺但不伤人",
     background_story="曾是顶级咨询公司分析师...",
     emotional_traits={"sharpness": "高", "honesty": "高", "gentleness": "中"}
   - 小默: personality="安静沉稳、话少但每句有分量",
     speaking_style="简洁、不说废话",
     background_story="沉默的观察者...",
     emotional_traits={"calmness": "高", "insight": "高", "talkativeness": "低"}

完成标准:
- ✔ get_all() 返回 PersonaResponse 列表
- ✔ get_by_id() 找到返回对象，找不到返回 None
- ✔ seed_default_personas() 只在空表时插入
- ✔ 3 个角色的种子数据完整
- ✔ 无语法错误
```

---

## Wave 3（串行 — PH1-003 完成后启动）

---

### TASK PH1-004：Persona API Routes

```
TASK-ID: PH1-004
名称: Persona API Routes
Wave: 3（依赖 PH1-003）

目标: 实现 GET /api/v1/personas 和 GET /api/v1/personas/{id}
---

允许修改文件:
- backend/api/chat.py       (新建)
- backend/api/__init__.py   (修改，如需)

禁止修改:
- backend/api/ 以外的任何文件
- backend/main.py
- backend/services/
- backend/models/
- backend/schemas/

输入条件:
- PH1-003 PersonaService 已实现
- 标准响应格式: {"success": bool, "message": str, "data": ...}

输出要求:
1. APIRouter(prefix="/api/v1", tags=["personas"])
2. GET /api/v1/personas:
   - 调用 PersonaService.get_all()
   - 返回 {"success": true, "message": "", "data": {"personas": [...]}}
3. GET /api/v1/personas/{persona_id}:
   - 调用 PersonaService.get_by_id()
   - 找到 → {"success": true, "data": PersonaResponse}
   - 未找到 → 404 {"success": false, "message": "Persona not found", "data": null}
4. 依赖注入 get_db → PersonaService

完成标准:
- ✔ /api/v1/personas 返回 3 个预设角色
- ✔ /api/v1/personas/{valid_id} 返回正确角色
- ✔ /api/v1/personas/{invalid_id} 返回 404
- ✔ 响应格式统一 {"success", "message", "data"}
- ✔ 无语法错误
```

---

## Wave 4（串行 — PH1-004 完成后启动）

---

### TASK PH1-005：注册路由 + 启动验证

```
TASK-ID: PH1-005
名称: main.py 注册路由 + 启动时种子数据初始化
Wave: 4（依赖 PH1-004）

目标: 将 persona_router 注册到 FastAPI app，启动时自动建表+种子数据
---

允许修改文件:
- backend/main.py    (修改)

禁止修改:
- backend/main.py 以外的任何文件
- backend/api/
- backend/services/
- backend/models/
- backend/schemas/

输入条件:
- PH1-004 persona_router 已定义
- database.py 有 init_db()

输出要求:
1. from backend.api.chat import router as persona_router
2. app.include_router(persona_router)
3. lifespan context manager:
   - startup: await init_db() + 调用 PersonaService.seed_default_personas()
   - shutdown: await engine.dispose()
4. data/ 目录确保存在

完成标准:
- ✔ uvicorn backend.main:app 启动无报错
- ✔ 启动后 GET /api/v1/personas 返回 200
- ✔ 返回 3 个预设角色数据
- ✔ 再次启动不重复插入种子数据
- ✔ GET /api/v1/personas/{id} 返回 200
- ✔ 不存在的 id 返回 404
```

---

## Phase 1 修复 TASK（DeepSeek Review 验收发现）

### TASK PH1-FIX-001：修复 created_at 类型转换 (ISSUE-001)

```
TASK-ID: PH1-FIX-001
名称: 修复 PersonaResponse.created_at 类型转换
关联: ISSUE-001 (Critical)

目标: 修复 /api/v1/personas 500 错误
---

允许修改文件:
- backend/schemas/chat.py    (修改)

禁止修改:
- backend/schemas/chat.py 以外的任何文件

输出要求:
1. created_at 字段类型从 str 改为 datetime
2. 添加 field_serializer 输出 ISO 格式字符串:
   @field_serializer('created_at')
   def serialize_created_at(self, dt: datetime) -> str:
       return dt.isoformat()
3. 添加 from datetime import datetime 导入

完成标准:
- ✔ GET /api/v1/personas 不再返回 500
- ✔ created_at 字段返回 ISO 格式字符串
```

---

### TASK PH1-FIX-002：修复 404 状态码 (ISSUE-002)

```
TASK-ID: PH1-FIX-002
名称: 修复 get_persona 404 返回 HTTP 200 的问题
关联: ISSUE-002 (Medium)

目标: 不存在的 persona_id 返回 HTTP 404
---

允许修改文件:
- backend/api/chat.py    (修改)

禁止修改:
- backend/api/chat.py 以外的任何文件

输出要求:
1. 导入 JSONResponse: from fastapi.responses import JSONResponse
2. persona 为 None 时返回 JSONResponse(status_code=404, content={...})

完成标准:
- ✔ GET /api/v1/personas/{invalid_id} 返回 HTTP 404
```

---

### TASK PH1-FIX-003：修复 datetime.utcnow 弃用 (ISSUE-003)

```
TASK-ID: PH1-FIX-003
名称: 替换 datetime.utcnow 为 datetime.now(timezone.utc)
关联: ISSUE-003 (Low)

目标: 消除 Python 3.12+ 弃用警告
---

允许修改文件:
- backend/models/persona.py    (修改)

禁止修改:
- backend/models/persona.py 以外的任何文件

输出要求:
1. 添加 from datetime import timezone 导入
2. default=datetime.utcnow → default=lambda: datetime.now(timezone.utc)

完成标准:
- ✔ 模型定义无语法错误
- ✔ 不再使用已弃用的 datetime.utcnow
```

---

## Phase 1 总验收标准

全部 TASK 完成后，以下检查点必须全部通过：

- [x] `uvicorn backend.main:app` 启动无报错
- [x] `GET /api/v1/personas` → 200，返回 3 个角色
- [x] `GET /api/v1/personas/{valid_id}` → 200，返回正确角色
- [x] `GET /api/v1/personas/{invalid_id}` → 404
- [x] `GET /` → 200
- [x] `GET /health` → 200
- [x] 数据库文件 `data/app.db` 自动创建
- [x] 3 个角色（小暖/小锐/小默）人格定义完整、风格明显不同
- [x] 再次启动不重复插入数据

---

## Phase 2: Chat API + Prompt Builder

**目标：** SSE 流式聊天跑通，Prompt Pipeline 输出有角色感的回复

### 依赖图

```
Wave 1 (并行)        Wave 2 (串行)
PH2-001 ──┐
           ├──→ PH2-003
PH2-002 ──┘
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH2-001 | Chat Pydantic Schemas | 1 | ✅ DONE | DeepSeek |
| PH2-002 | Prompt Builder Service | 1 | ✅ DONE | DeepSeek |
| PH2-003 | Chat API Routes + SSE | 2 | ✅ DONE | DeepSeek |

---

## Wave 1（并行 — 2 Agent）

---

### TASK PH2-001：Chat Pydantic Schemas

```
TASK-ID: PH2-001
名称: Chat Pydantic Schemas
Wave: 1（与 PH2-002 并行）

目标: 定义聊天的请求/响应 Schema
---

允许修改文件:
- backend/schemas/chat.py    (修改，追加新 class)

禁止修改:
- backend/schemas/chat.py 以外的任何文件
- 已有的 PersonaResponse / PersonaListResponse

输入条件:
- Phase 1 完成，schemas/chat.py 已有 PersonaResponse

输出要求:
1. SessionCreate(BaseModel):
   - persona_id: str

2. SessionResponse(BaseModel):
   - session_id: str
   - persona_id: str
   - created_at: str

3. ChatRequest(BaseModel):
   - session_id: str
   - persona_id: str
   - message: str

4. ChatMessage(BaseModel):
   - role: str  (user / assistant / system)
   - content: str

完成标准:
- ✔ 所有 4 个 Schema 定义正确
- ✔ 不修改已有 PersonaResponse / PersonaListResponse
- ✔ 无语法错误
```

---

### TASK PH2-002：Prompt Builder Service

```
TASK-ID: PH2-002
名称: Prompt Builder Service
Wave: 1（与 PH2-001 并行）

目标: 实现 Prompt 构建器，将 Persona 设定 + 对话历史组装成 AI API 的 messages
---

允许修改文件:
- backend/services/prompt_builder.py    (新建)

禁止修改:
- backend/services/prompt_builder.py 以外的任何文件

输入条件:
- Phase 1 完成，PersonaResponse 可用
- Persona 有: name, personality, speaking_style, background_story, emotional_traits

输出要求:
1. build_system_prompt(persona: dict) -> str
   模板:
   "你是{name}。
   性格：{personality}
   说话风格：{speaking_style}
   背景：{background_story}
   情绪特质：{emotional_traits_json}
   ---
   请严格按照以上设定回复。不要跳出角色设定。"

2. build_messages(persona: dict, history: list[dict], user_message: str) -> list[dict]
   返回格式: [{"role": "system", "content": system_prompt}, ...history, {"role": "user", "content": user_message}]

完成标准:
- ✔ build_system_prompt 包含所有 persona 字段
- ✔ build_messages 返回完整的 messages 数组
- ✔ history 消息正确排列在 system 之后、user 之前
- ✔ 无语法错误
```

---

## Wave 2（串行 — PH2-001 + PH2-002 完成后启动）

---

### TASK PH2-003：Chat API Routes + SSE

```
TASK-ID: PH2-003
名称: Chat API Routes + SSE Stream
Wave: 2（依赖 PH2-001 + PH2-002）

目标: 实现 POST /api/v1/chat/session 和 POST /api/v1/chat/send (SSE)
---

允许修改文件:
- backend/api/chat.py    (修改，追加 chat routes)

禁止修改:
- backend/api/chat.py 以外的任何文件
- 已有的 persona routes (list_personas, get_persona)

输入条件:
- PH2-001 Chat schemas 已定义
- PH2-002 PromptBuilder 已实现
- config.py 有 AI_API_KEY, AI_BASE_URL, AI_MODEL

输出要求:
1. 内存会话存储: _sessions: dict[str, dict] = {}
   - key = session_id (str)
   - value = {"persona_id": str, "messages": list[dict]}

2. POST /api/v1/chat/session:
   - 接收 SessionCreate
   - 验证 persona 存在（调用 PersonaService.get_by_id）
   - 生成 session_id = str(uuid.uuid4())
   - 初始化空消息列表
   - 返回 {"success": true, "data": {"session_id": ..., "persona_id": ..., "created_at": ...}}

3. POST /api/v1/chat/send:
   - 接收 ChatRequest
   - 验证 session 存在，不存在返回 404
   - 调用 PromptBuilder.build_messages(persona_dict, history, user_message)
   - 使用 httpx.AsyncClient 流式请求 AI API（Gemini via OpenAI 兼容格式）
   - 请求 URL: f"{AI_BASE_URL}/v1/chat/completions"
   - 请求 Header: Authorization: Bearer {key}
   - 请求 Body: {"model": AI_MODEL, "max_tokens": 1024, "messages": messages, "stream": true}
   - 返回 StreamingResponse(content=stream_generator(), media_type="text/event-stream")
   - stream_generator 解析 OpenAI SSE 格式: choices[0].delta.content
   - 流结束后将 user message + AI reply 追加到 session messages

4. 新增 router 或复用已有 router

完成标准:
- ✔ POST /api/v1/chat/session 创建会话返回 session_id
- ✔ POST /api/v1/chat/send SSE 流式返回逐 token
- ✔ system_prompt 包含完整 Persona Block
- ✔ 不存在的 session_id 返回 404
- ✔ 不存在的 persona_id 返回 404
- ✔ 已有 persona routes 不受影响
- ✔ 无语法错误
```

---

## Phase 2 总验收标准

- [x] `POST /api/v1/chat/session` 创建会话成功
- [x] `POST /api/v1/chat/send` SSE 流式返回
- [x] system_prompt 包含 Persona Block
- [x] 不同角色回复风格明显不同
- [x] 流式输出不卡顿
- [x] 已有 persona API 不受影响

---

## Phase 3: Emotion System

**目标：** 情绪状态随对话动态变化，影响 Prompt

### 依赖图

```
Wave 1          Wave 2 (并行)            Wave 3
PH3-001 ──→ PH3-002 ──┐
             PH3-003 ──┴──→ PH3-004
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH3-001 | Emotion 数据模型 | 1 | ✅ DONE | DeepSeek |
| PH3-002 | Emotion Service | 2 | ✅ DONE | DeepSeek |
| PH3-003 | Prompt Builder Emotion Block | 2 | ✅ DONE | DeepSeek |
| PH3-004 | Emotion API + Chat 集成 | 3 | ✅ DONE | DeepSeek |

---

### TASK PH3-001：Emotion SQLAlchemy 模型

```
TASK-ID: PH3-001
Wave: 1

目标: 定义 Emotion ORM 模型，追踪情绪四维度变化
---

允许修改文件:
- backend/models/emotion.py     (新建)
- backend/models/__init__.py    (修改，导出 Emotion)

禁止修改: 以上两个文件之外的任何文件

输出要求:
1. Emotion(Base):
   - id: UUID, PK
   - session_id: str(36), index
   - favorability: int (0-100)
   - trust: int (0-100)
   - mood: str ("happy"/"neutral"/"sad"/"angry"/"anxious")
   - dependency: int (0-100)
   - trigger_message: str(500), nullable
   - created_at: datetime, default=lambda: datetime.now(timezone.utc)

2. __init__.py 导出 Emotion

完成标准:
- ✔ 字段类型正确，四维度完整
- ✔ session_id 有索引（方便查询最新情绪）
- ✔ 使用 timezone.utc（不用弃用的 utcnow）
- ✔ __init__.py 导出
```

---

### TASK PH3-002：EmotionService

```
TASK-ID: PH3-002
Wave: 2（依赖 PH3-001）

目标: 实现情绪分析业务逻辑
---

允许修改文件:
- backend/services/emotion_service.py    (新建)

禁止修改: 以上文件之外的任何文件

输出要求:
1. EmotionService(db_session):
   - async analyze_emotion(session_id, user_message, ai_reply) -> dict
     调用 AI API 分析四维度，返回 {favorability, trust, mood, dependency}
     AI prompt 要求输出 JSON
   - async get_current_state(session_id) -> dict | None
     返回最新一条 Emotion 记录
   - async get_history(session_id) -> list[dict]
     返回情绪变化时间线

完成标准:
- ✔ analyze_emotion 返回正确四维度值域
- ✔ get_current_state 无记录时返回 None
- ✔ get_history 按时间正序
```

---

### TASK PH3-003：Prompt Builder + Emotion Block

```
TASK-ID: PH3-003
Wave: 2（与 PH3-002 并行）

目标: system prompt 追加情绪状态信息
---

允许修改文件:
- backend/services/prompt_builder.py    (修改)

禁止修改: 以上文件之外的任何文件

输出要求:
1. build_system_prompt(persona, emotion_state=None):
   - 保留现有 Persona Block
   - emotion_state 非 None 时，追加:
     "当前用户情绪状态：好感度{favorability}、信任度{trust}、心情{mood}、依赖度{dependency}。请据此调整回复语气。"

2. build_messages(persona, history, user_message, emotion_state=None):
   - 内部调用 build_system_prompt 时传入 emotion_state

完成标准:
- ✔ emotion_state=None 时不追加 Emotion Block
- ✔ 不破坏已有 Persona Block
- ✔ 无语法错误
```

---

### TASK PH3-004：Emotion API + Chat 集成

```
TASK-ID: PH3-004
Wave: 3（依赖 PH3-002 + PH3-003）

目标: 暴露情绪 API，聊天中自动分析情绪
---

允许修改文件:
- backend/api/chat.py    (修改)

禁止修改: 以上文件之外的任何文件
❌ 禁止删除或修改已有路由 (list_personas, get_persona, create_chat_session, send_message)

输出要求:
1. GET /api/v1/emotion/{session_id}:
   - 调用 EmotionService.get_current_state()
   - 返回 {"success": true, "data": {...四维度...}}

2. GET /api/v1/emotion/{session_id}/history:
   - 调用 EmotionService.get_history()
   - 返回 {"success": true, "data": [...时间线...]}

3. POST /api/v1/chat/send 中追加:
   - AI 回复完成后调用 emotion_service.analyze_emotion()
   - 将结果存入 Emotion 表
   - 调用 build_messages 时传入当前 emotion_state

完成标准:
- ✔ /api/v1/emotion/{id} 返回当前情绪
- ✔ 不存在的 session 返回 404
- ✔ 聊天自动触发情绪分析
- ✔ 已有路由不受影响
```

---

## Phase 3 验收标准

- [ ] `GET /api/v1/emotion/{session_id}` 返回四维度
- [ ] 聊天后情绪状态自动更新
- [ ] `GET /api/v1/emotion/{session_id}/history` 返回变化时间线
- [ ] 不同情绪状态下 AI 回复语气不同
- [ ] 已有 API 不受影响

---

## Phase 4: Long-term Memory

### 依赖图

```
Wave 1 → Wave 2 → Wave 3
PH4-001 → PH4-002 → PH4-003
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH4-001 | Memory 数据模型 | 1 | ✅ DONE | DeepSeek |
| PH4-002 | Memory Service | 2 | ✅ DONE | DeepSeek |
| PH4-003 | Memory API + 对话提取 | 3 | ✅ DONE | DeepSeek |

---

### TASK PH4-001：Memory SQLAlchemy 模型

```
TASK-ID: PH4-001
Wave: 1

目标: 定义 Memory ORM 模型，支持多类型记忆持久化
---

允许修改文件:
- backend/models/memory.py      (新建)
- backend/models/__init__.py    (修改)

禁止修改: 以上两个文件之外的任何文件

输出要求:
1. Memory(Base):
   - id: UUID, PK
   - session_id: str(36), index
   - user_id: str(50), nullable (预留多用户)
   - type: str(20) (user_info / preference / event / emotion / summary)
   - content: str(1000)
   - importance: int (1-5), default=3
   - embedding: LargeBinary, nullable (Phase 5 填充)
   - created_at: datetime, timezone.utc

2. __init__.py 导出 Memory

完成标准:
- ✔ type 字段支持所有 5 种类型
- ✔ embedding 字段 nullable
- ✔ 使用 timezone.utc
```

---

### TASK PH4-002：MemoryService

```
TASK-ID: PH4-002
Wave: 2（依赖 PH4-001）

目标: 实现记忆提取和存储
---

允许修改文件:
- backend/services/memory_service.py    (新建)

禁止修改: 以上文件之外的任何文件

输出要求:
1. MemoryService(db_session):
   - async extract_from_conversation(user_message, ai_reply) -> list[dict]
     调用 AI 提取可存储信息
     prompt: "从对话中提取值得长期记住的信息。输出 JSON 数组 [{type, content, importance}]"
   - async add_memory(session_id, type, content, importance=3) -> Memory
   - async get_by_session(session_id) -> list[Memory]
   - async get_by_type(session_id, type) -> list[Memory]

完成标准:
- ✔ extract 返回结构化信息列表
- ✔ add_memory 写入数据库并 commit
- ✔ get_by_type 正确过滤
```

---

### TASK PH4-003：Memory API + Chat 集成

```
TASK-ID: PH4-003
Wave: 3（依赖 PH4-002）

目标: 暴露记忆 API，聊天中自动提取记忆
---

允许修改文件:
- backend/api/chat.py    (修改)

禁止修改: 以上文件之外的任何文件
❌ 禁止删除或修改已有路由

输出要求:
1. GET /api/v1/memories/{session_id}:
   - 调用 MemoryService.get_by_session()
   - 支持 ?type= 过滤参数

2. POST /api/v1/chat/send 中追加:
   - AI 回复完成后调用 memory_service.extract_from_conversation()
   - 提取结果逐条 add_memory 存储

完成标准:
- ✔ /api/v1/memories/{id} 返回记忆列表
- ✔ ?type=preference 正确过滤
- ✔ 聊天自动提取并存储记忆
- ✔ 已有路由不受影响
```

---

## Phase 4 验收标准

- [ ] `GET /api/v1/memories/{session_id}` 返回记忆
- [ ] 记忆按 type 正确分类
- [ ] 聊天后自动提取用户信息并存储
- [ ] 退出重进后记忆保留
- [ ] 已有 API 不受影响

---

## Phase 5: Lightweight RAG

### 依赖图

```
Wave 1          Wave 2 (并行)
PH5-001 ──→ PH5-002 ──┐
             PH5-003 ──┘
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH5-001 | RAG Service | 1 | ✅ DONE | DeepSeek |
| PH5-002 | Memory embedding 生成 | 2 | ✅ DONE | DeepSeek |
| PH5-003 | Prompt Builder Memory Block | 2 | ✅ DONE | DeepSeek |

---

### TASK PH5-001：RAGService

```
TASK-ID: PH5-001
Wave: 1

目标: 实现 sentence-transformers embedding + 余弦相似度召回
---

允许修改文件:
- backend/services/rag_service.py    (新建)

禁止修改: 以上文件之外的任何文件

输出要求:
1. RAGService:
   - __init__(): 加载 all-MiniLM-L6-v2，首次运行自动下载
   - encode(text: str) -> list[float]: 生成 384 维 embedding
   - search(query: str, memories: list[Memory], top_k=5, threshold=0.3) -> list[Memory]
     余弦相似度排序，低于 threshold 的过滤

重要:
- 模型加载失败 → 打印清晰错误信息
- 空文本 → 返回零向量

完成标准:
- ✔ encode 返回 384 维向量
- ✔ search 按相似度降序返回
- ✔ threshold=0.3 正确过滤
- ✔ 模型下载失败有明确提示
```

---

### TASK PH5-002：Memory Service + Embedding

```
TASK-ID: PH5-002
Wave: 2（依赖 PH5-001）

目标: 记忆存储时自动生成 embedding
---

允许修改文件:
- backend/services/memory_service.py    (修改)

禁止修改: 以上文件之外的任何文件

输出要求:
1. 修改 add_memory():
   - 创建 Memory 对象后调用 rag_service.encode(content)
   - 将 embedding 存入 memory.embedding 字段
   - 其他方法不变

2. 新增方法:
   - async search_memories(session_id, query, top_k=5) -> list[Memory]
     调用 rag_service.search()

完成标准:
- ✔ add_memory 自动填充 embedding
- ✔ search_memories 返回相关记忆
- ✔ 已有方法不受影响
```

---

### TASK PH5-003：Prompt Builder + Memory Block

```
TASK-ID: PH5-003
Wave: 2（与 PH5-002 并行）

目标: system prompt 注入 RAG 召回的相关记忆
---

允许修改文件:
- backend/services/prompt_builder.py    (修改)

禁止修改: 以上文件之外的任何文件

输出要求:
1. build_system_prompt(persona, emotion_state=None, memory_context=None):
   - 保留 Persona Block
   - 保留 Emotion Block（当 emotion_state 非 None）
   - memory_context 非 None 时追加:
     "相关记忆：\n{memory_context}\n请自然融入回复中，不要刻意列举。"

2. build_messages() 同步增加 memory_context 参数

完成标准:
- ✔ memory_context=None 时不追加
- ✔ 不破坏 Persona + Emotion Block
- ✔ 无语法错误
```

---

## Phase 5 验收标准

- [ ] sentence-transformers 加载成功
- [ ] 新记忆自动生成 embedding
- [ ] 用户消息触发相似记忆召回
- [ ] 召回记忆注入 system prompt
- [ ] Top-K=5, threshold=0.3 生效

---

## Phase 6: Conversation Summary

### 依赖图

```
Wave 1 → Wave 2
PH6-001 → PH6-002
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH6-001 | Summary Service | 1 | ✅ DONE | DeepSeek |
| PH6-002 | Chat 集成 + 摘要触发 | 2 | ✅ DONE | DeepSeek |

---

### TASK PH6-001：SummaryService

```
TASK-ID: PH6-001
Wave: 1

目标: 对话超过 20 轮自动生成摘要
---

允许修改文件:
- backend/services/summary_service.py    (新建)

禁止修改: 以上文件之外的任何文件

输出要求:
1. SummaryService(db_session):
   - async should_summarize(session_id) -> bool
     检查 session 对话轮数 > SUMMARY_TRIGGER_ROUNDS (20)
   - async generate_summary(messages: list[dict]) -> str
     调用 AI 生成摘要
     prompt: "总结以下对话关键信息：用户近况、情绪变化、关系变化。保留重要细节。"
   - async apply_summary(session_id, summary)
     将旧消息标记为 archived，新对话以摘要开头

完成标准:
- ✔ 20 轮后 should_summarize 返回 True
- ✔ generate_summary 返回中文摘要
- ✔ apply_summary 后对话保持连贯
```

---

### TASK PH6-002：Chat 集成 + 摘要触发

```
TASK-ID: PH6-002
Wave: 2（依赖 PH6-001）

目标: 聊天中自动触发摘要
---

允许修改文件:
- backend/api/chat.py    (修改)

禁止修改: 以上文件之外的任何文件
❌ 禁止删除或修改已有路由

输出要求:
1. POST /api/v1/chat/send 中追加:
   - 回复前检查 should_summarize()
   - 需要时调用 generate_summary + apply_summary
   - 摘要存入 memory (type="summary")

完成标准:
- ✔ 20 轮后自动触发摘要
- ✔ 摘要内容覆盖用户近况/情绪/关系
- ✔ 摘要后对话仍连贯
- ✔ 已有路由不受影响
```

---

## Phase 6 验收标准

- [ ] 20 轮对话自动触发摘要
- [ ] 摘要存入 memory
- [ ] 摘要后对话连贯

---

## Phase 7: Product Chat UI

### 依赖图

```
Wave 1        Wave 2 (并行)        Wave 3      Wave 4
PH7-001 ──→ PH7-002 ──┐
             PH7-003 ──┴──→ PH7-004 ──→ PH7-005
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH7-001 | Next.js 项目初始化 | 1 | ✅ DONE | DeepSeek |
| PH7-002 | 角色选择页 | 2 | ✅ DONE | DeepSeek |
| PH7-003 | 聊天 UI 组件 | 2 | ✅ DONE | DeepSeek |
| PH7-004 | SSE 集成 + 情绪面板 | 3 | ✅ DONE | DeepSeek |
| PH7-005 | 响应式 + 打磨 | 4 | ✅ DONE | DeepSeek |

---

### TASK PH7-001：Next.js 项目初始化

```
TASK-ID: PH7-001
Wave: 1

目标: 创建 Next.js + TailwindCSS + shadcn/ui 前端项目骨架
---

允许操作:
- 创建 frontend/ 目录和 Next.js 项目
- 安装依赖
- 创建 API client 封装

输出要求:
1. npx create-next-app@latest frontend --typescript --tailwind --app --src-dir
2. 安装 shadcn/ui: npx shadcn@latest init
3. API client: src/lib/api.ts
   - const API_BASE = "http://localhost:8000/api/v1"
   - fetchPersonas(), createSession(), sendMessage() 等封装
4. CSS 变量: 温暖柔和配色（暖橙/奶油/浅棕）
5. 首页重定向到 /personas

完成标准:
- ✔ npm run dev 启动无报错
- ✔ shadcn/ui 组件可用
- ✔ API client 编译通过
```

---

### TASK PH7-002：角色选择页

```
TASK-ID: PH7-002
Wave: 2（依赖 PH7-001）

目标: 角色选择页，3 个角色卡片展示
---

允许操作:
- 创建 frontend/src/app/personas/ 页面
- 创建角色卡片组件

输出要求:
1. /personas 页面加载时调用 fetchPersonas()
2. 3 张卡片（小暖/小锐/小默），每张显示:
   - 名字 + 一句话性格描述
   - 选中按钮
3. 点击角色 → 跳转 /chat?persona_id={id}
4. Loading / Error 状态处理
5. shadcn/ui Card 组件

完成标准:
- ✔ 页面加载显示 3 个角色
- ✔ 点击跳转携带 persona_id
- ✔ API 失败时显示错误提示
```

---

### TASK PH7-003：聊天 UI 组件

```
TASK-ID: PH7-003
Wave: 2（与 PH7-002 并行）

目标: 聊天气泡、输入框、typing 动画
---

允许操作:
- 创建 frontend/src/app/chat/ 页面
- 创建聊天相关组件

输出要求:
1. /chat 页面（接收 persona_id query param）
2. ChatBubble 组件: 左 AI（浅色底）+ 右用户（主色底）
3. MessageInput 组件: 输入框 + 发送按钮
4. TypingIndicator 组件: 三个点跳动动画
5. 消息列表自动滚动到底部

完成标准:
- ✔ 气泡左右对齐
- ✔ typing 动画可见
- ✔ 输入框聚焦可用
- ✔ 自动滚动
```

---

### TASK PH7-004：SSE 集成 + 情绪面板

```
TASK-ID: PH7-004
Wave: 3（依赖 PH7-003）

目标: 接入 SSE 流式聊天 + 情绪状态实时展示
---

允许操作:
- 修改 chat 页面
- 创建 EmotionPanel 组件

输出要求:
1. 页面初始化:
   - 调用 createSession(persona_id) 创建 session
   - 开始对话
2. 发送消息:
   - 调用 sendMessage SSE 接口
   - 逐字显示 AI 回复
   - 发送中禁用输入框
3. EmotionPanel 组件:
   - 定时 / 每次回复后刷新 GET /api/v1/emotion/{session_id}
   - 显示四维度（好感/信任/心情/依赖）
   - 使用进度条或表情图标

完成标准:
- ✔ SSE 逐字显示
- ✔ 情绪四维度可见
- ✔ 发送中按钮禁用
- ✔ SSE 中断时显示错误
```

---

### TASK PH7-005：响应式 + 打磨

```
TASK-ID: PH7-005
Wave: 4（依赖 PH7-004）

目标: 移动端适配 + 状态覆盖
---

允许操作:
- 修改现有页面和组件

输出要求:
1. 响应式布局: 移动端（<768px）全屏聊天，桌面端居中 max-w-2xl
2. Loading 状态: 页面加载 spinner
3. Empty 状态: 无消息时显示问候语
4. Error 状态: API 失败 toast 提示
5. 过渡动画: 气泡出现动画、页面切换过渡

完成标准:
- ✔ 手机/桌面均可正常使用
- ✔ 所有状态有对应 UI
- ✔ 动画流畅
```

---

## Phase 7 验收标准

- [ ] 角色选择页 3 张卡片可选
- [ ] 聊天气泡 + typing 动画
- [ ] SSE 流式逐字显示
- [ ] 情绪状态面板实时更新
- [ ] 响应式布局
- [ ] Loading/Empty/Error 状态覆盖

---

## Phase 8: 集成调试 + Demo 打磨

### 状态一览

| TASK-ID | 描述 | 状态 | 分配 |
|---------|------|:----:|:----:|
| PH8-001 | 全链路走通 | 1 | ✅ DONE | DeepSeek |
| PH8-002 | Bug 修复 | 2 | ✅ DONE | DeepSeek |
| PH8-003 | 边界情况处理 | 3 | ✅ DONE | DeepSeek |
| PH8-004 | 最终打磨 | 4 | ✅ DONE | DeepSeek |

---

### TASK PH8-001：全链路走通

```
目标: 验证完整用户流程
测试路径:
1. 启动后端 → 角色列表 API 返回 3 个角色
2. 前端选择"小暖" → 创建 session → 发送消息
3. SSE 流式显示"小暖"风格回复（温柔语气）
4. 切换"小锐" → 回复风格变直接利落
5. 多轮对话 → 情绪状态变化 → 情绪面板更新
6. 对话中提及个人信息 → Memory API 可查到
7. 再次发送消息 → RAG 召回相关记忆
8. 20+ 轮对话 → 自动触发摘要

完成标准: 以上 8 步全部通过
```

---

### TASK PH8-002：Bug 修复

```
目标: 修复走通测试中发现的问题
- 每个 bug 写一条 ISSUES_LOG
- 修复后打 ✅
- 严格按文件范围修复，不扩大
```

---

### TASK PH8-003：边界情况处理

```
目标: 覆盖异常场景
- 空消息提交 → 前端拦截 + 后端 422
- 超长消息 (>2000字) → 截断 + 警告
- AI API 超时 → 前端显示"正在思考中..."
- 网络断开 → SSE 重连提示
- persona_id 无效 → 404 页面
- session_id 无效 → 返回角色选择页
```

---

### TASK PH8-004：最终打磨

```
目标: Demo 演示就绪
- 首次加载问候语个性化（"你好，我是小暖~"）
- 页面标题 + favicon
- 聊天滚动平滑
- 消息时间戳显示
- README 更新
```

---

## Phase 8 验收标准

- [ ] 全链路 8 步通过
- [ ] 边界情况有对应处理
- [ ] Demo 演示流畅
- [ ] 所有 ISSUES_LOG 已修复或标记 WONT_FIX

---

## Bug Fix Wave 2026-05-27

**目标：** 修复用户在 `docs/BUG_REPORTS.md` 中记录的当前 4 个问题，并验证受影响链路不回归。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| BUG-FIX-001 | 修复聊天卡死与发送后不可恢复问题 | BUG-001 | ✅ DONE | DeepSeek |
| BUG-FIX-002 | 修复聊天页流式感知、禁用态按钮与返回入口 | BUG-002, BUG-003, BUG-004 | ✅ DONE | DeepSeek |

### TASK BUG-FIX-001：修复 BUG-001 — 聊天卡死与发送后不可恢复

```
TASK-ID: BUG-FIX-001
名称: 修复 BUG-001 — 聊天卡死与发送后不可恢复
关联: docs/BUG_REPORTS.md / BUG-001

目标:
- 修复聊天在首轮后或多轮发送时 AI 不再回复的问题
- 确保前端输入框、按钮和本地消息状态能在成功/失败/中断后恢复
- 验证聊天主链路不会因 SSE 完成信号、异常响应或空回复而卡死

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\backend\api\chat.py

禁止修改:
- E:\ai-companion\frontend\src\app\chat\page.tsx
- 其他 backend/services/、backend/models/、frontend/ 代码

验收标准:
- ✔ 连续发送两条及以上消息，后续请求仍能收到回复
- ✔ 任一失败路径下输入框都会重新可用
- ✔ 无论 AI 返回空片段、错误片段或 done 片段，前端都不会永久 disabled
- ✔ 会话消息不会因失败回调被错误回滚
```

### TASK BUG-FIX-002：修复 BUG-002 / BUG-003 / BUG-004 — 聊天页交互与可用性

```
TASK-ID: BUG-FIX-002
名称: 修复 BUG-002 / BUG-003 / BUG-004 — 聊天页交互与可用性
关联: docs/BUG_REPORTS.md / BUG-002, BUG-003, BUG-004

目标:
- 提升用户对 SSE 流式输出的可感知性
- 确认后端确实按流式发送，前端确实按增量消费
- 在不破坏现有聊天 API 的前提下，保证逐字/逐段输出明显可见
- 将发送按钮禁用态调整为明显的纯灰色视觉
- 在聊天页提供稳定、清晰的返回角色选择入口

允许修改文件:
- E:\ai-companion\frontend\src\app\chat\page.tsx

禁止修改:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\backend\api\chat.py
- 其他 frontend/、backend/ 代码

验收标准:
- ✔ 发送消息后用户能明确观察到回复逐步出现
- ✔ typing indicator 与流式展示衔接自然
- ✔ 回复结束后不会额外重复渲染整段消息
- ✔ 不破坏现有发送、自动滚动与错误提示逻辑
- ✔ 输入框为空或发送中时，发送按钮呈纯灰色禁用态
- ✔ 聊天页顶部始终可见返回 `/personas` 的入口
- ✔ 不影响现有聊天页布局、响应式和交互
```

---

## Frontend Integration Wave 2026-05-27

**目标：** 把后端已完成的记忆、情绪历史与摘要能力接入 `frontend/` 聊天页，形成可见、可验收的产品功能。

### 状态一览

| TASK-ID | 描述 | 关联功能 | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| FE-INTEGRATION-001 | 扩展前端 API 客户端，接入 memories / emotion history | 7.3, 7.7, 9.1, 9.2 | ❌ FAILED | DeepSeek |
| FE-INTEGRATION-002 | 新建聊天洞察组件，展示记忆列表与情绪时间线 | 6.1, 7.4, 7.5, 9.2 | ❌ FAILED | DeepSeek |
| FE-INTEGRATION-003 | 在聊天页集成洞察面板与摘要入口状态 | 6.1, 7.3, 9.1, 10.3 | ❌ FAILED | DeepSeek |

### TASK FE-INTEGRATION-001：前端 API 客户端扩展

```
TASK-ID: FE-INTEGRATION-001
名称: 前端 API 客户端扩展（memories / emotion history）
关联: USER_FEATURE_CHECKLIST 7.3, 7.7, 9.1, 9.2

目标:
- 在前端 API 层补齐记忆与情绪历史请求能力
- 为聊天页后续接入提供清晰、稳定的类型定义

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts

禁止修改:
- E:\ai-companion\frontend\src\app\chat\page.tsx
- E:\ai-companion\frontend\src\components\**
- backend/**

输出要求:
1. 新增 MemoryItem / EmotionHistoryItem 等前端类型
2. 新增 fetchMemories(sessionId: string, type?: string)
3. 新增 fetchEmotionHistory(sessionId: string)
4. 处理空数据与非 200 错误，返回结构稳定
5. 不破坏已有 fetchPersonas / createSession / fetchEmotion / sendMessage

完成标准:
- ✔ TypeScript 编译通过
- ✔ 能请求 `GET /api/v1/memories/{session_id}` 与 `GET /api/v1/emotion/{session_id}/history`
- ✔ 保持 API_BASE 与现有错误处理风格一致
```

### TASK FE-INTEGRATION-002：聊天洞察组件

```
TASK-ID: FE-INTEGRATION-002
名称: 聊天洞察组件（记忆列表 + 情绪时间线）
关联: USER_FEATURE_CHECKLIST 6.1, 7.4, 7.5, 9.2

目标:
- 创建可复用的前端组件，用于展示长期记忆与情绪变化
- UI 风格保持当前暖色系产品语言，不做泛化后台表格

允许修改文件:
- E:\ai-companion\frontend\src\components\chat\insight-panel.tsx    (新建)
- E:\ai-companion\frontend\src\components\chat\emotion-history.tsx  (新建，如需)
- E:\ai-companion\frontend\src\components\chat\memory-list.tsx      (新建，如需)

禁止修改:
- E:\ai-companion\frontend\src\app\chat\page.tsx
- E:\ai-companion\frontend\src\lib\api.ts
- backend/**

输出要求:
1. 展示最近记忆列表，至少显示 type / content / importance
2. 展示情绪历史时间线，至少显示 favorability / trust / mood / dependency
3. 包含 loading / empty / error 三种 UI 状态
4. 组件 props 清晰，可直接被 chat page 集成

完成标准:
- ✔ 组件独立编译通过
- ✔ 空数据时不白屏
- ✔ 视觉上适配移动端和桌面端
```

### TASK FE-INTEGRATION-003：聊天页接入洞察面板

```
TASK-ID: FE-INTEGRATION-003
名称: 聊天页接入记忆 / 情绪历史 / 摘要状态
关联: USER_FEATURE_CHECKLIST 6.1, 7.3, 9.1, 10.3

目标:
- 在聊天页中接入新的前端 API 和洞察组件
- 让用户在单页内可看到当前情绪、历史情绪、长期记忆与 summary 相关结果

允许修改文件:
- E:\ai-companion\frontend\src\app\chat\page.tsx

禁止修改:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\components\chat\**
- backend/**

输入条件:
- FE-INTEGRATION-001 与 FE-INTEGRATION-002 完成后可直接消费其导出

输出要求:
1. 在 session 建立后拉取 memories 与 emotion history
2. 在每轮回复完成后刷新 memories / emotion history
3. 在聊天页中接入洞察组件，桌面端与移动端均可访问
4. 若存在 type=`summary` 记忆，要有自然的摘要状态展示
5. 不破坏现有聊天、流式、返回按钮、错误横幅

完成标准:
- ✔ 页面可看到记忆列表与情绪历史
- ✔ 对话后数据会刷新
- ✔ summary 存在时可见
- ✔ Next.js 构建通过
```

### 返工结论（Review 失败）

- FE-INTEGRATION-001 失败原因：`fetchMemories()` 与 `fetchEmotionHistory()` 吞掉非 200 错误并返回空数组，导致页面无法进入 error 状态。
- FE-INTEGRATION-002 失败原因：组件错误态在真实链路中不可达；桌面侧栏双列布局过窄；记忆类型标签映射不完整。
- FE-INTEGRATION-003 失败原因：当前前后端组合下 chat session 主链路返回 `Session not found`，导致洞察刷新和 summary 真实验收无法成立。

---

## Frontend Integration Fix Wave 2026-05-27

**目标：** 修复前端集成审查发现的问题，并恢复聊天主链路后的真实洞察验收。

### 状态一览

| TASK-ID | 描述 | 关联 Issue | 状态 | 分配 |
|---------|------|------------|:----:|:----:|
| FE-FIX-001 | 修复前端 API 错误吞掉问题 | ISSUE-007 | ✅ DONE | DeepSeek |
| FE-FIX-002 | 修复洞察组件响应式与标签映射 | ISSUE-008 | ✅ DONE | DeepSeek |
| FE-FIX-003 | 修复 chat session 丢失导致的主链路回归 | ISSUE-009 | ✅ DONE | DeepSeek |

### TASK FE-FIX-001：前端 API 错误透传

```
TASK-ID: FE-FIX-001
名称: 修复 memories / emotion history API 错误被吞掉的问题
关联: ISSUE-007

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts

禁止修改:
- E:\ai-companion\frontend\src\components\chat\**
- E:\ai-companion\frontend\src\app\chat\page.tsx
- backend/**

目标:
- 让 `fetchMemories()` 与 `fetchEmotionHistory()` 在非 200 / 无效响应时 reject，而不是伪装成空数组
- 保持成功路径与类型定义稳定

完成标准:
- ✔ 页面能区分 empty 与 error
- ✔ 失败时组件 error 态可达
- ✔ 不破坏现有成功路径
```

### TASK FE-FIX-002：洞察组件 UI 返工

```
TASK-ID: FE-FIX-002
名称: 修复洞察组件响应式布局与记忆标签映射
关联: ISSUE-008

允许修改文件:
- E:\ai-companion\frontend\src\components\chat\insight-panel.tsx
- E:\ai-companion\frontend\src\components\chat\emotion-history.tsx
- E:\ai-companion\frontend\src\components\chat\memory-list.tsx

禁止修改:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\app\chat\page.tsx
- backend/**

目标:
- 修复桌面侧栏内组件过窄双列问题
- 补齐 `user_info` / `emotion` 等记忆类型标签映射
- 保持 loading / empty / error 三态完整

完成标准:
- ✔ 侧栏宽度下仍可读
- ✔ 标签展示不退化为原始枚举
- ✔ 浏览器验收通过
```

### TASK FE-FIX-003：chat session 主链路修复

```
TASK-ID: FE-FIX-003
名称: 修复 chat session 创建后立即丢失的问题
关联: ISSUE-009

允许修改文件:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\backend\main.py

禁止修改:
- backend/services/**
- backend/models/**
- frontend/**
- frontend/src/components/chat/**

目标:
- 修复 `POST /chat/session` 成功后，`POST /chat/send` 立即返回 `Session not found` 的回归
- 确保 emotion / history / memories 相关接口与同一 session 一致可用

完成标准:
- ✔ 创建 session 后发送消息返回正常
- ✔ `GET /emotion/{session_id}` 与 `/history` 不再错误返回 session not found
- ✔ 聊天主链路恢复后，前端洞察数据能真实刷新
```

### Review 结果（2026-05-27 19:46 Wave）

- FE-FIX-001：三轮审查通过，错误透传与成功路径稳定性已验收。
- FE-FIX-002：三轮审查通过，桌面/移动端洞察组件与三态 UI 已验收。
- FE-FIX-003：初次审查被 `ISSUE-010` 阻断；在 `FE-FIX-004` 修复浏览器 E2E 环境后，重新审查三轮通过。

---

## Browser E2E Unblock Wave 2026-05-27

**目标：** 修复前端开发环境在 `127.0.0.1:3000` 下的资源拦截问题，恢复 `/personas -> /chat` 浏览器验收闭环，并为 FE-FIX-003 重新验收创造条件。

### 状态一览

| TASK-ID | 描述 | 关联 Issue | 状态 | 分配 |
|---------|------|------------|:----:|:----:|
| FE-FIX-004 | 修复 Next.js dev allowedDevOrigins，解除 127.0.0.1 E2E 阻断 | ISSUE-010 | ✅ DONE | DeepSeek |
| FE-FIX-IDLE-001 | 闲置 Agent | - | ⬜ TODO | DeepSeek |
| FE-FIX-IDLE-002 | 闲置 Agent | - | ⬜ TODO | DeepSeek |

### TASK FE-FIX-004：修复 127.0.0.1 开发资源拦截

```
TASK-ID: FE-FIX-004
名称: 修复 Next.js allowedDevOrigins，解除浏览器 E2E 阻断
关联: ISSUE-010

允许修改文件:
- E:\ai-companion\frontend\next.config.ts

禁止修改:
- E:\ai-companion\frontend\src\**
- backend/**
- docs/**

目标:
- 修复 `http://127.0.0.1:3000/personas` 在浏览器中因 Next.js dev 资源被拦截而停留 spinner 的问题
- 允许浏览器从 `127.0.0.1` 正常加载 HMR / 字体等开发资源
- 不破坏现有 `/api/:path* -> http://localhost:8000/api/v1/:path*` rewrite

完成标准:
- ✔ `http://127.0.0.1:3000/personas` 不再卡在 loading spinner
- ✔ 浏览器能发起角色列表请求并显示 3 个角色卡片
- ✔ 不破坏现有 dev server 启动
```

### Browser E2E Unblock 结果（2026-05-27 20:36）

- FE-FIX-004：三轮审查通过，`127.0.0.1` 下 Next.js dev 资源不再被拦截，`/personas` 页面与 `/api` rewrite 均通过验证。
- FE-FIX-003：在 FE-FIX-004 落地后重新执行三轮审查，`/personas -> /chat -> create session -> send message` 浏览器链路通过，不再出现 `Session not found`。

---

## Phase 9: Voice System

**目标：** 打通 `STT + TTS` 语音闭环，同时保持现有文本聊天链路稳定可用。

### 依赖图

```
Wave 1 (并行)                  Wave 2 (并行)          Review
PH9-001 ─┐
PH9-002 ─┼──→ PH9-004 ─┐
PH9-003 ─┘             ├──→ PH9 Review Round
                        PH9-005 ─┘
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH9-001 | 语音配置与 Schema | 1 | ✅ DONE | DeepSeek |
| PH9-002 | VoiceService 实现 | 1 | ✅ DONE | DeepSeek |
| PH9-003 | 前端语音 API Client | 1 | ✅ DONE | DeepSeek |
| PH9-004 | 语音后端路由接入 | 2 | ✅ DONE | DeepSeek |
| PH9-005 | 聊天页录音与播放 UI | 2 | ✅ DONE | DeepSeek |

### Wave 1（并行 — 3 Agent）

### TASK PH9-001：语音配置与 Schema

```
TASK-ID: PH9-001
名称: 语音配置与 Schema
Wave: 1（与 PH9-002、PH9-003 并行）

目标:
- 为语音功能补齐后端配置项与接口请求/响应 Schema
- 不触碰语音业务实现与聊天 UI

允许修改文件:
- E:\ai-companion\backend\config.py
- E:\ai-companion\backend\schemas\chat.py

禁止修改:
- E:\ai-companion\backend\services\voice_service.py
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

输出要求:
1. 新增配置项:
   - VOICE_ENABLED
   - VOICE_STT_MODEL
   - VOICE_TTS_MODEL
   - VOICE_TTS_VOICE
   - VOICE_MAX_UPLOAD_MB
2. 在 schemas 中新增语音接口所需 model:
   - VoiceHealthResponse
   - VoiceTranscriptionResponse
   - VoiceSynthesisRequest
3. 保持现有 chat / persona schema 不回归

完成标准:
- ✔ 配置项有合理默认值
- ✔ Schema 可直接供路由层使用
- ✔ 不破坏现有导入与类型检查
```

### TASK PH9-002：VoiceService 实现

```
TASK-ID: PH9-002
名称: VoiceService 实现
Wave: 1（与 PH9-001、PH9-003 并行）

目标:
- 将 voice_service.py 从 stub 升级为真实 STT / TTS 服务
- 默认复用现有 OpenAI-compatible provider

允许修改文件:
- E:\ai-companion\backend\services\voice_service.py

禁止修改:
- E:\ai-companion\backend\config.py
- E:\ai-companion\backend\schemas\chat.py
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

输出要求:
1. speech_to_text(audio_bytes, mime_type) 调用音频转写端点
2. text_to_speech(text, voice) 调用语音合成端点
3. is_available() 基于配置和 provider 可用性返回结果
4. 对 provider 异常给出明确错误，不吞掉原因

完成标准:
- ✔ STT 返回文本
- ✔ TTS 返回音频字节
- ✔ provider 不可用时能清晰失败
- ✔ 仍保持独立服务层，不直接写路由代码
```

### TASK PH9-003：前端语音 API Client

```
TASK-ID: PH9-003
名称: 前端语音 API Client
Wave: 1（与 PH9-001、PH9-002 并行）

目标:
- 为聊天页补齐语音相关 API 封装
- 不改聊天页面本身

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts

禁止修改:
- E:\ai-companion\frontend\src\app\chat\page.tsx
- E:\ai-companion\frontend\src\components\**
- E:\ai-companion\backend\**

输出要求:
1. 新增 transcribeAudio(blob/file)
2. 新增 synthesizeSpeech(text, sessionId, personaId)
3. 与现有 API_BASE / 错误处理风格保持一致
4. 不破坏 fetchPersonas / createSession / sendMessage / memories / emotion 相关接口

完成标准:
- ✔ 语音 API 可被聊天页直接调用
- ✔ 错误会 reject，供 UI 进入 error 态
- ✔ TypeScript 编译通过
```

### Wave 2（并行 — Wave 1 完成后启动）

### TASK PH9-004：语音后端路由接入

```
TASK-ID: PH9-004
名称: 语音后端路由接入
Wave: 2（依赖 PH9-001 + PH9-002）

目标:
- 在现有 chat API 中新增 voice health / stt / tts 接口
- 保持已有 persona / chat / emotion / memories 路由不回归

允许修改文件:
- E:\ai-companion\backend\api\chat.py

禁止修改:
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\backend\services\emotion_service.py
- E:\ai-companion\frontend\**

输出要求:
1. GET /api/v1/voice/health
2. POST /api/v1/voice/stt
3. POST /api/v1/voice/tts
4. provider 不可用时返回明确错误且不影响文本聊天接口

完成标准:
- ✔ 3 个接口响应格式稳定
- ✔ STT 支持 multipart/form-data 音频上传
- ✔ TTS 返回可播放音频响应
- ✔ 已有 API 不回归
```

### TASK PH9-005：聊天页录音与播放 UI

```
TASK-ID: PH9-005
名称: 聊天页录音与播放 UI
Wave: 2（依赖 PH9-003 + PH9-004）

目标:
- 在聊天页接入录音、转写回填与回复语音播放
- 文本聊天主链路保持不变

允许修改文件:
- E:\ai-companion\frontend\src\app\chat\page.tsx

禁止修改:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\components\**
- E:\ai-companion\backend\**

输出要求:
1. 使用浏览器录音能力采集音频
2. 调用 transcribeAudio 后将文字回填输入框
3. 为 AI 回复增加播放语音入口
4. 麦克风拒权、浏览器不支持、provider 异常时只提示错误，不阻断文本聊天

完成标准:
- ✔ 用户可录音转文字
- ✔ 用户可播放 AI 回复语音
- ✔ 语音失败时文本输入与 SSE 仍可继续使用
- ✔ 移动端与桌面端均可操作
```

### Review Round（Wave 2 完成后启动）

- 合并执行静态审查、运行时验证、浏览器 E2E
- 重点验收：
  - `GET /api/v1/voice/health` 正常返回
  - `POST /api/v1/voice/stt` 可将录音转为文本
  - `POST /api/v1/voice/tts` 可返回可播放音频
  - 聊天页可录音、回填文本、发送消息、播放回复语音
  - 麦克风拒权或 provider 异常时不破坏文本聊天
  - 现有 SSE、情绪、记忆、摘要链路不回归

### Phase 9 验收标准

- [x] `GET /api/v1/voice/health` 正常返回可用状态
- [x] `POST /api/v1/voice/stt` 可将录音转为文本
- [x] `POST /api/v1/voice/tts` 可返回可播放音频
- [x] 聊天页可录音、回填文本、发送消息、播放回复语音
- [x] 麦克风拒权或 provider 异常时不破坏文本聊天
- [x] 现有 SSE、情绪、记忆、摘要链路不回归

### Phase 9 验收结论（2026-05-28）

- 运行时验收通过：`/voice/health` 返回 `200`，`/voice/tts` 返回 `audio/mpeg`，`/voice/stt` 返回转写文本。
- 文本聊天回归通过：`/chat/session` 与 `/chat/send` 已在拆分 provider 后恢复正常，SSE 流式返回稳定。
- 浏览器链路通过：`/personas -> /chat -> 发送消息 -> 播放语音` 已在页面上验证，“播放语音”按钮会进入 `停止播放` 状态。
- 语音 provider 最终配置：聊天继续走 `api.xykjy.com`，语音独立走 `SiliconFlow`；`STT` 最终使用 `TeleAI/TeleSpeechASR`，`TTS` 使用 `FunAudioLLM/CosyVoice2-0.5B`。

### Phase 9 修复 TASK（Review 阻断）

| TASK-ID | 描述 | 关联 Issue | 状态 | 分配 |
|---------|------|------------|:----:|:----:|
| PH9-FIX-001 | 修复 `/voice/tts` 前后端契约不一致 | ISSUE-011 | ✅ DONE | DeepSeek |
| PH9-FIX-002 | 修复 `VOICE_ENABLED` 默认关闭导致语音链路被阻断 | ISSUE-012 | ✅ DONE | DeepSeek |
| PH9-FIX-003 | 拆分聊天与语音 provider 配置，避免语音接入回归聊天主链路 | ISSUE-014 | ✅ DONE | DeepSeek |

### TASK PH9-FIX-001：修复 `/voice/tts` 契约不一致

```
TASK-ID: PH9-FIX-001
名称: 修复 /voice/tts JSON / Form 契约不一致
关联: ISSUE-011

允许修改文件:
- E:\ai-companion\backend\api\chat.py

禁止修改:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\app\chat\page.tsx
- E:\ai-companion\backend\services\**
- docs/**

目标:
- 让 `POST /api/v1/voice/tts` 与当前前端 `synthesizeSpeech()` 的 JSON 请求体契约保持一致
- 不破坏已完成的 `/voice/health` 与 `/voice/stt`

完成标准:
- ✔ `POST /api/v1/voice/tts` 可直接接收 JSON body
- ✔ 失败时仍返回统一错误 envelope
- ✔ 不影响现有其他 `/api/v1` 路由
- ✔ 运行时验证通过后再进入 Review Round
```

### TASK PH9-FIX-002：修复 `VOICE_ENABLED` 默认关闭

```
TASK-ID: PH9-FIX-002
名称: 修复 VOICE_ENABLED 默认关闭导致的运行时阻断
关联: ISSUE-012

允许修改文件:
- E:\ai-companion\backend\config.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\backend\services\**
- E:\ai-companion\frontend\**
- docs/**

目标:
- 让当前已有 AI provider 配置的环境默认开启语音功能
- 保留通过 `.env` 显式关闭语音的能力

完成标准:
- ✔ `VOICE_ENABLED` 默认值调整为启用
- ✔ 仍支持通过环境变量显式关闭
- ✔ 修复后重启后端并重新验证 `/voice/health`
```

### TASK PH9-FIX-003：拆分聊天与语音 provider 配置

```
TASK-ID: PH9-FIX-003
名称: 拆分聊天与语音 provider 配置，避免回归文本聊天主链路
关联: ISSUE-014

允许修改文件:
- E:\ai-companion\backend\config.py
- E:\ai-companion\backend\services\voice_service.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**
- docs/**

目标:
- 保留现有聊天 provider 配置给 `/chat/send`
- 新增独立的语音 provider 配置给 `voice_service.py`
- 让语音走 `SiliconFlow`，聊天继续走原有网关，不互相影响

完成标准:
- ✔ 新增 `VOICE_API_KEY` / `VOICE_BASE_URL`（必要时保留 fallback）
- ✔ `voice_service.py` 仅消费语音专属配置
- ✔ 不破坏已有聊天接口调用配置
- ✔ 修复后重新验证聊天与语音链路都可用
```

---

## Phase 10: Advanced Memory

**目标：** 在现有长期记忆基础上升级为混合检索与排序体系，提升命中率与回复稳定性。

### 依赖图

```
Wave 1 (并行)                  Wave 2 (并行)
PH10-001 ─┐
PH10-002 ─┼──→ PH10-004
PH10-003 ─┘
            ├──→ PH10-005
            └──→ PH10-006
```

### 状态一览

| TASK-ID | 描述 | Wave | 状态 | 分配 |
|---------|------|:----:|:----:|:----:|
| PH10-001 | RAG 分数输出改造 | 1 | ✅ DONE | DeepSeek |
| PH10-002 | Memory 混合排序 | 1 | ✅ DONE | DeepSeek |
| PH10-003 | 检索配置常量补齐 | 1 | ✅ DONE | DeepSeek |
| PH10-FIX-001 | 修复混合排序未消费配置常量 | FIX | ✅ DONE | DeepSeek |
| PH10-004 | Prompt Memory Block 重构 | 2 | ✅ DONE | DeepSeek |
| PH10-005 | /chat/send 接入混合检索 | 2 | ✅ DONE | DeepSeek |
| PH10-006 | /memories 查询参数与分数输出 | 2 | ✅ DONE | DeepSeek |

### Wave 1（并行 — 3 Agent）

### TASK PH10-001：RAG 分数输出改造

```
TASK-ID: PH10-001
名称: RAG 分数输出改造
Wave: 1

允许修改文件:
- E:\ai-companion\backend\services\rag_service.py

禁止修改:
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

目标:
- 在保留现有编码能力的前提下，补齐可返回语义分数的检索能力

完成标准:
- ✔ 可输出原始 semantic score
- ✔ 兼容现有向量检索逻辑
- ✔ 不破坏已有 encode / search 主路径
```

### TASK PH10-002：Memory 混合排序

```
TASK-ID: PH10-002
名称: Memory 混合排序
Wave: 1

允许修改文件:
- E:\ai-companion\backend\services\memory_service.py

禁止修改:
- E:\ai-companion\backend\services\rag_service.py
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

目标:
- 将 search_memories() 升级为 semantic + importance + recency + type weight 混合排序

完成标准:
- ✔ 混合排序权重可配置
- ✔ summary 不会长期压过核心用户事实
- ✔ 兼容现有记忆提取与存储链路
```

### TASK PH10-003：检索配置常量补齐

```
TASK-ID: PH10-003
名称: 检索配置常量补齐
Wave: 1

允许修改文件:
- E:\ai-companion\backend\config.py

禁止修改:
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\backend\services\rag_service.py
- E:\ai-companion\frontend\**

目标:
- 为混合检索补齐阈值、权重、半衰期等配置常量

完成标准:
- ✔ 常量命名清晰
- ✔ 默认值可直接用于 Phase 10 检索逻辑
- ✔ 不影响现有配置读取
```

### Wave 1 Review 结果（2026-05-28）

- PH10-001：三轮审查通过，`search_with_scores()` 可输出原始 `semantic_score`，且未破坏既有 `encode/search` 主路径。
- PH10-002：三轮审查中 Round 1 失败，阻塞于 `memory_service.py` 仍使用文件内硬编码权重/阈值/类型上限，未真正消费 `backend/config.py` 中 Phase 10 新增配置常量。
- PH10-003：三轮审查通过，检索配置常量命名、默认值与现有配置读取均验收通过。

### Phase 10 修复 TASK（Wave 1 Review 阻断）

### TASK PH10-FIX-001：修复混合排序未消费配置常量

```
TASK-ID: PH10-FIX-001
名称: 修复混合排序未消费配置常量
关联: ISSUE-015

允许修改文件:
- E:\ai-companion\backend\services\memory_service.py

禁止修改:
- E:\ai-companion\backend\config.py
- E:\ai-companion\backend\services\rag_service.py
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

目标:
- 让 Phase 10 的混合排序逻辑真正消费 `backend/config.py` 中新增的阈值、权重、半衰期与类型上限配置

完成标准:
- ✔ `search_memories()` 不再依赖文件内硬编码检索参数
- ✔ `MEMORY_WEIGHT_*`、`MEMORY_TYPE_WEIGHT_*`、`MEMORY_SEMANTIC_THRESHOLD`、`MEMORY_RECENCY_HALFLIFE_DAYS`、`MEMORY_MAX_*` 全部生效
- ✔ `return_debug_scores=True` 时返回的权重信息与实际配置一致
- ✔ `summary` 不会长期压过核心用户事实
- ✔ 不破坏现有记忆提取与存储链路
```

### Phase 10 修复验收结果（2026-05-28）

- PH10-FIX-001：三轮审查通过，`memory_service.py` 已真正消费 `backend/config.py` 中的 Phase 10 检索配置常量。
- PH10-002：经 `PH10-FIX-001` 修复并重新验收后，原始完成标准已恢复成立：混合排序权重可配置、`summary` 不会长期压过核心用户事实、现有记忆提取与存储链路不回归。

### Wave 2（并行 — Wave 1 完成后启动）

### TASK PH10-004：Prompt Memory Block 重构

```
TASK-ID: PH10-004
名称: Prompt Memory Block 重构
Wave: 2（依赖 PH10-001 + PH10-002 + PH10-003）

允许修改文件:
- E:\ai-companion\backend\services\prompt_builder.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**

目标:
- 按用户事实 / 偏好 / 近期事件组织记忆块，避免直接拼接杂乱列表

完成标准:
- ✔ 记忆块结构清晰
- ✔ 与 Persona / Emotion block 并存不冲突
- ✔ memory_context 缺失时可安全降级
```

### TASK PH10-005：/chat/send 接入混合检索

```
TASK-ID: PH10-005
名称: /chat/send 接入混合检索
Wave: 2（依赖 PH10-001 + PH10-002 + PH10-003）

允许修改文件:
- E:\ai-companion\backend\api\chat.py

禁止修改:
- E:\ai-companion\backend\services\prompt_builder.py
- E:\ai-companion\frontend\**

目标:
- 让聊天主链路消费新的混合检索结果

完成标准:
- ✔ SSE 主链路不回归
- ✔ 命中记忆时注入结果更稳定
- ✔ 情绪 / 摘要 / 记忆提取后处理不受影响
```

### TASK PH10-006：/memories 查询参数与分数输出

```
TASK-ID: PH10-006
名称: /memories 查询参数与分数输出
Wave: 2（依赖 PH10-001 + PH10-002 + PH10-003）

允许修改文件:
- E:\ai-companion\backend\api\chat.py

禁止修改:
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\frontend\**

目标:
- 扩展 GET /api/v1/memories/{session_id} 以支持 query、top_k、include_scores

完成标准:
- ✔ 不带 query 时保持原行为
- ✔ 带 query 时返回排序结果
- ✔ include_scores=true 时返回 semantic_score 与 final_score
```

### Wave 2 当前结果（2026-05-28）

- PH10-004：三轮审查通过，Prompt 中的 Memory Block 已改为结构化分组展示，并验证了空值安全降级。
- PH10-005：三轮审查通过，`/chat/send` 已切换到消费混合检索结果，SSE 主链路、情绪链路、记忆提取链路与浏览器 E2E 均通过。
- PH10-006：三轮审查通过，真实 `127.0.0.1:8000` API 已验证 `query`、`top_k`、`include_scores` 生效，且默认列表行为不回归。

### Phase 10 当前执行策略

- Wave 1 已全部通过
- Wave 2 已全部完成并通过审查
- Phase 10 进入最终验收完成状态

### Phase 10 验收标准

- [x] 混合检索在用户事实、偏好、近期事件之间排序合理
- [x] `/memories` 普通列表行为不回归
- [x] `/memories?query=...` 可返回带分数的检索结果
- [x] `summary` 不压过核心长期记忆
- [x] `/chat/send` 注入新检索结果后 SSE、情绪、摘要链路不回归

### Phase 10 最终验收结果（2026-05-28）

- PH10-001 ~ PH10-006 与修复任务 `PH10-FIX-001` 已全部完成并通过审查。
- `/api/v1/memories/{session_id}` 已支持 `query`、`top_k`、`include_scores`，并在真实 `127.0.0.1:8000` 请求下确认默认列表模式与检索模式均可正常工作。
- `/chat/send` 已切换到消费混合检索结果，SSE、情绪、摘要、记忆提取后处理链路未出现回归。
- Phase 10 全部验收通过，可视为完成。

---

## Bug Fix Wave 2026-05-30

**目标：** 修复用户在 `docs/BUG_REPORTS.md` 中记录的 `BUG-005` ~ `BUG-008`，并验证语音体验、回复风格、聊天滚动体验与刷新后会话恢复不回归。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| BUG-FIX-003 | 修复默认语音声线与角色体验不一致 | BUG-005 | ❌ FAILED | DeepSeek |
| BUG-FIX-004 | 修复 AI 回复过长、AI 味过重 | BUG-006 | ❌ FAILED | DeepSeek |
| BUG-FIX-005 | 修复聊天区滚动体验差与刷新后消息丢失 | BUG-007, BUG-008 | ❌ FAILED | DeepSeek |

### TASK BUG-FIX-003：修复 BUG-005 — 默认语音声线与角色体验不一致

```
TASK-ID: BUG-FIX-003
名称: 修复 BUG-005 — 默认语音声线与角色体验不一致
关联: docs/BUG_REPORTS.md / BUG-005

目标:
- 修复当前 TTS 默认输出为男性声线、与女性陪伴角色体验不一致的问题
- 在不破坏现有语音接口契约与播放链路的前提下，让默认语音更符合当前 Demo 角色设定
- 保留后续扩展为按角色或配置区分 voice 的空间，但本次不扩展用户设置 UI

允许修改文件:
- E:\ai-companion\backend\config.py
- E:\ai-companion\backend\services\voice_service.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**
- docs/**

验收标准:
- ✔ 不传 voice 时，TTS 默认使用更符合女性陪伴角色体验的声线
- ✔ `/api/v1/voice/tts` 现有 JSON 契约不变
- ✔ 前端“播放语音”按钮无需修改即可正常播放
- ✔ 不影响 STT、文本聊天与现有语音错误处理
```

### TASK BUG-FIX-004：修复 BUG-006 — AI 回复过长、AI 味过重

```
TASK-ID: BUG-FIX-004
名称: 修复 BUG-006 — AI 回复过长、AI 味过重
关联: docs/BUG_REPORTS.md / BUG-006

目标:
- 降低单轮回复长度，减少明显的大段式 AI 输出
- 让回复更贴近日常陪伴聊天：更短、更自然、节奏更轻
- 保持角色差异、情绪注入与记忆召回能力不回归

允许修改文件:
- E:\ai-companion\backend\services\prompt_builder.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\backend\services\emotion_service.py
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\frontend\**
- docs/**

验收标准:
- ✔ 默认日常聊天场景下，单轮回复明显短于当前版本
- ✔ 回复风格更像即时陪伴聊天，不再频繁出现长篇大论
- ✔ 不破坏角色人设差异、情绪语气调整与记忆自然融入
- ✔ SSE 流式主链路与现有前端逐步渲染表现不回归
```

### TASK BUG-FIX-005：修复 BUG-007 / BUG-008 — 聊天滚动体验与刷新后消息恢复

```
TASK-ID: BUG-FIX-005
名称: 修复 BUG-007 / BUG-008 — 聊天滚动体验与刷新后消息恢复
关联: docs/BUG_REPORTS.md / BUG-007, BUG-008

目标:
- 改善长对话时聊天区与洞察区的滚动浏览体验
- 降低顶部大块信息对长消息阅读的持续干扰
- 修复页面刷新后消息全部消失的问题，让当前会话可恢复

允许修改文件:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\app\chat\page.tsx

禁止修改:
- E:\ai-companion\backend\services\**
- E:\ai-companion\frontend\src\components\chat\**
- 其他 frontend/**
- docs/**

验收标准:
- ✔ 长对话场景下，聊天消息区可顺畅滚动浏览最新内容
- ✔ 洞察区在桌面端和移动端都有可接受的浏览方式
- ✔ 页面刷新后可恢复当前会话的历史消息，而不是回到空白聊天态
- ✔ 不破坏现有发送、流式、语音播放、情绪刷新、记忆刷新与返回入口
- ✔ 新增的会话恢复逻辑在无历史会话或无效会话时能安全降级
```

### Review 结果（2026-05-30）

- BUG-FIX-003：Review FAILED。代码默认值已改为 `nova`，但实际运行环境 `.env` 仍把 `VOICE_TTS_VOICE` 覆盖为 `FunAudioLLM/CosyVoice2-0.5B:alex`，导致真实用户仍听到男性默认声线。
- BUG-FIX-004：Review FAILED。`prompt_builder.py` 已加入“短回复”指令，但仍是软提示；真实运行时小暖默认日常聊天仍经常输出 200~300 字、约 7 句的长回复。
- BUG-FIX-005：Review FAILED。滚动体验改动基本成立，但“刚发送完成就立即刷新”仍存在会话快照可见性窗口，导致最新一轮消息可能暂时恢复不到。

---

## Bug Fix Retry Wave 2026-05-30

**目标：** 处理 `BUG-FIX-003` ~ `BUG-FIX-005` 的 Review 阻断项，修复运行时默认语音仍为男音、默认回复仍偏长、以及“发送完成即刷新”时最新消息可能丢失的问题。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| BUG-FIX-006 | 修复运行时默认语音仍被 `.env` 覆盖为男音 | BUG-005 | ✅ DONE | DeepSeek |
| BUG-FIX-007 | 强化默认短回复约束，继续压低 AI 味和回复长度 | BUG-006 | ✅ DONE | DeepSeek |
| BUG-FIX-008 | 修复发送完成即刷新时最新消息恢复不稳定 | BUG-008 | ✅ DONE | DeepSeek |

### TASK BUG-FIX-006：修复 BUG-005 — 运行时默认语音仍被 `.env` 覆盖为男音

```
TASK-ID: BUG-FIX-006
名称: 修复 BUG-005 — 运行时默认语音仍被 .env 覆盖为男音
关联: docs/BUG_REPORTS.md / BUG-005

目标:
- 让真实运行中的默认 TTS 声线不再落到男性默认声线
- 保持现有 `/api/v1/voice/tts` JSON 契约、前端播放链路与 provider 配置结构不变
- 不触碰聊天 provider、STT 模型或语音路由逻辑

允许修改文件:
- E:\ai-companion\.env

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\**
- docs\**

验收标准:
- ✔ `GET /api/v1/voice/health` 返回的 `tts_voice` 不再是 `FunAudioLLM/CosyVoice2-0.5B:alex`
- ✔ 不传 `voice` 时，前端“播放语音”走新的默认声线
- ✔ 不影响现有 STT、TTS 接口连通性与文本聊天主链路
```

### TASK BUG-FIX-007：修复 BUG-006 — 强化默认短回复约束

```
TASK-ID: BUG-FIX-007
名称: 修复 BUG-006 — 强化默认短回复约束
关联: docs/BUG_REPORTS.md / BUG-006

目标:
- 在保持角色差异、情绪与记忆注入的前提下，继续压低默认日常聊天的回复长度
- 让“随便聊聊/陪我说两句”这类默认场景更稳定地产出短回复，而不是依赖模型自觉
- 本次只改 Prompt 约束，不修改 API、模型参数或前端渲染逻辑

允许修改文件:
- E:\ai-companion\backend\services\prompt_builder.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\backend\services\emotion_service.py
- E:\ai-companion\backend\services\memory_service.py
- E:\ai-companion\frontend\**
- docs\**

验收标准:
- ✔ 默认日常聊天场景下，回复通常控制在 1~3 句、明显短于当前版本
- ✔ “小暖”这类安抚型角色也不会轻易回成长篇抒情文
- ✔ 角色差异、情绪语气调整与记忆自然融入不回归
- ✔ SSE 流式主链路与现有前端逐步渲染表现不回归
```

### TASK BUG-FIX-008：修复 BUG-008 — 发送完成即刷新时最新消息恢复不稳定

```
TASK-ID: BUG-FIX-008
名称: 修复 BUG-008 — 发送完成即刷新时最新消息恢复不稳定
关联: docs/BUG_REPORTS.md / BUG-008

目标:
- 修复“刚发送完成就刷新页面”时最新一轮消息可能短暂恢复不到的问题
- 优先保证用户刷新后能看到刚刚完成的那一轮消息，即使后端快照存在短暂可见性窗口
- 不破坏现有会话恢复、滚动体验、语音播放、情绪刷新和记忆刷新

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts
- E:\ai-companion\frontend\src\app\chat\page.tsx

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\src\components\chat\**
- docs\**

验收标准:
- ✔ 发送完成后立即刷新，页面仍能恢复到刚才的最新消息，而不是回到空白聊天态
- ✔ 旧会话恢复与新会话创建逻辑仍能安全降级
- ✔ 不破坏现有滚动优化、洞察面板、语音播放与返回入口
- ✔ 本地缓存或恢复兜底逻辑不会让消息无限重复或串会话
```

---

## Verification Wave 2026-06-01

**目标：** 对 `BUG-005`、`BUG-006`、`BUG-007/008` 进行重新验真。只接受“运行时确实生效”或“文档已写但实际未生效”两种结论；若任一项失败，再按单项重开 `BUG-FIX` 任务，不允许 Orchestrator 直接改业务代码。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| VERIFY-VOICE-001 | 重新核验默认语音声线是否在真实运行时生效 | BUG-005 | ✅ DONE | DeepSeek Review |
| VERIFY-REPLY-001 | 重新核验默认日常聊天是否仍然过长 | BUG-006 | ✅ DONE | DeepSeek Review |
| VERIFY-SESSION-001 | 重新核验刷新恢复与滚动体验是否真实生效 | BUG-007, BUG-008 | ✅ DONE | DeepSeek Review |

### TASK VERIFY-VOICE-001：核验 BUG-005 — 默认语音声线

```
TASK-ID: VERIFY-VOICE-001
名称: 核验 BUG-005 — 默认语音声线
关联: docs/BUG_REPORTS.md / BUG-005

目标:
- 确认默认 TTS 声线修复是否在真实运行环境中生效
- 区分“代码/文档已写”与“用户实际听到的默认声线已改变”
- 本任务只做核验，不改代码

允许修改文件:
- 无（只读核验）

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\**
- docs\**

必做检查:
- 检查 E:\ai-companion\.env
- 检查 E:\ai-companion\backend\config.py
- 检查 E:\ai-companion\backend\services\voice_service.py
- 运行 GET http://127.0.0.1:8000/api/v1/voice/health
- 运行 POST http://127.0.0.1:8000/api/v1/voice/tts

验收标准:
- ✔ 给出运行时结论，而不是只给静态代码结论
- ✔ 明确说明不传 voice 或传 default 时，默认声线是否已改变
- ✔ 若失败，明确指出是配置未生效、服务未重启、还是默认分支未命中
```

### TASK VERIFY-REPLY-001：核验 BUG-006 — 默认短回复

```
TASK-ID: VERIFY-REPLY-001
名称: 核验 BUG-006 — 默认短回复
关联: docs/BUG_REPORTS.md / BUG-006

目标:
- 确认默认日常聊天是否已经稳定收敛到短回复
- 重点验证“小暖”是否仍会输出长段安抚文
- 本任务只做核验，不改代码

允许修改文件:
- 无（只读核验）

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\**
- docs\**

必做检查:
- 检查 E:\ai-companion\backend\services\prompt_builder.py
- 新建 persona 会话做运行时抽样
- 固定抽样话术：
  1. 陪我说两句
  2. 我准备睡了
  3. 今天有点累
- 重点记录小暖的句数、字数、语气与是否仍像长篇安慰文

验收标准:
- ✔ 结论基于真实抽样，而不是只看 prompt 文本
- ✔ 明确说明回复是否通常控制在 1~3 句
- ✔ 若失败，给出可复现样本与输出特征
```

### TASK VERIFY-SESSION-001：核验 BUG-007 / BUG-008 — 刷新恢复与滚动体验

```
TASK-ID: VERIFY-SESSION-001
名称: 核验 BUG-007 / BUG-008 — 刷新恢复与滚动体验
关联: docs/BUG_REPORTS.md / BUG-007, BUG-008

目标:
- 确认“发送完成即刷新”场景下，最新消息是否真的能恢复
- 确认聊天区与洞察区滚动体验没有回归
- 本任务只做核验，不改代码

允许修改文件:
- 无（只读核验）

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\**
- docs\**

必做检查:
- 检查 E:\ai-companion\frontend\src\lib\api.ts
- 检查 E:\ai-companion\frontend\src\app\chat\page.tsx
- 检查 GET http://127.0.0.1:8000/api/v1/chat/session/{session_id}
- 浏览器 E2E 验收：
  1. 进入 persona 聊天
  2. 发送消息
  3. 等待回复完成后立即刷新
  4. 检查消息恢复、滚动、persona 一致性

验收标准:
- ✔ 明确说明立即刷新是否还能看到最新一轮消息
- ✔ 明确说明是否出现重复消息或跨 persona 串会话
- ✔ 若失败，给出稳定复现路径
```

### Verification 结果（2026-06-01）

- VERIFY-VOICE-001：PASSED。运行时 `GET /api/v1/voice/health` 返回 `tts_voice=FunAudioLLM/CosyVoice2-0.5B:anna`，`POST /api/v1/voice/tts` 在省略 `voice` 与传 `default` 两种入口下都返回音频，确认默认女性声线已真实生效。
- VERIFY-REPLY-001：PASSED。真实运行时对小暖的 6 次固定话术抽样均收敛为 1~2 句、约 21~39 字；小锐对照样本也保持 1~2 句且人设差异未回归。
- VERIFY-SESSION-001：PASSED。浏览器 E2E 下“发送完成即刷新”可恢复最新一轮消息，未复现重复消息或跨 persona 串会话；聊天区与洞察区独立滚动保持可用。

---

## Bug Fix Wave 2026-06-01B

**目标：** 修复用户新发现的 `BUG-009`，恢复“录音 -> 语音转写 -> 文本回填输入框”的 STT 主链路，不允许 Orchestrator 直接改业务代码。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| BUG-FIX-009 | 修复语音转写上传字段名不匹配导致的 422 | BUG-009 | ✅ DONE | DeepSeek |

### TASK BUG-FIX-009：修复 BUG-009 — 语音转写 422

```
TASK-ID: BUG-FIX-009
名称: 修复 BUG-009 — 语音转写 422
关联: docs/BUG_REPORTS.md / BUG-009

目标:
- 修复聊天页录音后调用 `/api/v1/voice/stt` 返回 422 的问题
- 恢复“录音 -> 上传音频 -> STT 转写 -> 文本回填输入框”的用户主链路
- 优先保持后端 `/api/v1/voice/stt` 现有接口契约不变，只修正前端上传字段名与必要的请求兼容逻辑

允许修改文件:
- E:\ai-companion\frontend\src\lib\api.ts

禁止修改:
- E:\ai-companion\backend\**
- E:\ai-companion\frontend\src\app\chat\page.tsx
- docs\**

验收标准:
- ✔ 录音上传请求不再因 multipart 字段名不匹配而返回 422
- ✔ `transcribeAudio()` 仍返回 `text` 字符串，并保持现有调用方式不变
- ✔ 不影响 `/voice/tts`、文本聊天、会话恢复与页面其他功能
- ✔ 浏览器端录音完成后，转写文本能正常回填输入框，或至少接口运行时返回 200 + text
```

### Review 结果（2026-06-01）

- BUG-FIX-009：PASSED。前端 `transcribeAudio()` 已将 multipart 字段名从 `file` 改为与后端契约一致的 `audio`，运行时验证确认 `/api/v1/voice/stt` 不再因字段名问题返回 `422`。
- Review 同时观察到：在等价运行时验证里，`audio` 字段上传已穿过 FastAPI 参数绑定层，但 synthetic 音频样本触发了上游 `STT provider response did not include transcribed text` 的 `503`。这说明本任务修复的是“422 契约阻断”，不再是旧的字段名问题；真实录音路径需继续由用户复测。

---

## Bug Fix Wave 2026-06-01C

**目标：** 修复 `BUG-010`，让真实浏览器录音使用的 `audio/webm;codecs=opus` / `audio/ogg;codecs=opus` 等 MIME 变体能被后端正确识别并转发给 `STT provider`，不允许 Orchestrator 直接改业务代码。

### 状态一览

| TASK-ID | 描述 | 关联 BUG | 状态 | 分配 |
|---------|------|----------|:----:|:----:|
| BUG-FIX-010 | 修复 STT 对带 codec 参数 MIME 的格式识别错误 | BUG-010 | ✅ DONE | DeepSeek |

### TASK BUG-FIX-010：修复 BUG-010 — STT Unsupported audio format

```
TASK-ID: BUG-FIX-010
名称: 修复 BUG-010 — STT Unsupported audio format
关联: docs/BUG_REPORTS.md / BUG-010

目标:
- 修复真实浏览器录音上传后，STT provider 报 Unsupported audio format 的问题
- 让后端对 `audio/webm;codecs=opus`、`audio/ogg;codecs=opus` 等常见浏览器录音 MIME 变体做正确归一化与扩展名推断
- 不修改前端录音逻辑、不修改聊天主链路、不改 TTS

允许修改文件:
- E:\ai-companion\backend\services\voice_service.py

禁止修改:
- E:\ai-companion\backend\api\chat.py
- E:\ai-companion\frontend\**
- docs\**

验收标准:
- ✔ 真实浏览器录音常见 MIME 变体不再被推断成 `bin` 扩展名
- ✔ 使用 `audio/webm;codecs=opus`、`audio/ogg;codecs=opus` 等 MIME 做运行时请求时，不再因为格式识别错误触发 Unsupported audio format
- ✔ 不影响现有 `/voice/tts`、文本聊天、会话恢复与前端调用方式
```

### Review 结果（2026-06-06）

- BUG-FIX-010：PASSED。当前发布前复核中，代码已包含浏览器录音 MIME 归一化修复，且用户在本地真实浏览器路径下确认语音输入可用，因此本任务状态更新为完成，不再阻断 `master` 发布。
