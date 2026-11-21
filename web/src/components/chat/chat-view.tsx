"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { ArrowUp, Database, FileText, RotateCcw, Square } from "lucide-react";
import { cx } from "@/lib/format";
import { useLang } from "@/lib/i18n";
import { Answer } from "@/components/chat/answer";
import { EvidencePanel } from "@/components/chat/evidence";
import { Trace } from "@/components/chat/trace";
import { ChartFromSpec } from "@/components/charts";
import { DocReader } from "@/components/doc-reader";
import { useChat, type AssistantMsg } from "@/components/chat/use-chat";

type Props = {
  category?: string;
  categoryName?: string;
  suggestions: string[];
  initialQuestion?: string;
  /** "full": page layout with a side evidence column. "panel": compact column (category page). */
  variant?: "full" | "panel";
  emptyState?: ReactNode;
};

/** The analyst conversation: trace, cited answer, charts, evidence and composer. */
export function ChatView({ category, categoryName, suggestions, initialQuestion, variant = "full", emptyState }: Props) {
  const { t, lang } = useLang();
  const chat = useChat({ category, lang, errorText: t("chat.error") });
  const [input, setInput] = useState(initialQuestion ?? "");
  const [activeCite, setActiveCite] = useState<string | null>(null);
  const [sheet, setSheet] = useState(false);
  const [reader, setReader] = useState<{ docId: string; section?: string } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);
  const full = variant === "full";

  useEffect(() => {
    const el = scrollRef.current;
    if (el) el.scrollTo({ top: el.scrollHeight, behavior: "smooth" });
  }, [chat.messages]);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, [input]);

  const submit = (text: string) => {
    if (!text.trim()) return;
    chat.send(text);
    setInput("");
    setActiveCite(null);
  };
  const openEvidence = (msgId: string, cite?: string) => {
    chat.setSelected(msgId);
    if (cite) setActiveCite(cite);
    if (!full || window.matchMedia("(max-width: 1279px)").matches) setSheet(true);
  };

  const evidence = (m: AssistantMsg | undefined, onOpen: (d: string, s: string) => void) => (
    <EvidencePanel sources={m?.sources ?? []} datasets={m?.datasets ?? []} active={activeCite} onOpenDoc={onOpen} />
  );

  const empty = chat.messages.length === 0;
  const placeholder = categoryName ? t("chat.placeholder_scoped", { name: categoryName }) : t("chat.placeholder");

  return (
    <div className={cx("flex min-h-0", full ? "h-[calc(100vh-4rem)]" : "h-full flex-col")}>
      <section className="flex min-h-0 min-w-0 flex-1 flex-col">
        {!empty && (
          <div className={cx("flex shrink-0 items-center justify-end gap-1 px-4 pt-3", full && "mx-auto w-full max-w-3xl")}>
            <button onClick={chat.reset} className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[12.5px] text-muted hover:bg-surface-2 hover:text-ink">
              <RotateCcw size={14} /> {t("chat.new")}
            </button>
          </div>
        )}
        <div ref={scrollRef} className="scroll-thin min-h-0 flex-1 overflow-y-auto">
          {empty ? (
            <div className={cx("flex flex-col px-5", full ? "mx-auto max-w-3xl pb-10 pt-12 sm:pt-20" : "pb-4 pt-5")}>
              {emptyState}
              <div className={cx("grid gap-2", full ? "mt-8 sm:grid-cols-2" : "mt-4")}>
                {suggestions.map((s) => (
                  <button
                    key={s}
                    onClick={() => submit(s)}
                    className="card group p-3.5 text-left text-[13px] leading-snug text-ink-2 transition-all hover:-translate-y-0.5 hover:border-line-strong hover:text-ink"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className={cx("flex flex-col gap-7 py-5", full ? "mx-auto max-w-3xl px-5" : "px-4")}>
              {chat.messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="flex justify-end">
                    <p className="max-w-[88%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-[14px] leading-relaxed text-bg">{m.content}</p>
                  </div>
                ) : (
                  <article key={m.id} onClick={() => chat.setSelected(m.id)}>
                    <Trace calls={m.calls} status={m.status ?? t("chat.thinking")} running={m.running && !m.content} />
                    {m.content && (
                      <Answer
                        text={m.content}
                        streaming={m.running}
                        activeCite={chat.selected === m.id ? activeCite : null}
                        onCite={(id) => openEvidence(m.id, id)}
                      />
                    )}
                    {m.charts.length > 0 && (
                      <div className="mt-4 grid gap-3">
                        {m.charts.map((c) => (
                          <ChartFromSpec key={c.id} spec={c} />
                        ))}
                      </div>
                    )}
                    {m.error && <p className="mt-3 rounded-xl border border-negative/30 bg-negative/5 px-3 py-2 text-[13px] text-negative">{m.error}</p>}
                    {m.meta && (
                      <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11.5px] text-muted">
                        <button onClick={() => openEvidence(m.id)} className="flex items-center gap-1 hover:text-ink">
                          <Database size={12} /> {m.datasets.length} {t("chat.datasets")}
                        </button>
                        <button onClick={() => openEvidence(m.id)} className="flex items-center gap-1 hover:text-ink">
                          <FileText size={12} /> {m.sources.length} {t("chat.passages")}
                        </button>
                        <span className="num">{(m.meta.latency_ms / 1000).toFixed(1)}s</span>
                        <span>{m.meta.mode === "claude" ? m.meta.model : t("status.offline")}</span>
                      </div>
                    )}
                  </article>
                ),
              )}
            </div>
          )}
        </div>

        <div className={cx("shrink-0", full ? "px-5 pb-5" : "border-t hairline p-3")}>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              submit(input);
            }}
            className={cx("card flex items-end gap-2 p-2 pl-4 focus-within:border-line-strong", full && "mx-auto max-w-3xl")}
          >
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit(input);
                }
              }}
              rows={1}
              placeholder={placeholder}
              aria-label={placeholder}
              className="max-h-[160px] flex-1 resize-none bg-transparent py-2 text-[14px] outline-none placeholder:text-muted"
            />
            {chat.busy ? (
              <button type="button" onClick={chat.stop} aria-label="Stop" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-surface-3 text-ink">
                <Square size={13} fill="currentColor" />
              </button>
            ) : (
              <button type="submit" disabled={!input.trim()} aria-label="Send" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-ink text-bg transition-opacity disabled:opacity-25">
                <ArrowUp size={16} />
              </button>
            )}
          </form>
          {full && <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted">{t("chat.disclaimer")}</p>}
        </div>
      </section>

      {full && (
        <aside className="scroll-thin hidden w-[380px] shrink-0 overflow-y-auto border-l hairline p-4 xl:block">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-[13px] font-medium">{t("chat.evidence")}</h3>
            {chat.current && (
              <span className="text-[11px] text-muted">
                {chat.current.datasets.length + chat.current.sources.length} {t("chat.items")}
              </span>
            )}
          </div>
          {evidence(chat.current, (docId, section) => setReader({ docId, section }))}
        </aside>
      )}

      {sheet && chat.current && (
        <div className={cx("fixed inset-0 z-50", full && "xl:hidden")} role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSheet(false)} />
          <div className="scroll-thin absolute inset-x-0 bottom-0 max-h-[80vh] overflow-y-auto rounded-t-3xl border-t hairline bg-bg p-4 pb-8 sm:inset-x-auto sm:bottom-4 sm:right-4 sm:top-4 sm:max-h-none sm:w-[420px] sm:rounded-3xl sm:border">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-[13px] font-medium">{t("chat.evidence")}</h3>
              <button onClick={() => setSheet(false)} className="text-[12px] text-muted hover:text-ink">
                {t("chat.close")}
              </button>
            </div>
            {evidence(chat.current, (docId, section) => {
              setSheet(false);
              setReader({ docId, section });
            })}
          </div>
        </div>
      )}
      <DocReader docId={reader?.docId ?? null} section={reader?.section} onClose={() => setReader(null)} />
    </div>
  );
}
