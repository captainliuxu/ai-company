"use client";

import { Suspense, useEffect, useState, useRef, useCallback } from "react";
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
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!personaId) return;
    fetchPersonas().then((ps) => {
      const p = ps.find((x) => x.id === personaId);
      if (p) setPersona(p);
    });
    createSession(personaId).then(setSessionId);
  }, [personaId]);

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

  const handleSend = async () => {
    if (!input.trim() || isTyping || !sessionId) return;
    const msg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: msg }]);
    setIsTyping(true);
    setCurrentReply("");

    replyRef.current = "";
    sendMessage(
      sessionId,
      personaId,
      msg,
      (token) => {
        replyRef.current += token;
        setCurrentReply(replyRef.current);
      },
      () => {
        const finalReply = replyRef.current;
        if (finalReply) {
          setMessages((msgs) => [
            ...msgs,
            { role: "assistant", content: finalReply },
          ]);
        }
        setCurrentReply("");
        setIsTyping(false);
        refreshEmotion();
      }
    );
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      handleSend();
    }
  };

  return (
    <div className="min-h-screen flex flex-col max-w-2xl mx-auto bg-white/60 backdrop-blur">
      {/* Header */}
      <div className="p-4 border-b border-orange-100 flex items-center justify-between">
        <div>
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
            className="flex-1 px-4 py-2 rounded-full border border-orange-200 focus:outline-none focus:ring-2 focus:ring-orange-300 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={isTyping || !input.trim()}
            className="px-6 py-2 bg-orange-400 text-white rounded-full hover:bg-orange-500 disabled:opacity-50 transition-colors"
          >
            发送
          </button>
        </div>
      </div>
    </div>
  );
}
