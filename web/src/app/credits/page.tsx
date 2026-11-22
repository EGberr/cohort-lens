"use client";

import { useEffect, useState } from "react";
import { useLang } from "@/lib/i18n";
import { Photo } from "@/components/photo";
import { PageHeader } from "@/components/ui";

type Credit = { file: string; title: string; creator: string | null; license: string; license_url: string; source: string; url: string };

export default function CreditsPage() {
  const { t } = useLang();
  const [credits, setCredits] = useState<Credit[]>([]);
  useEffect(() => {
    fetch("/img/credits.json")
      .then((r) => r.json())
      .then((d: Record<string, Credit>) => setCredits(Object.values(d)))
      .catch(() => setCredits([]));
  }, []);
  return (
    <div className="mx-auto max-w-[1320px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow="Zentrend" title={t("misc.credits_title")}>
        {t("misc.credits_sub")}
      </PageHeader>
      <ul className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {credits.map((c) => (
          <li key={c.file} className="card flex gap-3 p-3">
            <Photo src={`/img/${c.file}`} alt="" className="h-16 w-16 shrink-0" rounded="rounded-lg" sizes="64px" />
            <div className="min-w-0 text-[12px]">
              <a href={c.url} target="_blank" rel="noreferrer" className="line-clamp-1 font-medium text-ink hover:underline">
                {c.title || c.file}
              </a>
              <p className="truncate text-muted">{c.creator || "Unknown author"} · {c.source}</p>
              <a href={c.license_url} target="_blank" rel="noreferrer" className="text-accent-ink hover:underline">
                {c.license}
              </a>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
