"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useMemo, useState } from "react";
import { LayoutGrid, Map as MapIcon, Search } from "lucide-react";
import { api, type Overview } from "@/lib/api";
import { GROUP_COLORS } from "@/lib/format";
import { useLang, type TKey } from "@/lib/i18n";
import { OpportunityMap } from "@/components/charts";
import { CategoryCard } from "@/components/cards";
import { Chip, ErrorState, PageHeader, Panel, Skeleton } from "@/components/ui";

const SORTS = ["penetration", "yoy_growth", "annual_spend_per_capita", "dupe_rate", "sustainable_premium_rate"] as const;

function Categories() {
  const { t, pick } = useLang();
  const router = useRouter();
  const params = useSearchParams();
  const [data, setData] = useState<Overview | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [group, setGroup] = useState<string>(params.get("sector") ?? "all");
  const [sort, setSort] = useState<(typeof SORTS)[number]>("penetration");
  const [query, setQuery] = useState("");
  const [view, setView] = useState<"grid" | "map">("grid");

  useEffect(() => {
    api.overview().then(setData).catch((e) => setError(String(e)));
  }, []);

  const cats = useMemo(() => {
    if (!data) return [];
    const q = query.toLowerCase();
    return data.categories
      .filter((c) => (group === "all" || c.group === group) && (!q || c.name.toLowerCase().includes(q) || c.name_fr.toLowerCase().includes(q)))
      .sort((a, b) => b[sort] - a[sort]);
  }, [data, group, sort, query]);

  if (error) return <ErrorState message={error} />;

  return (
    <div className="mx-auto max-w-[1320px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow={t("nav.categories")} title={t("cats.title")}>
        {t("cats.subtitle")}
      </PageHeader>

      <div className="sticky top-16 z-10 -mx-5 flex flex-col gap-3 bg-bg/90 px-5 py-3 backdrop-blur sm:-mx-8 sm:px-8 md:flex-row md:items-center md:justify-between">
        <div className="scroll-thin -mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
          <Chip active={group === "all"} onClick={() => setGroup("all")}>
            {t("cats.all")}
          </Chip>
          {data?.groups.map((g) => (
            <Chip key={g.group} active={group === g.group} onClick={() => setGroup(g.group)}>
              <span className="mr-1.5 inline-block h-1.5 w-1.5 -translate-y-px rounded-full" style={{ background: GROUP_COLORS[g.group] }} />
              {pick(g, "name")}
            </Chip>
          ))}
        </div>
        <div className="flex items-center gap-2">
          <label className="flex items-center gap-2 rounded-full border hairline bg-surface px-3 py-1.5 text-[13px]">
            <Search size={14} className="text-muted" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t("cats.filter")} className="w-24 bg-transparent outline-none placeholder:text-muted" />
          </label>
          <select value={sort} onChange={(e) => setSort(e.target.value as typeof sort)} aria-label={t("cats.sort")} className="rounded-full border hairline bg-surface px-3 py-1.5 text-[13px] outline-none">
            {SORTS.map((s) => (
              <option key={s} value={s}>
                {t(`cats.sort.${s}` as TKey)}
              </option>
            ))}
          </select>
          <div className="flex rounded-full border hairline bg-surface p-0.5">
            {(["grid", "map"] as const).map((v) => (
              <button key={v} onClick={() => setView(v)} aria-label={v === "grid" ? t("cats.grid") : t("cats.map")} className={`rounded-full p-1.5 ${view === v ? "bg-ink text-bg" : "text-muted"}`}>
                {v === "grid" ? <LayoutGrid size={14} /> : <MapIcon size={14} />}
              </button>
            ))}
          </div>
        </div>
      </div>

      {view === "map" && data ? (
        <Panel className="mt-4" title={t("cats.map")} subtitle={t("cats.map_sub")}>
          <OpportunityMap
            data={cats.map((c) => ({ slug: c.slug, name: pick(c, "name"), group_name: pick(c, "group_name"), x: c.penetration, y: c.yoy_growth, z: c.annual_spend_per_capita, color: GROUP_COLORS[c.group] }))}
            onSelect={(slug) => router.push(`/categories/${slug}`)}
          />
        </Panel>
      ) : (
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {!data && Array.from({ length: 12 }).map((_, i) => <Skeleton key={i} className="aspect-[5/4]" />)}
          {cats.map((c) => (
            <CategoryCard key={c.slug} c={c} />
          ))}
        </div>
      )}
      {data && !cats.length && (
        <p className="mt-10 text-center text-[13px] text-muted">
          {t("cats.none")} “{query}”.
        </p>
      )}
    </div>
  );
}

export default function CategoriesPage() {
  return (
    <Suspense fallback={<div className="min-h-screen" />}>
      <Categories />
    </Suspense>
  );
}
