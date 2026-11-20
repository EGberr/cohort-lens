"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Search, XCircle } from "lucide-react";
import { api, type EvalReport, type SearchHit } from "@/lib/api";
import { cx } from "@/lib/format";
import { BarList } from "@/components/charts";
import { docTypeLabel } from "@/components/doc-reader";
import { PageHeader, Panel, Skeleton } from "@/components/ui";

const MODE_LABEL: Record<string, string> = {
  bm25: "BM25",
  dense: "Dense (bge-small)",
  hybrid: "Hybrid (RRF)",
  hybrid_rerank: "Hybrid + rerank",
};
const MODES = ["bm25", "dense", "hybrid", "hybrid_rerank"];

type LabResults = Record<string, { hits: SearchHit[]; latency_ms: number }>;
const INITIAL_QUERY = "Where do teens find new perfume?";

async function searchAllModes(q: string): Promise<LabResults> {
  const out: LabResults = {};
  await Promise.all(
    MODES.map(async (m) => {
      try {
        const r = await api.search(q, m, 5);
        out[m] = { hits: r.hits, latency_ms: r.latency_ms };
      } catch {
        /* mode unavailable on this server */
      }
    }),
  );
  return out;
}

function RetrievalLab() {
  const [query, setQuery] = useState(INITIAL_QUERY);
  const [results, setResults] = useState<LabResults>({});
  const [loading, setLoading] = useState(true);

  const run = (q: string) => {
    if (!q.trim()) return;
    setLoading(true);
    searchAllModes(q).then((r) => {
      setResults(r);
      setLoading(false);
    });
  };
  useEffect(() => {
    searchAllModes(INITIAL_QUERY).then((r) => {
      setResults(r);
      setLoading(false);
    });
  }, []);

  return (
    <Panel title="Retrieval lab" subtitle="Run one query through every retrieval strategy and compare the top five passages.">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          run(query);
        }}
        className="flex items-center gap-2 rounded-xl border hairline bg-surface-2 px-3 py-2"
      >
        <Search size={15} className="text-muted" />
        <input value={query} onChange={(e) => setQuery(e.target.value)} className="flex-1 bg-transparent text-[14px] outline-none" placeholder="Try a query…" />
        <button className="rounded-lg bg-ink px-3 py-1.5 text-[12.5px] font-medium text-bg">{loading ? "Searching…" : "Search"}</button>
      </form>
      <div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        {MODES.map((m) => (
          <div key={m} className="rounded-xl border hairline p-3">
            <div className="mb-2 flex items-center justify-between">
              <span className="text-[12.5px] font-medium">{MODE_LABEL[m]}</span>
              {results[m] && <span className="num text-[11px] text-muted">{results[m].latency_ms} ms</span>}
            </div>
            {!results[m] ? (
              <div className="flex flex-col gap-2">
                {Array.from({ length: 5 }).map((_, i) => (
                  <Skeleton key={i} className="h-10" />
                ))}
              </div>
            ) : (
              <ol className="flex flex-col gap-1.5">
                {results[m].hits.map((h, i) => (
                  <li key={h.chunk_id} className="rounded-lg bg-surface-2 px-2.5 py-2" title={h.text}>
                    <p className="flex gap-1.5 text-[12px] font-medium leading-snug text-ink">
                      <span className="num text-muted">{i + 1}.</span>
                      <span className="line-clamp-1">{h.title.replace(": Gen Z Category Report 2026", "")}</span>
                    </p>
                    <p className="pl-4 text-[11px] text-muted">
                      {h.section} · {docTypeLabel(h.doc_type)}
                    </p>
                  </li>
                ))}
              </ol>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}

export default function LabPage() {
  const [report, setReport] = useState<EvalReport | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    api.evalReport().then(setReport).catch(() => setMissing(true));
  }, []);

  const modes = report ? Object.entries(report.retrieval.modes) : [];
  const best = modes.length ? modes.reduce((a, b) => (b[1]["mrr@10"] > a[1]["mrr@10"] ? b : a))[0] : null;

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow="Quality" title="Evals & retrieval lab">
        Measured, not claimed. The retrieval benchmark uses {report?.retrieval.n_queries ?? 200} generated queries phrased with aliases and trend names; the answer benchmark checks every number against the panel and requires a dataset citation.
      </PageHeader>

      {missing && (
        <div className="card mb-6 p-5 text-[13px] text-muted">
          No evaluation report yet. Run <code className="num rounded bg-surface-2 px-1">make eval</code> to generate one.
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-[1.4fr_1fr]">
        <Panel title="Retrieval benchmark" subtitle={report ? `${report.retrieval.n_queries} queries · ${report.corpus.chunks} chunks · ${report.generated_at.slice(0, 10)}` : "Loading"}>
          {!report ? (
            <Skeleton className="h-[220px]" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr className="text-left text-[11.5px] text-muted">
                    <th className="pb-2 font-medium">Strategy</th>
                    <th className="whitespace-nowrap pb-2 pl-4 text-right font-medium">Hit@1</th>
                    <th className="whitespace-nowrap pb-2 pl-4 text-right font-medium">Hit@5</th>
                    <th className="whitespace-nowrap pb-2 pl-4 text-right font-medium">MRR@10</th>
                    <th className="whitespace-nowrap pb-2 pl-4 text-right font-medium">Section@5</th>
                    <th className="whitespace-nowrap pb-2 pl-4 text-right font-medium">p50</th>
                  </tr>
                </thead>
                <tbody>
                  {modes.map(([m, v]) => (
                    <tr key={m} className={cx("border-t hairline", m === best && "bg-accent-soft")}>
                      <td className="py-2.5 pr-2 font-medium">
                        {MODE_LABEL[m] ?? m}
                        {m === best && <span className="ml-2 rounded bg-accent px-1.5 py-0.5 text-[10px] font-semibold text-[#141414]">best MRR</span>}
                      </td>
                      <td className="num whitespace-nowrap py-2.5 pl-4 text-right">{(v["hit@1"] * 100).toFixed(1)}%</td>
                      <td className="num whitespace-nowrap py-2.5 pl-4 text-right">{(v["hit@5"] * 100).toFixed(1)}%</td>
                      <td className="num whitespace-nowrap py-2.5 pl-4 text-right">{v["mrr@10"].toFixed(3)}</td>
                      <td className="num whitespace-nowrap py-2.5 pl-4 text-right">{(v["section_hit@5"] * 100).toFixed(1)}%</td>
                      <td className="num whitespace-nowrap py-2.5 pl-4 text-right text-muted">{v.latency_p50_ms} ms</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
                Hit@k: gold document in the top k. Section@5: the exact gold section in the top five. The rerank blend weight was chosen on this same query set (no held-out split), so treat its gain as optimistic.
              </p>
            </div>
          )}
        </Panel>
        <Panel title="MRR@10 by strategy" subtitle="Higher is better">
          {!report ? <Skeleton className="h-[200px]" /> : <BarList unit="" max={1} data={modes.map(([m, v]) => ({ label: MODE_LABEL[m] ?? m, value: v["mrr@10"] })).sort((a, b) => b.value - a.value)} />}
        </Panel>
      </div>

      {report?.answers && (
        <Panel
          className="mt-4"
          title="Answer benchmark"
          subtitle={`${report.answers.n_questions} questions with panel-computed gold numbers · ${report.answers.analyst === "claude" ? report.answers.model : "offline analyst (rule-based baseline)"}`}
        >
          <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
            {[
              ["Numeric accuracy", report.answers.numeric_accuracy],
              ["Cites a dataset", report.answers.dataset_citation_rate],
              ["Any citation", report.answers.citation_rate],
              ["Error rate", report.answers.error_rate],
            ].map(([label, v]) => (
              <div key={label as string} className="rounded-xl bg-surface-2 p-3">
                <p className="text-[11.5px] text-muted">{label}</p>
                <p className="num mt-1 text-[24px] font-semibold">{((v as number) * 100).toFixed(0)}%</p>
              </div>
            ))}
          </div>
          <div className="mt-4 max-h-[360px] overflow-y-auto scroll-thin">
            <table className="w-full text-[12.5px]">
              <tbody>
                {report.answers.items.map((it, i) => (
                  <tr key={i} className="border-t hairline">
                    <td className="py-2 pr-2">{it.correct ? <CheckCircle2 size={15} className="text-positive" /> : <XCircle size={15} className="text-negative" />}</td>
                    <td className="py-2 pr-3 text-ink-2">{it.question}</td>
                    <td className="num whitespace-nowrap py-2 text-right text-ink">
                      gold {it.unit === "EUR" ? "€" : ""}
                      {it.gold}
                      {it.unit === "%" ? "%" : ""}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {report.answers.analyst !== "claude" && (
            <p className="mt-3 text-[11.5px] text-muted">
              This run used the offline rule-based analyst, whose templated questions it is built to answer; it is a pipeline smoke test, not a model score. Set <code className="num">ANTHROPIC_API_KEY</code> and run <code className="num">make eval</code> to benchmark Claude.
            </p>
          )}
        </Panel>
      )}

      <div className="mt-4">
        <RetrievalLab />
      </div>
    </div>
  );
}
