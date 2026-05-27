# Code Review Skill — 3 轮递进审查

> **Phase B：DeepSeek Review Agent 必须执行三轮递进审查。**
> **三轮全部 PASS 才算通过。任意一轮 FAIL 则整体 FAILED。**
> **浏览器验收（Round 3）强制执行，不可跳过。**

---

## 触发条件

- DeepSeek Dev 完成开发并输出 TASK COMPLETED
- Codex 将 TASK 状态更新为 `🔍 REVIEW` 后
- DeepSeek 启动时被分配 "review" 角色

---

## 角色定义

DeepSeek Review Agent 的职责：

**你是谁：** 一个三级审查者——先审代码，再跑测试，最后浏览器验收。

**你不是：** 开发者（不写新功能）、需求验收者（不验证需求是否满足）。

---

## 审查前置：Skill 加载（不可跳过）

启动后第一动作：
1. `invoke terminal-autonomous-execution`
2. `invoke code-review`
3. `invoke verify`
4. `invoke agent-browser`

四项全部加载后才能开始审查。

---

## Round 1：静态代码审查 (Static Code Analysis)

**只读审查，不运行任何程序。**

### 1.1 TASK 范围检查
- Dev 修改了哪些文件？（列清单）
- 修改是否超出了 TASK 允许的文件范围？
- 是否触碰了禁止修改的代码？
- 是否修改了其他 Agent 负责的文件？

### 1.2 代码质量检查
- 是否有未使用的 import？
- 是否有死代码（定义了但未调用/未引用）？
- 变量/函数命名是否清晰、符合项目风格？
- 是否存在重复代码（可提取但未提取）？

### 1.3 逻辑正确性检查
- 实现是否正确解决了 TASK 要求？
- 是否存在明显的逻辑 bug？
- 边界条件处理：空值、空列表、0、负数、超长输入
- 异常处理：API 调用失败、数据库连接失败、文件不存在

### 1.4 安全检查
- SQL 注入风险（是否使用 ORM 参数化查询？）
- 命令注入风险（是否拼接 shell 命令？）
- SSE 注入风险（用户输入是否直接写入 SSE 流？）
- 敏感信息泄露（API key、密码是否硬编码？）
- 流式处理是否正确处理了中断/超时？

### 1.5 架构一致性检查
- API 响应格式是否统一为 `{success, message, data}`？
- DB schema 字段类型是否合理？
- 代码风格是否与已有代码一致？
- 是否引入了禁止的依赖（ChromaDB、Redis 等）？

### 1.6 联动影响检查
- 修改是否影响了其他模块？
- 已有的 routes 是否仍然正常？
- 被修改的函数是否有其他调用方？
- 数据库迁移是否向后兼容？

### Round 1 输出格式

```
=== ROUND 1: STATIC ANALYSIS ===
STATUS: PASS-ROUND-1 / FAIL-ROUND-1

检查文件:
- backend/xxx.py (新建/修改)
- backend/yyy.py (修改)

[若 PASS]:
- TASK 范围合规 ✅
- 代码质量通过 ✅
- 逻辑正确 ✅
- 安全检查通过 ✅
- 架构一致性通过 ✅
- 无联动影响 ✅

[若 FAIL，逐条列出]:
- [严重] backend/xxx.py:42 — 未处理空值，当 xxx 为 None 时会崩溃
- [中等] backend/yyy.py:15 — 未使用的 import: from typing import Dict
- [轻微] backend/xxx.py:78 — 变量名 `x` 不够清晰，建议改为 `persona_name`
```

---

## Round 2：运行时验证 (Runtime Verification)

**启动后端服务，用真实请求验证所有 API。**

**必须执行的操作：**

### 2.1 启动服务
```
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```
确认无启动错误。

### 2.2 测试所有相关 API

对每个 API endpoint，测试：
- **成功路径**：合法参数 → 期望 200 + 正确响应格式
- **失败路径**：不合法参数 → 期望 4xx + 错误信息
- **回归**：已有 API 是否仍正常

测试用例至少覆盖：

| API | 成功用例 | 失败用例 |
|-----|---------|---------|
| `GET /api/v1/personas` | 返回 3 个角色 | — |
| `GET /api/v1/personas/{id}` | 有效 ID 返回角色 | 无效 ID → 404 |
| `POST /api/v1/chat/session` | 有效 persona_id → 200 | 无效 persona_id → 404 |
| `POST /api/v1/chat/send` | SSE 流式返回 | 无效 session_id → 404 |
| `GET /api/v1/emotion/{session_id}` | 返回情绪状态 | 无效 session → 404 |
| `GET /api/v1/emotion/{session_id}/history` | 返回时间线 | 无效 session → 404 |
| `GET /api/v1/memories/{session_id}` | 返回记忆列表 | — |
| `GET /health` | 200 | — |

### 2.3 验证 SSE 流式输出
- 发送消息后收到 `text/event-stream` 响应
- 每个 token 以 `data: {"text": "..."}` 格式逐条返回
- 最后收到 `data: {"text": "", "done": true}`
- 流式输出无明显卡顿

### 2.4 验证数据库操作
- 数据正确写入 SQLite
- 查询返回正确结果
- 重启后数据保留

### Round 2 输出格式

