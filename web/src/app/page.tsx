"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, ArrowUpRight, ChevronLeft, ChevronRight, Search, Sparkles } from "lucide-react";
import { api, type Home } from "@/lib/api";
import { cx, GROUP_COLORS } from "@/lib/format";
import { useLang } from "@/lib/i18n";
import { Photo } from "@/components/photo";
import { CategoryCard, ProductCard } from "@/components/cards";
import { ErrorState, Growth, Skeleton } from "@/components/ui";

const ASK_SAMPLES = {
  en: [
    "Which skincare products do 16-19 year-olds buy?",
    "Why do young drivers choose a used hybrid?",
    "Where do Gen Z discover fragrance?",
  ],
  fr: [
    "Quels soins du visage achètent les 16-19 ans ?",
    "Pourquoi les jeunes conducteurs choisissent-ils une hybride d'occasion ?",
    "Où la Gen Z découvre-t-elle les parfums ?",
  ],
};

function SectionHead({ title, sub, href, cta }: { title: string; sub?: string; href?: string; cta?: string }) {
  return (
    <div className="mb-5 flex items-end justify-between gap-4">
      <div>
        <h2 className="font-serif text-[30px] leading-tight tracking-tight sm:text-[36px]">{title}</h2>
        {sub && <p className="mt-1 text-[13.5px] text-muted">{sub}</p>}
      </div>
      {href && (
        <Link href={href} className="group hidden shrink-0 items-center gap-1 text-[13px] font-medium text-ink-2 hover:text-ink sm:flex">
          {cta} <ArrowRight size={15} className="transition-transform group-hover:translate-x-0.5" />
        </Link>
      )}
    </div>
  );
}

