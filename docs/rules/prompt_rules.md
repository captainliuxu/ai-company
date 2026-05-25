# Prompt Rules

## Structure Rules

- System Prompt 必须拆分为 Block（Persona / Emotion / Memory / Rules）
- 每个 Block 独立可测试
- Block 之间用 `\n\n` 分隔（不是随意的分隔符）
- 总 system_prompt ≤ 2000 tokens（避免吃掉太多上下文）

## Persona Block

- 包含：name, personality, speaking_style, background_story, emotional_traits
- 用第二人称 "你是XXX"（直接告诉模型它扮演谁）
- 不超过 500 tokens

## Emotion Block

- 包含：favorability, trust, mood, dependency 四个维度
- 数值 + 文字标签（如 "好感度 55/100，尚可"）
- 指导语气调整而非限制回复内容
- 不超过 200 tokens

## Memory Block

- 格式：bullet list "关于用户，你知道："
- 最多 5 条（RAG top_k）
- 自然融入回复，不要刻意复述
- 不超过 300 tokens

## Rules Block

- 回复格式约束
- 字数控制
- 身份声明（AI伴侣，不是人类）
- 不超过 200 tokens

## Testing Rules

- 每个角色的 Prompt 手动测试至少 3 轮对话
- 确认不同角色风格差异明显
- 确认 Prompt 注入后模型不崩（不乱码/不重复/不跑题）

## [FUTURE]

- A/B Testing 框架
- Prompt 版本管理
- 多语言模板
- 基于用户反馈的 Prompt 自动调优