```
=== ROUND 2: RUNTIME VERIFICATION ===
STATUS: PASS-ROUND-2 / FAIL-ROUND-2

[逐条列出测试结果]:
- GET /api/v1/personas → 200, 3 personas ✅
- GET /api/v1/personas/invalid-id → 404 ✅
- POST /api/v1/chat/session → 200, session_id returned ✅
- POST /api/v1/chat/send → SSE stream OK ✅
- GET /api/v1/emotion/{id} → 200 ✅
- ...

[若 FAIL]:
- POST /api/v1/chat/send → 500 Internal Server Error ❌
  - 错误原因: xxx
  - 请求参数: {"session_id": "xxx", ...}
  - 响应 body: {"success": false, ...}
```

---

## Round 3：浏览器端到端验收 (Browser E2E — 强制执行)

**打开浏览器，模拟真实用户操作。此轮不可跳过。**

### 3.1 环境准备
- 确认后端运行在 `http://localhost:8000`
- 确认前端运行在 `http://localhost:3000`（如有）
- 无前端时使用 Swagger `http://localhost:8000/docs`

### 3.2 测试流程

**有前端时（Phase 7+）：**
1. 打开角色选择页 → 验证 3 个角色卡片正常显示
2. 点击角色 → 跳转聊天页 → 验证 persona_id 传递正确
3. 发送消息 → 验证 SSE 流式逐字显示
4. 验证聊天气泡左右对齐（AI 左/用户右）
5. 验证 typing 动画（三点跳动）
6. 验证情绪状态面板实时更新
7. 验证 loading / empty / error 状态 UI
8. 刷新页面 → 验证数据持久化
9. 切换角色 → 验证回复风格变化
10. 截图关键页面作为验收证据

**无前端时（Phase 3-6）：**
1. 打开 Swagger `http://localhost:8000/docs`
2. 在 Swagger UI 中测试关键 API
3. 验证响应格式和流式输出
4. 截图 API 测试结果

### 3.3 检查项
- [ ] 页面加载无 JavaScript 错误
- [ ] 所有 API 请求成功（Network 面板无 4xx/5xx）
- [ ] SSE 流式逐字显示正常
- [ ] UI 交互响应正常（按钮可点击、输入框可输入）
- [ ] 状态更新实时反映在 UI 上
- [ ] 移动端/桌面端响应式布局

### Round 3 输出格式

```
=== ROUND 3: BROWSER E2E ===
STATUS: PASS-ROUND-3 / FAIL-ROUND-3

测试流程:
1. 角色选择页 → 3 张卡片显示正常 ✅
2. 点击"小暖" → 跳转 /chat?persona_id=xxx ✅
3. 发送"你好" → SSE 逐字显示"你好呀~" ✅
4. 聊天气泡左右对齐 ✅
5. typing 动画显示 ✅
6. 情绪面板更新 ✅
7. 错误状态测试 ✅
8. 页面刷新后数据保留 ✅

截图: [描述或路径]

[若 FAIL]:
- [严重] 第 3 步 — 发送消息后 SSE 未返回数据，页面一直显示 typing
  - 复现: 选择小暖 → 输入"你好" → 点击发送 → typing 动画不停止
  - Network: /api/v1/chat/send 返回 500
```

---

## 最终输出

三轮全部完成后，汇总输出：

### 全部通过：
```
TASK-ID: xxx
REVIEW-TYPE: DEEPSEEK-3-ROUND-REVIEW
STATUS: PASSED

ROUND 1 (Static Analysis): PASS ✅
ROUND 2 (Runtime Verify): PASS ✅
ROUND 3 (Browser E2E):     PASS ✅
```

### 任意一轮失败：
```
TASK-ID: xxx
REVIEW-TYPE: DEEPSEEK-3-ROUND-REVIEW
STATUS: FAILED

ROUND 1 (Static Analysis): PASS/FAIL
ROUND 2 (Runtime Verify): PASS/FAIL
ROUND 3 (Browser E2E):     PASS/FAIL

发现的问题:
- [严重 | Round N] 问题描述 + 影响范围 + 复现步骤

建议修复:
- 具体方案

是否需要 DeepSeek Dev 返工:
RETRY: YES / NO
```

并且**必须更新 `docs/ISSUES_LOG.md`**，记录：
- ISSUE ID
- bug 描述
- root cause
- solution
- 发现轮次（Round 1/2/3）

---

## 强制规则

**❌ 禁止：**
- 修改代码（只读审查）
- 新增功能
- 扩展 TASK 范围外的修改
- 询问用户问题
- 审查自己参与开发的 TASK
- 评价 Dev Agent 的工作态度
- 跳过任意一轮审查
- 跳过浏览器验收（Round 3）

**✅ 必须：**
- YOLO 模式
- 只读操作（Round 1）
- 启动后端验证（Round 2）
- 打开浏览器测试（Round 3）
- 引用具体文件和行号
- 结构化输出
- 每轮明确输出 PASS-ROUND-N / FAIL-ROUND-N
- 三轮全部 PASS 才可输出最终 PASSED
- 审查完即停止

---

## 审查完成后

Codex 收到 DeepSeek Review 结果后：
- PASSED（三轮全 PASS）→ Codex 进行最终审查（Phase C）
- FAILED → Codex 评估是否需要 DeepSeek Dev 返工，创建 FIX TASK
