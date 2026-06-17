import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface EmotionHistoryItem {
  id?: string;
  favorability: number;
  trust: number;
  mood: string;
  dependency: number;
  updated_at?: string;
  created_at?: string;
}

export interface EmotionHistoryProps {
  items: EmotionHistoryItem[];
  loading?: boolean;
  error?: string | null;
  title?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  className?: string;
  onRetry?: () => void;
}

const metricConfig = [
  { key: "favorability", label: "好感", accent: "bg-rose-400", tint: "bg-rose-50 text-rose-700" },
  { key: "trust", label: "信任", accent: "bg-sky-400", tint: "bg-sky-50 text-sky-700" },
  { key: "dependency", label: "依赖", accent: "bg-amber-400", tint: "bg-amber-50 text-amber-700" },
] as const;

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

function EmotionHistorySkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <div
          key={index}
          className="rounded-[1.75rem] border border-orange-100/80 bg-white/90 p-4 shadow-[0_18px_45px_-35px_rgba(154,52,18,0.45)]"
        >
          <div className="mb-4 flex flex-col items-start gap-3">
            <div className="h-5 w-16 animate-pulse rounded-full bg-orange-100" />
            <div className="h-4 w-24 animate-pulse rounded-full bg-stone-100" />
          </div>
          <div className="grid gap-3">
            {Array.from({ length: 3 }).map((__, innerIndex) => (
              <div key={innerIndex} className="space-y-2">
                <div className="h-4 w-12 animate-pulse rounded-full bg-stone-100" />
                <div className="h-2 w-full animate-pulse rounded-full bg-orange-100" />
                <div className="h-4 w-8 animate-pulse rounded-full bg-stone-100" />
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function EmotionHistoryEmpty({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <div className="rounded-[1.75rem] border border-dashed border-orange-200/80 bg-gradient-to-br from-white via-orange-50/70 to-amber-50/80 px-5 py-8 text-center shadow-[0_18px_45px_-35px_rgba(234,88,12,0.45)]">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-full bg-white text-xl shadow-sm">
        ∿
      </div>
      <p className="text-sm font-semibold text-stone-700">{title}</p>
      <p className="mt-2 text-sm leading-6 text-stone-500">{description}</p>
    </div>
  );
}

function EmotionHistoryError({
  message,
  onRetry,
}: {
  message: string;
  onRetry?: () => void;
}) {
  return (
    <div className="rounded-[1.75rem] border border-rose-200/80 bg-rose-50/80 px-5 py-6 shadow-[0_18px_45px_-35px_rgba(225,29,72,0.45)]">
      <p className="text-sm font-semibold text-rose-700">情绪轨迹加载失败</p>
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

function MetricBar({
  label,
  value,
  accentClassName,
  tintClassName,
}: {
  label: string;
  value: number;
  accentClassName: string;
  tintClassName: string;
}) {
  const safeValue = Number.isFinite(value) ? value : 0;
  const width = `${Math.max(0, Math.min(safeValue, 100))}%`;

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className={cn("rounded-full px-2.5 py-1 text-[11px] font-semibold", tintClassName)}>
          {label}
        </span>
        <span className="text-sm font-semibold text-stone-700">{safeValue}</span>
      </div>
      <div className="h-2.5 overflow-hidden rounded-full bg-stone-100">
        <div
          className={cn("h-full rounded-full transition-[width] duration-500", accentClassName)}
          style={{ width }}
        />
      </div>
    </div>
  );
}

export function EmotionHistory({
  items,
  loading = false,
  error,
  title = "情绪时间线",
  emptyTitle = "还没有情绪变化记录",
  emptyDescription = "开始对话后，这里会按时间展示角色的好感、信任与依赖变化，以及当下心情。",
  className,
  onRetry,
}: EmotionHistoryProps) {
  return (
    <Card
      className={cn(
        "overflow-hidden rounded-[2rem] border-orange-100/80 bg-[linear-gradient(180deg,rgba(255,255,255,0.98),rgba(255,251,235,0.92))] shadow-[0_24px_70px_-40px_rgba(194,65,12,0.45)]",
        className,
      )}
    >
      <CardHeader className="border-b border-orange-100/80 bg-[radial-gradient(circle_at_top_left,rgba(255,237,213,0.9),rgba(255,255,255,0)_55%)] pb-4">
        <div className="flex flex-col items-start gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.28em] text-orange-500/80">
              Emotion Timeline
            </p>
            <CardTitle className="mt-2 text-lg font-semibold text-stone-800">
              {title}
            </CardTitle>
          </div>
          <div className="rounded-full border border-orange-200/80 bg-white/90 px-3 py-1 text-xs font-medium text-orange-600 shadow-sm">
            {items.length} 个节点
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? <EmotionHistorySkeleton /> : null}
        {!loading && error ? (
          <EmotionHistoryError message={error} onRetry={onRetry} />
        ) : null}
        {!loading && !error && items.length === 0 ? (
          <EmotionHistoryEmpty
            title={emptyTitle}
            description={emptyDescription}
          />
        ) : null}
        {!loading && !error && items.length > 0 ? (
          <div className="space-y-4">
            {items.map((item, index) => {
              const timestamp = formatTimestamp(item.updated_at ?? item.created_at);

              return (
                <article
                  key={item.id ?? `${item.mood}-${index}`}
                  className="relative rounded-[1.75rem] border border-orange-100/80 bg-white/90 p-4 shadow-[0_18px_45px_-35px_rgba(154,52,18,0.45)]"
                >
                  <div className="relative space-y-4">
                    <div className="flex flex-col items-start gap-3">
                      <div className="inline-flex items-center gap-2">
                        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-orange-400 to-amber-300 text-sm font-bold text-white shadow-sm">
                          {index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-semibold text-stone-800">
                            情绪节点
                          </p>
                          <p className="text-xs text-stone-400">
                            {timestamp ?? "时间未知"}
                          </p>
                        </div>
                      </div>
                      <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
                        心情 {item.mood}
                      </span>
                    </div>
                    <div className="grid gap-3">
                      {metricConfig.map((metric) => (
                        <MetricBar
                          key={metric.key}
                          label={metric.label}
                          value={item[metric.key]}
                          accentClassName={metric.accent}
                          tintClassName={metric.tint}
                        />
                      ))}
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
