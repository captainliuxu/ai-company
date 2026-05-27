import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface MemoryListItem {
  id?: string;
  type: string;
  content: string;
  importance: number;
  created_at?: string;
}

export interface MemoryListProps {
  items: MemoryListItem[];
  loading?: boolean;
  error?: string | null;
  title?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
  onRetry?: () => void;
}

const memoryTypeLabelMap: Record<string, string> = {
  user_info: "用户信息",
  user_profile: "用户档案",
  personal_info: "个人信息",
  preference: "偏好",
  preferences: "偏好",
  emotion: "情绪",
  emotional_state: "情绪状态",
  profile: "档案",
  event: "事件",
  milestone: "里程碑",
  summary: "摘要",
  conversation_summary: "对话摘要",
  fact: "事实",
  relationship: "关系",
  observation: "观察",
};

function formatMemoryType(type: string) {
  const normalizedType = type.trim().toLowerCase().replace(/[\s-]+/g, "_");
  return memoryTypeLabelMap[normalizedType] ?? type;
}

function formatImportance(value: number) {
  if (Number.isNaN(value)) return "0.0";
  return value.toFixed(1);
}

function formatTimestamp(timestamp?: string) {
  if (!timestamp) return null;

  const date = new Date(timestamp);
  if (Number.isNaN(date.getTime())) {
    return timestamp;
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function MemoryListSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="overflow-hidden rounded-2xl border border-orange-100/80 bg-white/80 shadow-[0_18px_45px_-30px_rgba(194,65,12,0.45)]"
        >
          <div className="h-1.5 bg-gradient-to-r from-orange-200 via-amber-100 to-rose-100" />
          <div className="space-y-3 px-4 py-4">
            <div className="flex flex-col items-start gap-3">
              <div className="h-5 w-16 animate-pulse rounded-full bg-orange-100" />
              <div className="h-4 w-14 animate-pulse rounded-full bg-amber-100" />
            </div>
            <div className="space-y-2">
              <div className="h-4 w-full animate-pulse rounded-full bg-stone-100" />
              <div className="h-4 w-4/5 animate-pulse rounded-full bg-stone-100" />
            </div>
            <div className="h-4 w-24 animate-pulse rounded-full bg-orange-50" />
          </div>
        </div>
      ))}
    </div>
  );
}

function MemoryListEmpty({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-orange-200/80 bg-gradient-to-br from-orange-50/90 via-amber-50/70 to-white px-5 py-8 text-center shadow-[0_18px_45px_-35px_rgba(234,88,12,0.5)]">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white/90 text-xl shadow-sm">
        ◌
      </div>
      <p className="text-sm font-semibold text-stone-700">{title}</p>
      <p className="mt-2 text-sm leading-6 text-stone-500">{description}</p>
    </div>
  );
}

function MemoryListError({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-[1.75rem] border border-rose-200/80 bg-rose-50/80 px-5 py-6 shadow-[0_18px_45px_-35px_rgba(225,29,72,0.45)]">
      <p className="text-sm font-semibold text-rose-700">记忆加载失败</p>
      <p className="mt-2 text-sm leading-6 text-rose-600">{message}</p>
      {onRetry ? (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 inline-flex items-center rounded-full border border-rose-200 bg-white px-4 py-2 text-sm font-medium text-rose-700 transition hover:border-rose-300 hover:bg-rose-100"
        >
          重新加载
        </button>
      ) : null}
    </div>
  );
}

export function MemoryList({
  items,
  loading = false,
  error,
  title = "长期记忆",
  emptyTitle = "暂时还没有可展示的记忆",
  emptyDescription = "对话深入后，这里会沉淀偏好、关系事件和摘要片段，帮助角色保持连续感。",
  className,
  onRetry,
}: MemoryListProps) {
  return (
    <Card
      className={cn(
        "overflow-hidden rounded-[2rem] border-orange-100/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,247,237,0.92))] shadow-[0_24px_70px_-40px_rgba(194,65,12,0.45)]",
        className,
      )}
    >
      <CardHeader className="border-b border-orange-100/80 bg-[radial-gradient(circle_at_top_left,rgba(255,237,213,0.9),rgba(255,255,255,0)_55%)] pb-4">
        <div className="flex flex-col items-start gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-orange-500/80">
              Memory Ledger
            </p>
            <CardTitle className="mt-2 text-lg font-semibold text-stone-800">
              {title}
            </CardTitle>
          </div>
          <div className="rounded-full border border-orange-200/80 bg-white/90 px-3 py-1 text-xs font-medium text-orange-600 shadow-sm">
            {items.length} 条
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? <MemoryListSkeleton /> : null}
        {!loading && error ? <MemoryListError message={error} onRetry={onRetry} /> : null}
        {!loading && !error && items.length === 0 ? (
          <MemoryListEmpty
            title={emptyTitle}
            description={emptyDescription}
          />
        ) : null}
        {!loading && !error && items.length > 0 ? (
          <div className="space-y-3">
            {items.map((item, index) => {
              const timestamp = formatTimestamp(item.created_at);
              const isSummary = item.type === "summary";

              return (
                <article
                  key={item.id ?? `${item.type}-${index}`}
                  className={cn(
                    "group overflow-hidden rounded-[1.6rem] border border-orange-100/80 bg-white/85 shadow-[0_20px_50px_-35px_rgba(120,53,15,0.55)] transition duration-300 hover:-translate-y-0.5 hover:shadow-[0_24px_60px_-32px_rgba(194,65,12,0.45)]",
                    isSummary && "border-amber-200/80 bg-[linear-gradient(135deg,rgba(255,251,235,0.98),rgba(255,255,255,0.96))]",
                  )}
                >
                  <div
                    className={cn(
                      "h-1.5 bg-gradient-to-r from-orange-300 via-amber-200 to-rose-200",
                      isSummary && "from-amber-400 via-orange-200 to-yellow-100",
                    )}
                  />
                  <div className="space-y-3 px-4 py-4">
                    <div className="flex flex-col items-start gap-2">
                      <div className="inline-flex items-center gap-2">
                        <span className="rounded-full bg-orange-100 px-2.5 py-1 text-[11px] font-semibold tracking-[0.16em] text-orange-700">
                          {formatMemoryType(item.type)}
                        </span>
                        {isSummary ? (
                          <span className="rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-[11px] font-medium text-amber-700">
                            Summary
                          </span>
                        ) : null}
                      </div>
                      <div className="rounded-full bg-stone-100 px-2.5 py-1 text-[11px] font-medium text-stone-600">
                        重要度 {formatImportance(item.importance)}
                      </div>
                    </div>
                    <p className="text-sm leading-6 text-stone-700">{item.content}</p>
                    <div className="flex flex-col items-start gap-1 text-xs text-stone-400">
                      <span>记忆片段 {String(index + 1).padStart(2, "0")}</span>
                      {timestamp ? <span>{timestamp}</span> : null}
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
