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

### ISSUE-011 — FIXED
- **关联 TASK:** PH9-003, PH9-004
- **严重级别:** Critical
- **描述:** 前端 `synthesizeSpeech()` 调用 `POST /api/v1/voice/tts` 时发送的是 JSON 请求体，而后端 `/voice/tts` 当前实现使用 `Form(...)` 接收参数，导致语音播放链路会在运行时请求失败。
- **根因:** Wave 1/2 分别实现前后端时，`VoiceSynthesisRequest` 的 JSON 语义与后端 `Form` 风格未对齐，接口契约发生分叉。
- **影响:** STT 可以独立工作，但 TTS 播放按钮无法成功拿到音频响应，`Phase 9` 浏览器 E2E 无法通过。
- **建议修复:** 统一 `/voice/tts` 契约；优先让后端直接接收 `VoiceSynthesisRequest` JSON 体，与现有前端 API client 保持一致，并补运行时验证。
- **修复结果:** `PH9-FIX-001` 已完成，`/api/v1/voice/tts` 现已与前端 JSON 请求体对齐，运行时与浏览器播放链路通过。

### ISSUE-012 — FIXED
- **关联 TASK:** PH9-001, PH9-004, PH9-005
- **严重级别:** Critical
- **描述:** `Phase 9` 运行时验收中，`GET /api/v1/voice/health` 和浏览器“播放语音”链路都返回 `Voice service is disabled by configuration`，导致 STT/TTS 无法进入真实 provider 调用。
- **根因:** 当前 `backend/config.py` 将 `VOICE_ENABLED` 默认值设为 `false`。在现有环境里 `AI_API_KEY` 与 `AI_BASE_URL` 都已配置，因此真正阻断功能的是默认关闭策略。
- **影响:** 语音录音/播放 UI 虽已接入且降级提示正常，但 `Phase 9` 的核心语音闭环无法通过运行时与浏览器验收。
- **建议修复:** 将 `VOICE_ENABLED` 默认值改为启用，保留通过 `.env` 显式关闭的能力；修复后重启后端，重新执行 `/voice/health`、`/voice/tts` 与浏览器播放链路验证。
- **修复结果:** `PH9-FIX-002` 已完成，默认配置已恢复为启用，`/voice/health` 返回 `200`。

### ISSUE-013 — FIXED
- **关联 TASK:** PH9-002, PH9-004, PH9-005
- **严重级别:** Critical
- **描述:** 在 `VOICE_ENABLED` 默认开启后，`/voice/health` 已返回 `200`，但真实调用 `POST /api/v1/voice/tts` 与 `POST /api/v1/voice/stt` 时，provider 返回 `503: No available channel for model gpt-4o-mini-tts / gpt-4o-mini-transcribe`。
- **根因:** 当前网关 `api.xykjy.com` 对默认配置的音频模型没有可用通道；问题已从本地代码/配置层收敛为外部 provider 能力不足。
- **影响:** 文本聊天、语音 UI、错误降级都已正常，但 `Phase 9` 的“真实语音闭环”仍无法通过浏览器 E2E 验收。
- **建议修复:** 需要在产品/架构层二选一：1) 切换到 provider 实际支持的 STT/TTS 模型；2) 更换语音 provider（例如单独的 TTS/STT 服务）。在此决策前，不建议继续扩写本地业务代码。
- **修复结果:** 已切换语音 provider 到 `SiliconFlow`，并将 `STT` 调整为实测可用的 `TeleAI/TeleSpeechASR`、`TTS` 调整为 `FunAudioLLM/CosyVoice2-0.5B`，`/voice/stt` 与 `/voice/tts` 均已通过运行时验证。

### ISSUE-014 — FIXED
- **关联 TASK:** PH9-FIX-002
- **严重级别:** Critical
- **描述:** 将全局 `AI_BASE_URL` / `AI_API_KEY` 切到 `SiliconFlow` 后，语音端点已验证可用，但聊天主链路 `POST /api/v1/chat/send` 在浏览器中返回 `AI API error (400)`。
- **根因:** 当前项目的聊天与语音共用同一套 `AI_BASE_URL` / `AI_API_KEY` 配置；`SiliconFlow` 的音频接口可用，但不应直接替代现有聊天 provider 配置。
- **影响:** 如果继续共用一套 provider，`Phase 9` 会出现“语音通了、聊天坏了”的回归，无法满足“语音功能不破坏文本聊天主链路”的验收要求。
- **建议修复:** 拆分“聊天 provider”与“语音 provider”配置。保留现有聊天网关给 `/chat/send`，新增 `VOICE_API_KEY` / `VOICE_BASE_URL` 专供 `voice_service.py` 使用。
- **修复结果:** `PH9-FIX-003` 已完成，聊天继续使用 `api.xykjy.com`，语音改为独立 `VOICE_API_KEY` / `VOICE_BASE_URL` 配置；`/chat/send` 与页面文本聊天已恢复通过。

