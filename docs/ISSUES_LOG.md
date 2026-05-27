# ISSUES LOG

> **问题日志。DeepSeek Review 验收失败时必须在此记录。Claude 定期审查。**

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

---

## 新发现 Issues (Frontend Integration Review)

### ISSUE-007 — FIXED
- **关联 TASK:** FE-INTEGRATION-001
- **严重级别:** High
- **描述:** `fetchMemories()` 与 `fetchEmotionHistory()` 吞掉请求错误并返回空数组，导致页面无法区分 empty 与 error。
- **根因:** API 客户端 catch 了非 200 / 解析异常后直接返回 `[]`，上层页面拿不到 reject。
- **影响:** 洞察组件的 error 状态与重试按钮在真实链路中不可达。
- **建议修复:** 仅对明确可接受的空数据返回 `[]`，其余失败路径抛错给页面处理。

### ISSUE-008 — FIXED
- **关联 TASK:** FE-INTEGRATION-002
- **严重级别:** Medium
- **描述:** 洞察面板在桌面侧栏中使用双列布局时过窄，且记忆类型标签缺少 `user_info` / `emotion` 映射。
- **根因:** 组件响应式断点按整页宽度设计，未适配 `24rem` 侧栏容器；标签映射未跟随当前 MemoryType 完整更新。
- **影响:** 桌面端可读性差，部分标签会退化为原始枚举值。
- **建议修复:** 调整为更稳妥的单列或容器感知布局，并补齐标签字典。

### ISSUE-009 — FIXED
- **关联 TASK:** FE-INTEGRATION-003
- **严重级别:** Critical
- **描述:** `POST /api/v1/chat/session` 成功返回 `session_id` 后，紧接着 `POST /api/v1/chat/send` 与 emotion/history 接口返回 `Session not found`。
- **根因:** 当前 chat session 依赖进程内 `_sessions`，实际运行链路中 session 状态未稳定保留或请求未命中同一内存态。
- **影响:** 聊天主链路回归，前端洞察刷新、summary 验收与浏览器 E2E 均被阻断。
- **建议修复:** 修复 session 生命周期与请求一致性，保证 send/emotion/history 使用同一有效 session。

### ISSUE-010 — FIXED
- **关联 TASK:** FE-FIX-003
- **严重级别:** Major
- **描述:** 浏览器访问 `http://127.0.0.1:3000/personas` 时页面停留在 loading spinner，无法发起角色列表请求，导致 FE-FIX-003 第 3 轮前端 E2E 无法闭环。
- **根因:** `frontend/next.config.ts` 的 `allowedDevOrigins` 未包含 `127.0.0.1`，Next.js dev server 拦截了来自 `127.0.0.1` 的 `/_next/webpack-hmr` 与字体等开发资源请求。
- **影响:** 后端 session 修复虽然已通过静态与运行时验证，但浏览器端真实用户路径被前端 dev 环境阻断，整体验收不能通过。
- **建议修复:** 在 `frontend/next.config.ts` 中补充 `127.0.0.1`（必要时同时补 `localhost`）到 `allowedDevOrigins`，重启前端开发服务后重新执行 `/personas -> /chat` 浏览器 E2E。
