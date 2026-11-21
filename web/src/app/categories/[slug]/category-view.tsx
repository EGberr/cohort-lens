"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { ArrowLeft, FileText, MessageSquareText, Sparkles, X } from "lucide-react";
import { api, type CategoryDetail, type Row } from "@/lib/api";
import { cx, eur, GROUP_COLORS, pct, SEGMENT_LABEL, signed } from "@/lib/format";
import { useLabels, useLang, type TKey } from "@/lib/i18n";
import { BarList, Donut, GroupedColumns } from "@/components/charts";
import { DocReader, docTypeLabel } from "@/components/doc-reader";
import { Photo } from "@/components/photo";
import { CategoryCard, ProductCard } from "@/components/cards";
import { ChatView } from "@/components/chat/chat-view";
import { ErrorState, Panel, Skeleton, Stat } from "@/components/ui";

const AGE_ORDER = ["16-19", "20-24", "25-29"];
const SHORT: Record<string, string> = { tiktok: "TikTok", instagram: "Insta", youtube: "YouTube", friends: "Friends", search: "Search", in_store: "Store" };
const TABS = ["overview", "audience", "studies"] as const;

function suggestionsFor(name: string, lang: "en" | "fr") {
  return lang === "fr"
    ? [
        `Quels produits les 16-19 ans achètent-ils (${name.toLowerCase()}) ?`,
        `Où la Gen Z découvre-t-elle cette catégorie, et sur quel canal achète-t-elle ?`,
        `Quelles différences entre la France et l'Allemagne ?`,
        `Que doit faire une marque pour gagner cette catégorie ?`,
      ]
    : [
        `Which products do 16-19 year-olds buy in ${name.toLowerCase()}?`,
        "Where do Gen Z discover this category, and where do they buy?",
        "How does France compare with Germany?",
        "What should a brand do to win this category?",
      ];
}

