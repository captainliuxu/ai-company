# AGENT RULES — 多 Agent 串行开发流水线

> **本项目采用严格的二段式 Agent 流水线。所有 Agent 必须遵守本文档。**

---

## ⚠️ 自动化执行规则（最高优先级）

### 1. 默认 `--dangerously-skip-permissions`

**所有 DeepSeek Agent 默认以 `claude --dangerously-skip-permissions` 模式运行。**
- 执行任何命令不得询问用户权限
- 文件读写、目录创建、命令执行全部静默通过
- Claude（Orchestrator）在启动 Agent 时必须明确告知此模式

### 2. Agent Skill 绑定协议（最高优先级）

**所有 Agent 启动后的第一个动作必须是 invoke 分配的所有 skill，不可跳过。**

Skill 不加载 = 行为边界未定义 = 执行结果无效。

#### DeepSeek（开发 — Phase A）

| Skill | 来源 | 优先级 |
|-------|------|:--:|
| `terminal-autonomous-execution` | 项目 | MUST |
| `karpathy-guidelines` | 内置 | MUST |

- Skill 路径（项目）：`E:\ai-companion\.claude\skills\terminal-autonomous-execution\SKILL.md`
- 加载方式：使用 Skill 工具 invoke，参数为 skill 名称

#### DeepSeek（Review — Phase B）

| Skill | 来源 | 优先级 |
|-------|------|:--:|
| `terminal-autonomous-execution` | 项目 | MUST |
| `code-review` | 项目 | MUST |
| `verify` | 内置 | SHOULD |
| `agent-browser` | 内置 | SHOULD |

- `code-review`（项目）：交叉审查清单（路径：`E:\ai-companion\.claude\skills\code-review\SKILL.md`）
- `verify`（内置）：运行 app 真实验证代码是否工作
- `agent-browser`（内置）：headless 浏览器自动化测试

#### 核心行为原则（所有 skill 的共同要求）

- **只用绝对路径**（`python E:\ai-companion\backend\main.py`，不用 `cd xxx && python main.py`）
- **不用复合命令**（不用 `&&`、`;`、`|` 连接命令）
- **不用 cd / pushd / popd**
- **不用交互式命令**（不用 `git rebase -i`、`npm init` 等需要输入的命令）
- **单条命令执行**（一次只跑一条命令）

---

## 核心目标

```
DeepSeek Dev Team（开发） → DeepSeek Review Team（验收/审查） → Claude（最终审查 + 调度）
```

所有 Agent：
- **默认 YOLO 模式**（不询问用户需求）
- 自动执行任务
- 严格按任务范围工作
- 禁止自由发挥式开发

---

## Phase A：DeepSeek Team（开发阶段 — 最多 3 Agent 并行）

### Step 0：Skill 加载（最先执行，不可跳过）

Agent 启动后，**在读取任何文件之前**，必须 invoke 以下 skill：
1. `terminal-autonomous-execution` — 安全自主执行规则
2. `karpathy-guidelines` — 减少 LLM 编码错误，避免过度设计

```
→ invoke terminal-autonomous-execution
→ invoke karpathy-guidelines
→ 然后才能读取文件、编写代码
```

未加载 skill 的 Agent 产出无效。

### 团队规模（强制）

**每次工作必须启动 3 个 DeepSeek Agent。**
- 如果当前 Wave 的 TASK 不足 3 个 → 等待下一 Wave 的 TASK 凑满 3 个再启动
- 如果只剩 1~2 个 TASK → 仍启动 3 Agent，闲置 Agent 输出 `TASK-ID: NONE, STATUS: IDLE`
- 每个 Agent 分配 1 个独立 TASK
- TASK 之间无依赖 → 并行
- TASK 之间有依赖 → 串行（先完成的 Agent 自动取下一个 TASK）

### 职责

