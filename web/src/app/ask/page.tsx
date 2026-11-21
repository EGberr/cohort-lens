"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { ChatView } from "@/components/chat/chat-view";
import { useLang } from "@/lib/i18n";

const SUGGESTIONS = {
  en: [
    "Where does Gen Z discover and buy skincare, and how does it differ by age band?",
    "Which categories show the biggest sustainability say-do gap?",
    "Which electric vehicles do young drivers choose, and through which channel?",
    "How big is dupe culture in beauty, and how should prestige brands respond?",
    "Is resale fashion more popular in France than in Germany?",
    "Which fast-growing categories should a brand targeting young men prioritise?",
  ],
  fr: [
    "Où la Gen Z découvre-t-elle et achète-t-elle ses soins du visage, selon l'âge ?",
    "Quelles catégories montrent le plus grand écart entre discours et achats durables ?",
    "Quelles voitures électriques choisissent les jeunes conducteurs, et par quel canal ?",
    "Quelle est l'ampleur des dupes en beauté, et comment les marques premium doivent-elles réagir ?",
    "La mode de seconde main est-elle plus populaire en France qu'en Allemagne ?",
    "Quelles catégories en croissance prioriser pour cibler les jeunes hommes ?",
  ],
};

function Ask() {
  const params = useSearchParams();
  const { t, lang } = useLang();
  const category = params.get("category") ?? undefined;
  return (
    <ChatView
      key={category ?? "all"}
      category={category}
      initialQuestion={params.get("q") ?? ""}
      suggestions={SUGGESTIONS[lang]}
      emptyState={
        <>
          <p className="mb-4 inline-flex w-fit items-center gap-2 rounded-full border hairline bg-surface px-3 py-1 text-[11.5px] text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent-ink" /> {t("chat.grounded")}
          </p>
          <h1 className="font-serif text-[44px] leading-[1.02] tracking-tight sm:text-[56px]">{t("chat.hero")}</h1>
          <p className="mt-4 max-w-xl text-[15px] leading-relaxed text-ink-2">{t("chat.hero_sub")}</p>
        </>
      }
    />
  );
}

export default function AskPage() {
  return (
    <Suspense fallback={<div className="h-[calc(100vh-4rem)]" />}>
      <Ask />
    </Suspense>
  );
}
