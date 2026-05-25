# TASK BOARD

> **当前任务看板。Claude 负责维护，每个 TASK 生命周期在此追踪。**

---

## 状态生命周期

每个 TASK 必须经过 4 个状态，**Claude 是 TASK_BOARD 的唯一修改者**：

```
⬜ TODO        → Claude 创建 TASK 时设置
🔨 IN_PROGRESS → Claude 分配 TASK 给 DeepSeek 时设置
🔍 REVIEW      → Claude 收到 DeepSeek 完成信号后设置（此时 GLM 可领取审查）
✅ DONE        → Claude 收到 GLM PASSED 后设置
❌ FAILED      → Claude 收到 GLM FAILED 后设置
```

**关键规则：只有 `🔍 REVIEW` 状态的 TASK 才会被 GLM 领取审查。Claude 必须在 DeepSeek 完成后立即更新状态，否则 GLM 无法开始工作。**

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

## Phase 1 修复 TASK（GLM 验收发现）

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
| PH3-001 | Emotion 数据模型 | 1 | ⬜ TODO | DeepSeek |
| PH3-002 | Emotion Service | 2 | ⬜ TODO | DeepSeek |
| PH3-003 | Prompt Builder Emotion Block | 2 | ⬜ TODO | DeepSeek |
| PH3-004 | Emotion API + Chat 集成 | 3 | ⬜ TODO | DeepSeek |

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
| PH4-001 | Memory 数据模型 | 1 | ⬜ TODO | DeepSeek |
| PH4-002 | Memory Service | 2 | ⬜ TODO | DeepSeek |
| PH4-003 | Memory API + 对话提取 | 3 | ⬜ TODO | DeepSeek |

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
| PH5-001 | RAG Service | 1 | ⬜ TODO | DeepSeek |
| PH5-002 | Memory embedding 生成 | 2 | ⬜ TODO | DeepSeek |
| PH5-003 | Prompt Builder Memory Block | 2 | ⬜ TODO | DeepSeek |

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
| PH6-001 | Summary Service | 1 | ⬜ TODO | DeepSeek |
| PH6-002 | Chat 集成 + 摘要触发 | 2 | ⬜ TODO | DeepSeek |

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
| PH7-001 | Next.js 项目初始化 | 1 | ⬜ TODO | DeepSeek |
| PH7-002 | 角色选择页 | 2 | ⬜ TODO | DeepSeek |
| PH7-003 | 聊天 UI 组件 | 2 | ⬜ TODO | DeepSeek |
| PH7-004 | SSE 集成 + 情绪面板 | 3 | ⬜ TODO | DeepSeek |
| PH7-005 | 响应式 + 打磨 | 4 | ⬜ TODO | DeepSeek |

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
| PH8-001 | 全链路走通 | ⬜ TODO | DeepSeek |
| PH8-002 | Bug 修复 | ⬜ TODO | DeepSeek |
| PH8-003 | 边界情况处理 | ⬜ TODO | DeepSeek |
| PH8-004 | 最终打磨 | ⬜ TODO | DeepSeek |

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
