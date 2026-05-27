import { cn } from "@/lib/utils";

import {
  EmotionHistory,
  type EmotionHistoryItem,
  type EmotionHistoryProps,
} from "./emotion-history";
import {
  MemoryList,
  type MemoryListItem,
  type MemoryListProps,
} from "./memory-list";

export interface InsightPanelProps {
  memories: MemoryListItem[];
  emotionHistory: EmotionHistoryItem[];
  memoryLoading?: boolean;
  emotionLoading?: boolean;
  memoryError?: string | null;
  emotionError?: string | null;
  className?: string;
  memoryListProps?: Partial<Omit<MemoryListProps, "items" | "loading" | "error">>;
  emotionHistoryProps?: Partial<
    Omit<EmotionHistoryProps, "items" | "loading" | "error">
  >;
}

export function InsightPanel({
  memories,
  emotionHistory,
  memoryLoading = false,
  emotionLoading = false,
  memoryError,
  emotionError,
  className,
  memoryListProps,
  emotionHistoryProps,
}: InsightPanelProps) {
  return (
    <section
      className={cn(
        "space-y-4 rounded-[2.25rem] border border-orange-100/70 bg-[linear-gradient(180deg,rgba(255,251,235,0.72),rgba(255,255,255,0.9))] p-3 shadow-[0_35px_80px_-55px_rgba(194,65,12,0.5)] sm:p-4",
        className,
      )}
      aria-label="聊天洞察"
    >
      <div className="flex flex-col gap-2 rounded-[1.75rem] border border-white/80 bg-white/65 px-4 py-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)]">
        <div className="inline-flex w-fit items-center rounded-full bg-orange-100 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.28em] text-orange-700">
          Companion Insight
        </div>
        <div className="flex flex-col gap-3">
          <div className="max-w-xl">
            <h2 className="text-xl font-semibold text-stone-800">关系与记忆面板</h2>
            <p className="mt-1 text-sm leading-6 text-stone-500">
              用统一组件呈现长期记忆沉淀与情绪波动轨迹，便于聊天页直接拼装和后续扩展。
            </p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-stone-500">
            <span className="rounded-full border border-orange-200/80 bg-orange-50 px-3 py-1">
              记忆 {memories.length}
            </span>
            <span className="rounded-full border border-amber-200/80 bg-amber-50 px-3 py-1">
              情绪节点 {emotionHistory.length}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-4">
        <MemoryList
          items={memories}
          loading={memoryLoading}
          error={memoryError}
          {...memoryListProps}
        />
        <EmotionHistory
          items={emotionHistory}
          loading={emotionLoading}
          error={emotionError}
          {...emotionHistoryProps}
        />
      </div>
    </section>
  );
}
