"use client";

import { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ArrowUp, Database, FileText, PanelRightClose, PanelRightOpen, RotateCcw, Square } from "lucide-react";
import { streamChat, type ChartSpec, type Dataset, type PassageSource, type StreamEvent } from "@/lib/api";
import { cx } from "@/lib/format";
import { Answer } from "@/components/chat/answer";
import { EvidencePanel } from "@/components/chat/evidence";
import { Trace, type ToolCall } from "@/components/chat/trace";
import { ChartFromSpec } from "@/components/charts";
import { DocReader } from "@/components/doc-reader";

type AssistantMsg = {
  id: string;
  role: "assistant";
  content: string;
  status?: string;
  running: boolean;
  calls: ToolCall[];
  sources: PassageSource[];
  datasets: Dataset[];
  charts: ChartSpec[];
  meta?: { model: string; latency_ms: number; usage: Record<string, number>; mode: string };
  error?: string;
};
type UserMsg = { id: string; role: "user"; content: string };
type Msg = UserMsg | AssistantMsg;

const SUGGESTIONS = [
  { tag: "Path to purchase", q: "Where does Gen Z discover and buy skincare, and how does it differ between 16-19 and 25-29 year-olds?" },
  { tag: "Values", q: "Which categories show the biggest sustainability say-do gap among Gen Z?" },
  { tag: "Compare", q: "Compare sneakers and athleisure: who buys them, where, and why?" },
  { tag: "Dupe culture", q: "How big is dupe culture in beauty, and how should prestige brands respond?" },
  { tag: "Markets", q: "Is resale fashion more popular in France than in Germany?" },
  { tag: "Targeting", q: "Which fast-growing categories should a brand targeting young men prioritise?" },
];

const uid = () => Math.random().toString(36).slice(2, 10);

export default function Page() {
  return (
    <Suspense fallback={<div className="h-screen" />}>
      <AskPage />
    </Suspense>
  );
}

