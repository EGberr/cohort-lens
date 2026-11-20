"use client";

import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { X } from "lucide-react";
import { api, type DocFull } from "@/lib/api";

const TYPE_LABEL: Record<string, string> = {
  category_report: "Category report",
  sector_report: "Sector overview",
  thematic_report: "Thematic report",
  methodology: "Methodology",
  external: "Imported document",
};
export const docTypeLabel = (t: string) => TYPE_LABEL[t] ?? t;

/** Slide-over reader for a corpus document; optionally scrolls to and highlights a section. */
export function DocReader({ docId, section, onClose }: { docId: string | null; section?: string; onClose: () => void }) {
  const [state, setState] = useState<{ id: string; doc?: DocFull; error?: string } | null>(null);
  const bodyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!docId) return;
    let live = true;
    api
      .document(docId)
      .then((doc) => live && setState({ id: docId, doc }))
      .catch((e) => live && setState({ id: docId, error: String(e) }));
    return () => {
      live = false;
    };
  }, [docId]);
  const doc = state?.id === docId ? (state.doc ?? null) : null;
  const error = state?.id === docId ? (state.error ?? null) : null;

  useEffect(() => {
    if (!doc || !section || !bodyRef.current) return;
    const h = Array.from(bodyRef.current.querySelectorAll("h2")).find((el) => el.textContent?.trim() === section);
    if (h) {
      h.scrollIntoView({ block: "start", behavior: "smooth" });
      h.classList.add("highlight");
    }
  }, [doc, section]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!docId) return null;
  const body = doc?.body.replace(/^# .+\n/, "") ?? "";
  return (
    <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/35 backdrop-blur-[2px]" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-[720px] flex-col bg-surface shadow-2xl">
        <div className="flex items-center justify-between border-b hairline px-6 py-4">
          <span className="text-xs font-medium uppercase tracking-[0.14em] text-muted">{doc ? docTypeLabel(doc.type) : "Loading"}</span>
          <button aria-label="Close" onClick={onClose} className="rounded-lg p-1.5 text-muted hover:bg-surface-2 hover:text-ink">
            <X size={18} />
          </button>
        </div>
        <div ref={bodyRef} className="scroll-thin flex-1 overflow-y-auto px-6 py-8 sm:px-10">
          {error && <p className="text-sm text-negative">{error}</p>}
          {!doc && !error && (
            <div className="flex flex-col gap-3">
              <div className="shimmer h-9 w-3/4 rounded-lg" />
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="shimmer h-4 rounded" style={{ width: `${90 - (i % 3) * 12}%` }} />
              ))}
            </div>
          )}
          {doc && (
            <article className="prose-doc">
              <h1>{doc.title}</h1>
              <p className="!mb-6 text-xs text-muted">
                {doc.meta.publisher} · {doc.meta.wave} · {doc.meta.date}
              </p>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{body}</ReactMarkdown>
            </article>
          )}
        </div>
      </div>
    </div>
  );
}
