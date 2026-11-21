"use client";

import Link from "next/link";
import { ArrowUpRight, TrendingDown, TrendingUp, Minus } from "lucide-react";
import type { CategoryKpi, Product } from "@/lib/api";
import { cx, eur, GROUP_COLORS, pct } from "@/lib/format";
import { useLang } from "@/lib/i18n";
import { Photo } from "@/components/photo";
import { Growth } from "@/components/ui";

export function TrendBadge({ trend, className }: { trend: Product["trend"]; className?: string }) {
  const { t } = useLang();
  const Icon = trend === "rising" ? TrendingUp : trend === "cooling" ? TrendingDown : Minus;
  return (
    <span
      className={cx(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium backdrop-blur",
        trend === "rising" && "bg-accent text-[#141414]",
        trend === "steady" && "bg-surface/85 text-ink",
        trend === "cooling" && "bg-surface/85 text-negative",
        className,
      )}
    >
      <Icon size={11} /> {t(`trend.${trend}`)}
    </span>
  );
}

export function priceLabel(p: Product, monthWord: string) {
  return `${eur(p.price)}${p.per_month ? monthWord : ""}`;
}

export function ProductCard({ p, showCategory = true, className }: { p: Product; showCategory?: boolean; className?: string }) {
  const { t, pick } = useLang();
  return (
    <Link href={`/products/${p.slug}`} className={cx("group flex flex-col", className)}>
      <div className="relative">
        <Photo src={p.image} alt={pick(p, "name")} className="aspect-[4/5]" sizes="(max-width: 640px) 70vw, 280px" />
        <TrendBadge trend={p.trend} className="absolute left-3 top-3" />
      </div>
      <div className="mt-3 flex items-start justify-between gap-3 px-0.5">
        <div className="min-w-0">
          {showCategory && <p className="truncate text-[11.5px] text-muted">{pick(p, "category_name")}</p>}
          <h3 className="truncate text-[14.5px] font-medium tracking-tight">{pick(p, "name")}</h3>
        </div>
        <span className="num shrink-0 text-[13px] text-ink-2">{priceLabel(p, t("prod.month"))}</span>
      </div>
      <p className="mt-1 px-0.5 text-[12px] text-muted">
        <span className="num text-ink">{pct(p.share_of_category)}</span> {t("prod.share")}
      </p>
    </Link>
  );
}

export function CategoryCard({ c, size = "md" }: { c: CategoryKpi; size?: "md" | "lg" }) {
  const { t, pick } = useLang();
  return (
    <Link href={`/categories/${c.slug}`} className="group relative block overflow-hidden rounded-2xl">
      <Photo src={c.image} alt={pick(c, "name")} className={size === "lg" ? "aspect-[4/3]" : "aspect-[5/4]"} sizes="(max-width: 640px) 90vw, 400px" />
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 flex items-end justify-between gap-3 p-4 text-white">
        <div className="min-w-0">
          <p className="flex items-center gap-1.5 text-[11px] text-white/75">
            <span className="h-1.5 w-1.5 rounded-full" style={{ background: GROUP_COLORS[c.group] }} />
            {pick(c, "group_name")}
          </p>
          <h3 className={cx("mt-0.5 font-medium tracking-tight", size === "lg" ? "text-[20px]" : "text-[16px]")}>{pick(c, "name")}</h3>
          <p className="mt-1 text-[12px] text-white/80">
            <span className="num font-medium text-white">{pct(c.penetration)}</span> {t("cats.bought")}
          </p>
        </div>
        <div className="flex shrink-0 flex-col items-end gap-2">
          <span className="rounded-md bg-black/35 backdrop-blur">
            <Growth value={c.yoy_growth} />
          </span>
          <ArrowUpRight size={18} className="opacity-0 transition-opacity group-hover:opacity-100" />
        </div>
      </div>
    </Link>
  );
}
