# API Design

## Base URL

```
http://localhost:8000/api/v1
```

## Response Format

```json
{
  "success": true,
  "message": "",
  "data": {}
}
```

Error:

```json
{
  "success": false,
  "message": "Persona not found",
  "data": null
}
```

---

## Endpoints

### 1. Personas

#### GET /personas
获取所有可用角色列表。

Response: `[{id, name, personality, speaking_style, background_story, emotional_traits, avatar_url}]`

#### GET /personas/{persona_id}
获取单个角色详情。

---

### 2. Chat Session

#### POST /chat/session
创建新对话会话。

Request: `{persona_id: str, user_id: str?}`

Response: `{session_id: str, persona: Persona, created_at: datetime}`

---

### 3. Chat

#### POST /chat/send
发送消息，SSE 流式返回。

Request: `{session_id: str, message: str}`

SSE Events:
```
event: token
data: {"content": "你"}

event: token
data: {"content": "好"}

event: emotion
data: {"favorability": 55, "trust": 42, "mood": 0.3, "dependency": 20}

event: done
data: {"total_tokens": 156}
```

#### GET /chat/{session_id}/history
获取会话历史。

Query: `?limit=50&offset=0`

Response: `[{role, content, created_at}]`

---

### 4. Emotion

#### GET /emotion/{session_id}
获取当前会话的情绪状态。

Response:
```json
{
  "session_id": "...",
  "favorability": 55,
  "trust": 42,
  "mood": 0.3,
  "dependency": 20,
  "mood_label": "平静",
  "history": [
    {"mood": 0.0, "event": "conversation_start", "created_at": "..."},
    {"mood": 0.3, "event": "user_compliment", "created_at": "..."}
  ]
}
```

---

### 5. Memories

#### GET /memories/{session_id}
获取会话关联的用户记忆列表。

Query: `?type=user_info&limit=20`

---

### 6. [FUTURE] Voice

#### POST /voice/asr
语音转文字。（占位，返回 501）

#### POST /voice/tts
文字转语音。（占位，返回 501）

---

## Error Codes

| Code | Meaning |
|------|---------|
| 400 | 请求参数错误 |
| 404 | 资源不存在（persona/session） |
| 500 | 服务内部错误 |
| 501 | [FUTURE] 功能尚未实现 |

---

## SSE Stream Flow

```
Client                    Server
  │                         │
  │── POST /chat/send ────>│
  │                         │── Emotion Analysis
  │                         │── RAG Recall
  │                         │── Prompt Build
  │                         │── LLM Stream
  │<──── SSE: token ────────│
  │<──── SSE: token ────────│
  │<──── SSE: token ────────│
  │<──── SSE: emotion ──────│
  │<──── SSE: done ─────────│
  │                         │── Memory Store
  │                         │── Summary Check
```