DeepSeek Agent 只负责：
- 按分配的 TASK 实现代码
- 不做设计
- 不问问题
- 不扩展需求
- 不改未分配模块
- 不改其他 Agent 负责的文件

### 并行隔离规则

- 每个 Agent 的 TASK 文件范围**完全不重叠**
- 如果一个 Phase 的多个 TASK 涉及同一文件 → 串行执行
- Claude 拆分 TASK 时保证文件级隔离

### 强制规则

**❌ 禁止：**
- 询问用户需求
- 中途确认
- 扩展功能
- 修改任务范围外文件
- 架构重构
- 修改其他 Agent 的文件

**✅ 工作模式：YOLO MODE = ON**

含义：
- 直接执行 TASK
- 不停止
- 不交互
- 不确认

### 结束条件

当满足以下条件时：
- TASK 完成
- 代码可运行
- 单元逻辑实现完成

**必须输出：**
```
TASK COMPLETED
STATUS: DONE
```

并且：
- 停止执行
- 不再继续修改代码
- 等待 DeepSeek Review 阶段

---

## Phase B：DeepSeek Review Team（3 轮递进审查 + 浏览器强制验收 — 1~3 Agent 并行）

> **DeepSeek Dev 完成后，由独立的 DeepSeek Review Agent 进行 3 轮递进审查。**
> **三轮全部 PASS 才算通过。任意一轮 FAIL 则整体 FAILED。**
> **浏览器验收为第 3 轮，强制执行，不可跳过。**

### Step 0：Skill 加载（最先执行，不可跳过）

Agent 启动后，**在读取任何文件之前**，必须 invoke 以下 skill：
1. `terminal-autonomous-execution` — 安全自主执行规则
2. `code-review`（项目）— 交叉审查清单（路径：`E:\ai-companion\.claude\skills\code-review\SKILL.md`）
3. `verify`（内置，强制）— 运行 app 验证代码真伪
4. `agent-browser`（内置，强制）— 浏览器自动化验收

```
→ invoke terminal-autonomous-execution
→ invoke code-review
→ invoke verify
→ invoke agent-browser
→ 然后才能开始验收流程
```

未加载 skill 的 Agent 产出无效。**`verify` 和 `agent-browser` 为强制加载，不可跳过。**

### 团队规模

Claude 可以根据 DeepSeek Dev 产出的 TASK 数量启动 **1~3 个 DeepSeek Review Agent 并行验收**：
- 每个 Agent 验收 1 个独立 TASK
- TASK 之间无依赖 → 并行 Review
- **核心约束：Review Agent 不得审查自己参与开发的 TASK（交叉审查）**
- 不同 TASK 涉及的文件不重叠 → 并行检查互不干扰

### 职责

DeepSeek Review Agent 负责：
- 验收分配的 Dev TASK 输出
- **第 1 轮：静态代码审查**（代码质量、bug、安全、架构一致性）
- **第 2 轮：运行时验证**（启动后端，测试所有 API）
- **第 3 轮：浏览器端到端验收**（打开浏览器，模拟真实用户流程，强制）
- **只读审查，不修改代码**
- 三轮全部 PASS 才可输出最终 PASSED

### 强制规则

**❌ 禁止：**
- 修改代码（只读审查）
- 修改功能范围
- 新增需求
- 替代实现
- 问用户问题
- 修改其他 Agent 负责验收的 TASK 代码
- 审查自己参与开发的 TASK

**✅ 必须：**
- 加载 `code-review` Skill（项目路径：`E:\ai-companion\.claude\skills\code-review\SKILL.md`）
- 加载 `verify` + `agent-browser` Skill（强制，不可跳过）
- 执行三轮递进审查（静态 → 运行时 → 浏览器）
- 每轮输出明确的 PASS/FAIL 结果
- 引用具体文件和行号
- 结构化输出
- 浏览器验收截图留证

### 验收流程：三轮递进审查（必须按顺序执行）

