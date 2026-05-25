# Backend Rules

## Stack Constraints

| 允许 | 禁止 |
|------|------|
| FastAPI | Django / Flask |
| SQLAlchemy 2.0 | Raw SQL strings |
| SQLite | PostgreSQL / MySQL (Demo不需要) |
| sentence-transformers | 自训 embedding 模型 |
| OpenAI SDK | 自写 HTTP client |
| Pydantic v2 | dataclass / plain dict |
| SSE | WebSocket (Demo不需要) |
| uvicorn | gunicorn / hypercorn |

## Code Rules

### API Layer (`backend/api/`)
- 只做：参数校验、调用 service、返回响应
- 不做：数据库操作、Prompt 拼装、业务计算
- 每个 route 函数 ≤ 15 行

### Service Layer (`backend/services/`)
- 所有业务逻辑在这里
- 每个 service 是一个独立 class
- Service 之间通过依赖注入关联，不直接 import
- 每个 service 有明确的 public interface（3-5 个方法）

### Model Layer (`backend/models/`)
- SQLAlchemy 2.0 Mapped class
- 字段有 type annotation
- 有 `to_dict()` 方法

### Schema Layer (`backend/schemas/`)
- Pydantic v2 BaseModel
- Request schema 有 field validation
- Response schema 有 example

## Database

- SQLite 文件放在 `data/app.db`
- 表创建用 SQLAlchemy `create_all`
- 不写 migration（Demo 不需要）
- 数据库可随时删除重建（`data/` 目录）

## Async

- 所有 route handler 用 `async def`
- LLM 调用用 async client
- embedding 生成用 `run_in_executor`（sentence-transformers 是同步的）

## Error Handling

- 统一 try/except 在 route 层
- 返回标准格式 `{success, message, data}`
- 不暴露内部 traceback 给前端

## [FUTURE] Notes

- Session 管理目前用 session_id 字符串（未来可改 JWT）
- 单用户模式（未来加 user table）
- voice_service.py 仅 stub
