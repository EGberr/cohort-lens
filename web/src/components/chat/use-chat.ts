"use client";

import { useCallback, useRef, useState } from "react";
import { streamChat, type ChartSpec, type Dataset, type PassageSource, type StreamEvent } from "@/lib/api";
import type { ToolCall } from "@/components/chat/trace";
import type { Lang } from "@/lib/i18n";

export type AssistantMsg = {
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
export type UserMsg = { id: string; role: "user"; content: string };
export type Msg = UserMsg | AssistantMsg;

const uid = () => Math.random().toString(36).slice(2, 10);

/** Conversation state + SSE streaming for the analyst, optionally scoped to one category. */
export function useChat({ category, lang, errorText }: { category?: string; lang: Lang; errorText: string }) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const patch = useCallback((id: string, fn: (m: AssistantMsg) => AssistantMsg) => {
    setMessages((ms) => ms.map((m) => (m.id === id && m.role === "assistant" ? fn(m) : m)));
  }, []);

  const send = useCallback(
    async (text: string) => {
      const q = text.trim();
      if (!q || busy) return;
      const user: UserMsg = { id: uid(), role: "user", content: q };
      const asst: AssistantMsg = { id: uid(), role: "assistant", content: "", running: true, calls: [], sources: [], datasets: [], charts: [] };
      const history = [...messages, user].map((m) => ({ role: m.role, content: m.content }));
      setMessages((ms) => [...ms, user, asst]);
      setSelected(asst.id);
      setBusy(true);
      const ctrl = new AbortController();
      abortRef.current = ctrl;
      const onEvent = (e: StreamEvent) =>
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
      try {
        await streamChat(history, onEvent, { signal: ctrl.signal, category, lang });
      } catch {
        if (!ctrl.signal.aborted) patch(asst.id, (m) => ({ ...m, error: errorText }));
      } finally {
        patch(asst.id, (m) => ({ ...m, running: false }));
        setBusy(false);
        abortRef.current = null;
      }
    },
    [busy, messages, patch, category, lang, errorText],
  );

  const stop = useCallback(() => abortRef.current?.abort(), []);
  const reset = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setSelected(null);
  }, []);

  const current = messages.find((m) => m.id === selected && m.role === "assistant") as AssistantMsg | undefined;
  return { messages, busy, send, stop, reset, selected, setSelected, current };
}
