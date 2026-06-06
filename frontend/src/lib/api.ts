const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

interface ApiEnvelope<T> {
  success?: boolean;
  message?: string;
  data?: T | null;
}

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
  created_at: string | null;
  updated_at: string | null;
}

export type MemoryType = "user_info" | "preference" | "event" | "emotion" | "summary";

export interface MemoryItem {
  id: string;
  session_id: string;
  type: MemoryType;
  content: string;
  importance: number;
  created_at: string | null;
}

export interface EmotionHistoryItem {
  session_id: string;
  favorability: number;
  trust: number;
  mood: string;
  dependency: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatSessionSnapshot {
  session_id: string;
  persona_id: string;
  created_at: string;
  messages: ChatMessage[];
}

export interface CachedChatSessionSnapshot {
  session_id: string;
  persona_id: string;
  messages: ChatMessage[];
  updated_at: string;
}

const CHAT_SNAPSHOT_STORAGE_PREFIX = "ai-companion:chat-snapshot:";

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readString(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function readNullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function readNumber(value: unknown, fallback = 0): number {
  return typeof value === "number" && Number.isFinite(value) ? value : fallback;
}

function readApiMessage(payload: unknown): string | null {
  if (!isRecord(payload)) return null;
  const message = payload.message;
  return typeof message === "string" && message.trim() ? message.trim() : null;
}

async function parseApiEnvelope<T>(res: Response, fallbackMessage: string): Promise<ApiEnvelope<T>> {
  const payload: unknown = await res.json().catch(() => null);

  if (!res.ok) {
    const message = readApiMessage(payload) || fallbackMessage;
    throw new Error(`${message} (${res.status})`);
  }

  if (!isRecord(payload)) {
    throw new Error(`${fallbackMessage}：响应格式无效`);
  }

  return payload as ApiEnvelope<T>;
}

async function parseApiError(res: Response, fallbackMessage: string): Promise<never> {
  const responseText = await res.text().catch(() => "");
  let payload: unknown = null;

  if (responseText) {
    try {
      payload = JSON.parse(responseText) as unknown;
    } catch {
      payload = null;
    }
  }

  const message = readApiMessage(payload) || responseText.trim() || fallbackMessage;
  throw new Error(`${message} (${res.status})`);
}

function requireEnvelopeDataRecord<T>(payload: ApiEnvelope<T>, fallbackMessage: string): Record<string, unknown> {
  if (!isRecord(payload.data)) {
    throw new Error(`${fallbackMessage}：响应数据无效`);
  }

  return payload.data;
}

function requireEnvelopeArrayField(
  data: Record<string, unknown>,
  field: string,
  fallbackMessage: string,
): unknown[] {
  const value = data[field];
  if (!Array.isArray(value)) {
    throw new Error(`${fallbackMessage}：响应数据无效`);
  }

  return value;
}

function requireNormalizedArrayItem<T>(
  raw: unknown,
  index: number,
  normalize: (value: unknown) => T | null,
  fallbackMessage: string,
): T {
  const item = normalize(raw);
  if (item === null) {
    throw new Error(`${fallbackMessage}：第 ${index + 1} 项数据无效`);
  }

  return item;
}

function buildApiUrl(path: string, query?: URLSearchParams): string {
  const queryString = query?.toString();
  return queryString ? `${API_BASE}${path}?${queryString}` : `${API_BASE}${path}`;
}

function canUseStorage(): boolean {
  return typeof window !== "undefined" && typeof window.localStorage !== "undefined";
}

function buildChatSnapshotStorageKey(sessionId: string): string {
  return `${CHAT_SNAPSHOT_STORAGE_PREFIX}${sessionId}`;
}

function normalizeChatMessages(raw: unknown): ChatMessage[] | null {
  if (!Array.isArray(raw)) {
    return null;
  }

  const messages: ChatMessage[] = [];
  for (const item of raw) {
    const normalized = normalizeChatMessage(item);
    if (!normalized) {
      return null;
    }
    messages.push(normalized);
  }

  return messages;
}

function isMessagePrefix(prefix: ChatMessage[], full: ChatMessage[]): boolean {
  if (prefix.length > full.length) {
    return false;
  }

  for (let index = 0; index < prefix.length; index += 1) {
    const left = prefix[index];
    const right = full[index];
    if (left.role !== right.role || left.content !== right.content) {
      return false;
    }
  }

  return true;
}

function normalizeCachedChatSessionSnapshot(raw: unknown): CachedChatSessionSnapshot | null {
  if (!isRecord(raw)) return null;

  const sessionId = readString(raw.session_id).trim();
  const personaId = readString(raw.persona_id).trim();
  const updatedAt = readString(raw.updated_at).trim();
  const messages = normalizeChatMessages(raw.messages);

  if (!sessionId || !personaId || !updatedAt || !messages) {
    return null;
  }

  return {
    session_id: sessionId,
    persona_id: personaId,
    messages,
    updated_at: updatedAt,
  };
}

function normalizeEmotionState(raw: unknown): EmotionState | null {
  if (!isRecord(raw)) return null;

  const createdAt = readNullableString(raw.created_at);
  const updatedAt = readNullableString(raw.updated_at) ?? createdAt;

  return {
    session_id: readString(raw.session_id),
    favorability: readNumber(raw.favorability),
    trust: readNumber(raw.trust),
    mood: readString(raw.mood, "neutral"),
    dependency: readNumber(raw.dependency),
    created_at: createdAt,
    updated_at: updatedAt,
  };
}

function normalizeMemoryItem(raw: unknown): MemoryItem | null {
  if (!isRecord(raw)) return null;

  return {
    id: readString(raw.id),
    session_id: readString(raw.session_id),
    type: readString(raw.type) as MemoryType,
    content: readString(raw.content),
    importance: readNumber(raw.importance, 3),
    created_at: readNullableString(raw.created_at),
  };
}

function normalizeChatMessage(raw: unknown): ChatMessage | null {
  if (!isRecord(raw)) return null;

  const role = raw.role;
  const content = readString(raw.content).trim();
  if ((role !== "user" && role !== "assistant") || !content) {
    return null;
  }

  return {
    role,
    content,
  };
}

export async function fetchPersonas(): Promise<Persona[]> {
  const res = await fetch(buildApiUrl("/personas"));
  const payload = await parseApiEnvelope<{ personas?: Persona[] }>(res, "获取角色列表失败");
  return Array.isArray(payload.data?.personas) ? payload.data.personas : [];
}

export async function createSession(personaId: string): Promise<string> {
  const res = await fetch(buildApiUrl("/chat/session"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona_id: personaId }),
  });
  const payload = await parseApiEnvelope<{ session_id?: string }>(res, "创建会话失败");
  const sessionId = payload.data?.session_id;
  if (typeof sessionId !== "string" || !sessionId) {
    throw new Error("创建会话失败：响应缺少 session_id");
  }
  return sessionId;
}

