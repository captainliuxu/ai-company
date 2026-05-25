# AGENT RULES — 多 Agent 串行开发流水线

> **本项目采用严格的三段式 Agent 流水线。所有 Agent 必须遵守本文档。**

---

## ⚠️ 自动化执行规则（最高优先级）

### 1. 默认 `--dangerously-skip-permissions`

**所有 Agent（DeepSeek / GLM）默认以 `claude --dangerously-skip-permissions` 模式运行。**
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

#### GLM（验收 — Phase B）

| Skill | 来源 | 优先级 |
|-------|------|:--:|
| `terminal-autonomous-execution` | 项目 | MUST |
| `code-review` | 内置 | MUST |
| `verify` | 内置 | SHOULD |
| `agent-browser` | 内置 | SHOULD |

- `code-review`（内置）：提供系统化的 security/performance/maintainability/correctness/testing 审查模式
- `verify`（内置）：运行 app 真实验证代码是否工作
- `agent-browser`（内置）：headless 浏览器自动化测试

#### DeepSeek（Code-Review — Phase B2）

| Skill | 来源 | 优先级 |
|-------|------|:--:|
| `terminal-autonomous-execution` | 项目 | MUST |
| `code-review` | 项目 | MUST |

- Skill 路径（项目 code-review）：`E:\ai-companion\.claude\skills\code-review\SKILL.md`

#### 核心行为原则（所有 skill 的共同要求）

- **只用绝对路径**（`python E:\ai-companion\backend\main.py`，不用 `cd xxx && python main.py`）
- **不用复合命令**（不用 `&&`、`;`、`|` 连接命令）
- **不用 cd / pushd / popd**
- **不用交互式命令**（不用 `git rebase -i`、`npm init` 等需要输入的命令）
- **单条命令执行**（一次只跑一条命令）

---

## 核心目标

```
DeepSeek（开发） → GLM（验收/审查） → DeepSeek（Code-Review） → Claude（最终审查 + 调度）
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
- 等待 GLM 阶段

---

## Phase B：GLM Team（验收 + 审查阶段 — 最多 3 Agent 并行）

### Step 0：Skill 加载（最先执行，不可跳过）

Agent 启动后，**在读取任何文件之前**，必须 invoke 以下 skill：
1. `terminal-autonomous-execution` — 安全自主执行规则
2. `code-review`（内置）— 系统化代码审查模式（security/performance/maintainability/correctness/testing）
3. `verify`（内置，可选）— 运行 app 验证代码真伪
4. `agent-browser`（内置，可选）— 浏览器自动化验收

```
→ invoke terminal-autonomous-execution
→ invoke code-review
→ （按需 invoke verify / agent-browser）
→ 然后才能开始验收流程
```

未加载 skill 的 Agent 产出无效。

### 团队规模

Claude 可以根据 DeepSeek 产出的 TASK 数量启动 **1~3 个 GLM Agent 并行验收**：
- 每个 Agent 验收 1 个独立 TASK
- TASK 之间无依赖 → 并行 Review
- 不同 TASK 涉及的文件不重叠 → 并行检查互不干扰

### 职责

GLM Agent 只负责：
- 验收分配的 DeepSeek TASK 输出
- Code Review
- Bug 检查
- 架构一致性检查
- 文档同步检查
- UI/接口一致性检查

### 强制规则

**❌ 禁止：**
- 修改功能范围
- 新增需求
- 替代实现
- 问用户问题
- 修改其他 Agent 负责验收的 TASK 代码

### 验收流程（必须按顺序执行）

**1️⃣ 代码检查**
- 是否符合 TASK 范围
- 是否越权修改文件
- 是否破坏现有结构

**2️⃣ 逻辑检查**
- 是否存在 bug
- 是否有边界问题
- 是否存在空值/异常处理缺失

**3️⃣ 架构检查**
- API 是否一致
- DB schema 是否一致
- Prompt 是否一致

**4️⃣ 工具验收（强制）**

GLM 必须使用浏览器工具 / 前端运行环境进行真实验证：
- 打开页面
- 点击交互
- 测试 API 请求
- 验证 UI 是否正常
- 验证流式输出是否正常

### 验收通过输出

```
TASK-ID: xxx
STATUS: PASSED
```

### 验收失败规则

如果任务未通过，必须输出：

```
TASK-ID: xxx
STATUS: FAILED

问题列表:
- bug 描述
- 影响范围

修改建议:
- 具体修复方案
- 推荐代码结构

