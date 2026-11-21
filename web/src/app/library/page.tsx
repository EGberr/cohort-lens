"use client";

import { useEffect, useMemo, useState } from "react";
import { FileText, Search } from "lucide-react";
import { api, type DocSummary } from "@/lib/api";
import { DocReader, docTypeLabel } from "@/components/doc-reader";
import { Chip, ErrorState, PageHeader, Skeleton } from "@/components/ui";
import { useLang } from "@/lib/i18n";

const TYPES = ["all", "category_report", "sector_report", "thematic_report", "methodology"];

export default function LibraryPage() {
  const fr = useLang().lang === "fr";
  const [docs, setDocs] = useState<DocSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [type, setType] = useState("all");
  const [q, setQ] = useState("");
  const [open, setOpen] = useState<string | null>(null);

  useEffect(() => {
    api.documents().then(setDocs).catch((e) => setError(String(e)));
  }, []);

  const shown = useMemo(
    () => (docs ?? []).filter((d) => (type === "all" || d.type === type) && (!q || d.title.toLowerCase().includes(q.toLowerCase()))),
    [docs, type, q],
  );
  if (error) return <ErrorState message={error} />;

  return (
    <div className="mx-auto max-w-[1240px] px-5 py-10 sm:px-8">
      <PageHeader eyebrow="Corpus" title={fr ? "Bibliothèque d'études" : "Research library"}>
        {fr
          ? "Tous les documents que l'analyste peut citer (en anglais). Les rapports sont découpés par section, vectorisés et indexés pour la recherche hybride. Ajoutez vos PDF ou fichiers Markdown avec l'outil d'import."
          : "Every document the analyst can cite. Reports are chunked by section, embedded, and indexed for hybrid search. Add your own PDFs or Markdown with the ingestion CLI."}
      </PageHeader>
      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div className="scroll-thin flex gap-1.5 overflow-x-auto pb-1">
          {TYPES.map((t) => (
            <Chip key={t} active={type === t} onClick={() => setType(t)}>
              {t === "all" ? "All" : docTypeLabel(t)}
              {docs && <span className="num ml-1.5 opacity-60">{t === "all" ? docs.length : docs.filter((d) => d.type === t).length}</span>}
            </Chip>
          ))}
        </div>
        <label className="flex items-center gap-2 rounded-full border hairline bg-surface px-3 py-1.5 text-[13px]">
          <Search size={14} className="text-muted" />
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Filter titles" className="w-40 bg-transparent outline-none placeholder:text-muted" />
        </label>
      </div>
      <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
        {!docs && Array.from({ length: 12 }).map((_, i) => <Skeleton key={i} className="h-[74px]" />)}
        {shown.map((d) => (
          <button key={d.doc_id} onClick={() => setOpen(d.doc_id)} className="card flex items-start gap-3 p-4 text-left transition-colors hover:border-line-strong">
            <FileText size={17} className="mt-0.5 shrink-0 text-accent-ink" />
            <span className="min-w-0">
              <span className="block text-[13.5px] font-medium leading-snug">{d.title}</span>
              <span className="text-[11.5px] text-muted">{docTypeLabel(d.type)}</span>
            </span>
          </button>
        ))}
      </div>
      <DocReader docId={open} onClose={() => setOpen(null)} />
    </div>
  );
}