export async function fetchSession(sessionId: string): Promise<ChatSessionSnapshot> {
  const res = await fetch(buildApiUrl(`/chat/session/${encodeURIComponent(sessionId)}`));
  const payload = await parseApiEnvelope<unknown>(res, "获取会话失败");
  const data = requireEnvelopeDataRecord(payload, "获取会话失败");
  const messages = requireEnvelopeArrayField(data, "messages", "获取会话失败");
  const personaId = readString(data.persona_id);
  const createdAt = readString(data.created_at);
  const normalizedMessages = messages.map((item, index) =>
    requireNormalizedArrayItem(item, index, normalizeChatMessage, "获取会话失败"),
  );

  if (!personaId || !createdAt) {
    throw new Error("获取会话失败：响应数据无效");
  }

  return {
    session_id: readString(data.session_id, sessionId),
    persona_id: personaId,
    created_at: createdAt,
    messages: normalizedMessages,
  };
}

export function readCachedSessionSnapshot(sessionId: string): CachedChatSessionSnapshot | null {
  if (!sessionId || !canUseStorage()) {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(buildChatSnapshotStorageKey(sessionId));
    if (!raw) {
      return null;
    }

    return normalizeCachedChatSessionSnapshot(JSON.parse(raw) as unknown);
  } catch {
    return null;
  }
}

