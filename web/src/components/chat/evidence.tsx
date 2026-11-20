"use client";

import { useEffect, useRef } from "react";
import { BarChart3, ChevronRight, Database, FileText } from "lucide-react";
import type { Dataset, PassageSource } from "@/lib/api";
import { cx, SEGMENT_LABEL } from "@/lib/format";
import { fmtValue } from "@/components/charts";
import { docTypeLabel } from "@/components/doc-reader";

export function DatasetTable({ ds, compact }: { ds: Dataset; compact?: boolean }) {
  const multiCat = Object.keys(ds.category_names).length > 1;
  const rows = compact ? ds.rows.slice(0, 8) : ds.rows;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-[12px]">
        <thead>
          <tr className="text-left text-muted">
            {multiCat && <th className="pb-1.5 pr-2 font-medium">Category</th>}
            {ds.breakdown && <th className="pb-1.5 pr-2 font-medium capitalize">{ds.breakdown.replace("_", " ")}</th>}
            {rows[0]?.option && <th className="pb-1.5 pr-2 font-medium">Option</th>}
            <th className="pb-1.5 pr-2 text-right font-medium">Value</th>
            <th className="pb-1.5 text-right font-medium">n</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t hairline">
              {multiCat && <td className="py-1.5 pr-2 text-ink-2">{ds.category_names[r.category]}</td>}
              {ds.breakdown && <td className="py-1.5 pr-2 text-ink-2">{SEGMENT_LABEL(r.segment)}</td>}
              {r.option && <td className="py-1.5 pr-2 text-ink-2">{r.option}</td>}
              <td className="num py-1.5 pr-2 text-right text-ink">{fmtValue(r.value, ds.unit)}</td>
              <td className={cx("num py-1.5 text-right", r.n < 80 ? "text-warning" : "text-muted")}>{r.n.toLocaleString("en-GB")}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {compact && ds.rows.length > rows.length && <p className="mt-1.5 text-[11px] text-muted">+ {ds.rows.length - rows.length} more rows</p>}
    </div>
  );
}

export function EvidencePanel({
  sources,
  datasets,
  active,
  onOpenDoc,
}: {
  sources: PassageSource[];
  datasets: Dataset[];
  active: string | null;
  onOpenDoc: (docId: string, section: string) => void;
}) {
  const refs = useRef<Record<string, HTMLDivElement | null>>({});
  useEffect(() => {
    if (active) refs.current[active]?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [active]);

  if (!sources.length && !datasets.length) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 px-6 text-center text-[13px] text-muted">
        <BarChart3 size={20} />
        Evidence used in an answer appears here — survey datasets and research passages, each with its citation ID.
      </div>
    );
  }
  return (
    <div className="flex flex-col gap-5">
      {datasets.length > 0 && (
        <section>
          <h4 className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-muted">
            <Database size={12} /> Survey datasets
          </h4>
          <div className="flex flex-col gap-2">
            {datasets.map((d) => (
              <div
                key={d.id}
                ref={(el) => {
                  refs.current[d.id] = el;
                }}
                className={cx("rounded-xl border bg-surface p-3 transition-shadow", active === d.id ? "border-accent-ink shadow-card" : "hairline")}
              >
                <div className="mb-2 flex items-start gap-2">
                  <span className="num rounded-md bg-accent px-1.5 py-[1px] text-[10.5px] font-semibold text-[#141414]">{d.id}</span>
                  <div className="min-w-0">
                    <p className="text-[12.5px] font-medium text-ink">{d.description}</p>
                    <p className="text-[11px] text-muted">
                      {Object.values(d.category_names).join(", ")}
                      {d.breakdown ? ` · by ${d.breakdown.replace("_", " ")}` : ""}
                      {Object.keys(d.filters).length ? ` · filters: ${Object.entries(d.filters).map(([k, v]) => `${k}=${Array.isArray(v) ? v.join("/") : v}`).join(", ")}` : ""}
                    </p>
                  </div>
                </div>
                <DatasetTable ds={d} compact />
                {d.notes.map((n) => (
                  <p key={n} className="mt-2 text-[11px] text-warning">
                    {n}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </section>
      )}
      {sources.length > 0 && (
        <section>
          <h4 className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-muted">
            <FileText size={12} /> Research passages
          </h4>
          <div className="flex flex-col gap-2">
            {sources.map((s) => (
              <div
                key={s.id}
                ref={(el) => {
                  refs.current[s.id] = el;
                }}
                className={cx("group rounded-xl border bg-surface p-3 transition-shadow", active === s.id ? "border-accent-ink shadow-card" : "hairline")}
              >
                <div className="mb-1.5 flex items-start gap-2">
                  <span className="num rounded-md border border-line-strong bg-accent-soft px-1.5 py-[1px] text-[10.5px] font-semibold text-accent-ink">{s.id}</span>
                  <div className="min-w-0">
                    <p className="truncate text-[12.5px] font-medium text-ink">{s.title.replace(": Gen Z Category Report 2026", "")}</p>
                    <p className="text-[11px] text-muted">
                      {docTypeLabel(s.doc_type)} · {s.section}
                    </p>
                  </div>
                </div>
                <p className="line-clamp-6 whitespace-pre-line text-[12.5px] leading-relaxed text-ink-2">{s.text.replace(/^\*Also covers:.*?\*\s*/, "").replace(/\*\*/g, "")}</p>
                <button
                  onClick={() => onOpenDoc(s.doc_id, s.section)}
                  className="mt-2 inline-flex items-center gap-0.5 text-[11.5px] font-medium text-accent-ink hover:underline"
                >
                  Open in report <ChevronRight size={13} />
                </button>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