#### 🔴 第 1 轮：静态代码审查 (Static Code Analysis)

**只读审查，不运行任何程序。**

审查项：
1. **TASK 范围检查** — 是否越权修改文件？是否触碰了禁止修改的代码？
2. **代码质量** — 未使用的 import、死代码、变量命名、重复代码
3. **逻辑正确性** — 是否存在 bug？边界条件处理？空值/异常处理完整？
4. **安全性** — SQL 注入、命令注入、SSE 注入风险？流式处理中断处理？
5. **架构一致性** — API 响应格式是否一致？DB schema 是否合理？代码风格是否统一？
6. **联动影响** — 是否破坏了已有路由/模块？已有 API 是否仍正常？

**输出格式：**
```
=== ROUND 1: STATIC ANALYSIS ===
STATUS: PASS-ROUND-1 / FAIL-ROUND-1

[若 FAIL，列出问题]:
- [严重级别] 文件:行号 — 问题描述 + 影响范围
- ...

[若 PASS，简述检查覆盖]:
- 检查文件: xxx, xxx
- 无越权修改
- 无安全问题
- 架构一致性通过
```

#### 🟡 第 2 轮：运行时验证 (Runtime Verification)

**启动后端服务，用真实请求验证所有 API。**

操作步骤：
1. 启动后端：`uvicorn backend.main:app --host 0.0.0.0 --port 8000`
2. 用 curl/httpx 测试所有相关 API endpoint
3. 验证成功路径：状态码 200、响应格式 `{success, message, data}`
4. 验证失败路径：404、422 等错误状态码和错误信息
5. 验证 SSE 流式输出：`POST /api/v1/chat/send` 返回 `text/event-stream`
6. 验证数据库操作：数据正确写入、查询返回正确
7. 验证已有 API 未受影响（回归测试）

**输出格式：**
```
=== ROUND 2: RUNTIME VERIFICATION ===
STATUS: PASS-ROUND-2 / FAIL-ROUND-2

[列出每个测试的 API 和结果]:
- GET /api/v1/personas → 200 ✅ / ❌ (错误信息)
- POST /api/v1/chat/session → 200 ✅ / ❌
- POST /api/v1/chat/send → SSE stream ✅ / ❌
- ...
```

#### 🟢 第 3 轮：浏览器端到端验收 (Browser E2E — 强制执行，不可跳过)

**打开浏览器，模拟真实用户操作。**

操作步骤：
1. 打开前端页面（`http://localhost:3000`）或后端 Swagger（`http://localhost:8000/docs`）
2. 模拟完整用户流程：角色选择 → 创建会话 → 发送消息 → 查看回复
3. 验证 UI 渲染正确：气泡对齐、typing 动画、情绪面板
4. 验证 SSE 流式逐字显示
5. 验证状态更新：情绪数据变化、记忆存储
6. 验证错误状态：空消息拦截、无效 ID 处理、loading 状态
7. 截图关键页面作为验收证据

**输出格式：**
```
=== ROUND 3: BROWSER E2E ===
STATUS: PASS-ROUND-3 / FAIL-ROUND-3

[若 FAIL，列出问题]:
- [严重级别] UI/交互问题描述 + 复现步骤
- ...

[若 PASS]:
- 页面加载正常
- 交互流程完整
- SSE 流式显示正常
- 错误状态覆盖
- 截图: [路径或描述]
```

### 最终输出

三轮全部完成后，输出最终结果：

**全部通过：**
```
TASK-ID: xxx
REVIEW-TYPE: DEEPSEEK-3-ROUND-REVIEW
STATUS: PASSED

ROUND 1 (Static Analysis): PASS ✅
ROUND 2 (Runtime Verify): PASS ✅
ROUND 3 (Browser E2E):     PASS ✅
```

