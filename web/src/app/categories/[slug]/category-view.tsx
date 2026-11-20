"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { ArrowLeft, FileText, MessageSquareText, Sparkles } from "lucide-react";
import { api, type CategoryDetail, type Row } from "@/lib/api";
import { eur, GROUP_COLORS, pct, SEGMENT_LABEL, signed } from "@/lib/format";
import { BarList, Donut, GroupedColumns } from "@/components/charts";
import { DocReader, docTypeLabel } from "@/components/doc-reader";
import { ErrorState, Growth, Panel, Skeleton, Stat } from "@/components/ui";

const toBars = (rows: Row[]) => rows.map((r) => ({ label: r.option ?? SEGMENT_LABEL(r.segment), value: r.value }));
const toCols = (rows: Row[]) => rows.map((r) => ({ label: SEGMENT_LABEL(r.segment), value: r.value }));
const AGE_ORDER = ["16-19", "20-24", "25-29"];
const SHORT: Record<string, string> = { tiktok: "TikTok", instagram: "Insta", youtube: "YouTube", friends: "Friends", search: "Search", in_store: "In store" };

export function CategoryView({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const [state, setState] = useState<{ slug: string; data?: CategoryDetail; error?: string } | null>(null);
  const [doc, setDoc] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    api
      .category(slug)
      .then((data) => live && setState({ slug, data }))
      .catch((e) => live && setState({ slug, error: String(e) }));
    return () => {
      live = false;
    };
  }, [slug]);
  const d = state?.slug === slug ? (state.data ?? null) : null;
  const error = state?.slug === slug ? state.error : undefined;

  if (error) return <ErrorState message={error} />;
  if (!d)
    return (
      <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
        <Skeleton className="h-12 w-2/3" />
        <div className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Skeleton key={i} className="h-[98px]" />
          ))}
        </div>
        <div className="mt-6 grid gap-4 lg:grid-cols-2">
          <Skeleton className="h-[300px]" />
          <Skeleton className="h-[300px]" />
        </div>
      </div>
    );

  const k = d.kpi;
  const color = GROUP_COLORS[k.group];
  const ages = [...d.penetration_by.age_band].sort((a, b) => AGE_ORDER.indexOf(String(a.segment)) - AGE_ORDER.indexOf(String(b.segment)));
  const discAge = d.discovery_by_age.filter((r) => r.segment === "16-19" || r.segment === "25-29");
  const topDisc = d.discovery_mix.slice(0, 5).map((r) => r.option_key);
  const discAgeData = discAge
    .filter((r) => topDisc.includes(r.option_key))
    .map((r) => ({ label: SHORT[r.option_key ?? ""] ?? r.option ?? "", value: r.value, series: `${r.segment} yrs` }));
  const ask = encodeURIComponent(`What should a brand know about Gen Z and ${k.name.toLowerCase()}? Cover who buys, the path to purchase and what to do.`);

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
      <Link href="/explore" className="inline-flex items-center gap-1.5 text-[12.5px] text-muted hover:text-ink">
        <ArrowLeft size={14} /> All categories
      </Link>

      <header className="mt-5 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="max-w-2xl">
          <p className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.16em] text-muted">
            <span className="h-2 w-2 rounded-full" style={{ background: color }} />
            {k.group_name}
          </p>
          <h1 className="mt-2 font-serif text-[44px] leading-[1.02] tracking-tight sm:text-[56px]">{k.name}</h1>
          <p className="mt-2 text-[12.5px] text-muted">Also covers: {d.aliases.join(" · ")}</p>
        </div>
        <Link href={`/?q=${ask}`} className="inline-flex w-fit items-center gap-2 rounded-xl bg-ink px-4 py-2.5 text-[13px] font-medium text-bg hover:opacity-90">
          <MessageSquareText size={15} /> Ask the analyst
        </Link>
      </header>

      <div className="mt-8 grid grid-cols-2 gap-3 lg:grid-cols-5">
        <Stat label="Penetration" value={pct(k.penetration)} hint="bought in last 12 months" />
        <Stat label="Avg monthly spend" value={eur(k.avg_monthly_spend)} hint="among buyers" />
        <Stat label="Annual spend / consumer" value={eur(k.annual_spend_per_capita)} hint="all Gen Z respondents" />
        <Stat label="Spend growth" value={signed(k.yoy_growth)} tone={k.yoy_growth >= 0 ? "positive" : "negative"} hint="vs 2025 wave" />
        <Stat label="Buyers in panel" value={k.buyers.toLocaleString("en-GB")} hint="base for mixes" />
      </div>

      <section className="card relative mt-4 overflow-hidden p-6">
        <div className="absolute inset-y-0 left-0 w-1" style={{ background: color }} />
        <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-accent-ink">
          <Sparkles size={12} /> Key insight
        </p>
        <p className="mt-2 font-serif text-[22px] leading-snug text-ink sm:text-[26px]">{d.insight}</p>
        <p className="mt-4 text-[14px] leading-relaxed text-ink-2">
          <span className="font-medium text-ink">So what: </span>
          {d.recommendation}
        </p>
      </section>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Panel title="Main purchase channel" subtitle="Share of buyers">
          <Donut data={toBars(d.channel_mix)} />
        </Panel>
        <Panel title="Where they discover it" subtitle="First discovery source, share of buyers">
          <BarList data={toBars(d.discovery_mix)} color={color} />
        </Panel>
        <Panel title="Why they buy" subtitle="Top purchase driver, share of buyers">
          <BarList data={toBars(d.driver_mix).slice(0, 6)} color="var(--chart-2)" />
          <p className="mt-4 text-[12px] text-muted">
            Barriers mentioned: <span className="text-ink-2">{d.barriers.join(" · ")}</span>
          </p>
        </Panel>
        <Panel title="Discovery: younger vs older Gen Z" subtitle="16–19 vs 25–29 year-olds, top five sources">
          <GroupedColumns data={discAgeData} height={240} />
        </Panel>
      </div>

      <h2 className="mb-3 mt-10 text-[11px] font-medium uppercase tracking-[0.16em] text-muted">Who buys · penetration by segment</h2>
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Panel title="Gender" subtitle="Share who bought">
          <BarList data={toCols(d.penetration_by.gender)} color={color} max={100} highlightFirst={false} />
        </Panel>
        <Panel title="Age band" subtitle="Share who bought">
          <BarList data={toCols(ages).map((r) => ({ ...r, label: `${r.label} years` }))} color={color} max={100} highlightFirst={false} />
        </Panel>
        <Panel title="Income" subtitle="Share who bought">
          <BarList
            data={toCols(["low", "mid", "high"].map((s) => d.penetration_by.income_band.find((r) => r.segment === s)!).filter(Boolean)).map((r) => ({ ...r, label: `${r.label} income` }))}
            color={color}
            max={100}
            highlightFirst={false}
          />
        </Panel>
        <Panel title="Values" subtitle="Share of buyers">
          <BarList
            highlightFirst={false}
            max={100}
            color="var(--chart-3)"
            data={[
              { label: "Price decisive", value: k.price_decisive_rate },
              { label: "Brand loyal", value: k.brand_loyalty_rate },
              { label: "Pays sustainable premium", value: k.sustainable_premium_rate },
              { label: "Bought a dupe", value: k.dupe_rate },
            ]}
          />
        </Panel>
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        <Panel title="By market" subtitle="Penetration and average monthly spend" className="lg:col-span-2">
          <div className="grid gap-6 sm:grid-cols-2">
            <BarList data={[...toCols(d.penetration_by.country)].sort((a, b) => b.value - a.value)} color={color} />
            <BarList data={[...toCols(d.spend_by_country)].sort((a, b) => b.value - a.value)} unit="EUR" color="var(--chart-6)" />
          </div>
        </Panel>
        <Panel title="Trends to watch">
          <ul className="flex flex-col gap-2">
            {d.trends.map((t) => (
              <li key={t} className="flex items-center gap-2.5 rounded-xl bg-surface-2 px-3 py-2.5 text-[13px] capitalize text-ink">
                <span className="h-1.5 w-1.5 rounded-full bg-accent-ink" /> {t}
              </li>
            ))}
          </ul>
        </Panel>
      </div>

      <Panel title="Research on this category" subtitle="Category report, sector overview and cross-category themes" className="mt-4">
        <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          {d.documents.map((doc) => (
            <button key={doc.doc_id} onClick={() => setDoc(doc.doc_id)} className="flex items-start gap-3 rounded-xl border hairline p-3 text-left hover:border-line-strong hover:bg-surface-2">
              <FileText size={16} className="mt-0.5 shrink-0 text-accent-ink" />
              <span>
                <span className="block text-[13px] font-medium leading-snug text-ink">{doc.title}</span>
                <span className="text-[11.5px] text-muted">{docTypeLabel(doc.type)}</span>
              </span>
            </button>
          ))}
        </div>
      </Panel>
      <p className="mt-6 text-[11.5px] text-muted">
        Synthetic demo data. <Growth value={k.yoy_growth} /> growth vs 2025 wave.
      </p>
      <DocReader docId={doc} onClose={() => setDoc(null)} />
    </div>
  );
}
