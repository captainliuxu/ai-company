# AI 伴侣项目完整开发计划（Claude Agent 开发版）

## 文档目标

本文件用于：

- 指导 Claude / Codex / 国产模型 Agent 开发
- 统一项目开发顺序
- 防止 AI 在开发过程中失控
- 将复杂项目拆分为 AI 可稳定完成的小目标
- 保证每个阶段都可运行、可测试、可回滚

本项目采用：

> 阶段式增量开发 + 小任务原子化 + 可运行里程碑

禁止：

- 一次性开发多个大型系统
- AI 自由重构整个项目
- AI 随意修改数据库结构
- AI 跨层级修改代码
- AI 未经允许新增复杂依赖

---

# 一、项目最终目标

打造一个：

- 多角色 AI 伴侣系统
- 支持长期记忆
- 支持角色人格
- 支持情绪系统
- 支持语音交互
- 支持多模型切换
- 支持持续扩展
- 支持未来移动端/App 化

项目定位：

> 类 Character AI / Replika / 猫箱 的 AI 陪伴应用

技术定位：

> AI Native Application

核心重点：

- Prompt 架构
- 记忆系统
- 状态管理
- 角色人格一致性
- 长期可维护性

---

# 二、核心开发原则（必须遵守）

# 1. 每个阶段必须可运行

禁止：

- 写大量未接入代码
- 写未来功能占位垃圾代码
- 堆积 TODO

要求：

每个阶段结束后：

- 项目必须可启动
- 前后端必须可运行
- 至少存在一个可演示功能

---

# 2. AI 一次只完成小任务

禁止：

```txt
帮我完成整个记忆系统
```

正确方式：

```txt
只实现 Memory SQLAlchemy Model
不要实现 retrieval
不要修改 frontend
不要新增第三方依赖
```

Claude 单次任务推荐规模：

- 修改文件数量 <= 3
- 核心逻辑 <= 300 行
- 单一职责
- 单模块修改

---

# 3. 禁止跨模块重构

例如：

禁止：

- 修改聊天模块时顺便重构数据库
- 修改 Prompt 时顺便修改前端状态
- 修改 UI 时顺便改 API

要求：

一次任务只允许：

- 一个模块
- 一个目标
- 一个职责

---

# 4. 所有功能必须阶段化

错误开发方式：

```txt
先把语音、记忆、情绪、角色全部做完
```

正确开发方式：

```txt
先做最小聊天
再做角色
再做记忆
再做语音
```

---

# 三、项目目录结构（标准版）

```txt
project-root/
│
├── frontend/
│   ├── src/
│   ├── components/
│   ├── pages/
│   ├── stores/
│   ├── services/
│   └── hooks/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── models/
│   │   ├── services/
│   │   ├── memory/
│   │   ├── prompts/
│   │   ├── llm/
│   │   ├── character/
│   │   └── utils/
│   │
│   ├── alembic/
│   ├── logs/
│   └── tests/
│
├── shared/
├── docs/
├── scripts/
├── assets/
├── .env
├── .env.example
└── README.md
```

---

# 四、完整开发路线

---

# 阶段 1：项目基础稳定化

目标：

> 让项目具备长期开发能力

本阶段不开发复杂 AI 功能。

---

# 阶段 1-1：统一项目结构

## 目标

整理整个项目目录。

## Claude 任务

- 整理 frontend/backend
- 删除废弃代码
- 删除 demo 文件
- 删除测试垃圾文件
- 统一命名规范
- 统一 import 结构

## 完成标准

- 项目结构清晰
- 不存在重复组件
- 不存在未知用途文件
- 前后端职责明确

## 禁止事项

- 禁止修改业务逻辑
- 禁止新增功能
- 禁止重构数据库

---

# 阶段 1-2：配置系统

## 目标

建立统一配置管理。

## Claude 任务

实现：

```txt
.env
.env.example
config.py
settings.ts
```

## 必须支持

```txt
OPENAI_API_KEY
GLM_API_KEY
DEEPSEEK_API_KEY
TTS_PROVIDER
STT_PROVIDER
DATABASE_URL
```

## 完成标准

- API Key 不写死
- 支持多环境
- 前后端配置分离

## 禁止事项

- 禁止硬编码 token
- 禁止把密钥上传 git

---

# 阶段 1-3：日志系统

## 目标

建立 AI 项目调试能力。

## Claude 任务

实现：

- 后端日志
- API 请求日志
- LLM 请求日志
- 错误日志
- Token 消耗日志

## 日志目录

```txt
logs/
```

## 必须记录

- 用户输入
- Prompt
- 模型响应
- 响应时间
- 错误信息

## 完成标准

- 出错时能定位问题
- 能查看 Prompt
- 能查看 LLM 返回

---

# 阶段 1-4：数据库初始化

## 目标

建立最小数据库结构。

## Claude 任务

