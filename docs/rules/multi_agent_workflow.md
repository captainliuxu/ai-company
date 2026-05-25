# Multi-Agent Collaboration Workflow

> **参见 `docs/AGENT_RULES.md`** — 完整的 Agent 流水线规范。
> 本文档保留模块 Ownership 和 TASK 模板，与 AGENT_RULES.md 互补。

---

## 文档分工

| 文档 | 内容 |
|------|------|
| `AGENT_RULES.md` | **权威** — Agent 行为规则、三段式流水线、YOLO 模式、并行规则 |
| `multi_agent_workflow.md`（本文档） | 模块 Ownership + TASK 模板 + Review 模板 |
| `TASK_BOARD.md` | 实时任务看板 |
| `ISSUES_LOG.md` | 问题追踪日志 |

---

## 模块 Ownership

| 模块 | Owner | 可读 | 可写 |
|------|-------|:----:|:----:|
| `backend/api/` | DeepSeek | ALL | DeepSeek / DeepSeek(Review) |
| `backend/services/` | DeepSeek | ALL | DeepSeek / DeepSeek(Review) |
| `backend/models/` | DeepSeek | ALL | DeepSeek / DeepSeek(Review) |
| `backend/schemas/` | DeepSeek | ALL | DeepSeek / DeepSeek(Review) |
| `docs/` | Claude | ALL | Claude |
| Prompt System | Claude | Claude | Claude |
| Architecture | Claude | ALL | Claude |
| `PROJECT_PLAN.md` | Claude | ALL | Claude |
| `TASK_BOARD.md` | Claude | ALL | Claude |
| `ISSUES_LOG.md` | GLM | ALL | GLM |
| Code Review | DeepSeek(Review) | ALL | DeepSeek(Review) |
| Browser Testing | GLM | ALL | GLM（最多 3 Agent 并行） |
| `frontend/` | DeepSeek | ALL | DeepSeek |

---

## 并行执行规则

### DeepSeek Team: 强制 3 Agent 并行

- 用户说 **"开始工作"** → Claude 强制启动 3 个 Agent
- Claude 从 `TASK_BOARD.md` 选当前 Wave 的 TASK，分配到 3 个 Agent
- TASK 不足 3 个 → 仍启动 3 Agent，闲置输出 IDLE
- 每个 Agent = 1 个独立 TASK，文件范围不重叠
- 涉及同一文件的 TASK → 串行执行
- 所有 DeepSeek Agent 完成后 → Claude 必须立即将 TASK_BOARD 状态更新为 `🔍 REVIEW`
- 只有 `🔍 REVIEW` 状态的 TASK 才能进入 GLM 验收阶段
- GLM Team 启动（最多 3 Agent 并行验收）

### TASK 拆分原则（Claude 责任）
- 每个 TASK 涉及的文件不与其他 TASK 重叠
- 优先将独立文件分配给不同 Agent
- 同一文件必须串行 → 拆分到串行 TASK 序列

---

## TASK 标准模板

```markdown
TASK-ID: PHASE{N}-{序号}
名称: xxx

目标: xxx
---

允许修改文件:
- backend/xxx.py

禁止修改:
- 明确列出不可触碰的文件

输入条件:
- 依赖的已有模块

输出要求:
- 具体产出物

完成标准:
- ✔ 标准1
- ✔ 标准2
```

---

## GLM Review 输出模板

**通过：**
```
TASK-ID: xxx
STATUS: PASSED
```

**失败：**
```
TASK-ID: xxx
STATUS: FAILED

问题列表:
- bug描述 + 影响范围

修改建议:
- 具体修复方案
- 推荐代码结构

是否重跑 DeepSeek:
RETRY REQUIRED: YES / NO
```
