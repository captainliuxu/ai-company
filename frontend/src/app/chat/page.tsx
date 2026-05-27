"use client";

import { Suspense, useEffect, useState, useRef, useCallback } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import {
  createSession,
  sendMessage,
  fetchPersonas,
  fetchEmotion,
  Persona,
  EmotionState,
} from "@/lib/api";

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
  const [error, setError] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
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

  // Auto-fetch emotion after each reply
  const refreshEmotion = useCallback(async () => {
    if (!sessionId) return;
    const data = await fetchEmotion(sessionId);
    if (data) setEmotion(data);
  }, [sessionId]);

  useEffect(() => {
    refreshEmotion();
  }, [messages.length, refreshEmotion]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentReply]);

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
    refreshEmotion();
  }, [refreshEmotion]);

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
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto bg-white/60 backdrop-blur">
      {/* Header */}
      <div className="sticky top-0 z-10 border-b border-orange-100 bg-white/95 px-4 py-4 backdrop-blur">
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
      </div>

      {/* Error banner */}
      {error && (
        <div className="mx-4 mt-2 px-4 py-2 bg-red-50 border border-red-200 rounded-lg text-red-600 text-sm">
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
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-20">
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
            <div className="max-w-[80%] px-4 py-2 rounded-2xl bg-gray-100 text-gray-800">
              {currentReply}
              <span className="inline-block w-1 h-4 bg-gray-400 animate-pulse ml-1" />
            </div>
          </div>
        )}
        {isTyping && !currentReply && (
          <div className="flex justify-start">
            <div className="px-4 py-3 rounded-2xl bg-gray-100 flex gap-1">
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
      <div className="p-4 border-t border-orange-100">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="输入消息..."
            disabled={isTyping}
            className="flex-1 px-4 py-2 rounded-full border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 disabled:bg-gray-300 disabled:text-gray-400 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
            className="px-6 py-2 rounded-full bg-orange-400 text-white transition-colors hover:bg-orange-500 disabled:bg-gray-500 disabled:text-white disabled:hover:bg-gray-500 disabled:cursor-not-allowed"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
