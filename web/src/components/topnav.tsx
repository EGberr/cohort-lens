"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { Menu, X } from "lucide-react";
import { api, type Health } from "@/lib/api";
import { cx } from "@/lib/format";
import { useLang, type TKey } from "@/lib/i18n";

const NAV: { href: string; key: TKey }[] = [
  { href: "/", key: "nav.discover" },
  { href: "/categories", key: "nav.categories" },
  { href: "/ask", key: "nav.ask" },
  { href: "/compare", key: "nav.compare" },
  { href: "/library", key: "nav.library" },
  { href: "/lab", key: "nav.lab" },
];

export function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden>
        <circle cx="13" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2.4" />
        <circle cx="19" cy="16" r="10" fill="var(--accent)" fillOpacity="0.9" />
        <circle cx="19" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2.4" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight">Cohort Lens</span>
    </span>
  );
}

function LangSwitch() {
  const { lang, setLang } = useLang();
  return (
    <div className="flex rounded-full border hairline bg-surface p-0.5 text-[11.5px] font-medium" role="group" aria-label="Language">
      {(["en", "fr"] as const).map((l) => (
        <button
          key={l}
          onClick={() => setLang(l)}
          aria-pressed={lang === l}
          className={cx("rounded-full px-2.5 py-1 uppercase transition-colors", lang === l ? "bg-ink text-bg" : "text-muted hover:text-ink")}
        >
          {l}
        </button>
      ))}
    </div>
  );
}

function Status() {
  const { t } = useLang();
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    api.health().then(setHealth).catch(() => setFailed(true));
  }, []);
  const label = failed ? t("status.offline_backend") : !health ? t("status.connecting") : health.analyst === "claude" ? health.model : t("status.offline");
  const dot = failed ? "bg-negative" : !health ? "bg-muted" : health.analyst === "claude" ? "bg-positive" : "bg-warning";
  return (
    <span className="hidden items-center gap-1.5 text-[11.5px] text-muted xl:flex" title={label}>
      <span className={cx("h-1.5 w-1.5 rounded-full", dot)} />
      {label}
    </span>
  );
}

export function TopNav() {
  const pathname = usePathname();
  const { t } = useLang();
  const [open, setOpen] = useState(false);
  const isActive = (href: string) =>
    href === "/" ? pathname === "/" : pathname.startsWith(href) || (href === "/categories" && pathname.startsWith("/products"));

  return (
    <header className="sticky top-0 z-40 border-b hairline bg-bg/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-[1320px] items-center gap-6 px-5 sm:px-8">
        <Link href="/" aria-label="Cohort Lens home" onClick={() => setOpen(false)}>
          <Logo />
        </Link>
        <nav className="hidden items-center gap-1 lg:flex">
          {NAV.map(({ href, key }) => (
            <Link
              key={href}
              href={href}
              className={cx(
                "rounded-full px-3.5 py-1.5 text-[13.5px] transition-colors",
                isActive(href) ? "bg-surface-2 font-medium text-ink" : "text-ink-2 hover:text-ink",
              )}
            >
              {t(key)}
            </Link>
          ))}
        </nav>
        <div className="ml-auto flex items-center gap-3">
          <Status />
          <LangSwitch />
          <button aria-label={t("nav.menu")} onClick={() => setOpen((o) => !o)} className="rounded-lg p-2 hover:bg-surface-2 lg:hidden">
            {open ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>
      </div>
      {open && (
        <nav className="flex flex-col gap-1 border-t hairline px-5 py-3 lg:hidden">
          {NAV.map(({ href, key }) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={cx("rounded-xl px-3 py-2.5 text-[14px]", isActive(href) ? "bg-surface-2 font-medium" : "text-ink-2")}
            >
              {t(key)}
            </Link>
          ))}
        </nav>
      )}
    </header>
  );
}

export function Footer() {
  const { t } = useLang();
  return (
    <footer className="mt-24 border-t hairline">
      <div className="mx-auto flex max-w-[1320px] flex-col gap-4 px-5 py-10 text-[12.5px] text-muted sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <div className="flex flex-col gap-2">
          <Logo />
          <p className="max-w-lg leading-relaxed">{t("footer.synthetic")}</p>
        </div>
        <div className="flex gap-5">
          <Link href="/credits" className="hover:text-ink">
            {t("footer.credits")}
          </Link>
          <a href="https://github.com/EGberr/cohort-lens" target="_blank" rel="noreferrer" className="hover:text-ink">
            GitHub
          </a>
        </div>
      </div>
    </footer>
  );
}
