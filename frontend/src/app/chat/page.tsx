"use client";

import { Suspense, useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  clearCachedSessionSnapshot,
  createSession,
  sendMessage,
  fetchPersonas,
  fetchSession,
  fetchEmotion,
  fetchMemories,
  fetchEmotionHistory,
  mergeSessionMessages,
  readCachedSessionSnapshot,
  transcribeAudio,
  synthesizeSpeech,
  Persona,
  EmotionState,
  type MemoryItem,
  type EmotionHistoryItem,
  writeCachedSessionSnapshot,
} from "@/lib/api";
import { InsightPanel } from "@/components/chat/insight-panel";

interface Message {
  role: "user" | "assistant";
  content: string;
}

interface BrowserMediaRecorder extends MediaRecorder {
  mimeType: string;
}

function buildSessionStorageKey(personaId: string): string {
  return `ai-companion:chat-session:${personaId}`;
}

function isNotFoundError(error: unknown): boolean {
  return error instanceof Error && error.message.includes("(404)");
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
  const [showSummaryDetails, setShowSummaryDetails] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [recordingSupported, setRecordingSupported] = useState(true);
  const [audioLoadingKey, setAudioLoadingKey] = useState<string | null>(null);
  const [playingAudioKey, setPlayingAudioKey] = useState<string | null>(null);
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const insightsRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const typingTimerRef = useRef<number | null>(null);
  const pendingReplyRef = useRef("");
  const streamDoneRef = useRef(false);
  const mediaRecorderRef = useRef<BrowserMediaRecorder | null>(null);
  const mediaStreamRef = useRef<MediaStream | null>(null);
  const recordedChunksRef = useRef<Blob[]>([]);
  const audioElementRef = useRef<HTMLAudioElement | null>(null);
  const audioCacheRef = useRef(new Map<string, string>());
  const shouldAutoScrollRef = useRef(true);

  const persistSessionSnapshot = useCallback(
    (targetSessionId: string, nextMessages: Message[]) => {
      if (!personaId || !targetSessionId || typeof window === "undefined") {
        return;
      }

      writeCachedSessionSnapshot({
        session_id: targetSessionId,
        persona_id: personaId,
        messages: nextMessages,
        updated_at: new Date().toISOString(),
      });
    },
    [personaId],
  );

  useEffect(() => {
    const supported =
      typeof window !== "undefined" &&
      typeof navigator !== "undefined" &&
      typeof MediaRecorder !== "undefined" &&
      typeof navigator.mediaDevices?.getUserMedia === "function";
    setRecordingSupported(supported);
  }, []);

  useEffect(() => {
    if (!personaId) return;
    let ignore = false;

    setPersona(null);
    setSessionId("");
    setMessages([]);
    setInput("");
    setIsTyping(false);
    setCurrentReply("");
    setEmotion(null);
    setMemories([]);
    setEmotionHistory([]);
    setError("");
    setShowMobileInsights(false);
    setShowSummaryDetails(false);
    replyRef.current = "";
    pendingReplyRef.current = "";
    streamDoneRef.current = false;
    abortRef.current?.abort();
    abortRef.current = null;
    if (typingTimerRef.current) {
      clearInterval(typingTimerRef.current);
      typingTimerRef.current = null;
    }
    shouldAutoScrollRef.current = true;

    const bootstrapChat = async () => {
      try {
        const personas = await fetchPersonas();
        if (ignore) return;

        const matchedPersona = personas.find((item) => item.id === personaId);
        if (!matchedPersona) {
          setError("角色不存在");
          return;
        }
        setPersona(matchedPersona);

        const storageKey = buildSessionStorageKey(personaId);
        const storedSessionId =
          typeof window !== "undefined" ? window.localStorage.getItem(storageKey)?.trim() ?? "" : "";
        const cachedSnapshot = storedSessionId ? readCachedSessionSnapshot(storedSessionId) : null;

        if (storedSessionId) {
          try {
            const snapshot = await fetchSession(storedSessionId);
            if (!ignore && snapshot.persona_id === personaId) {
              const mergedMessages =
                cachedSnapshot?.persona_id === personaId
                  ? mergeSessionMessages(snapshot.messages, cachedSnapshot.messages)
                  : snapshot.messages;
              setSessionId(snapshot.session_id);
              setMessages(mergedMessages);
              persistSessionSnapshot(snapshot.session_id, mergedMessages);
              return;
            }
          } catch (sessionError) {
            if (
              !ignore &&
              cachedSnapshot?.persona_id === personaId &&
              !isNotFoundError(sessionError)
            ) {
              setSessionId(cachedSnapshot.session_id);
              setMessages(cachedSnapshot.messages);
              return;
            }
          }

          if (typeof window !== "undefined") {
            window.localStorage.removeItem(storageKey);
          }
          clearCachedSessionSnapshot(storedSessionId);
        }

        const newSessionId = await createSession(personaId);
        if (ignore) return;
        setSessionId(newSessionId);
        if (typeof window !== "undefined") {
          window.localStorage.setItem(storageKey, newSessionId);
        }
      } catch {
        if (!ignore) {
          setError("初始化会话失败");
        }
      }
    };

    void bootstrapChat();

    return () => {
      ignore = true;
    };
  }, [persistSessionSnapshot, personaId]);

  useEffect(() => {
    if (!personaId || !sessionId || typeof window === "undefined") return;
    window.localStorage.setItem(buildSessionStorageKey(personaId), sessionId);
  }, [personaId, sessionId]);

  useEffect(() => {
    if (!personaId || !sessionId) return;
    persistSessionSnapshot(sessionId, messages);
  }, [messages, persistSessionSnapshot, personaId, sessionId]);

  // Cleanup typing timer on unmount
  useEffect(() => {
    return () => {
      if (typingTimerRef.current) clearInterval(typingTimerRef.current);
      if (abortRef.current) abortRef.current.abort();
      const activeRecorder = mediaRecorderRef.current;
      if (activeRecorder && activeRecorder.state !== "inactive") {
        activeRecorder.stop();
      }
      mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
      if (audioElementRef.current) {
        audioElementRef.current.pause();
        audioElementRef.current.src = "";
      }
      audioCacheRef.current.forEach((url) => URL.revokeObjectURL(url));
      audioCacheRef.current.clear();
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

  const scrollMessagesToBottom = useCallback((behavior: ScrollBehavior = "smooth") => {
    messagesEndRef.current?.scrollIntoView({ behavior, block: "end" });
  }, []);

  const updateAutoScrollState = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;
    const distanceFromBottom =
      container.scrollHeight - container.scrollTop - container.clientHeight;
    shouldAutoScrollRef.current = distanceFromBottom < 120;
  }, []);

  useEffect(() => {
    if (!messages.length && !currentReply) return;
    if (shouldAutoScrollRef.current) {
      scrollMessagesToBottom(messages.length > 0 && !currentReply ? "auto" : "smooth");
    }
  }, [currentReply, messages, scrollMessagesToBottom]);

  useEffect(() => {
    if (!showMobileInsights || typeof document === "undefined") return;
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = originalOverflow;
    };
  }, [showMobileInsights]);

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
      setMessages((msgs) => {
        const nextMessages: Message[] = [...msgs, { role: "assistant", content: finalReply }];
        persistSessionSnapshot(sessionId, nextMessages);
        return nextMessages;
      });
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
  }, [persistSessionSnapshot, refreshInsights, sessionId]);

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
    shouldAutoScrollRef.current = true;
    setMessages((prev) => {
      const nextMessages: Message[] = [...prev, { role: "user", content: msg }];
      persistSessionSnapshot(sessionId, nextMessages);
      return nextMessages;
    });
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
  const shouldShowSummaryPreview = showSummaryDetails || messages.length === 0;
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
  };

  const stopRecordingStream = useCallback(() => {
    mediaStreamRef.current?.getTracks().forEach((track) => track.stop());
    mediaStreamRef.current = null;
  }, []);

  const buildRecordingMimeType = () => {
    if (typeof MediaRecorder === "undefined") {
      return "";
    }

    const candidates = [
      "audio/webm;codecs=opus",
      "audio/webm",
      "audio/mp4",
      "audio/ogg;codecs=opus",
    ];

    return candidates.find((type) => MediaRecorder.isTypeSupported(type)) ?? "";
  };

  const handleRecordingStop = useCallback(async () => {
    const audioBlob = new Blob(recordedChunksRef.current, {
      type: mediaRecorderRef.current?.mimeType || "audio/webm",
    });
    recordedChunksRef.current = [];
    stopRecordingStream();

    if (!audioBlob.size) {
      setError("录音失败，请重试");
      return;
    }

    setIsTranscribing(true);
    setError("");

    try {
      const transcript = await transcribeAudio(audioBlob);
      setInput((current) => {
        const prefix = current.trim() ? `${current.trim()} ` : "";
        return `${prefix}${transcript.trim()}`.trim();
      });
    } catch (voiceError) {
      const message =
        voiceError instanceof Error ? voiceError.message : "语音转写失败，请稍后再试";
      setError(message);
    } finally {
      setIsTranscribing(false);
    }
  }, [stopRecordingStream]);

  const handleRecordToggle = useCallback(async () => {
    if (isTranscribing) {
      return;
    }

    if (!recordingSupported) {
      setError("当前浏览器不支持录音，仍可继续文字聊天");
      return;
    }

    if (isRecording) {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mimeType = buildRecordingMimeType();
      const recorder = mimeType
        ? new MediaRecorder(stream, { mimeType })
        : new MediaRecorder(stream);

      mediaStreamRef.current = stream;
      mediaRecorderRef.current = recorder as BrowserMediaRecorder;
      recordedChunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      recorder.onerror = () => {
        setError("录音失败，请稍后重试");
        setIsRecording(false);
        recordedChunksRef.current = [];
        stopRecordingStream();
      };

      recorder.onstop = () => {
        setIsRecording(false);
        void handleRecordingStop();
      };

      recorder.start();
      setError("");
      setIsRecording(true);
    } catch (recordingError) {
      const name = recordingError instanceof DOMException ? recordingError.name : "";
      if (name === "NotAllowedError" || name === "PermissionDeniedError") {
        setError("麦克风权限被拒绝，仍可继续文字聊天");
      } else {
        setError("无法启动录音，请检查浏览器或设备设置");
      }
      setIsRecording(false);
      stopRecordingStream();
    }
  }, [handleRecordingStop, isRecording, isTranscribing, recordingSupported, stopRecordingStream]);

  const handlePlayReply = useCallback(async (messageKey: string, text: string) => {
    if (!sessionId || !personaId || !text.trim()) {
      return;
    }

    if (!audioElementRef.current) {
      const element = new Audio();
      element.onended = () => setPlayingAudioKey(null);
      element.onpause = () => {
        if (!element.ended) {
          setPlayingAudioKey(null);
        }
      };
      audioElementRef.current = element;
    }

    const player = audioElementRef.current;

    if (playingAudioKey === messageKey) {
      player.pause();
      player.currentTime = 0;
      setPlayingAudioKey(null);
      return;
    }

    setAudioLoadingKey(messageKey);
    setError("");

    try {
      let audioUrl = audioCacheRef.current.get(messageKey);
      if (!audioUrl) {
        const audioBlob = await synthesizeSpeech(text, sessionId, personaId);
        audioUrl = URL.createObjectURL(audioBlob);
        audioCacheRef.current.set(messageKey, audioUrl);
      }

      player.src = audioUrl;
      await player.play();
      setPlayingAudioKey(messageKey);
    } catch (voiceError) {
      const message =
        voiceError instanceof Error ? voiceError.message : "语音播放失败，请稍后再试";
      setPlayingAudioKey(null);
      setError(message);
    } finally {
      setAudioLoadingKey(null);
    }
  }, [personaId, playingAudioKey, sessionId]);

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
        <div className="flex min-h-screen min-h-0 flex-col bg-white/60 backdrop-blur xl:h-[calc(100vh-3rem)] xl:min-h-0 xl:overflow-hidden xl:rounded-[2rem] xl:border xl:border-orange-100/80 xl:bg-white/80 xl:shadow-[0_35px_100px_-60px_rgba(194,65,12,0.55)]">
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
                <div className="flex flex-col gap-3">
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
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setShowSummaryDetails((current) => !current)}
                        className="inline-flex shrink-0 items-center justify-center rounded-full border border-stone-200 bg-white px-4 py-2 text-sm font-medium text-stone-600 shadow-sm transition hover:border-orange-300 hover:text-orange-700"
                      >
                        {shouldShowSummaryPreview ? "收起速览" : "展开速览"}
                      </button>
                      <button
                        type="button"
                        onClick={handleOpenInsights}
                        className="inline-flex shrink-0 items-center justify-center rounded-full border border-orange-200 bg-white px-4 py-2 text-sm font-medium text-orange-600 shadow-sm transition hover:border-orange-300 hover:text-orange-700 xl:hidden"
                      >
                        查看洞察面板
                      </button>
                    </div>
                  </div>
                  {shouldShowSummaryPreview ? (
                    <p className="text-sm leading-6 text-stone-600">
                      {summaryPreview || "当前还没有对话摘要，继续交流后会在洞察面板中展示总结片段。"}
                    </p>
                  ) : (
                    <p className="text-xs leading-5 text-stone-500">
                      长对话时可收起速览，减少顶部信息对消息阅读的持续干扰。
                    </p>
                  )}
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

          {/* Messages */}
          <div
            ref={messagesContainerRef}
            onScroll={updateAutoScrollState}
            className="flex-1 min-h-0 overflow-y-auto space-y-4 px-4 pb-4 pt-3"
          >
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
                  {m.role === "assistant" && (
                    <div className="mt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={() => void handlePlayReply(`assistant-${i}`, m.content)}
                        disabled={audioLoadingKey === `assistant-${i}`}
                        className="inline-flex items-center rounded-full border border-gray-300 bg-white/80 px-3 py-1 text-xs font-medium text-gray-600 transition hover:border-orange-200 hover:text-orange-600 disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {audioLoadingKey === `assistant-${i}`
                          ? "生成语音中..."
                          : playingAudioKey === `assistant-${i}`
                            ? "停止播放"
                            : "播放语音"}
                      </button>
                    </div>
                  )}
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
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between gap-3 text-xs text-gray-500">
                <span>
                  {isRecording
                    ? "录音中，点击按钮结束并转写"
                    : isTranscribing
                      ? "正在转写录音..."
                      : "可直接输入文本，或使用录音转写回填"}
                </span>
                {!recordingSupported && (
                  <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-amber-700">
                    当前浏览器不支持录音
                  </span>
                )}
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <button
                  type="button"
                  onClick={() => void handleRecordToggle()}
                  disabled={!recordingSupported || isTranscribing}
                  className={`inline-flex items-center justify-center rounded-full px-4 py-2 text-sm font-medium transition-colors sm:w-auto ${
                    isRecording
                      ? "bg-red-500 text-white hover:bg-red-600"
                      : "border border-orange-200 bg-orange-50 text-orange-700 hover:border-orange-300 hover:bg-orange-100"
                  } disabled:cursor-not-allowed disabled:border-gray-200 disabled:bg-gray-100 disabled:text-gray-400`}
                >
                  {isRecording ? "结束录音" : isTranscribing ? "转写中..." : "录音输入"}
                </button>
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
          </div>
        </div>

        <aside className="hidden xl:block">
          <div
            ref={insightsRef}
            className="sticky top-6 max-h-[calc(100vh-3rem)] overflow-y-auto overscroll-contain pr-1"
          >
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

        {showMobileInsights ? (
          <div className="fixed inset-0 z-40 bg-stone-950/35 px-3 py-4 xl:hidden">
            <div className="mx-auto flex h-full w-full max-w-xl flex-col overflow-hidden rounded-[2rem] border border-orange-100 bg-white shadow-[0_30px_80px_-45px_rgba(28,25,23,0.7)]">
              <div className="flex items-center justify-between border-b border-orange-100 px-4 py-3">
                <div>
                  <h2 className="text-sm font-semibold text-stone-800">洞察面板</h2>
                  <p className="text-xs text-stone-500">独立滚动查看记忆与情绪历史</p>
                </div>
                <button
                  type="button"
                  onClick={() => setShowMobileInsights(false)}
                  className="inline-flex items-center justify-center rounded-full border border-stone-200 bg-white px-3 py-1.5 text-sm text-stone-600 transition hover:border-orange-300 hover:text-orange-700"
                >
                  关闭
                </button>
              </div>
              <div ref={insightsRef} className="flex-1 overflow-y-auto overscroll-contain p-4">
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
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