function AskPage() {
  const searchParams = useSearchParams();
  const [messages, setMessages] = useState<Msg[]>([]);
  // Prefilled from ?q= (links from category pages).
  const [input, setInput] = useState(() => searchParams.get("q") ?? "");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [activeCite, setActiveCite] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(true);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [reader, setReader] = useState<{ docId: string; section?: string } | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: "end", behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    ta.style.height = "0px";
    ta.style.height = `${Math.min(ta.scrollHeight, 180)}px`;
  }, [input]);

  const patch = useCallback((id: string, fn: (m: AssistantMsg) => AssistantMsg) => {
    setMessages((ms) => ms.map((m) => (m.id === id && m.role === "assistant" ? fn(m) : m)));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || busy) return;
      const user: UserMsg = { id: uid(), role: "user", content: q };
      const asst: AssistantMsg = { id: uid(), role: "assistant", content: "", running: true, calls: [], sources: [], datasets: [], charts: [], status: "Planning the analysis" };
      const history = [...messages, user].map((m) => ({ role: m.role, content: m.content }));
      setMessages((ms) => [...ms, user, asst]);
      setSelected(asst.id);
      setActiveCite(null);
      setInput("");
      setBusy(true);
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      const onEvent = (e: StreamEvent) => {
        patch(asst.id, (m) => {
          switch (e.type) {
            case "status":
              return { ...m, status: e.text };
            case "text":
              return { ...m, content: m.content + e.delta };
            case "tool_call":
              return { ...m, calls: [...m.calls, { id: e.id, name: e.name, input: e.input, is_error: e.is_error, summary: e.summary }] };
            case "source":
              return { ...m, sources: [...m.sources, e.source] };
            case "dataset":
              return { ...m, datasets: [...m.datasets, e.dataset] };
            case "chart":
              return { ...m, charts: [...m.charts, e.chart] };
            case "done":
              return { ...m, running: false, meta: { model: e.model, latency_ms: e.latency_ms, usage: e.usage, mode: e.mode } };
            case "error":
              return { ...m, running: false, error: e.message };
          }
        });
      };
      try {
        await streamChat(history, onEvent, ctrl.signal);
      } catch {
        if (!ctrl.signal.aborted) patch(asst.id, (m) => ({ ...m, error: "Could not reach the analyst. Is the backend running on :8000?" }));
      } finally {
        patch(asst.id, (m) => ({ ...m, running: false }));
        setBusy(false);
        abortRef.current = null;
      }
    },
    [busy, messages, patch],
  );

  const stop = () => abortRef.current?.abort();
  const reset = () => {
    stop();
    setMessages([]);
    setSelected(null);
  };

  const current = messages.find((m) => m.id === selected && m.role === "assistant") as AssistantMsg | undefined;
  const onCite = (msgId: string) => (id: string) => {
    setSelected(msgId);
    setActiveCite(id);
    setPanelOpen(true);
    if (window.matchMedia("(max-width: 1279px)").matches) setSheetOpen(true);
  };

  const empty = messages.length === 0;

  return (
    <div className="flex h-[calc(100vh-3.5rem)] lg:h-screen">
      <section className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b hairline px-5">
          <div className="flex items-center gap-2 text-[13px]">
            <span className="font-medium">Ask the analyst</span>
            <span className="hidden text-muted sm:inline">· grounded in 65 reports and a 6,000-respondent panel</span>
          </div>
          <div className="flex items-center gap-1">
            {!empty && (
              <button onClick={reset} className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-[12.5px] text-muted hover:bg-surface-2 hover:text-ink">
                <RotateCcw size={14} /> New
              </button>
            )}
            <button onClick={() => setPanelOpen((o) => !o)} className="hidden rounded-lg p-2 text-muted hover:bg-surface-2 hover:text-ink xl:block" aria-label="Toggle evidence panel">
              {panelOpen ? <PanelRightClose size={16} /> : <PanelRightOpen size={16} />}
            </button>
          </div>
        </header>

        <div className="scroll-thin flex-1 overflow-y-auto">
          {empty ? (
            <div className="mx-auto flex max-w-3xl flex-col px-5 pb-10 pt-14 sm:pt-24">
              <p className="mb-4 inline-flex w-fit items-center gap-2 rounded-full border hairline bg-surface px-3 py-1 text-[11.5px] text-muted">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-ink" /> Agentic RAG · 50 categories · 6 markets
              </p>
              <h1 className="font-serif text-[44px] leading-[1.02] tracking-tight sm:text-[60px]">
                What does Gen Z <em className="highlight not-italic">actually</em> buy — and why?
              </h1>
              <p className="mt-5 max-w-xl text-[15px] leading-relaxed text-ink-2">
                Ask in plain language. The analyst searches the research library, runs exact queries on the survey panel, and answers with every number cited back to its source.
              </p>
              <div className="mt-10 grid gap-2.5 sm:grid-cols-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s.q}
                    onClick={() => send(s.q)}
                    className="card group flex flex-col gap-1.5 p-4 text-left transition-all hover:-translate-y-0.5 hover:border-line-strong"
                  >
                    <span className="text-[11px] font-medium uppercase tracking-[0.12em] text-accent-ink">{s.tag}</span>
                    <span className="text-[13.5px] leading-snug text-ink-2 group-hover:text-ink">{s.q}</span>
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="mx-auto flex max-w-3xl flex-col gap-8 px-5 py-8">
              {messages.map((m) =>
                m.role === "user" ? (
                  <div key={m.id} className="flex justify-end">
                    <p className="max-w-[85%] rounded-2xl rounded-br-md bg-ink px-4 py-2.5 text-[14.5px] leading-relaxed text-bg">{m.content}</p>
                  </div>
                ) : (
                  <article key={m.id} onClick={() => setSelected(m.id)} className={cx("rounded-2xl transition-colors", selected === m.id && messages.length > 2 && "")}>
                    <Trace calls={m.calls} status={m.status} running={m.running && !m.content} />
                    {m.content && <Answer text={m.content} streaming={m.running} activeCite={selected === m.id ? activeCite : null} onCite={onCite(m.id)} />}
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
                        <button onClick={() => { setSelected(m.id); setPanelOpen(true); if (window.matchMedia("(max-width: 1279px)").matches) setSheetOpen(true); }} className="flex items-center gap-1 hover:text-ink">
                          <Database size={12} /> {m.datasets.length} datasets
                        </button>
                        <button onClick={() => { setSelected(m.id); setPanelOpen(true); if (window.matchMedia("(max-width: 1279px)").matches) setSheetOpen(true); }} className="flex items-center gap-1 hover:text-ink">
                          <FileText size={12} /> {m.sources.length} passages
                        </button>
                        <span className="num">{(m.meta.latency_ms / 1000).toFixed(1)}s</span>
                        <span>{m.meta.mode === "claude" ? m.meta.model : "offline analyst"}</span>
                        {m.meta.usage?.input_tokens ? (
                          <span className="num">
                            {(m.meta.usage.input_tokens + (m.meta.usage.cache_read_input_tokens ?? 0)).toLocaleString("en-GB")} in · {m.meta.usage.output_tokens.toLocaleString("en-GB")} out
                          </span>
                        ) : null}
                      </div>
                    )}
                  </article>
                ),
              )}
              <div ref={endRef} className="h-4" />
            </div>
          )}
        </div>

        <div className="shrink-0 px-5 pb-5">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              send(input);
            }}
            className="card mx-auto flex max-w-3xl items-end gap-2 p-2 pl-4 focus-within:border-line-strong"
          >
            <textarea
              ref={taRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  send(input);
                }
              }}
              rows={1}
              placeholder="Ask about a category, a segment or a market…"
              className="max-h-[180px] flex-1 resize-none bg-transparent py-2 text-[14.5px] outline-none placeholder:text-muted"
            />
            {busy ? (
              <button type="button" onClick={stop} aria-label="Stop" className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-3 text-ink hover:brightness-95">
                <Square size={13} fill="currentColor" />
              </button>
            ) : (
              <button type="submit" disabled={!input.trim()} aria-label="Send" className="flex h-9 w-9 items-center justify-center rounded-xl bg-ink text-bg transition-opacity disabled:opacity-25">
                <ArrowUp size={16} />
              </button>
            )}
          </form>
          <p className="mx-auto mt-2 max-w-3xl text-center text-[11px] text-muted">Demo data is synthetic. Numbers are cited: [D#] survey datasets, [S#] research passages.</p>
        </div>
      </section>

      {panelOpen && (
        <aside className="scroll-thin hidden w-[380px] shrink-0 overflow-y-auto border-l hairline bg-bg p-4 xl:block">
          <div className="mb-3 flex items-center justify-between">
            <h3 className="text-[13px] font-medium">Evidence</h3>
            {current && <span className="text-[11px] text-muted">{current.datasets.length + current.sources.length} items</span>}
          </div>
          <EvidencePanel
            sources={current?.sources ?? []}
            datasets={current?.datasets ?? []}
            active={activeCite}
            onOpenDoc={(docId, section) => setReader({ docId, section })}
          />
        </aside>
      )}
      {sheetOpen && current && (
        <div className="fixed inset-0 z-40 xl:hidden" role="dialog" aria-modal="true">
          <div className="absolute inset-0 bg-black/40" onClick={() => setSheetOpen(false)} />
          <div className="scroll-thin absolute inset-x-0 bottom-0 max-h-[78vh] overflow-y-auto rounded-t-3xl border-t hairline bg-bg p-4 pb-8">
            <div className="mx-auto mb-3 h-1 w-10 rounded-full bg-surface-3" />
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-[13px] font-medium">Evidence</h3>
              <button onClick={() => setSheetOpen(false)} className="text-[12px] text-muted hover:text-ink">
                Close
              </button>
            </div>
            <EvidencePanel
              sources={current.sources}
              datasets={current.datasets}
              active={activeCite}
              onOpenDoc={(docId, section) => {
                setSheetOpen(false);
                setReader({ docId, section });
              }}
            />
          </div>
        </div>
      )}
      <DocReader docId={reader?.docId ?? null} section={reader?.section} onClose={() => setReader(null)} />
    </div>
  );
}