### ISSUE-015 — FIXED
- **关联 TASK:** PH10-002
- **严重级别:** Major
- **描述:** `PH10-002` 已实现混合排序公式，但 `backend/services/memory_service.py` 仍使用文件内硬编码的权重、阈值、半衰期和类型上限，导致 `backend/config.py` 中 Phase 10 新增的检索配置常量没有实际生效。
- **根因:** `MemoryService` 在引入混合排序时把配置默认值复制到了本文件常量中，而不是直接消费 `backend.config` 暴露的 `MEMORY_WEIGHT_*`、`MEMORY_TYPE_WEIGHT_*`、`MEMORY_SEMANTIC_THRESHOLD`、`MEMORY_RECENCY_HALFLIFE_DAYS`、`MEMORY_MAX_*`。
- **影响:** `PH10-002` 的“混合排序权重可配置”完成标准未满足；即使后续调整 `config.py`，`search_memories()` 排序行为也不会变化，`summary` 压制长期事实的问题无法通过调参修正。
- **建议修复:** 创建 `PH10-FIX-001`，将 `memory_service.py` 的硬编码检索参数切换为直接读取 `backend.config`，并补最小回归验证，确认 `return_debug_scores=True` 输出与实际配置一致。
- **修复结果:** `PH10-FIX-001` 已完成并通过三轮审查；`memory_service.py` 现已直接消费 Phase 10 检索配置常量，`return_debug_scores=True` 输出与配置一致，`PH10-002` 原始验收标准恢复通过。

### ISSUE-016 — FIXED
- **关联 TASK:** BUG-FIX-003, BUG-FIX-006
- **严重级别:** Major
- **描述:** `BUG-FIX-003` 已把代码默认 TTS 声线改为 `nova`，但真实运行中的 `/api/v1/voice/health` 仍返回 `tts_voice="FunAudioLLM/CosyVoice2-0.5B:alex"`，用户侧默认仍是男性声线。
- **根因:** `.env` 中的 `VOICE_TTS_VOICE` 覆盖了 `backend/config.py` 的默认值；代码默认值生效了，但运行环境没有同步更新。
- **影响:** BUG-005 在真实用户环境中仍未修复；前端“播放语音”继续使用男性默认声线，体验目标未达成。
- **建议修复:** 创建 `BUG-FIX-006`，只同步运行环境中的 `VOICE_TTS_VOICE` 到符合女性陪伴角色体验的默认声线，并重新验证 `/voice/health` 与前端播放链路。
- **修复结果:** `BUG-FIX-006` 已通过复验；现网 `/api/v1/voice/health` 返回的 `tts_voice` 已切换为 `FunAudioLLM/CosyVoice2-0.5B:anna`，且 `/api/v1/voice/tts` 在省略 `voice` 或传入 `default` 时都能返回音频。
- **再次复验（2026-06-01）:** `VERIFY-VOICE-001` 运行时复验通过；本地 `127.0.0.1:8000` 返回 `tts_voice=FunAudioLLM/CosyVoice2-0.5B:anna`，确认不是文档已写但进程未生效的假修复。

### ISSUE-017 — FIXED
- **关联 TASK:** BUG-FIX-004, BUG-FIX-007
- **严重级别:** Major
- **描述:** `BUG-FIX-004` 已在 `prompt_builder.py` 添加“短回复、轻节奏”指令，但真实运行时默认日常聊天仍经常输出 200~300 字、约 7 句的长回复。
- **根因:** 当前改动仍然主要依赖软提示约束，没有足够强的默认短回复限制来稳定压住安抚型角色的长篇表达倾向。
- **影响:** BUG-006 未通过；用户仍会明显感知到“大段 AI 输出”和偏重的 AI 味。
- **建议修复:** 创建 `BUG-FIX-007`，继续加强默认短回复约束，只改 `prompt_builder.py`，并重点复验小暖这类安抚型角色的默认日常聊天场景。
- **修复结果:** `BUG-FIX-007` 已通过静态、运行时与浏览器复验；新建会话下“小暖”对“陪我说两句 / 我准备睡了 / 今天有点累”等默认日常输入，回复稳定收敛到 2 句、约 25~34 字，不再回成长篇安慰文；浏览器端流式渲染与角色差异表现未回归。
- **再次复验（2026-06-01）:** `VERIFY-REPLY-001` 运行时复验通过；小暖 6 次固定话术抽样均为 1~2 句、约 21~39 字，小锐对照样本也保持短回复且人设差异正常。