export function CategoryView({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { t, lang, pick } = useLang();
  const L = useLabels();
  const [state, setState] = useState<{ slug: string; data?: CategoryDetail; error?: string } | null>(null);
  const [doc, setDoc] = useState<string | null>(null);
  const [tab, setTab] = useState<(typeof TABS)[number]>("overview");
  const [mobileChat, setMobileChat] = useState(false);

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
      <div className="mx-auto max-w-[1320px] px-5 py-8 sm:px-8">
        <Skeleton className="h-[340px] rounded-3xl" />
        <div className="mt-6 grid grid-cols-2 gap-3 lg:grid-cols-5">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-[98px]" />
          ))}
        </div>
      </div>
    );

  const k = d.kpi;
  const name = pick(k, "name");
  const color = GROUP_COLORS[k.group];
  const bars = (rows: Row[]) => rows.map((r) => ({ label: L.option(r.option_key, r.option ?? ""), value: r.value }));
  const segs = (rows: Row[]) => rows.map((r) => ({ label: L.segment(SEGMENT_LABEL(r.segment)), value: r.value }));
  const ages = [...d.penetration_by.age_band].sort((a, b) => AGE_ORDER.indexOf(String(a.segment)) - AGE_ORDER.indexOf(String(b.segment)));
  const topDisc = d.discovery_mix.slice(0, 5).map((r) => r.option_key);
  const discAge = d.discovery_by_age
    .filter((r) => (r.segment === "16-19" || r.segment === "25-29") && topDisc.includes(r.option_key))
    .map((r) => ({ label: SHORT[r.option_key ?? ""] ?? r.option ?? "", value: r.value, series: `${r.segment} ${t("cat.years")}` }));
  const products = [...d.products].sort((a, b) => b.share_of_category - a.share_of_category);

  const chat = (
    <ChatView
      key={`${slug}-${lang}`}
      variant="panel"
      category={slug}
      categoryName={name}
      suggestions={suggestionsFor(name, lang)}
      emptyState={
        <div>
          <p className="flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-accent-ink">
            <Sparkles size={12} /> {t("chat.title")}
          </p>
          <p className="mt-2 text-[13.5px] leading-relaxed text-ink-2">
            {t("chat.scope")} <span className="font-medium text-ink">{name}</span> · {t("chat.grounded")}.
          </p>
        </div>
      }
    />
  );

  return (
    <div className="mx-auto max-w-[1320px] px-5 py-6 sm:px-8">
      {/* Hero */}
      <section className="relative overflow-hidden rounded-3xl">
        <Photo src={k.image} alt={name} className="h-[440px] sm:h-[400px]" rounded="rounded-3xl" priority sizes="100vw" />
        <div className="pointer-events-none absolute inset-0 rounded-3xl bg-gradient-to-t from-black/85 via-black/35 to-black/10" />
        <div className="absolute inset-x-0 top-0 p-5 sm:p-7">
          <Link href="/categories" className="inline-flex items-center gap-1.5 rounded-full bg-black/35 px-3 py-1.5 text-[12.5px] text-white/90 backdrop-blur hover:bg-black/50">
            <ArrowLeft size={14} /> {t("cat.back")}
          </Link>
        </div>
        <div className="absolute inset-x-0 bottom-0 flex flex-col gap-4 p-5 text-white sm:p-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-2xl">
            <p className="flex items-center gap-2 text-[11px] font-medium uppercase tracking-[0.16em] text-white/75">
              <span className="h-2 w-2 rounded-full" style={{ background: color }} />
              {pick(k, "group_name")}
            </p>
            <h1 className="mt-2 font-serif text-[40px] leading-[1] tracking-tight sm:text-[64px]">{name}</h1>
            <p className="mt-3 line-clamp-3 max-w-xl text-[14px] leading-relaxed text-white/85 sm:line-clamp-none">{d.insight}</p>
          </div>
          <button onClick={() => setMobileChat(true)} className="inline-flex w-fit items-center gap-2 rounded-xl bg-accent px-4 py-2.5 text-[13px] font-semibold text-[#141414] lg:hidden">
            <MessageSquareText size={15} /> {t("cat.ask")}
          </button>
        </div>
      </section>

      <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-5">
        <Stat label={t("cat.penetration")} value={pct(k.penetration)} hint={t("cat.penetration_hint")} />
        <Stat label={t("cat.spend")} value={eur(k.avg_monthly_spend)} hint={t("cat.spend_hint")} />
        <Stat label={t("cat.wallet")} value={eur(k.annual_spend_per_capita)} hint={t("cat.wallet_hint")} />
        <Stat label={t("cat.growth")} value={signed(k.yoy_growth)} tone={k.yoy_growth >= 0 ? "positive" : "negative"} hint={t("cat.growth_hint")} />
        <Stat label={t("cat.buyers")} value={k.buyers.toLocaleString("en-GB")} hint={t("cat.buyers_hint")} />
      </div>

      <div className="mt-10 grid gap-8 lg:grid-cols-[minmax(0,1fr)_400px]">
        <div className="min-w-0">
          {/* Products */}
          <h2 className="font-serif text-[32px] leading-tight tracking-tight">{t("cat.products")}</h2>
          <p className="mb-5 mt-1 text-[13px] text-muted">{t("cat.products_sub")}</p>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
            {products.map((p) => (
              <ProductCard key={p.slug} p={p} showCategory={false} />
            ))}
          </div>

          {/* Tabs */}
          <div className="mt-12 flex gap-1 border-b hairline">
            {TABS.map((x) => (
              <button
                key={x}
                onClick={() => setTab(x)}
                className={cx("-mb-px border-b-2 px-4 py-2.5 text-[13.5px] transition-colors", tab === x ? "border-ink font-medium text-ink" : "border-transparent text-muted hover:text-ink")}
              >
                {t(`cat.tab.${x}` as TKey)}
              </button>
            ))}
          </div>

          {tab === "overview" && (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <Panel title={t("cat.channel")} subtitle={t("cat.channel_sub")}>
                <Donut data={bars(d.channel_mix)} height={180} />
              </Panel>
              <Panel title={t("cat.discovery")} subtitle={t("cat.discovery_sub")}>
                <BarList data={bars(d.discovery_mix)} color={color} />
              </Panel>
              <Panel title={t("cat.drivers")} subtitle={t("cat.drivers_sub")}>
                <BarList data={bars(d.driver_mix).slice(0, 5)} color="var(--chart-2)" />
                <p className="mt-4 text-[12px] text-muted">
                  {t("cat.barriers")}: <span className="text-ink-2">{d.barriers.join(" · ")}</span>
                </p>
              </Panel>
              <Panel title={t("cat.disc_age")} subtitle={t("cat.disc_age_sub")}>
                <GroupedColumns data={discAge} height={230} />
              </Panel>
              <section className="card relative overflow-hidden p-5 md:col-span-2">
                <div className="absolute inset-y-0 left-0 w-1" style={{ background: color }} />
                <p className="text-[11px] font-medium uppercase tracking-[0.14em] text-accent-ink">{t("cat.so_what")}</p>
                <p className="mt-2 font-serif text-[22px] leading-snug">{d.recommendation}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  {d.trends.map((tr) => (
                    <span key={tr} className="rounded-full bg-surface-2 px-3 py-1 text-[12.5px] capitalize text-ink-2">
                      {tr}
                    </span>
                  ))}
                </div>
              </section>
            </div>
          )}

          {tab === "audience" && (
            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <Panel title={t("cat.gender")} subtitle={t("cat.share_bought")}>
                <BarList data={segs(d.penetration_by.gender)} color={color} max={100} highlightFirst={false} />
              </Panel>
              <Panel title={t("cat.age")} subtitle={t("cat.share_bought")}>
                <BarList data={segs(ages).map((r) => ({ ...r, label: `${r.label} ${t("cat.years")}` }))} color={color} max={100} highlightFirst={false} />
              </Panel>
              <Panel title={t("cat.income")} subtitle={t("cat.share_bought")}>
                <BarList
                  data={segs(["low", "mid", "high"].map((s) => d.penetration_by.income_band.find((r) => r.segment === s)!).filter(Boolean)).map((r) => ({ ...r, label: `${r.label} ${t("cat.income_suffix")}` }))}
                  color={color}
                  max={100}
                  highlightFirst={false}
                />
              </Panel>
              <Panel title={t("cat.values")} subtitle={t("cat.values_sub")}>
                <BarList
                  highlightFirst={false}
                  max={100}
                  color="var(--chart-3)"
                  data={[
                    { label: t("values.price"), value: k.price_decisive_rate },
                    { label: t("values.loyal"), value: k.brand_loyalty_rate },
                    { label: t("values.sustainable"), value: k.sustainable_premium_rate },
                    { label: t("values.dupe"), value: k.dupe_rate },
                  ]}
                />
              </Panel>
              <Panel title={t("cat.markets")} subtitle={t("cat.markets_sub")} className="md:col-span-2">
                <div className="grid gap-6 sm:grid-cols-2">
                  <BarList data={segs(d.penetration_by.country).sort((a, b) => b.value - a.value)} color={color} />
                  <BarList data={segs(d.spend_by_country).sort((a, b) => b.value - a.value)} unit="EUR" color="var(--chart-6)" />
                </div>
              </Panel>
            </div>
          )}

          {tab === "studies" && (
            <div className="mt-5 grid gap-2 sm:grid-cols-2">
              {d.documents.map((doc) => (
                <button key={doc.doc_id} onClick={() => setDoc(doc.doc_id)} className="card flex items-start gap-3 p-4 text-left hover:border-line-strong">
                  <FileText size={17} className="mt-0.5 shrink-0 text-accent-ink" />
                  <span>
                    <span className="block text-[13.5px] font-medium leading-snug">{doc.title}</span>
                    <span className="text-[11.5px] text-muted">{docTypeLabel(doc.type)}</span>
                  </span>
                </button>
              ))}
            </div>
          )}

          {d.related.length > 0 && (
            <section className="mt-14">
              <h2 className="mb-4 font-serif text-[28px] tracking-tight">{t("cat.related")}</h2>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {d.related.slice(0, 6).map((c) => (
                  <CategoryCard key={c.slug} c={c} />
                ))}
              </div>
            </section>
          )}
        </div>

        {/* Ask the studies (desktop) */}
        <aside className="hidden lg:block">
          <div className="card sticky top-20 h-[calc(100vh-6.5rem)] overflow-hidden">{chat}</div>
        </aside>
      </div>

      {mobileChat && (
        <div className="fixed inset-0 z-50 flex flex-col bg-bg lg:hidden" role="dialog" aria-modal="true">
          <div className="flex h-14 shrink-0 items-center justify-between border-b hairline px-4">
            <span className="text-[14px] font-medium">
              {t("cat.ask")} · {name}
            </span>
            <button onClick={() => setMobileChat(false)} aria-label={t("chat.close")} className="rounded-lg p-2 hover:bg-surface-2">
              <X size={18} />
            </button>
          </div>
          <div className="min-h-0 flex-1">{chat}</div>
        </div>
      )}
      <DocReader docId={doc} onClose={() => setDoc(null)} />
    </div>
  );
}