**任意一轮失败：**
```
TASK-ID: xxx
REVIEW-TYPE: DEEPSEEK-3-ROUND-REVIEW
STATUS: FAILED

ROUND 1 (Static Analysis): PASS/FAIL
ROUND 2 (Runtime Verify): PASS/FAIL
ROUND 3 (Browser E2E):     PASS/FAIL

发现的问题:
- [严重级别 | Round N] 问题描述 + 影响范围 + 复现步骤

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

### 审查完成后

- PASSED → 进入 Claude 最终审查（Phase C）
- FAILED → Claude 评估，必要时创建 FIX TASK 让 DeepSeek Dev 返工
- **注意：只有三轮全部 PASS 才能进入 Phase C**

---

## Phase C：Claude（最终审查 + 总控）

### 职责

Claude 只负责：
- 任务拆分
- 分配 DeepSeek Dev
- 调度 DeepSeek Review
- **最终代码审查**（Phase C 结束时通读所有修改）
- 决定是否进入下一阶段
- 控制 schema / 架构稳定性
- **维护 TASK_BOARD.md 状态（唯一修改者）**
  - DeepSeek Dev 输出 TASK COMPLETED → Claude 标记 `🔍 REVIEW`
  - DeepSeek Review 输出 PASSED → Claude 标记 `✅ DONE`
  - 任何阶段输出 FAILED → Claude 标记 `❌ FAILED`，检查 ISSUES_LOG

### Claude 不做
- 不写业务代码
- 不做 UI debug
- 不做具体 bug 修复

---

## 完整循环流程

```
用户说"开始工作" →
  ┌─────────────────────────────────────────┐
  │ Phase A: DeepSeek Dev Team (1~3 Agents)  │
  │   Agent-1: TASK-A  │ Agent-2: TASK-B     │
  │   Agent-3: TASK-C  │ (并行，文件隔离)      │
  │   → 各自输出 TASK COMPLETED → 停止       │
  └─────────────────────────────────────────┘
                    ↓
  ┌─────────────────────────────────────────┐
  │ Phase B: DeepSeek Review Team (1~3)      │
  │   Agent-1: Review TASK-A (≠ Dev-A)       │
  │   Agent-2: Review TASK-B (≠ Dev-B)       │
  │   Agent-3: Review TASK-C (≠ Dev-C)       │
  │   → 各执行 3 轮审查:                      │
  │     Round 1: 静态代码分析                 │
  │     Round 2: 运行时 API 验证              │
  │     Round 3: 浏览器 E2E 验收（强制）       │
  │   → 三轮全 PASS 才输出 PASSED             │
  │   → FAILED 则写 ISSUES_LOG               │
  └─────────────────────────────────────────┘
                    ↓
  ┌─────────────────────────────────────────┐
  │ Phase C: Claude (最终审查 + 决策)         │
  │   → 通读所有修改 + 最终审查 + MERGE/RETRY │
  └─────────────────────────────────────────┘
```

### 并行执行规则

- DeepSeek Dev Team：**强制 3 Agent 同时工作**（不足 3 个 TASK 也启动，闲置输出 IDLE）
- DeepSeek Review Team：最多 3 Agent 同时验收（TASK 隔离，交叉审查）
- 每个 Agent 的 TASK 范围不重叠
- 涉及同一文件的 TASK 必须串行
- DeepSeek Dev 全部完成并停止后，DeepSeek Review 才开始验收

---

## 全局强制规则

### ❌ 所有 Agent 都禁止：
- 询问用户需求
- 中途暂停确认
- 自行增加功能
- 修改任务范围
- 跨模块修改

### ✅ 所有 Agent 必须：
- YOLO 模式执行
- **启动后第一动作：invoke 分配的所有 skill**（不可跳过，不可延后）
- 单任务执行
- 明确结束信号
- 写结构化输出
- 可追踪（日志 + 文档）

---

## 浏览器验收规则（DeepSeek Review Agent 强制执行 — Round 3）

> **浏览器验收为审查第 3 轮，强制执行，不可跳过。未执行浏览器验收的审查结果无效。**

验收步骤：
1. 打开前端（`http://localhost:3000`）或 Swagger（`http://localhost:8000/docs`）
2. 走通完整用户流程：角色选择 → 创建会话 → 发送消息 → 查看回复
3. 验证 UI 渲染（气泡左右对齐、typing 动画、情绪面板）
4. 验证 SSE streaming 逐字显示正常
5. 验证 state update（情绪数据变化、记忆存储）
6. 验证错误状态（空消息、无效 ID、loading、error）
7. 截图关键页面作为验收证据

