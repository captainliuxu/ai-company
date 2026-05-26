"""Prompt Builder — assembles persona + history into AI API messages."""

import json


def build_system_prompt(persona: dict, emotion_state: dict | None = None, memory_context: str | None = None) -> str:
    traits_str = json.dumps(persona.get("emotional_traits", {}), ensure_ascii=False)
    base = (
        f"你是{persona.get('name', 'AI助手')}。\n"
        f"性格：{persona.get('personality', '')}\n"
        f"说话风格：{persona.get('speaking_style', '')}\n"
        f"背景：{persona.get('background_story', '')}\n"
        f"情绪特质：{traits_str}\n"
        f"---\n"
        f"请严格按照以上设定回复。不要跳出角色设定。"
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
    if memory_context:
        base += f"\n\n【相关记忆】\n{memory_context}\n\n请自然融入回复中，不要刻意列举。"
    return base


def build_messages(persona: dict, history: list[dict], user_message: str, emotion_state: dict | None = None, memory_context: str | None = None) -> list[dict]:
    system_content = build_system_prompt(persona, emotion_state, memory_context)
    messages = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    return messages