是否重跑 DeepSeek:
RETRY REQUIRED: YES / NO
```

并且**必须更新 `docs/ISSUES_LOG.md`**，记录：
- ISSUE ID
- bug 描述
- root cause
- solution

---

## Phase B2：DeepSeek Code-Review Team（交叉审查 — 1~3 Agent 并行）

> **GLM 修改后，由 DeepSeek 以 Code-Review 角色再次审查，形成"交叉审查"闭环。**

### Step 0：Skill 加载（最先执行，不可跳过）

Agent 启动后，**在读取任何文件之前**，必须 invoke 以下 skill：
1. `terminal-autonomous-execution` — 安全自主执行规则
2. `code-review`（项目）— 交叉审查清单和输出规范（路径：`E:\ai-companion\.claude\skills\code-review\SKILL.md`）

```
→ invoke terminal-autonomous-execution
→ invoke code-review
→ 然后才能开始只读审查
```

未加载 skill 的 Agent 产出无效。

### 职责

DeepSeek Code-Review Agent 只负责：
- 审查 GLM 的修改是否正确
- 检查 GLM 修改是否引入新问题
- 检查边界、安全、联动影响
- **只读审查，不修改代码**

### 强制规则

**❌ 禁止：**
- 修改代码
- 新增功能
- 询问用户
- 评价 GLM

**✅ 必须：**
- 加载 `code-review` Skill（路径：`E:\ai-companion\.claude\skills\code-review\SKILL.md`）
- 逐项检查审查清单
- 引用具体文件和行号
- 结构化输出

### 审查输出

通过 → `STATUS: PASSED`
失败 → `STATUS: FAILED` + 问题列表 + 修复建议 + `RETRY: YES/NO`

### 审查完成后

- PASSED → 进入 Claude 最终审查
- FAILED → Claude 评估，必要时创建 FIX TASK 让 GLM 返工

---

## Phase C：Claude（最终审查 + 总控）

### 职责

Claude 只负责：
- 任务拆分
- 分配 DeepSeek
- 调度 GLM
- 调度 DeepSeek Code-Review
- **最终代码审查**（Phase C 结束时通读所有修改）
- 决定是否进入下一阶段
- 控制 schema / 架构稳定性
- **维护 TASK_BOARD.md 状态（唯一修改者）**
  - DeepSeek 输出 TASK COMPLETED → Claude 标记 `🔍 REVIEW`
  - GLM 输出 PASSED → Claude 标记（准备进入 Code-Review）
  - DeepSeek Code-Review 输出 PASSED → Claude 标记 `✅ DONE`
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
  │ Phase A: DeepSeek Team (1~3 Agents)      │
  │   Agent-1: TASK-A  │ Agent-2: TASK-B     │
  │   Agent-3: TASK-C  │ (并行，文件隔离)      │
  │   → 各自输出 TASK COMPLETED → 停止       │
  └─────────────────────────────────────────┘
                    ↓
  ┌─────────────────────────────────────────┐
  │ Phase B: GLM Team (1~3 Agents 并行验收)  │
  │   Agent-1: Review TASK-A                 │
  │   Agent-2: Review TASK-B                 │
  │   Agent-3: Review TASK-C                 │
  │   → 各自输出 PASSED/FAILED + 写 ISSUES_LOG│
  └─────────────────────────────────────────┘
                    ↓
  ┌─────────────────────────────────────────┐
  │ Phase B2: DeepSeek Code-Review Team      │
  │   Agent-1: Code-Review GLM 修改          │
  │   Agent-2: Code-Review GLM 修改          │
  │   → 只读审查，输出 PASSED/FAILED         │
  └─────────────────────────────────────────┘
                    ↓
  ┌─────────────────────────────────────────┐
  │ Phase C: Claude (最终审查 + 决策)         │
  │   → 通读所有修改 + 最终审查 + MERGE/RETRY │
  └─────────────────────────────────────────┘
```

### 并行执行规则

- DeepSeek Team：**强制 3 Agent 同时工作**（不足 3 个 TASK 也启动，闲置输出 IDLE）
- GLM Team：最多 3 Agent 同时验收（TASK 隔离）
- 每个 Agent 的 TASK 范围不重叠
- 涉及同一文件的 TASK 必须串行
- DeepSeek 全部完成并停止后，GLM 才开始验收

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

## 浏览器验收规则（GLM 必须执行）

验收时必须：
- 打开本地/部署前端
- 点击 UI
- 验证 API response
- 验证 streaming
- 验证 state update

验收失败必须记录格式：
```
ISSUE: xxx
CAUSE: xxx
SOLUTION: xxx
```

---

## 核心设计哲学

> 这个系统本质是 **"无对话 AI 工程流水线"**

- Agent 不问问题
- Agent 不解释需求
- Agent 不自由发挥
- 所有行为来自 TASK

最终效果：
- DeepSeek = 自动写代码（CI builder）
- GLM = 自动 QA（测试工程师）
- Claude = 项目经理 + 架构师