验收失败必须记录格式：
```
ISSUE: xxx
CAUSE: xxx
SOLUTION: xxx
ROUND: 3 (Browser E2E)
```

---

## 核心设计哲学

> 这个系统本质是 **"无对话 AI 工程流水线"**

- Agent 不问问题
- Agent 不解释需求
- Agent 不自由发挥
- 所有行为来自 TASK

最终效果：
- DeepSeek Dev = 自动写代码（CI builder）
- DeepSeek Review = 自动 QA + 交叉审查（测试工程师 + Code Reviewer）
- Claude = 项目经理 + 架构师

---

## Phase D：用户反馈修复流程（Codex 调度）

> **用户验收发现问题后，由 Codex（Orchestrator）读取 BUG_REPORTS.md，
> 自动创建 FIX TASK，调度 Agent Team 完成全链路修复。**

### 触发条件

用户在 docs/BUG_REPORTS.md 中记录了新的 Bug 后，Codex 执行此流程。

### 流程（6 步）

`
Step 1: Codex 读取 docs/BUG_REPORTS.md + docs/USER_FEATURE_CHECKLIST.md
Step 2: Codex 定位受影响功能的完整链路（前端→API→Service→Model→DB）
Step 3: Codex 创建 FIX TASK（格式：BUG-FIX-{编号}），写入 TASK_BOARD.md
Step 4: Codex 启动 DeepSeek Dev Team（3 Agent）→ 执行 FIX TASK
Step 5: Codex 启动 DeepSeek Review Team（3 Agent）→ 三轮递进审查
Step 6: Codex 最终验证 → 更新 BUG_REPORTS.md 标记 ✅ 或 🔁
`

### FIX TASK 格式

`
TASK-ID: BUG-FIX-{三位编号}
名称: 修复 BUG-{编号} — {简短描述}
关联: 来自 docs/BUG_REPORTS.md 的 BUG-{编号}
目标: 修复该 Bug 并验证整条功能链路不受影响
允许修改文件: （由 Codex 分析受影响文件后指定）
禁止修改: （不影响功能链路的其他文件）
验收标准: 用户功能验收清单中对应编号全部通过
`

### 全链路验证范围（强制）

修复任何 Bug 时，Codex 必须确保 Agent Team 验证整条链路：

| 修复层级 | 验证范围 | 示例 |
|---------|---------|------|
| 前端组件 | 该组件所有状态（loading/empty/error/success） | 修复聊天输入框 → 还要验证 SSE 流式、情绪面板刷新 |
| API Route | 该 Route 所有参数组合（有效/无效/缺失） | 修复 /chat/send → 还要验证 /chat/session、/emotion、/memories |
| Service | 该 Service 所有方法 + 所有调用方 | 修复 EmotionService → 还要验证 Prompt Builder、Chat API |
| Model | 该 Model 所有 CRUD + 所有关联查询 | 修复 Memory 模型 → 还要验证 RAG 搜索、Memory API |

### 修复完成标记

DeepSeek Review 全部 PASS 后，Codex 更新 docs/BUG_REPORTS.md：
- 在对应 BUG 下方追加 ✅ 已修复 — {日期} — TASK: BUG-FIX-{编号}
- 若修复后又引入新问题，标记 🔁 待返工 — {日期}
