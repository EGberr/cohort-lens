"use client";

import { useEffect, useMemo, useState } from "react";
import { Plus, X } from "lucide-react";
import { api, type CategoryKpi, type Overview } from "@/lib/api";
import { CHART_COLORS, eur, pct, signed } from "@/lib/format";
import { CompareRadar } from "@/components/charts";
import { ErrorState, PageHeader, Panel, Skeleton } from "@/components/ui";
import { useLang } from "@/lib/i18n";

const RADAR = [
  { key: "penetration", label: "Penetration" },
  { key: "price_decisive_rate", label: "Price decisive" },
  { key: "brand_loyalty_rate", label: "Brand loyal" },
  { key: "sustainable_premium_rate", label: "Sustainable premium" },
  { key: "dupe_rate", label: "Bought a dupe" },
] as const;

const ROWS: { key: keyof CategoryKpi; label: string; fmt: (v: number) => string }[] = [
  { key: "penetration", label: "Penetration", fmt: (v) => pct(v) },
  { key: "avg_monthly_spend", label: "Avg monthly spend", fmt: (v) => eur(v) },
  { key: "annual_spend_per_capita", label: "Annual spend / consumer", fmt: (v) => eur(v) },
  { key: "yoy_growth", label: "Spend growth vs 2025", fmt: (v) => signed(v) },
  { key: "price_decisive_rate", label: "Price decisive", fmt: (v) => pct(v) },
  { key: "brand_loyalty_rate", label: "Brand loyal", fmt: (v) => pct(v) },
  { key: "sustainable_premium_rate", label: "Pays sustainable premium", fmt: (v) => pct(v) },
  { key: "dupe_rate", label: "Bought a dupe", fmt: (v) => pct(v) },
];

export default function ComparePage() {
  const { lang, pick } = useLang();
  const fr = lang === "fr";
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [picked, setPicked] = useState<string[]>(["sneakers", "athleisure", "secondhand-fashion"]);

  useEffect(() => {
    api.overview().then(setData).catch((e) => setError(String(e)));
  }, []);

  const selected = useMemo(() => (data ? picked.map((s) => data.categories.find((c) => c.slug === s)!).filter(Boolean) : []), [data, picked]);
  if (error) return <ErrorState message={error} />;

  const radarData = RADAR.map((m) => {
    const row: Record<string, string | number> = { metric: m.label };
    selected.forEach((c) => (row[c.slug] = c[m.key]));
    return row;
  });

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow={fr ? "Côte à côte" : "Side by side"} title={fr ? "Comparer des catégories" : "Compare categories"}>
        {fr
          ? "Choisissez jusqu'à quatre catégories pour comparer portée, dépenses, croissance et valeurs d'achat de la Gen Z."
          : "Pick up to four categories to compare reach, spend, growth and the values that shape Gen Z purchase decisions."}
      </PageHeader>

      <div className="flex flex-wrap items-center gap-2">
        {selected.map((c, i) => (
          <span key={c.slug} className="flex items-center gap-2 rounded-full border hairline bg-surface py-1.5 pl-3 pr-1.5 text-[13px]">
            <span className="h-2.5 w-2.5 rounded-full" style={{ background: CHART_COLORS[i] }} />
            {pick(c, "name")}
            <button aria-label={`Remove ${c.name}`} onClick={() => setPicked((p) => p.filter((s) => s !== c.slug))} className="rounded-full p-0.5 text-muted hover:bg-surface-2 hover:text-ink">
              <X size={13} />
            </button>
          </span>
        ))}
        {data && picked.length < 4 && (
          <label className="flex items-center gap-1.5 rounded-full border border-dashed border-line-strong px-3 py-1.5 text-[13px] text-muted">
            <Plus size={14} />
            <select
              value=""
              onChange={(e) => e.target.value && setPicked((p) => [...p, e.target.value])}
              className="bg-transparent outline-none"
              aria-label="Add category"
            >
              <option value="">{fr ? "Ajouter une catégorie" : "Add category"}</option>
              {data.groups.map((g) => (
                <optgroup key={g.group} label={g.name}>
                  {data.categories
                    .filter((c) => c.group === g.group && !picked.includes(c.slug))
                    .map((c) => (
                      <option key={c.slug} value={c.slug}>
                        {pick(c, "name")}
                      </option>
                    ))}
                </optgroup>
              ))}
            </select>
          </label>
        )}
      </div>

      {!data ? (
        <Skeleton className="mt-6 h-[420px]" />
      ) : selected.length === 0 ? (
        <p className="mt-16 text-center text-[13px] text-muted">Add a category to start comparing.</p>
      ) : (
        <div className="mt-6 grid gap-4 lg:grid-cols-[1.1fr_1fr]">
          <Panel title={fr ? "Profil de valeurs" : "Value profile"} subtitle={fr ? "Part de tous les répondants (pénétration) ou des acheteurs (autres axes)" : "Share of all respondents (penetration) or of buyers (other axes)"}>
            <CompareRadar data={radarData} series={selected.map((c) => ({ key: c.slug, name: pick(c, "name") }))} />
          </Panel>
          <Panel title={fr ? "Tableau comparatif" : "Scorecard"} subtitle={fr ? "La meilleure valeur de chaque ligne est surlignée" : "Best value per row is highlighted"}>
            <div className="overflow-x-auto">
              <table className="w-full text-[13px]">
                <thead>
                  <tr>
                    <th className="pb-2 text-left font-normal text-muted" />
                    {selected.map((c, i) => (
                      <th key={c.slug} className="pb-2 text-right font-medium">
                        <span className="inline-flex items-start justify-end gap-1.5 pl-3">
                          <span className="mt-[7px] h-2 w-2 shrink-0 rounded-full" style={{ background: CHART_COLORS[i] }} />
                          <span>{pick(c, "name")}</span>
                        </span>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ROWS.map((r) => {
                    const vals = selected.map((c) => Number(c[r.key]));
                    const best = Math.max(...vals);
                    return (
                      <tr key={r.key} className="border-t hairline">
                        <td className="py-2.5 pr-3 text-ink-2">{r.label}</td>
                        {selected.map((c, i) => (
                          <td key={c.slug} className="num py-2.5 text-right">
                            <span className={vals[i] === best && selected.length > 1 ? "rounded-md bg-accent px-1.5 py-0.5 font-medium text-[#141414]" : "text-ink"}>{r.fmt(vals[i])}</span>
                          </td>
                        ))}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </Panel>
        </div>
      )}
    </div>
  );
}
