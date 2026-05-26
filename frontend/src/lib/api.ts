const API_BASE = "http://localhost:8000/api/v1";

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
  mood: number;
  dependency: number;
  updated_at: string;
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch(`${API_BASE}/personas`);
  const data = await res.json();
  return data.data.personas;
}

export async function createSession(personaId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/chat/session`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona_id: personaId }),
  });
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

// SSE stream helper
export function sendMessage(
  sessionId: string,
  personaId: string,
  message: string,
  onToken: (text: string) => void,
  onDone: () => void
): AbortController {
  const controller = new AbortController();
  fetch(`${API_BASE}/chat/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, persona_id: personaId, message }),
    signal: controller.signal,
  }).then(async (response) => {
    const reader = response.body?.getReader();
    if (!reader) return;
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n\n");
      buffer = lines.pop() || "";
      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const json = JSON.parse(line.slice(6));
          if (json.done) {
            onDone();
            return;
          }
          if (json.text) onToken(json.text);
        }
      }
    }
  }).catch(() => {});
  return controller;
}
