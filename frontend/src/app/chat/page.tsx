"use client";

import { Suspense, useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  createSession,
  sendMessage,
  fetchPersonas,
  fetchEmotion,
  fetchMemories,
  fetchEmotionHistory,
  Persona,
  EmotionState,
  type MemoryItem,
  type EmotionHistoryItem,
} from "@/lib/api";
import { InsightPanel } from "@/components/chat/insight-panel";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen"><div className="animate-spin w-8 h-8 border-4 border-orange-400 border-t-transparent rounded-full" /></div>}>
      <ChatContent />
    </Suspense>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const personaId = searchParams.get("persona_id") || "";
  const [persona, setPersona] = useState<Persona | null>(null);
  const [sessionId, setSessionId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const replyRef = useRef("");
  const [isTyping, setIsTyping] = useState(false);
  const [currentReply, setCurrentReply] = useState("");
  const [emotion, setEmotion] = useState<EmotionState | null>(null);
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [emotionHistory, setEmotionHistory] = useState<EmotionHistoryItem[]>([]);
  const [memoriesLoading, setMemoriesLoading] = useState(false);
  const [emotionHistoryLoading, setEmotionHistoryLoading] = useState(false);
  const [memoriesError, setMemoriesError] = useState<string | null>(null);
  const [emotionHistoryError, setEmotionHistoryError] = useState<string | null>(null);
  const [showMobileInsights, setShowMobileInsights] = useState(false);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const insightsRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const typingTimerRef = useRef<number | null>(null);
  const pendingReplyRef = useRef("");
  const streamDoneRef = useRef(false);

  useEffect(() => {
    if (!personaId) return;
    let ignore = false;
    fetchPersonas()
      .then((ps) => {
        if (!ignore) {
          const p = ps.find((x) => x.id === personaId);
          if (p) {
            setPersona(p);
            setError("");
          } else {
            setError("角色不存在");
          }
        }
      })
      .catch(() => { if (!ignore) setError("加载角色失败"); });
    createSession(personaId)
      .then((id) => { if (!ignore) setSessionId(id); })
      .catch(() => { if (!ignore) setError("创建会话失败"); });
    return () => { ignore = true; };
  }, [personaId]);

  // Cleanup typing timer on unmount
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearInterval(typingTimerRef.current);
      if (abortRef.current) abortRef.current.abort();
    };
  }, []);

  const refreshEmotion = useCallback(async () => {
    if (!sessionId) return;
    try {
      const data = await fetchEmotion(sessionId);
      setEmotion(data);
    } catch {
      setEmotion(null);
    }
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    setMemoriesLoading(true);
    setMemoriesError(null);
    fetchMemories(sessionId)
      .then((items) => {
        if (!cancelled) {
          setMemories(items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setMemories([]);
          setMemoriesError("记忆加载失败，请稍后重试");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setMemoriesLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;

    setEmotionHistoryLoading(true);
    setEmotionHistoryError(null);
    fetchEmotionHistory(sessionId)
      .then((items) => {
        if (!cancelled) {
          setEmotionHistory(items);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setEmotionHistory([]);
          setEmotionHistoryError("情绪历史加载失败，请稍后重试");
        }
      })
      .finally(() => {
        if (!cancelled) {
          setEmotionHistoryLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    refreshEmotion();
  }, [refreshEmotion]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentReply]);

  const refreshMemories = useCallback(async () => {
    if (!sessionId) return;
    setMemoriesLoading(true);
    setMemoriesError(null);
    try {
      const items = await fetchMemories(sessionId);
      setMemories(items);
    } catch {
      setMemories([]);
      setMemoriesError("记忆加载失败，请稍后重试");
    } finally {
      setMemoriesLoading(false);
    }
  }, [sessionId]);

  const refreshEmotionHistory = useCallback(async () => {
    if (!sessionId) return;
    setEmotionHistoryLoading(true);
    setEmotionHistoryError(null);
    try {
      const items = await fetchEmotionHistory(sessionId);
      setEmotionHistory(items);
    } catch {
      setEmotionHistory([]);
      setEmotionHistoryError("情绪历史加载失败，请稍后重试");
    } finally {
      setEmotionHistoryLoading(false);
    }
  }, [sessionId]);

  const refreshInsights = useCallback(async () => {
    await Promise.all([
      refreshEmotion(),
      refreshMemories(),
      refreshEmotionHistory(),
    ]);
  }, [refreshEmotion, refreshMemories, refreshEmotionHistory]);

  const finalizeStreamingReply = useCallback(() => {
    const finalReply = replyRef.current.trim();
    if (finalReply) {
      setMessages((msgs) => [...msgs, { role: "assistant", content: finalReply }]);
    }
    setCurrentReply("");
    setIsTyping(false);
    abortRef.current = null;
    streamDoneRef.current = false;
    pendingReplyRef.current = "";
    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
    void refreshInsights();
  }, [refreshInsights]);

  const startStreamingDisplay = useCallback(() => {
    if (typingTimerRef.current) return;

    typingTimerRef.current = window.setInterval(() => {
      if (pendingReplyRef.current) {
        const nextChunk = pendingReplyRef.current.slice(0, 2);
        pendingReplyRef.current = pendingReplyRef.current.slice(2);
        replyRef.current += nextChunk;
        setCurrentReply(replyRef.current);
        return;
      }

      if (streamDoneRef.current) {
        if (typingTimerRef.current) {
          clearInterval(typingTimerRef.current);
        }
        typingTimerRef.current = null;
        finalizeStreamingReply();
      }
    }, 28);
  }, [finalizeStreamingReply]);

  const handleSend = async () => {
    if (!input.trim() || isTyping || !sessionId) return;

    // Abort previous stream if still in progress
    if (abortRef.current) {
      abortRef.current.abort();
    }

    const msg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setIsTyping(true);
    setCurrentReply("");
    setError("");

    replyRef.current = "";
    pendingReplyRef.current = "";
    streamDoneRef.current = false;
    abortRef.current = sendMessage(
      sessionId,
      personaId,
      msg,
      (token) => {
        pendingReplyRef.current += token;
        startStreamingDisplay();
      },
      (error) => {
        if (error) {
          if (typingTimerRef.current) {
            clearInterval(typingTimerRef.current);
            typingTimerRef.current = null;
          }
          pendingReplyRef.current = "";
          replyRef.current = "";
          streamDoneRef.current = false;
          setCurrentReply("");
          setError(error);
          setIsTyping(false);
          abortRef.current = null;
        } else {
          streamDoneRef.current = true;
          if (!typingTimerRef.current && !pendingReplyRef.current) {
            finalizeStreamingReply();
          } else {
            startStreamingDisplay();
          }
        }
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  const latestSummary = memories
    .filter((item) => item.type === "summary")
    .sort((left, right) => {
      const leftTime = left.created_at ? new Date(left.created_at).getTime() : 0;
      const rightTime = right.created_at ? new Date(right.created_at).getTime() : 0;
      return rightTime - leftTime;
    })[0] ?? null;

  const summaryLabel = latestSummary ? "摘要已生成" : "摘要待生成";
  const summaryPreview = latestSummary?.content.trim() ?? "";
  const insightMemories = memories.map((item) => ({
    ...item,
    created_at: item.created_at ?? undefined,
  }));
  const insightEmotionHistory = emotionHistory.map((item) => ({
    ...item,
    created_at: item.created_at ?? undefined,
    updated_at: item.updated_at ?? undefined,
  }));

  const handleOpenInsights = () => {
    setShowMobileInsights(true);
    insightsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  if (!personaId) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-500 mb-4">缺少角色ID</p>
          <Link href="/personas" className="text-orange-500 underline">返回角色选择</Link>
        </div>
      </div>
    );
  }

  if (error && !persona) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Link href="/personas" className="text-orange-500 underline">返回角色选择</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[linear-gradient(180deg,rgba(255,247,237,0.78),rgba(255,255,255,0.96))]">
      <div className="mx-auto flex min-h-screen w-full max-w-7xl flex-col xl:grid xl:grid-cols-[minmax(0,1.25fr)_24rem] xl:gap-6 xl:px-6 xl:py-6">
        <div className="flex min-h-screen flex-col bg-white/60 backdrop-blur xl:min-h-0 xl:overflow-hidden xl:rounded-[2rem] xl:border xl:border-orange-100/80 xl:bg-white/80 xl:shadow-[0_35px_100px_-60px_rgba(194,65,12,0.55)]">
          {/* Header */}
          <div className="sticky top-0 z-10 border-b border-orange-100 bg-white/95 px-4 py-4 backdrop-blur xl:rounded-t-[2rem]">
            <div className="flex flex-col gap-4">
              <div className="flex items-start justify-between gap-3">
                <Link
                  href="/personas"
                  className="inline-flex items-center gap-2 rounded-full border border-gray-200 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 shadow-sm transition-colors hover:border-orange-200 hover:text-orange-600"
                >
                  <span aria-hidden="true">&#8592;</span>
                  <span>返回角色选择</span>
                </Link>
                <div className="flex-1">
                  <h1 className="text-lg font-semibold text-gray-800">
                    {persona?.name || "..."}
                  </h1>
                  <p className="text-xs text-gray-500">{persona?.personality}</p>
                </div>
                {emotion && (
                  <div className="flex gap-3 text-xs">
                    <div className="text-center">
                      <div className="text-pink-500 font-bold">
                        {emotion.favorability}
                      </div>
                      <div className="text-gray-400">好感</div>
                    </div>
                    <div className="text-center">
                      <div className="text-blue-500 font-bold">{emotion.trust}</div>
                      <div className="text-gray-400">信任</div>
                    </div>
                    <div className="text-center">
                      <div className="text-orange-500 font-bold">{emotion.mood}</div>
                      <div className="text-gray-400">心情</div>
                    </div>
                    <div className="text-center">
                      <div className="text-purple-500 font-bold">
                        {emotion.dependency}
                      </div>
                      <div className="text-gray-400">依赖</div>
                    </div>
                  </div>
                )}
              </div>

              <div className="rounded-[1.5rem] border border-orange-100/80 bg-[linear-gradient(135deg,rgba(255,247,237,0.85),rgba(255,255,255,0.95))] px-4 py-3 shadow-[0_18px_45px_-35px_rgba(194,65,12,0.45)]">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                        {summaryLabel}
                      </span>
                      <span className="rounded-full border border-orange-200 bg-white px-3 py-1 text-xs font-medium text-orange-600">
                        记忆 {memories.length}
                      </span>
                      <span className="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-medium text-sky-700">
                        情绪节点 {emotionHistory.length}
                      </span>
                    </div>
                    <p className="mt-2 line-clamp-2 text-sm leading-6 text-stone-600">
                      {summaryPreview || "当前还没有对话摘要，继续交流后会在洞察面板中展示总结片段。"}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={handleOpenInsights}
                    className="inline-flex shrink-0 items-center justify-center rounded-full border border-orange-200 bg-white px-4 py-2 text-sm font-medium text-orange-600 shadow-sm transition hover:border-orange-300 hover:text-orange-700 xl:hidden"
                  >
                    查看洞察面板
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Error banner */}
          {error && (
            <div className="mx-4 mt-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-600">
              {error}
              <button
                onClick={() => setError("")}
                className="ml-2 text-red-400 hover:text-red-600"
              >
                x
              </button>
            </div>
          )}

          <div className="px-4 pt-4 xl:hidden">
            {showMobileInsights ? (
              <div ref={insightsRef}>
                <InsightPanel
                  memories={insightMemories}
                  emotionHistory={insightEmotionHistory}
                  memoryLoading={memoriesLoading}
                  emotionLoading={emotionHistoryLoading}
                  memoryError={memoriesError}
                  emotionError={emotionHistoryError}
                  memoryListProps={{ onRetry: refreshMemories }}
                  emotionHistoryProps={{ onRetry: refreshEmotionHistory }}
                />
              </div>
            ) : null}
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="mt-20 text-center text-gray-400">
                {persona
                  ? `向${persona.name}发送第一条消息吧~`
                  : "加载中..."}
              </div>
            )}
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`max-w-[80%] px-4 py-2 rounded-2xl ${
                    m.role === "user"
                      ? "bg-orange-400 text-white"
                      : "bg-gray-100 text-gray-800"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {isTyping && currentReply && (
              <div className="flex justify-start">
                <div className="max-w-[80%] rounded-2xl bg-gray-100 px-4 py-2 text-gray-800">
                  {currentReply}
                  <span className="ml-1 inline-block h-4 w-1 animate-pulse bg-gray-400" />
                </div>
              </div>
            )}
            {isTyping && !currentReply && (
              <div className="flex justify-start">
                <div className="flex gap-1 rounded-2xl bg-gray-100 px-4 py-3">
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "0ms" }}
                  />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "150ms" }}
                  />
                  <span
                    className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                    style={{ animationDelay: "300ms" }}
                  />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-orange-100 p-4">
            <div className="flex gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入消息..."
                disabled={isTyping}
                className="flex-1 rounded-full border border-orange-200 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-orange-300 disabled:cursor-not-allowed disabled:bg-gray-300 disabled:text-gray-400"
              />
              <button
                onClick={handleSend}
                disabled={isTyping || !input.trim()}
                className="rounded-full bg-orange-400 px-6 py-2 text-white transition-colors hover:bg-orange-500 disabled:cursor-not-allowed disabled:bg-gray-500 disabled:text-white disabled:hover:bg-gray-500"
              >
                发送
              </button>
            </div>
          </div>
        </div>

        <aside className="hidden xl:block">
          <div ref={insightsRef} className="sticky top-6">
            <InsightPanel
              memories={insightMemories}
              emotionHistory={insightEmotionHistory}
              memoryLoading={memoriesLoading}
              emotionLoading={emotionHistoryLoading}
              memoryError={memoriesError}
              emotionError={emotionHistoryError}
              memoryListProps={{ onRetry: refreshMemories }}
              emotionHistoryProps={{ onRetry: refreshEmotionHistory }}
            />
          </div>
        </aside>
      </div>
    </div>
  );
}