实现：

- SQLAlchemy Models
- Alembic
- SQLite 初版

## 第一批表

```txt
users
sessions
messages
memories
```

## 完成标准

- 能保存聊天
- 能创建会话
- 能查询历史消息

## 禁止事项

- 禁止提前设计复杂关系
- 禁止过度抽象

---

# 阶段 1-5：基础 API 架构

## 目标

建立后端 API 规范。

## Claude 任务

建立：

```txt
/api/v1/
```

规范：

- response 格式统一
- 错误格式统一
- status code 统一

## 完成标准

- 所有 API 风格统一
- 前端可稳定调用

---

# 阶段 2：聊天核心系统

目标：

> 建立最小 AI 对话能力

这是项目真正核心。

---

# 阶段 2-1：最小聊天链路

## 目标

实现：

```txt
用户输入 -> LLM -> 返回结果
```

## Claude 任务

实现：

- Chat API
- Chat 页面
- Streaming 输出
- WebSocket 或 SSE

## 完成标准

- 能连续聊天
- 支持流式输出
- 支持长文本返回

## 禁止事项

- 禁止做记忆系统
- 禁止做角色系统

---

# 阶段 2-2：前端消息状态管理

## 目标

解决聊天状态问题。

## Claude 任务

实现：

- message store
- loading 状态
- retry
- abort
- reconnect

## 完成标准

- 不重复消息
- 不错位
- 可中断生成
- 可重新生成

---

# 阶段 2-3：Prompt 基础架构

## 目标

Prompt 模块化。

## Claude 任务

拆分：

```txt
system prompt
character prompt
memory prompt
safety prompt
user context
```

## 完成标准

- Prompt 可组合
- Prompt 可维护
- Prompt 不写死

---

# 阶段 2-4：LLM Provider 抽象层

## 目标

支持多模型切换。

## Claude 任务

实现：

```txt
OpenAI Provider
GLM Provider
DeepSeek Provider
```

统一接口：

```python
chat()
stream_chat()
```

## 完成标准

- 一键切换模型
- 不影响业务逻辑

---

# 阶段 3：角色系统

目标：

> AI 伴侣真正开始形成“人格”

---

# 阶段 3-1：角色数据结构

## Claude 任务

建立：

```txt
character_profiles
```

字段：

```txt
name
personality
speaking_style
background
emotion_style
avatar
voice
```

## 完成标准

- 可新增角色
- 可切换角色

---

# 阶段 3-2：角色 Prompt Engine

## 目标

让不同角色真的不同。

## Claude 任务

实现：

```txt
Prompt Builder
```

组合：

```txt
system
+ character
+ memory
+ mood
+ context
```

## 完成标准

- 不同角色风格明显
- 人格稳定

---

# 阶段 3-3：角色 UI

## Claude 任务

实现：

- 角色选择页
- 角色详情页
- 角色卡片
- 头像系统

## 完成标准

- 看起来像产品
- 不像 demo

---

# 阶段 3-4：角色配置热更新

## 目标

无需重启即可更新角色。

## Claude 任务

实现：

- JSON/YAML 配置加载
- 热更新
- 配置校验

## 完成标准

- 新角色无需改代码

---

# 阶段 4：记忆系统（核心难点）

目标：

> AI 能长期记住用户

这是整个项目技术核心。

必须慢慢开发。

---

# 阶段 4-1：短期记忆

## 目标

管理上下文窗口。

## Claude 任务

实现：

- 最近 N 条消息
- Token 截断
- Context 压缩

## 完成标准

- 长聊天不爆 token
- 上下文稳定

---

# 阶段 4-2：记忆提取

## 目标

从聊天中提取重要信息。

## Claude 任务

实现：

```txt
memory extraction service
```

提取：

- 用户喜好
- 用户身份
- 长期目标
- 重要事件

## 完成标准

- AI 能自动生成记忆

---

# 阶段 4-3：长期记忆存储

## Claude 任务

实现：

- memory table
- embedding 存储
- 向量检索

## 完成标准

- 可检索历史重要信息

---

# 阶段 4-4：记忆分类

## 分类

```txt
profile memory
event memory
relationship memory
preference memory
```

## 完成标准

- 检索准确
- 不乱记忆

---

# 阶段 4-5：记忆注入

## 目标

把记忆正确加入 Prompt。

## Claude 任务

实现：

- retrieval
- ranking
- context merge

## 完成标准

- AI 能自然提到过去事情
- 不生硬

---

# 阶段 5：语音系统（后期开发）

目标：

> 增强沉浸感

注意：

语音属于增强功能。

不是项目核心。

---

# 阶段 5-1：TTS

## Claude 任务

支持：

```txt
edge-tts
fish audio
minimax
```

## 完成标准

- AI 能语音播放

---

# 阶段 5-2：STT

## Claude 任务

实现：

- whisper
- 实时语音输入

