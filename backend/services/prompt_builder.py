"""Prompt Builder — assembles persona + history into AI API messages."""

import json
import re


_MEMORY_SECTION_LABELS = {
    "facts": "用户事实",
    "preferences": "偏好习惯",
    "recent_events": "近期事件",
    "other": "补充上下文",
}
_MAX_MEMORY_ENTRIES_PER_SECTION = 2


def _clean_memory_line(line: str) -> str:
    """Normalize a raw memory line coming from the memory search context."""
    cleaned = line.strip()
    cleaned = re.sub(r"^\d+\.\s*", "", cleaned)
    cleaned = re.sub(r"^[-*•]\s*", "", cleaned)
    return cleaned.strip()


def _classify_memory_line(line: str) -> str:
    """Group a memory line into a small set of prompt-friendly sections."""
    lowered = line.lower()

    preference_keywords = (
        "喜欢", "不喜欢", "偏好", "习惯", "爱吃", "爱喝", "常常", "平时", "更喜欢",
        "prefer", "favorite", "like ", "dislike", "usually",
    )
    recent_event_keywords = (
        "今天", "昨天", "前天", "最近", "刚刚", "刚才", "这周", "上周", "本周",
        "明天", "今晚", "周末", "目前", "这几天", "recently", "today", "yesterday",
        "tomorrow", "just", "currently",
    )
    fact_keywords = (
        "我是", "我叫", "名字", "年龄", "岁", "职业", "工作", "上班", "学校", "学生",
        "住在", "来自", "家里", "家人", "专业", "生日", "name", "age", "job",
        "work", "live", "family", "study",
    )

    if any(keyword in lowered for keyword in preference_keywords):
        return "preferences"
    if any(keyword in lowered for keyword in recent_event_keywords):
        return "recent_events"
    if any(keyword in lowered for keyword in fact_keywords):
        return "facts"
    return "other"


def _format_memory_context(memory_context: str | None) -> str | None:
    """Convert raw memory lines into a compact structured memory block."""
    if not memory_context or not memory_context.strip():
        return None

    grouped_memories = {key: [] for key in _MEMORY_SECTION_LABELS}
    for raw_line in memory_context.splitlines():
        cleaned_line = _clean_memory_line(raw_line)
        if not cleaned_line:
            continue

        bucket = _classify_memory_line(cleaned_line)
        if cleaned_line not in grouped_memories[bucket]:
            grouped_memories[bucket].append(cleaned_line)

    sections = []
    for key, label in _MEMORY_SECTION_LABELS.items():
        entries = grouped_memories[key][:_MAX_MEMORY_ENTRIES_PER_SECTION]
        if not entries:
            continue
        section_lines = [f"- {entry}" for entry in entries]
        sections.append(f"{label}：\n" + "\n".join(section_lines))

    if not sections:
        return None

    return "\n\n".join(sections)


def build_system_prompt(persona: dict, emotion_state: dict | None = None, memory_context: str | None = None) -> str:
    traits_str = json.dumps(persona.get("emotional_traits", {}), ensure_ascii=False)
    base = (
        f"你是{persona.get('name', 'AI助手')}。\n"
        f"性格：{persona.get('personality', '')}\n"
        f"说话风格：{persona.get('speaking_style', '')}\n"
        f"背景：{persona.get('background_story', '')}\n"
        f"情绪特质：{traits_str}\n"
        f"---\n"
        f"请严格按照以上设定回复。不要跳出角色设定。\n\n"
        f"【回复节奏要求】\n"
        f"- 默认按即时陪伴聊天来回复，整体短一点、轻一点、自然一点。\n"
        f"- 把短回复当作默认硬规则，不要依赖自己自由发挥控制长度。\n"
        f"- 单轮回复默认只写1到2句，只有确实需要补一句时才写到3句。\n"
        f"- 每句尽量短，优先一句表达一个意思，不要把一句拉成长复句。\n"
        f"- 先用一句直接接住用户此刻的话题、情绪或动作，再决定要不要补第二句。\n"
        f"- 如果用户只是随便聊聊、求陪伴、打招呼、说晚安、撒娇、倾诉一下，通常回1到2句就够了。\n"
        f"- 先回应用户当下的话题或情绪，再继续聊，不要上来就长篇解释。\n"
        f"- 除非用户明确要求详细分析、建议、步骤或长回答，否则不要展开成长文。\n"
        f"- 除非用户明确追问，否则不要主动补背景、举例、分析原因、做总结或给多条建议。\n"
        f"- 默认不要自发输出三句以上，不要分很多小段，不要列条目，不要写成小作文。\n"
        f"- 避免总结腔、教程腔、条目式说教，像日常陪伴聊天那样表达。\n"
        f"- 安抚型、温柔型角色也要克制长度，重点是轻轻回应，不要堆抒情、不做长段安慰文。\n"
        f"- 保留角色差异，可以有各自的语气和态度，但不要输出大段空泛内容。"
    )
    if emotion_state:
        base += (
            f"\n\n【当前情绪状态】\n"
            f"- 好感度：{emotion_state.get('favorability', 0)}/100\n"
            f"- 信任度：{emotion_state.get('trust', 0)}/100\n"
            f"- 心情：{emotion_state.get('mood', 'neutral')}\n"
            f"- 依赖度：{emotion_state.get('dependency', 0)}/100\n"
            f"\n请根据当前情绪状态调整回复的语气和内容。"
        )
    structured_memory_context = _format_memory_context(memory_context)
    if structured_memory_context:
        base += (
            f"\n\n【相关记忆】\n"
            f"{structured_memory_context}\n\n"
            f"请优先结合用户事实、偏好和近期事件自然回应，不要机械复述或逐条列举。"
            f" 只挑最相关的1到2个点轻轻带入当前回复即可。"
        )
    return base


def build_messages(persona: dict, history: list[dict], user_message: str, emotion_state: dict | None = None, memory_context: str | None = None) -> list[dict]:
    system_content = build_system_prompt(persona, emotion_state, memory_context)
    messages = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    return messages
