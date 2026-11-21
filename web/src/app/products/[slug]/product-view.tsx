"use client";

import Link from "next/link";
import { use, useEffect, useState } from "react";
import { ArrowLeft, FileText, Sparkles } from "lucide-react";
import { api, type ProductDetail } from "@/lib/api";
import { eur, pct, SEGMENT_LABEL } from "@/lib/format";
import { useLabels, useLang } from "@/lib/i18n";
import { BarList } from "@/components/charts";
import { DocReader, docTypeLabel } from "@/components/doc-reader";
import { Photo } from "@/components/photo";
import { ProductCard, TrendBadge, priceLabel } from "@/components/cards";
import { ErrorState, Panel, Skeleton } from "@/components/ui";

const AGE_ORDER = ["16-19", "20-24", "25-29"];

export function ProductView({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const { t, lang, pick } = useLang();
  const L = useLabels();
  const [state, setState] = useState<{ slug: string; data?: ProductDetail; error?: string } | null>(null);
  const [doc, setDoc] = useState<{ id: string; section: string } | null>(null);

  useEffect(() => {
    let live = true;
    api
      .product(slug)
      .then((data) => live && setState({ slug, data }))
      .catch((e) => live && setState({ slug, error: String(e) }));
    return () => {
      live = false;
    };
  }, [slug]);
  const d = state?.slug === slug ? (state.data ?? null) : null;
  if (state?.slug === slug && state.error) return <ErrorState message={state.error} />;
  if (!d)
    return (
      <div className="mx-auto grid max-w-[1320px] gap-10 px-5 py-10 sm:px-8 lg:grid-cols-2">
        <Skeleton className="aspect-[4/5]" />
        <Skeleton className="h-[420px]" />
      </div>
    );

  const p = d.product;
  const name = pick(p, "name");
  const catName = pick(d.category, "name");
  const ask =
    lang === "fr"
      ? `Que disent les études sur le produit « ${name} » (${catName}) : qui l'achète, où et pourquoi ?`
      : `What do the studies say about ${name} in ${catName}: who buys it, where and why?`;

  return (
    <div className="mx-auto max-w-[1320px] px-5 py-8 sm:px-8">
      <Link href={`/categories/${p.category}`} className="inline-flex items-center gap-1.5 text-[12.5px] text-muted hover:text-ink">
        <ArrowLeft size={14} /> {catName}
      </Link>

      <section className="mt-5 grid gap-10 lg:grid-cols-[1fr_1.05fr]">
        <div className="relative">
          <Photo src={p.image} alt={name} className="aspect-[4/5] lg:aspect-[5/6]" rounded="rounded-3xl" priority sizes="(max-width: 1024px) 100vw, 600px" />
          <TrendBadge trend={p.trend} className="absolute left-4 top-4 text-[12px]" />
        </div>

        <div className="flex flex-col">
          <p className="text-[12px] font-medium uppercase tracking-[0.14em] text-muted">{catName}</p>
          <h1 className="mt-2 font-serif text-[46px] leading-[1.02] tracking-tight sm:text-[58px]">{name}</h1>
          <div className="mt-5 flex items-baseline gap-3">
            <span className="num text-[30px] font-semibold">{priceLabel(p, t("prod.month"))}</span>
            <span className="text-[13px] text-muted">{t("prod.price")}</span>
          </div>

          <div className="mt-8 grid grid-cols-2 gap-3">
            {[
              [pct(p.share_of_category), t("prod.share")],
              [pct(p.reach, 1), t("prod.reach")],
              [pct(p.share_16_19), t("prod.young")],
              [pct(p.share_25_29), t("prod.old")],
              [pct(p.share_female), t("prod.female")],
              [L.channel(p.top_channel), t("prod.channel")],
            ].map(([v, label]) => (
              <div key={label} className="rounded-2xl bg-surface-2 p-4">
                <p className="num truncate text-[22px] font-semibold leading-tight">{v}</p>
                <p className="mt-1 text-[12px] text-muted">{label}</p>
              </div>
            ))}
          </div>

          <Link
            href={`/ask?q=${encodeURIComponent(ask)}&category=${p.category}`}
            className="mt-8 inline-flex w-fit items-center gap-2 rounded-xl bg-ink px-5 py-3 text-[14px] font-medium text-bg hover:opacity-90"
          >
            <Sparkles size={15} /> {t("prod.ask")}
          </Link>
        </div>
      </section>

      <div className="mt-12 grid gap-4 md:grid-cols-2">
        <Panel title={t("prod.by_age")}>
          <BarList
            data={[...d.share_by_age]
              .sort((a, b) => AGE_ORDER.indexOf(String(a.segment)) - AGE_ORDER.indexOf(String(b.segment)))
              .map((r) => ({ label: `${r.segment} ${t("cat.years")}`, value: r.value }))}
            highlightFirst={false}
            max={100}
          />
        </Panel>
        <Panel title={t("prod.by_country")}>
          <BarList data={d.share_by_country.map((r) => ({ label: L.segment(SEGMENT_LABEL(r.segment)), value: r.value })).sort((a, b) => b.value - a.value)} color="var(--chart-2)" max={100} />
        </Panel>
      </div>

      <section className="mt-12">
        <h2 className="mb-4 font-serif text-[30px] tracking-tight">{t("prod.evidence")}</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {d.passages.map((h) => (
            <button key={h.chunk_id} onClick={() => setDoc({ id: h.doc_id, section: h.section })} className="card flex flex-col gap-2 p-4 text-left hover:border-line-strong">
              <span className="flex items-center gap-2 text-[12px] text-muted">
                <FileText size={14} className="text-accent-ink" />
                {docTypeLabel(h.doc_type)} · {h.section}
              </span>
              <span className="line-clamp-4 whitespace-pre-line text-[13.5px] leading-relaxed text-ink-2">
                {h.text.replace(/^\*Also covers:.*?\*\s*/, "").replace(/\*\*/g, "")}
              </span>
            </button>
          ))}
        </div>
      </section>

      <section className="mt-12">
        <h2 className="mb-4 font-serif text-[30px] tracking-tight">
          {t("prod.siblings")} {catName}
        </h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {d.siblings.map((s) => (
            <ProductCard key={s.slug} p={s} showCategory={false} />
          ))}
          <Link href={`/categories/${p.category}`} className="group flex aspect-[4/5] flex-col justify-end rounded-2xl bg-surface-2 p-5 hover:bg-surface-3">
            <span className="text-[12px] text-muted">{eur(d.category.avg_monthly_spend)} · {pct(d.category.penetration)}</span>
            <span className="mt-1 text-[16px] font-medium">{catName} →</span>
          </Link>
        </div>
      </section>
      <DocReader docId={doc?.id ?? null} section={doc?.section} onClose={() => setDoc(null)} />
    </div>
  );
}
