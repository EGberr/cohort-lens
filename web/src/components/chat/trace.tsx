"use client";

import { useState } from "react";
import { AlertTriangle, BarChart3, ChevronDown, Database, ListTree, Search, Sparkles } from "lucide-react";
import { cx } from "@/lib/format";

export type ToolCall = { id: string; name: string; input: Record<string, unknown>; is_error: boolean; summary: string };

const ICONS: Record<string, typeof Search> = {
  search_research: Search,
  query_survey: Database,
  list_categories: ListTree,
  create_chart: BarChart3,
};
const LABELS: Record<string, string> = {
  search_research: "Searched research",
  query_survey: "Queried survey",
  list_categories: "Listed categories",
  create_chart: "Built chart",
};

function describe(call: ToolCall) {
  const i = call.input as Record<string, unknown>;
  if (call.name === "search_research") return `“${i.query as string}”`;
  if (call.name === "query_survey") {
    const cats = (i.categories as string[]) ?? [];
    const parts = [String(i.metric).replaceAll("_", " "), cats.slice(0, 3).join(", ") + (cats.length > 3 ? ` +${cats.length - 3}` : "")];
    if (i.breakdown) parts.push(`by ${String(i.breakdown).replace("_", " ")}`);
    if (i.filters && Object.keys(i.filters as object).length) parts.push(`filtered`);
    return parts.join(" · ");
  }
  if (call.name === "create_chart") return String(i.title ?? "");
  return "";
}

export function Trace({ calls, status, running }: { calls: ToolCall[]; status?: string; running: boolean }) {
  const [open, setOpen] = useState(false);
  if (!calls.length && !running) return null;
  return (
    <div className="mb-4 rounded-2xl border hairline bg-surface-2/60">
      <button onClick={() => setOpen((o) => !o)} className="flex w-full items-center gap-2.5 px-3.5 py-2.5 text-left text-[12.5px]">
        <Sparkles size={14} className="shrink-0 text-accent-ink" />
        {running ? (
          <span className="text-shimmer font-medium">{status ?? "Thinking"}…</span>
        ) : (
          <span className="font-medium text-ink-2">
            Analysis trace · {calls.length} step{calls.length === 1 ? "" : "s"}
          </span>
        )}
        <span className="ml-auto flex items-center gap-1.5 text-muted">
          {calls.slice(-5).map((c) => {
            const Icon = ICONS[c.name] ?? Search;
            return <Icon key={c.id} size={12} className={c.is_error ? "text-negative" : undefined} />;
          })}
          <ChevronDown size={14} className={cx("transition-transform", open && "rotate-180")} />
        </span>
      </button>
      {open && (
        <ol className="relative mx-3.5 mb-3 border-l hairline pl-4">
          {calls.map((c) => {
            const Icon = c.is_error ? AlertTriangle : (ICONS[c.name] ?? Search);
            return (
              <li key={c.id} className="relative py-1.5">
                <span className={cx("absolute -left-[25px] top-2 flex h-[18px] w-[18px] items-center justify-center rounded-full border bg-surface", c.is_error ? "border-negative text-negative" : "hairline text-accent-ink")}>
                  <Icon size={10} />
                </span>
                <p className="text-[12.5px] text-ink">
                  <span className="font-medium">{LABELS[c.name] ?? c.name}</span> <span className="text-ink-2">{describe(c)}</span>
                </p>
                <p className={cx("num text-[11px]", c.is_error ? "text-negative" : "text-muted")}>{c.summary}</p>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