## 完成标准

- 用户可语音输入

---

# 阶段 5-3：语音 UI

## Claude 任务

实现：

- 麦克风按钮
- 播放控制
- 音频波形

## 完成标准

- 用户体验完整

---

# 阶段 5 禁止事项

禁止提前开发：

- 实时 RTC
- Live2D
- 口型同步
- 超低延迟语音

这些会导致项目复杂度爆炸。

---

# 阶段 6：高级 AI 系统

目标：

> 提升陪伴感

---

# 阶段 6-1：情绪系统

## Claude 任务

实现：

```txt
emotion state
mood drifting
emotion memory
```

## 情绪示例

```txt
开心
疲惫
冷淡
依赖
生气
```

## 完成标准

- AI 情绪连续变化

---

# 阶段 6-2：主动消息系统

## Claude 任务

实现：

- 定时消息
- 长时间未聊天提醒
- 主动关心

## 完成标准

- AI 能主动找用户

---

# 阶段 6-3：关系成长系统

## Claude 任务

实现：

```txt
affinity system
relationship stages
```

阶段：

```txt
陌生
熟悉
依赖
```

## 完成标准

- 不同关系阶段行为不同

---

# 阶段 6-4：动态人格

## 目标

让 AI 人格成长。

## Claude 任务

实现：

- personality drift
- user influence

## 完成标准

- 长期聊天后人格微变化

---

# 阶段 7：产品化

目标：

> 让项目真正可上线

---

# 阶段 7-1：用户系统

## Claude 任务

实现：

- 注册
- 登录
- JWT
- 用户资料

## 完成标准

- 多用户支持

---

# 阶段 7-2：部署系统

## Claude 任务

实现：

- Docker
- Nginx
- HTTPS
- 环境变量

## 完成标准

- 云服务器可部署

---

# 阶段 7-3：监控系统

## Claude 任务

实现：

- Sentry
- Metrics
- Token 统计

## 完成标准

- 能查看错误
- 能查看成本

---

# 阶段 7-4：成本控制

## Claude 任务

实现：

- Prompt 缓存
- Token 限制
- 历史压缩

## 完成标准

- 降低 API 成本

---

# 五、推荐里程碑（Milestone）

# M1：最小可运行版本

功能：

- 能聊天
- 有基础 UI
- 支持流式输出

---

# M2：角色版本

功能：

- 多角色
- 角色 Prompt
- 角色 UI

---

# M3：记忆版本

功能：

- 长期记忆
- 记忆检索
- 记忆注入

---

# M4：语音版本

功能：

- TTS
- STT
- 音频播放

---

# M5：完整 AI 伴侣版本

功能：

- 情绪
- 主动消息
- 关系成长

---

# 六、Claude Agent 开发规范

# Claude 单次任务模板

以后所有 Agent 任务必须遵守：

```txt
任务目标：

限制：

允许修改文件：

禁止修改：

输入：

输出：

完成标准：
```

---

# 正确示例

```txt
任务目标：
实现 Message SQLAlchemy Model

允许修改文件：
models/message.py
models/base.py

禁止修改：
frontend
API
memory system

完成标准：
消息可存储
支持 user/assistant role
```

---

# 错误示例

```txt
帮我完善整个聊天系统
```

这种任务范围太大。

Claude 极易失控。

---

# 七、AI 开发高危行为（禁止）

# 1. 一次开发多个系统

禁止：

```txt
聊天 + 记忆 + 语音 一起做
```

---

# 2. 提前优化

禁止：

- 微服务
- Kubernetes
- 分布式
- 超复杂缓存

项目初期完全没必要。

---

# 3. 提前抽象

禁止：

```txt
抽象 15 个 base class
```

项目早期只会增加混乱。

---

# 4. AI 自由重构

禁止：

```txt
Claude 自动优化整个项目结构
```

风险极高。

---

# 八、推荐开发节奏

推荐：

```txt
一天只推进一个模块
```

例如：

```txt
今天只做聊天 streaming
明天只做 message store
后天只做 Prompt Builder
```

不要同时推进多个系统。

---

# 九、当前推荐下一步

现在推荐开发顺序：

```txt
1. 项目结构整理
2. 配置系统
3. 日志系统
4. 数据库初始化
5. 最小聊天链路
6. 流式输出
7. Prompt 架构
8. 多模型支持
9. 角色系统
10. 短期记忆
11. 长期记忆
12. UI 美化
13. 语音系统
14. 高级 AI 系统
15. 部署上线
```

---

# 十、最终核心原则

这个项目最重要的不是：

- 功能数量
- 花哨 UI
- 高级技术名词

而是：

```txt
稳定
可维护
可扩展
AI 能持续开发
```

真正成功的 AI 项目：

不是一次性做完。

而是：

> 每个阶段都稳定可运行。

这才是最适合 Claude Agent 的开发方式。