export function writeCachedSessionSnapshot(snapshot: CachedChatSessionSnapshot): void {
  if (!canUseStorage()) {
    return;
  }

  try {
    window.localStorage.setItem(buildChatSnapshotStorageKey(snapshot.session_id), JSON.stringify(snapshot));
  } catch {
    // Ignore storage failures and keep network-backed recovery path available.
  }
}

export function clearCachedSessionSnapshot(sessionId: string): void {
  if (!sessionId || !canUseStorage()) {
    return;
  }

  try {
    window.localStorage.removeItem(buildChatSnapshotStorageKey(sessionId));
  } catch {
    // Ignore storage failures.
  }
}

export function mergeSessionMessages(
  snapshotMessages: ChatMessage[],
  cachedMessages: ChatMessage[],
): ChatMessage[] {
  if (!cachedMessages.length) {
    return snapshotMessages;
  }

  if (!snapshotMessages.length) {
    return cachedMessages;
  }

  if (isMessagePrefix(snapshotMessages, cachedMessages)) {
    return cachedMessages;
  }

  if (isMessagePrefix(cachedMessages, snapshotMessages)) {
    return snapshotMessages;
  }

  return snapshotMessages;
}

export async function transcribeAudio(audio: Blob | File): Promise<string> {
  const formData = new FormData();
  const fileName =
    typeof File !== "undefined" && audio instanceof File && audio.name
      ? audio.name
      : "recording.webm";

  formData.append("audio", audio, fileName);

  const res = await fetch(buildApiUrl("/voice/stt"), {
    method: "POST",
    body: formData,
  });
  const payload = await parseApiEnvelope<{ text?: string }>(res, "语音转写失败");
  const text = payload.data?.text;

  if (typeof text !== "string" || !text.trim()) {
    throw new Error("语音转写失败：响应缺少 text");
  }

  return text;
}

export async function synthesizeSpeech(
  text: string,
  sessionId: string,
  personaId: string,
): Promise<Blob> {
  const res = await fetch(buildApiUrl("/voice/tts"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text,
      session_id: sessionId,
      persona_id: personaId,
    }),
  });

  if (!res.ok) {
    return parseApiError(res, "语音合成失败");
  }

  const audio = await res.blob().catch(() => null);
  if (!(audio instanceof Blob) || audio.size === 0) {
    throw new Error("语音合成失败：响应音频无效");
  }

  return audio;
}

export async function fetchEmotion(sessionId: string): Promise<EmotionState | null> {
  try {
    const res = await fetch(buildApiUrl(`/emotion/${encodeURIComponent(sessionId)}`));
    const payload = await parseApiEnvelope<unknown>(res, "获取当前情绪失败");
    return normalizeEmotionState(payload.data);
  } catch {
    return null;
  }
}

export async function fetchMemories(sessionId: string, type?: string): Promise<MemoryItem[]> {
  if (!sessionId) return [];

  const query = new URLSearchParams();
  if (type) {
    query.set("type", type);
  }

  const res = await fetch(buildApiUrl(`/memories/${encodeURIComponent(sessionId)}`, query));
  const payload = await parseApiEnvelope<{ memories?: unknown[] }>(res, "获取记忆列表失败");
  const data = requireEnvelopeDataRecord(payload, "获取记忆列表失败");
  const memories = requireEnvelopeArrayField(data, "memories", "获取记忆列表失败");
  return memories.map((memory, index) =>
    requireNormalizedArrayItem(memory, index, normalizeMemoryItem, "获取记忆列表失败"),
  );
}

export async function fetchEmotionHistory(sessionId: string): Promise<EmotionHistoryItem[]> {
  if (!sessionId) return [];

  const res = await fetch(buildApiUrl(`/emotion/${encodeURIComponent(sessionId)}/history`));
  const payload = await parseApiEnvelope<{ history?: unknown[] }>(res, "获取情绪历史失败");
  const data = requireEnvelopeDataRecord(payload, "获取情绪历史失败");
  const history = requireEnvelopeArrayField(data, "history", "获取情绪历史失败");
  return history.map((item, index) =>
    requireNormalizedArrayItem(item, index, normalizeEmotionState, "获取情绪历史失败"),
  );
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