### ISSUE-018 — FIXED
- **关联 TASK:** BUG-FIX-005, BUG-FIX-008
- **严重级别:** Major
- **描述:** `BUG-FIX-005` 的滚动与会话恢复主链路基本成立，但“刚发送完成就立即刷新”时，最新一轮消息仍可能暂时恢复不到。
- **根因:** 会话快照存在短暂可见性窗口：同一会话在 `POST /chat/send` 完成后立刻请求 `GET /chat/session/{id}`，可能先返回 `messages: []`，等待约 2 秒后才返回完整消息。
- **影响:** BUG-008 仍未完全修复；用户在极端但真实的刷新时机会回到空白聊天态或丢失刚完成的一轮消息。
- **建议修复:** 创建 `BUG-FIX-008`，在前端为当前会话补充最新消息恢复兜底，确保“发送完成即刷新”也能恢复最新内容，同时不破坏现有滚动与洞察体验。
- **修复结果:** `BUG-FIX-008` 已通过浏览器与 API 复验；刷新后当前 persona 会恢复到正确会话，本地快照可兜住“发送完成即刷新”场景，且未出现重复消息、跨 persona 串会话或滚动体验回归。
- **再次复验（2026-06-01）:** `VERIFY-SESSION-001` 浏览器与 API 复验通过；立即刷新可恢复最新一轮消息，未复现重复消息、跨 persona 串会话，聊天区与洞察区独立滚动也保持可用。

### ISSUE-019 — FIXED
- **关联 TASK:** BUG-FIX-009
- **严重级别:** Critical
- **描述:** 用户在聊天页完成录音后，`POST /api/v1/voice/stt` 返回 `422`，导致语音转写失败，文本无法回填到输入框。
- **根因:** 前端 [frontend/src/lib/api.ts](/E:/ai-companion/frontend/src/lib/api.ts:378) 当前使用 `formData.append("file", ...)` 上传音频，但后端 [backend/api/chat.py](/E:/ai-companion/backend/api/chat.py:203) 的 `speech_to_text(audio: UploadFile = File(...))` 要求 multipart 字段名为 `audio`。字段名不一致会直接触发 FastAPI `422` 校验错误。
- **影响:** 语音录音按钮表面可用，但录音后的核心 `STT` 闭环被阻断，用户无法完成“录音 -> 转写 -> 回填输入框”链路。
- **建议修复:** 创建 `BUG-FIX-009`，优先保持后端 `/voice/stt` 现有契约不变，只修正前端上传字段名与错误提示链路；修复后需做运行时与浏览器录音转写复验。
- **修复结果:** `BUG-FIX-009` 已通过独立 Review；前端上传字段名已改为 `audio`，运行时验证确认 `/api/v1/voice/stt` 不再因为字段名问题返回 `422`。
- **复验说明:** Review 的等价运行时验证还观察到 synthetic 音频样本会触发上游 `503: Speech-to-text provider response did not include transcribed text`。这表明 `422` 契约问题已修复，但真实录音链路仍建议继续做用户复测。

### ISSUE-020 — FIXED
- **关联 TASK:** BUG-FIX-010
- **严重级别:** Critical
- **描述:** 用户用真实浏览器录音后，`/api/v1/voice/stt` 不再返回 `422`，但页面报错升级为 `Speech-to-text provider returned HTTP 400: Unsupported audio format... (503)`。
- **根因:** 前端录音优先使用 `audio/webm;codecs=opus` / `audio/ogg;codecs=opus` 这类带 codec 参数的 MIME；后端 [backend/services/voice_service.py](/E:/ai-companion/backend/services/voice_service.py:216) 当前 `_extension_for_mime()` 只按精确字符串做映射，遇到带 `;codecs=...` 的 MIME 会回落为 `bin` 扩展名，导致上游 `STT provider` 将文件识别为不支持格式。
- **影响:** 语音录音请求已经穿过前后端契约层，但真实用户录音仍无法完成转写，`录音 -> STT -> 文本回填` 主链路继续中断。
- **建议修复:** 创建 `BUG-FIX-010`，仅修正后端 `voice_service.py` 的 MIME 归一化与扩展名推断逻辑，正确兼容 `audio/webm;codecs=opus`、`audio/ogg;codecs=opus` 以及其它 provider 支持的常见 MIME 变体；修复后必须用真实 MIME 样本做运行时复验。
- **修复结果:** `BUG-FIX-010` 已合入当前发布版本；后端已补充 MIME 归一化与扩展名推断，真实浏览器语音输入经用户验收确认可用，不再作为主分支发布阻断项。
