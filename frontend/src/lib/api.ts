const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export interface Persona {
  id: string;
  name: string;
  personality: string;
  speaking_style: string;
  background_story: string;
  emotional_traits: Record<string, string>;
  avatar_url: string | null;
  created_at: string;
}

export interface EmotionState {
  session_id: string;
  favorability: number;
  trust: number;
  mood: string;
  dependency: number;
  updated_at: string;
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch(`${API_BASE}/personas`);
  if (!res.ok) throw new Error(`获取角色列表失败 (${res.status})`);
  const data = await res.json();
  return data.data.personas;
}

export async function createSession(personaId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/chat/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona_id: personaId }),
  });
  if (!res.ok) throw new Error(`创建会话失败 (${res.status})`);
  const data = await res.json();
  return data.data.session_id;
}

export async function fetchEmotion(sessionId: string): Promise<EmotionState | null> {
  try {
    const res = await fetch(`${API_BASE}/emotion/${sessionId}`);
    const data = await res.json();
    return data.data || null;
  } catch {
    return null;
  }
}

export function sendMessage(
  sessionId: string,
  personaId: string,
  message: string,
  onToken: (text: string) => void,
  onDone: (error?: string) => void,
): AbortController {
  const controller = new AbortController();
  let reader: ReadableStreamDefaultReader<Uint8Array> | null = null;
  let finished = false;

  const finish = (error?: string) => {
    if (finished) return;
    finished = true;
    if (reader) {
      void reader.cancel().catch(() => undefined);
    }
    onDone(error);
  };

  const processEvent = (eventBlock: string) => {
    const dataLines = eventBlock
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart());

    for (const dataLine of dataLines) {
      if (!dataLine) continue;
      if (dataLine === "[DONE]") {
        finish();
        return;
      }

      try {
        const json = JSON.parse(dataLine);
        if (json.error) {
          finish(json.error);
          return;
        }
        if (json.text) {
          onToken(json.text);
        }
        if (json.done) {
          finish();
          return;
        }
      } catch {
        // Skip malformed SSE frames without breaking the session.
      }
    }
  };

  fetch(`${API_BASE}/chat/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, persona_id: personaId, message }),
    signal: controller.signal,
  }).then(async (response) => {
    if (!response.ok) {
      const errText = await response.text().catch(() => "");
      finish(`服务器错误 (${response.status}): ${errText}`);
      return;
    }

    reader = response.body?.getReader() ?? null;
    if (!reader) {
      finish("无法读取响应流");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";
    try {
      while (!finished) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const normalized = buffer.replace(/\r\n/g, "\n");
        const events = normalized.split("\n\n");
        buffer = events.pop() || "";
        for (const eventBlock of events) {
          if (finished) break;
          processEvent(eventBlock);
        }
      }
    } catch (e: any) {
      if (controller.signal.aborted) {
        finish();
        return;
      }
      finish(e?.message || "连接中断");
      return;
    }

    if (!finished) {
      buffer += decoder.decode();
      const tail = buffer.replace(/\r\n/g, "\n").trim();
      if (tail) {
        processEvent(tail);
      }
    }

    finish();
  }).catch((e) => {
    if (e.name === "AbortError" || controller.signal.aborted) {
      finish();
      return;
    }
    finish(`网络错误: ${e.message}`);
  });

  return controller;
}