function Rail({ children }: { children: React.ReactNode }) {
  const ref = useRef<HTMLDivElement>(null);
  const scroll = (dir: number) => ref.current?.scrollBy({ left: dir * ref.current.clientWidth * 0.8, behavior: "smooth" });
  return (
    <div className="relative">
      <div ref={ref} className="scroll-thin -mx-5 flex snap-x snap-mandatory gap-4 overflow-x-auto px-5 pb-3 sm:-mx-8 sm:px-8">
        {children}
      </div>
      <div className="pointer-events-none absolute -top-14 right-0 hidden gap-2 sm:flex">
        {[-1, 1].map((d) => (
          <button
            key={d}
            aria-label={d < 0 ? "Previous" : "Next"}
            onClick={() => scroll(d)}
            className="pointer-events-auto flex h-9 w-9 items-center justify-center rounded-full border hairline bg-surface hover:border-line-strong"
          >
            {d < 0 ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
          </button>
        ))}
      </div>
    </div>
  );
}

export default function HomePage() {
  const { t, lang, pick } = useLang();
  const router = useRouter();
  const [data, setData] = useState<Home | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [cats, setCats] = useState<{ slug: string; name: string; name_fr: string; image: string }[]>([]);

  useEffect(() => {
    api.home().then(setData).catch((e) => setError(String(e)));
    api
      .overview()
      .then((o) => setCats(o.categories.map((c) => ({ slug: c.slug, name: c.name, name_fr: c.name_fr, image: c.image }))))
      .catch(() => undefined);
  }, []);

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (q.length < 2) return [];
    return cats.filter((c) => c.name.toLowerCase().includes(q) || c.name_fr.toLowerCase().includes(q)).slice(0, 5);
  }, [query, cats]);

  if (error) return <ErrorState message={error} />;
  const heroCats = data?.hero_categories ?? [];

  return (
    <div className="mx-auto max-w-[1320px] px-5 sm:px-8">
      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className="grid items-center gap-10 pb-16 pt-10 lg:grid-cols-[1.05fr_1fr] lg:pt-16">
        <div>
          <p className="mb-5 inline-flex items-center gap-2 rounded-full border hairline bg-surface px-3 py-1 text-[11.5px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-ink" /> {t("home.eyebrow")}
          </p>
          <h1 className="font-serif text-[48px] leading-[0.98] tracking-tight sm:text-[72px]">
            {t("home.title_a")} <em className="highlight not-italic">{t("home.title_b")}</em> {t("home.title_c")}
          </h1>
          <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-ink-2">{t("home.subtitle")}</p>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (matches[0] && matches[0].name.toLowerCase() === query.trim().toLowerCase()) router.push(`/categories/${matches[0].slug}`);
              else if (query.trim()) router.push(`/ask?q=${encodeURIComponent(query.trim())}`);
            }}
            className="relative mt-8 max-w-xl"
          >
            <label className="card flex items-center gap-3 p-2 pl-4 focus-within:border-line-strong">
              <Search size={18} className="shrink-0 text-muted" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={t("home.search")}
                aria-label={t("home.search")}
                className="min-w-0 flex-1 bg-transparent py-2 text-[15px] outline-none placeholder:text-muted"
              />
              <button className="flex h-10 shrink-0 items-center gap-1.5 rounded-xl bg-ink px-4 text-[13px] font-medium text-bg">
                <Sparkles size={14} /> {t("nav.ask")}
              </button>
            </label>
            {matches.length > 0 && (
              <ul className="card absolute inset-x-0 top-[calc(100%+6px)] z-20 overflow-hidden p-1.5">
                {matches.map((m) => (
                  <li key={m.slug}>
                    <Link href={`/categories/${m.slug}`} className="flex items-center gap-3 rounded-xl p-2 hover:bg-surface-2">
                      <Photo src={m.image} alt="" className="h-10 w-10 shrink-0" rounded="rounded-lg" sizes="40px" />
                      <span className="text-[14px]">{lang === "fr" ? m.name_fr : m.name}</span>
                      <ArrowUpRight size={15} className="ml-auto text-muted" />
                    </Link>
                  </li>
                ))}
                <li className="px-2 pb-1 pt-2 text-[11.5px] text-muted">{t("home.search_hint")}</li>
              </ul>
            )}
          </form>

          <dl className="mt-10 grid max-w-xl grid-cols-4 gap-4">
            {[
              [data?.categories, t("home.stats.categories")],
              [data?.products, t("home.stats.products")],
              [data?.respondents.toLocaleString("en-GB"), t("home.stats.respondents")],
              [data?.documents, t("home.stats.reports")],
            ].map(([v, label]) => (
              <div key={String(label)}>
                <dt className="num text-[24px] font-semibold leading-none">{v ?? "—"}</dt>
                <dd className="mt-1 text-[12px] text-muted">{label}</dd>
              </div>
            ))}
          </dl>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:gap-4">
          {heroCats.length
            ? heroCats.map((c, i) => (
                <Link key={c.slug} href={`/categories/${c.slug}`} className={cx("group relative block", i % 2 === 1 && "translate-y-8")}>
                  <Photo src={c.image} alt={pick(c, "name")} className="aspect-[3/4]" priority sizes="(max-width: 1024px) 45vw, 300px" />
                  <div className="pointer-events-none absolute inset-0 rounded-2xl bg-gradient-to-t from-black/70 via-transparent to-transparent" />
                  <span className="absolute bottom-3 left-3 right-3 text-[14px] font-medium text-white">{pick(c, "name")}</span>
                </Link>
              ))
            : Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className={cx("aspect-[3/4]", i % 2 === 1 && "translate-y-8")} />)}
        </div>
      </section>

      {/* ── Sectors ─────────────────────────────────────────────────────── */}
      <section className="pt-10">
        <SectionHead title={t("home.sectors")} sub={t("home.sectors_sub")} href="/categories" cta={t("home.see_all")} />
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
          {data
            ? data.sectors.map((s, i) => (
                <Link
                  key={s.group}
                  href={`/categories?sector=${s.group}`}
                  className={cx("group relative block overflow-hidden rounded-2xl", i === 0 && "col-span-2 row-span-2 lg:col-span-2")}
                >
                  <Photo src={s.image} alt={pick(s, "name")} className={cx("h-full", i === 0 ? "min-h-[280px]" : "aspect-[4/3]")} sizes="(max-width: 640px) 50vw, 260px" />
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/80 via-black/10 to-transparent" />
                  <div className="absolute inset-x-0 bottom-0 p-4 text-white">
                    <span className="mb-2 block h-1 w-8 rounded-full" style={{ background: GROUP_COLORS[s.group] }} />
                    <h3 className={cx("font-medium tracking-tight", i === 0 ? "text-[24px]" : "text-[15px]")}>{pick(s, "name")}</h3>
                    <p className="text-[12px] text-white/75">
                      {s.categories} {t("home.categories_n")}
                    </p>
                  </div>
                </Link>
              ))
            : Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className={cx("aspect-[4/3]", i === 0 && "col-span-2 row-span-2")} />)}
        </div>
      </section>

      {/* ── Trending products ────────────────────────────────────────────── */}
      <section className="pt-20">
        <SectionHead title={t("home.trending")} sub={t("home.trending_sub")} />
        <Rail>
          {data
            ? data.trending_products.map((p) => <ProductCard key={p.slug} p={p} className="w-[220px] shrink-0 snap-start sm:w-[250px]" />)
            : Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="aspect-[4/5] w-[250px] shrink-0" />)}
        </Rail>
      </section>

      {/* ── Ask band ─────────────────────────────────────────────────────── */}
      <section className="pt-20">
        <div className="relative overflow-hidden rounded-3xl bg-ink px-6 py-10 text-bg sm:px-12 sm:py-14">
          <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-accent opacity-80 blur-3xl" />
          <div className="relative grid gap-8 lg:grid-cols-[1fr_1.1fr] lg:items-center">
            <div>
              <p className="text-[11.5px] font-medium uppercase tracking-[0.16em] opacity-60">Claude · RAG · DuckDB</p>
              <h2 className="mt-3 font-serif text-[38px] leading-[1.02] sm:text-[48px]">{t("home.ask_title")}</h2>
              <p className="mt-3 max-w-md text-[14.5px] leading-relaxed opacity-75">{t("home.ask_sub")}</p>
            </div>
            <div className="flex flex-col gap-2.5">
              {ASK_SAMPLES[lang].map((q) => (
                <Link
                  key={q}
                  href={`/ask?q=${encodeURIComponent(q)}`}
                  className="group flex items-center justify-between gap-4 rounded-2xl border border-white/15 bg-white/5 px-4 py-3.5 text-[14px] transition-colors hover:bg-white/10 dark:border-black/15 dark:bg-black/5"
                >
                  {q}
                  <ArrowRight size={16} className="shrink-0 transition-transform group-hover:translate-x-0.5" />
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── Rising categories ───────────────────────────────────────────── */}
      <section className="pt-20">
        <SectionHead title={t("home.rising")} sub={t("home.rising_sub")} href="/categories" cta={t("home.see_all")} />
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data
            ? data.rising_categories.map((c) => <CategoryCard key={c.slug} c={c} />)
            : Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="aspect-[5/4]" />)}
        </div>
      </section>

      {/* ── Cars spotlight ──────────────────────────────────────────────── */}
      <section className="pt-20">
        <SectionHead title={t("home.cars")} sub={t("home.cars_sub")} href="/categories?sector=mobility" cta={t("home.see_all")} />
        <div className="grid gap-4 md:grid-cols-2">
          {data?.spotlight.slice(0, 2).map((c) => <CategoryCard key={c.slug} c={c} size="lg" />)}
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          {data?.spotlight.slice(2).map((c) => (
            <Link key={c.slug} href={`/categories/${c.slug}`} className="card group flex items-center gap-4 p-3 hover:border-line-strong">
              <Photo src={c.image} alt={pick(c, "name")} className="h-20 w-28 shrink-0" rounded="rounded-xl" sizes="112px" />
              <div className="min-w-0">
                <p className="text-[15px] font-medium">{pick(c, "name")}</p>
                <p className="mt-1 flex items-center gap-2 text-[12.5px] text-muted">
                  <span className="num text-ink">{c.penetration.toFixed(0)}%</span> {t("cats.bought")} <Growth value={c.yoy_growth} />
                </p>
              </div>
              <ArrowUpRight size={18} className="ml-auto text-muted group-hover:text-ink" />
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
