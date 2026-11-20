"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { ArrowUpRight, Search } from "lucide-react";
import { api, type Overview } from "@/lib/api";
import { eur, GROUP_COLORS, METRIC_LABELS, pct } from "@/lib/format";
import { OpportunityMap } from "@/components/charts";
import { Chip, ErrorState, Growth, PageHeader, Panel, Skeleton, Stat } from "@/components/ui";

const SORTS = [
  { key: "penetration", label: "Penetration" },
  { key: "yoy_growth", label: "Growth" },
  { key: "annual_spend_per_capita", label: "Wallet share" },
  { key: "dupe_rate", label: "Dupe rate" },
  { key: "sustainable_premium_rate", label: "Sustainability" },
] as const;

export default function ExplorePage() {
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [group, setGroup] = useState<string>("all");
  const [sort, setSort] = useState<(typeof SORTS)[number]["key"]>("penetration");
  const [query, setQuery] = useState("");
  const router = useRouter();

  useEffect(() => {
    api.overview().then(setData).catch((e) => setError(String(e)));
  }, []);

  const cats = useMemo(() => {
    if (!data) return [];
    const q = query.toLowerCase();
    return data.categories
      .filter((c) => (group === "all" || c.group === group) && (!q || c.name.toLowerCase().includes(q)))
      .sort((a, b) => b[sort] - a[sort]);
  }, [data, group, sort, query]);

  if (error) return <ErrorState message={error} />;

  const fastest = data ? [...data.categories].sort((a, b) => b.yoy_growth - a.yoy_growth)[0] : null;
  const biggest = data ? [...data.categories].sort((a, b) => b.annual_spend_per_capita - a.annual_spend_per_capita)[0] : null;
  const totalWallet = data ? data.categories.reduce((s, c) => s + c.annual_spend_per_capita, 0) : 0;

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow="Category intelligence" title="Explore 50 categories">
        Penetration, spend, growth and values for every category in the Gen Z panel. Click any category for its full profile.
      </PageHeader>

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {data ? (
          <>
            <Stat label="Respondents" value={data.respondents.toLocaleString("en-GB")} hint="Aged 16–29 · 6 markets" />
            <Stat label="Annual spend / Gen Z consumer" value={eur(totalWallet)} hint="Across the 50 categories" />
            <Stat label="Fastest growing" value={<span className="font-sans text-[19px] font-semibold leading-tight tracking-tight">{fastest?.name}</span>} hint={<Growth value={fastest?.yoy_growth ?? 0} />} />
            <Stat label="Largest share of wallet" value={<span className="font-sans text-[19px] font-semibold leading-tight tracking-tight">{biggest?.name}</span>} hint={`${eur(biggest?.annual_spend_per_capita ?? 0)} per consumer / year`} />
          </>
        ) : (
          Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-[98px]" />)
        )}
      </div>

      <Panel
        className="mt-6"
        title="Opportunity map"
        subtitle="Penetration (x) vs spend growth (y); bubble size = annual spend per consumer. Top-right = large and growing."
      >
        {data ? (
          <>
            <OpportunityMap
              data={data.categories.map((c) => ({
                slug: c.slug,
                name: c.name,
                group_name: c.group_name,
                x: c.penetration,
                y: c.yoy_growth,
                z: c.annual_spend_per_capita,
                color: GROUP_COLORS[c.group],
              }))}
              onSelect={(slug) => router.push(`/categories/${slug}`)}
            />
            <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1.5">
              {data.groups.map((g) => (
                <span key={g.group} className="flex items-center gap-1.5 text-[11.5px] text-muted">
                  <span className="h-2 w-2 rounded-full" style={{ background: GROUP_COLORS[g.group] }} /> {g.name}
                </span>
              ))}
            </div>
          </>
        ) : (
          <Skeleton className="h-[380px]" />
        )}
      </Panel>

      <div className="sticky top-14 z-10 -mx-5 mt-8 flex flex-col gap-3 bg-bg/90 px-5 py-3 backdrop-blur sm:-mx-8 sm:px-8 lg:top-0">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="scroll-thin -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
            <Chip active={group === "all"} onClick={() => setGroup("all")}>
              All
            </Chip>
            {data?.groups.map((g) => (
              <Chip key={g.group} active={group === g.group} onClick={() => setGroup(g.group)}>
                {g.name}
              </Chip>
            ))}
          </div>
          <div className="flex items-center gap-2">
            <label className="flex items-center gap-2 rounded-full border hairline bg-surface px-3 py-1.5 text-[13px]">
              <Search size={14} className="text-muted" />
              <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Filter" className="w-28 bg-transparent outline-none placeholder:text-muted" />
            </label>
            <select
              value={sort}
              onChange={(e) => setSort(e.target.value as typeof sort)}
              className="rounded-full border hairline bg-surface px-3 py-1.5 text-[13px] outline-none"
              aria-label="Sort by"
            >
              {SORTS.map((s) => (
                <option key={s.key} value={s.key}>
                  Sort: {s.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {!data && Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className="h-[178px]" />)}
        {cats.map((c, i) => (
          <Link key={c.slug} href={`/categories/${c.slug}`} className="card group flex flex-col p-4 transition-all hover:-translate-y-0.5 hover:border-line-strong">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="flex items-center gap-1.5 text-[11px] text-muted">
                  <span className="h-1.5 w-1.5 rounded-full" style={{ background: GROUP_COLORS[c.group] }} />
                  {c.group_name}
                </p>
                <h3 className="mt-1 text-[15.5px] font-medium tracking-tight">{c.name}</h3>
              </div>
              <span className="num text-[11px] text-muted">#{i + 1}</span>
            </div>
            <div className="mt-4 flex items-end justify-between">
              <div>
                <p className="num text-[30px] font-semibold leading-none">{pct(c.penetration)}</p>
                <p className="mt-1 text-[11.5px] text-muted">bought in the last 12 months</p>
              </div>
              <Growth value={c.yoy_growth} />
            </div>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-surface-2">
              <div className="h-full rounded-full" style={{ width: `${c.penetration}%`, background: GROUP_COLORS[c.group] }} />
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2 border-t hairline pt-3 text-[11.5px]">
              <div>
                <p className="text-muted">Spend / mo</p>
                <p className="num mt-0.5 text-ink">{eur(c.avg_monthly_spend)}</p>
              </div>
              <div>
                <p className="text-muted">{METRIC_LABELS[sort === "penetration" || sort === "yoy_growth" || sort === "annual_spend_per_capita" ? "dupe_rate" : sort]}</p>
                <p className="num mt-0.5 text-ink">{pct(sort === "sustainable_premium_rate" ? c.sustainable_premium_rate : c.dupe_rate)}</p>
              </div>
              <div className="flex items-end justify-end text-muted transition-colors group-hover:text-accent-ink">
                <ArrowUpRight size={16} />
              </div>
            </div>
          </Link>
        ))}
      </div>
      {data && !cats.length && <p className="mt-10 text-center text-[13px] text-muted">No category matches “{query}”.</p>}
    </div>
  );
}
