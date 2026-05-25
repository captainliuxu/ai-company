# AI Companion Pro Demo — 开发规则

本文档定义 Claude / AI Coding Agent 在本项目中的行为规范。

---

# 一、核心原则

## 0. 编码纪律（最高优先级，不可违反）

**禁止在以下任一条件不满足时编写任何代码：**

1. **没有完善的阶段计划** — 每个开发阶段必须先在 plan file 中写出完整的实现计划，包括：要改哪些文件、每个文件的改动范围、依赖关系、验收标准
2. **没有用户明确许可** — 计划写完后，必须通过 `ExitPlanMode` 提交用户审批。用户说"开始"/"执行"/"go ahead"之后才允许写代码
3. **禁止擅自扩展范围** — 计划外的文件不改，计划外的功能不加，计划外的"顺便优化"不做。发现更好的做法？写进计划里让用户审批，而不是直接改

**违规对照：**
- "我觉得顺便改一下这里更好" → **禁止**。写到计划里，下次做。
- "这个重构很简单，两分钟" → **禁止**。写到计划里，下次做。
- "用户说了方向，我直接实现看看" → **禁止**。先写计划，审批后再写代码。

**正确的流程：**
```
用户方向 → 探索代码 → 写计划 → ExitPlanMode → 用户审批 → 写代码
```

**违反此规则的后果：**
计划模式就是用来防止这个的。如果你在计划模式下尝试写非计划文件之外的代码，工具层面会被拦。如果你退出计划模式后擅自写未经审批的代码，用户会注意到。

---

## 1. 当前可运行 > 未来可扩展
- 先让功能跑通，再考虑扩展点
- 不要为了预留扩展性而增加当前复杂度
- 用 TODO / [FUTURE] 注释标记未来方向

## 2. AI 产品感 > 技术炫技
- 用户能感知的功能优先
- 后端实现再优雅，前端体验差也不行
- 聊天气泡、typing 动画、情绪展示同样重要

## 3. 单体优先
- 不分服务、不分容器
- 一个 FastAPI app + 一个 SQLite 文件
- 前端一个 Next.js app

## 4. 可独立测试
- 每个 service 可单独 import 测试
- 不依赖复杂的 mock 环境
- 数据库可随时删掉重建

---

# 二、代码规范

## Python (Backend)

### 必须
- FastAPI 路由只做参数校验和调用 service，不写业务逻辑
- 所有模型用 SQLAlchemy + Pydantic
- 类型注解（函数签名 + Pydantic model）
- 异步 handler (`async def`)

### 禁止
- `route` 函数里写超过 10 行业务代码
- 巨型 God class
- 全局可变状态
- `.env` 提交到 git

### 目录分工

```
backend/
├── api/         # 路由层：解析请求 → 调用 service → 返回响应
├── services/    # 业务层：所有逻辑在这里
├── models/      # 数据层：SQLAlchemy ORM 模型
└── schemas/     # 接口层：Pydantic 请求/响应定义
```

---

## Frontend

### 必须
- shadcn/ui 组件优先
- TailwindCSS 样式优先
- SSE 接收流式消息
- 响应式布局

### 禁止
- 原生 HTML 按钮（用 shadcn/ui Button）
- 硬编码颜色（用 TailwindCSS token）
- 巨型单文件组件

---

# 三、Prompt 规范

## Prompt 必须模块化

```
system_prompt = (
    persona_block      # 角色人格
    + emotion_block    # 当前情绪
    + memory_block     # 召回记忆
    + rules_block      # 回复规则
)
```

禁止：一个 2000 行 prompt.txt

## Prompt 优先级

```
System Safety > Persona > Emotion > Memory > Context > User Input
```

---

# 四、Memory 规范

### 必须
- 保存前 LLM 判断是否为新信息
- 记忆类型明确标记 (user_info / preference / event / emotion)
- RAG 召回数量限制 (top_k ≤ 5)

### 禁止
- 每条对话都无脑存
- 无限追加导致上下文爆炸
- embedding 全量重算

### [FUTURE]
- 记忆重要性评分
- 时间衰减权重
- 向量数据库替换 SQLite BLOB

---

# 五、Emotion 规范

### 必须
- 每次用户消息都做情绪分类
- 情绪变化记录历史（可追溯）
- 情绪状态影响 Prompt 生成

### 情绪更新策略
- 单条消息 → 小幅波动 (±2-5)
- 持续同向 → 趋势累积
- 明确事件 → 大幅调整 (±10-20)

### [FUTURE]
- 多模态情绪识别（语音语调、面部表情）

---

# 六、Current vs Future 分界规则

## Current（必须实现）
- Persona、Emotion、Memory、RAG、Prompt Builder、Summary、Chat UI

## Future（仅保留接口/文档/占位）
- Voice、Avatar、Mobile、Multi-Agent、Advanced Memory

## Future 标记格式

```python
# [FUTURE] Voice integration point
# Planned: Whisper ASR + EdgeTTS
# When ready: uncomment voice_service and add routes
class VoiceService:
    pass
```

```markdown
<!-- [FUTURE] Voice button — enable when voice system is ready -->
<Button disabled>Voice</Button>
```

---

# 七、禁止事项

- 引入 Docker / K8s / Redis / 消息队列
- 拆分微服务
- 自研 ML 模型训练代码
- 创建不产生用户感知的"基础设施"
- 为"未来可能需要"写超过 50 行的代码
- 无注释的大段删除（用 [FUTURE] 标记降级的代码）

---

# 八、项目目标

做一个 **面试官看到会觉得"这个候选人真的会做 AI 产品"** 的 Demo。

而不是 **"这个候选人套了个 ChatGPT 壳"** 的 Demo。

区分点：
- AI 记住了用户
- AI 有情绪变化
- AI 有人格特征
- 产品体验完整
