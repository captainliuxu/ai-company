# ISSUES LOG

> **问题日志。GLM 验收失败时必须在此记录。Claude 定期审查。**

---

## 已关闭 Issues (Phase 1)

### ISSUE-001 — FIXED
- Critical: PersonaResponse.created_at 类型不匹配 → 500 错误
- 修复: datetime 类型 + field_serializer

### ISSUE-002 — FIXED
- Medium: GET /personas/{invalid_id} 返回 200 而非 404
- 修复: JSONResponse(status_code=404)

### ISSUE-003 — FIXED
- Low: datetime.utcnow 已弃用
- 修复: datetime.now(timezone.utc)

---

## 已关闭 Issues (Phase 2)

### ISSUE-004 — FIXED
- **关联 TASK:** PH2-002, PH2-003
- **严重级别:** Critical
- **描述:** system prompt 放入 messages 数组，Anthropic API 返回 400
- **修复:** 将 system prompt 提取为请求体顶层 `system` 参数，messages 只含 user/assistant

### ISSUE-005 — FIXED
- **关联 TASK:** PH2-003
- **严重级别:** Critical
- **描述:** SSE 解析逻辑无法识别 Anthropic 原生流式格式（content_block_delta + text_delta），AI 回复全部丢弃
- **修复:** 重写解析逻辑，匹配 `data.type == "content_block_delta"` + `delta.type == "text_delta"`

### ISSUE-006 — FIXED
- **关联 TASK:** PH2-001
- **严重级别:** Low
- **描述:** SessionResponse 定义但未使用
- **修复:** create_chat_session 中使用 SessionResponse 构建响应
