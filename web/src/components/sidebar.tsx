"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { BookOpen, FlaskConical, GitCompareArrows, LayoutGrid, Menu, MessageSquareText, X } from "lucide-react";
import { api, type Health } from "@/lib/api";
import { cx } from "@/lib/format";

const NAV = [
  { href: "/", label: "Ask the analyst", icon: MessageSquareText },
  { href: "/explore", label: "Explore categories", icon: LayoutGrid },
  { href: "/compare", label: "Compare", icon: GitCompareArrows },
  { href: "/library", label: "Research library", icon: BookOpen },
  { href: "/lab", label: "Evals & retrieval lab", icon: FlaskConical },
];

export function Logo({ className }: { className?: string }) {
  return (
    <div className={cx("flex items-center gap-2.5", className)}>
      <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden>
        <circle cx="13" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2.4" />
        <circle cx="19" cy="16" r="10" fill="var(--accent)" fillOpacity="0.9" />
        <circle cx="19" cy="16" r="10" fill="none" stroke="currentColor" strokeWidth="2.4" />
      </svg>
      <span className="text-[15px] font-semibold tracking-tight">Cohort Lens</span>
    </div>
  );
}

function StatusPill() {
  const [health, setHealth] = useState<Health | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    api.health().then(setHealth).catch(() => setFailed(true));
  }, []);
  const label = failed ? "Backend offline" : !health ? "Connecting…" : health.analyst === "claude" ? health.model : "Offline analyst";
  const dot = failed ? "bg-negative" : !health ? "bg-muted" : health.analyst === "claude" ? "bg-positive" : "bg-warning";
  return (
    <div className="rounded-xl border hairline bg-surface-2 px-3 py-2.5 text-xs">
      <div className="flex items-center gap-2">
        <span className={cx("h-2 w-2 rounded-full", dot, health && "animate-pulse")} />
        <span className="font-medium text-ink">{label}</span>
      </div>
      {health && (
        <p className="mt-1 text-muted">
          {health.documents} docs · {health.chunks} chunks · {health.respondents.toLocaleString("en-GB")} respondents
        </p>
      )}
    </div>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  const nav = (
    <nav className="flex flex-col gap-0.5">
      {NAV.map(({ href, label, icon: Icon }) => {
        const active = href === "/" ? pathname === "/" : pathname.startsWith(href) || (href === "/explore" && pathname.startsWith("/categories"));
        return (
          <Link
            key={href}
            href={href}
            onClick={() => setOpen(false)}
            className={cx(
              "group flex items-center gap-3 rounded-xl px-3 py-2 text-[13.5px] transition-colors",
              active ? "bg-surface text-ink shadow-card" : "text-ink-2 hover:bg-surface-2 hover:text-ink",
            )}
          >
            <Icon size={16} className={cx(active ? "text-accent-ink" : "text-muted group-hover:text-ink")} />
            {label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="fixed inset-x-0 top-0 z-40 flex h-14 items-center justify-between border-b hairline bg-bg/85 px-4 backdrop-blur lg:hidden">
        <Logo />
        <button aria-label="Open navigation" onClick={() => setOpen(true)} className="rounded-lg p-2 hover:bg-surface-2">
          <Menu size={18} />
        </button>
      </div>
      <div className="h-14 lg:hidden" />
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-black/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 flex w-[280px] flex-col gap-6 bg-bg p-4">
            <div className="flex items-center justify-between">
              <Logo />
              <button aria-label="Close navigation" onClick={() => setOpen(false)} className="rounded-lg p-2 hover:bg-surface-2">
                <X size={18} />
              </button>
            </div>
            {nav}
            <div className="mt-auto">
              <StatusPill />
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="sticky top-0 hidden h-screen w-[248px] shrink-0 flex-col gap-7 border-r hairline px-3 py-5 lg:flex">
        <Link href="/" className="px-2">
          <Logo />
        </Link>
        <div>
          <p className="mb-2 px-3 text-[11px] font-medium uppercase tracking-[0.14em] text-muted">Workspace</p>
          {nav}
        </div>
        <div className="mt-auto flex flex-col gap-3">
          <p className="px-1 text-[11px] leading-relaxed text-muted">
            Demo corpus: synthetic Gen Z panel by a fictional research firm. Swap in licensed research via the ingestion CLI.
          </p>
          <StatusPill />
        </div>
      </aside>
    </>
  );
}
