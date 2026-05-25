"""Prompt Builder — assembles persona + history into AI API messages."""

import json


def build_system_prompt(persona: dict) -> str:
    traits_str = json.dumps(persona.get("emotional_traits", {}), ensure_ascii=False)
    return (
        f"你是{persona.get('name', 'AI助手')}。\n"
        f"性格：{persona.get('personality', '')}\n"
        f"说话风格：{persona.get('speaking_style', '')}\n"
        f"背景：{persona.get('background_story', '')}\n"
        f"情绪特质：{traits_str}\n"
        f"---\n"
        f"请严格按照以上设定回复。不要跳出角色设定。"
    )


def build_messages(persona: dict, history: list[dict], user_message: str) -> list[dict]:
    system_content = build_system_prompt(persona)
    messages = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
    messages.append({"role": "user", "content": user_message})
    return messages
