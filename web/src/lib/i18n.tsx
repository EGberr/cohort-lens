"use client";

import { useEffect, useMemo, useSyncExternalStore, type ReactNode } from "react";

export type Lang = "en" | "fr";

const EN = {
  // navigation
  "nav.discover": "Discover",
  "nav.categories": "Categories",
  "nav.ask": "Ask the studies",
  "nav.compare": "Compare",
  "nav.library": "Library",
  "nav.lab": "Evals",
  "nav.menu": "Menu",
  "status.connecting": "Connecting…",
  "status.offline_backend": "Backend offline",
  "status.offline": "Offline analyst",
  "footer.synthetic": "Demo corpus: a synthetic Gen Z panel published by a fictional research firm. Photos are openly licensed.",
  "footer.credits": "Image credits",
  // home
  "home.eyebrow": "Gen Z consumer intelligence",
  "home.title_a": "What does Gen Z",
  "home.title_b": "actually",
  "home.title_c": "buy — and why?",
  "home.subtitle": "Pick a category, browse what young consumers buy, and ask the studies anything. Every answer is grounded in research reports and a 6,000-respondent panel.",
  "home.search": "Search a category or product, or ask a question…",
  "home.search_hint": "Press Enter to ask the analyst",
  "home.stats.categories": "categories",
  "home.stats.products": "product types",
  "home.stats.respondents": "respondents",
  "home.stats.reports": "reports",
  "home.sectors": "Shop the research by sector",
  "home.sectors_sub": "Nine sectors, from beauty to cars. Open one to see its categories.",
  "home.trending": "Trending products",
  "home.trending_sub": "Rising product types, ranked by reach among 16–29 year-olds.",
  "home.rising": "Fastest-growing categories",
  "home.rising_sub": "Spend growth versus the 2025 wave.",
  "home.popular": "Most bought categories",
  "home.cars": "Spotlight: cars & mobility",
  "home.cars_sub": "From a first used car to shared e-bikes — how Gen Z gets around.",
  "home.ask_title": "Ask the studies",
  "home.ask_sub": "An AI analyst reads the reports, queries the panel and cites every number.",
  "home.see_all": "See all",
  "home.categories_n": "categories",
  // categories
  "cats.title": "All categories",
  "cats.subtitle": "52 categories across 9 sectors. Pick one to explore its products and ask its studies.",
  "cats.all": "All",
  "cats.filter": "Filter",
  "cats.sort": "Sort",
  "cats.sort.penetration": "Most bought",
  "cats.sort.yoy_growth": "Fastest growing",
  "cats.sort.annual_spend_per_capita": "Biggest wallet share",
  "cats.sort.dupe_rate": "Most dupes",
  "cats.sort.sustainable_premium_rate": "Most sustainable",
  "cats.map": "Opportunity map",
  "cats.map_sub": "Penetration (x) vs spend growth (y); bubble size = annual spend per consumer.",
  "cats.grid": "Grid",
  "cats.bought": "bought in 12 months",
  "cats.none": "No category matches",
  // category page
  "cat.back": "All categories",
  "cat.ask": "Ask the studies",
  "cat.penetration": "Penetration",
  "cat.penetration_hint": "bought in last 12 months",
  "cat.spend": "Avg monthly spend",
  "cat.spend_hint": "among buyers",
  "cat.wallet": "Annual spend / consumer",
  "cat.wallet_hint": "all respondents",
  "cat.growth": "Spend growth",
  "cat.growth_hint": "vs 2025 wave",
  "cat.buyers": "Buyers in panel",
  "cat.buyers_hint": "base for mixes",
  "cat.insight": "Key insight",
  "cat.so_what": "So what",
  "cat.products": "Products Gen Z buys",
  "cat.products_sub": "Share of category buyers who chose each product type",
  "cat.tab.overview": "Overview",
  "cat.tab.audience": "Audience",
  "cat.tab.studies": "Studies",
  "cat.channel": "Main purchase channel",
  "cat.channel_sub": "Share of buyers",
  "cat.discovery": "Where they discover it",
  "cat.discovery_sub": "First discovery source, share of buyers",
  "cat.drivers": "Why they buy",
  "cat.drivers_sub": "Top purchase driver, share of buyers",
  "cat.barriers": "Barriers mentioned",
  "cat.disc_age": "Discovery: younger vs older Gen Z",
  "cat.disc_age_sub": "16–19 vs 25–29 year-olds",
  "cat.who": "Who buys",
  "cat.gender": "Gender",
  "cat.age": "Age band",
  "cat.income": "Income",
  "cat.share_bought": "Share who bought",
  "cat.values": "Values",
  "cat.values_sub": "Share of buyers",
  "cat.markets": "By market",
  "cat.markets_sub": "Penetration and average monthly spend",
  "cat.trends": "Trends to watch",
  "cat.research": "Studies on this category",
  "cat.research_sub": "Category report, sector overview and cross-category themes",
  "cat.related": "More in this sector",
  "cat.years": "years",
  "cat.income_suffix": "income",
  "values.price": "Price decisive",
  "values.loyal": "Brand loyal",
  "values.sustainable": "Pays sustainable premium",
  "values.dupe": "Bought a dupe",
  // product
  "prod.share": "of category buyers",
  "prod.reach": "of Gen Z",
  "prod.price": "Typical price",
  "prod.month": "/month",
  "prod.spend": "Category spend / month",
  "prod.channel": "Main channel",
  "prod.young": "Aged 16–19",
  "prod.old": "Aged 25–29",
  "prod.female": "Women",
  "prod.by_age": "Share of category buyers by age",
  "prod.by_country": "Share of category buyers by market",
  "prod.evidence": "What the studies say",
  "prod.siblings": "Other products in",
  "prod.ask": "Ask about this product",
  "trend.rising": "Rising",
  "trend.steady": "Steady",
  "trend.cooling": "Cooling",
  // chat
  "chat.title": "Ask the studies",
  "chat.scope": "Answers focus on",
  "chat.grounded": "grounded in 67 reports and a 6,000-respondent panel",
  "chat.placeholder": "Ask about a category, a product, a segment or a market…",
  "chat.placeholder_scoped": "Ask the studies about {name}…",
  "chat.new": "New",
  "chat.evidence": "Evidence",
  "chat.items": "items",
  "chat.datasets": "datasets",
  "chat.passages": "passages",
  "chat.disclaimer": "Demo data is synthetic. Citations: [D#] survey datasets, [S#] research passages.",
  "chat.error": "Could not reach the analyst. Is the backend running on :8000?",
  "chat.empty_evidence": "Evidence used in an answer appears here — survey datasets and research passages, each with its citation ID.",
  "chat.trace": "Analysis trace",
  "chat.steps": "steps",
  "chat.thinking": "Thinking",
  "chat.hero": "Ask the studies anything",
  "chat.hero_sub": "The analyst searches the research library, runs exact queries on the survey panel, and cites every number.",
  "chat.datasets_title": "Survey datasets",
  "chat.passages_title": "Research passages",
  "chat.open_report": "Open in report",
  "chat.close": "Close",
  // misc
  "misc.loading_error": "Could not load data",
  "misc.start_api": "Start the API with make api and refresh.",
  "misc.credits_title": "Image credits",
  "misc.credits_sub": "All photos are openly licensed (CC0, Public Domain, CC BY or CC BY-SA) and served from this repository.",
} as const;

export type TKey = keyof typeof EN;

const FR: Record<TKey, string> = {
  "nav.discover": "Découvrir",
  "nav.categories": "Catégories",
  "nav.ask": "Interroger les études",
  "nav.compare": "Comparer",
  "nav.library": "Bibliothèque",
  "nav.lab": "Évaluations",
  "nav.menu": "Menu",
  "status.connecting": "Connexion…",
  "status.offline_backend": "Serveur hors ligne",
  "status.offline": "Analyste hors ligne",
  "footer.synthetic": "Corpus de démonstration : panel Gen Z synthétique publié par un institut fictif. Les photos sont sous licence libre.",
  "footer.credits": "Crédits photo",
  "home.eyebrow": "Intelligence consommateur Gen Z",
  "home.title_a": "Qu'achète",
  "home.title_b": "vraiment",
  "home.title_c": "la Gen Z — et pourquoi ?",
  "home.subtitle": "Choisissez une catégorie, parcourez ce que les jeunes achètent et posez vos questions aux études. Chaque réponse s'appuie sur des rapports et un panel de 6 000 répondants.",
  "home.search": "Cherchez une catégorie, un produit, ou posez une question…",
  "home.search_hint": "Entrée pour interroger l'analyste",
  "home.stats.categories": "catégories",
  "home.stats.products": "types de produits",
  "home.stats.respondents": "répondants",
  "home.stats.reports": "rapports",
  "home.sectors": "Explorez les études par secteur",
  "home.sectors_sub": "Neuf secteurs, de la beauté à l'automobile. Ouvrez-en un pour voir ses catégories.",
  "home.trending": "Produits en vogue",
  "home.trending_sub": "Types de produits en hausse, classés par portée chez les 16-29 ans.",
  "home.rising": "Catégories en plus forte croissance",
  "home.rising_sub": "Croissance des dépenses par rapport à la vague 2025.",
  "home.popular": "Catégories les plus achetées",
  "home.cars": "Zoom : voitures & mobilité",
  "home.cars_sub": "De la première voiture d'occasion au vélo électrique partagé : comment la Gen Z se déplace.",
  "home.ask_title": "Interrogez les études",
  "home.ask_sub": "Un analyste IA lit les rapports, interroge le panel et cite chaque chiffre.",
  "home.see_all": "Tout voir",
  "home.categories_n": "catégories",
  "cats.title": "Toutes les catégories",
  "cats.subtitle": "52 catégories dans 9 secteurs. Choisissez-en une pour explorer ses produits et interroger ses études.",
  "cats.all": "Toutes",
  "cats.filter": "Filtrer",
  "cats.sort": "Trier",
  "cats.sort.penetration": "Les plus achetées",
  "cats.sort.yoy_growth": "Plus forte croissance",
  "cats.sort.annual_spend_per_capita": "Plus grosse part du budget",
  "cats.sort.dupe_rate": "Le plus de dupes",
  "cats.sort.sustainable_premium_rate": "Les plus durables",
  "cats.map": "Carte des opportunités",
  "cats.map_sub": "Pénétration (x) et croissance des dépenses (y) ; taille = dépense annuelle par consommateur.",
  "cats.grid": "Grille",
  "cats.bought": "ont acheté en 12 mois",
  "cats.none": "Aucune catégorie ne correspond à",
  "cat.back": "Toutes les catégories",
  "cat.ask": "Interroger les études",
  "cat.penetration": "Pénétration",
  "cat.penetration_hint": "achat sur 12 mois",
  "cat.spend": "Dépense mensuelle moy.",
  "cat.spend_hint": "par acheteur",
  "cat.wallet": "Dépense annuelle / conso.",
  "cat.wallet_hint": "tous répondants",
  "cat.growth": "Croissance",
  "cat.growth_hint": "vs vague 2025",
  "cat.buyers": "Acheteurs du panel",
  "cat.buyers_hint": "base des répartitions",
  "cat.insight": "Insight clé",
  "cat.so_what": "Et concrètement",
  "cat.products": "Les produits achetés par la Gen Z",
  "cat.products_sub": "Part des acheteurs de la catégorie ayant choisi chaque type de produit",
  "cat.tab.overview": "Vue d'ensemble",
  "cat.tab.audience": "Audience",
  "cat.tab.studies": "Études",
  "cat.channel": "Canal d'achat principal",
  "cat.channel_sub": "Part des acheteurs",
  "cat.discovery": "Où ils le découvrent",
  "cat.discovery_sub": "Première source de découverte",
  "cat.drivers": "Pourquoi ils achètent",
  "cat.drivers_sub": "Motivation principale",
  "cat.barriers": "Freins cités",
  "cat.disc_age": "Découverte : jeunes vs plus âgés",
  "cat.disc_age_sub": "16-19 ans vs 25-29 ans",
  "cat.who": "Qui achète",
  "cat.gender": "Genre",
  "cat.age": "Tranche d'âge",
  "cat.income": "Revenus",
  "cat.share_bought": "Part ayant acheté",
  "cat.values": "Valeurs",
  "cat.values_sub": "Part des acheteurs",
  "cat.markets": "Par marché",
  "cat.markets_sub": "Pénétration et dépense mensuelle moyenne",
  "cat.trends": "Tendances à suivre",
  "cat.research": "Études sur cette catégorie",
  "cat.research_sub": "Rapport de catégorie, synthèse sectorielle et thèmes transversaux",
  "cat.related": "Dans le même secteur",
  "cat.years": "ans",
  "cat.income_suffix": "revenus",
  "values.price": "Prix décisif",
  "values.loyal": "Fidèle à une marque",
  "values.sustainable": "Paie plus pour le durable",
  "values.dupe": "A acheté un dupe",
  "prod.share": "des acheteurs de la catégorie",
  "prod.reach": "de la Gen Z",
  "prod.price": "Prix typique",
  "prod.month": "/mois",
  "prod.spend": "Dépense catégorie / mois",
  "prod.channel": "Canal principal",
  "prod.young": "16-19 ans",
  "prod.old": "25-29 ans",
  "prod.female": "Femmes",
  "prod.by_age": "Part des acheteurs par âge",
  "prod.by_country": "Part des acheteurs par marché",
  "prod.evidence": "Ce que disent les études",
  "prod.siblings": "Autres produits :",
  "prod.ask": "Poser une question sur ce produit",
  "trend.rising": "En hausse",
  "trend.steady": "Stable",
  "trend.cooling": "En baisse",
  "chat.title": "Interroger les études",
  "chat.scope": "Réponses centrées sur",
  "chat.grounded": "fondé sur 67 rapports et un panel de 6 000 répondants",
  "chat.placeholder": "Une question sur une catégorie, un produit, un segment ou un marché…",
  "chat.placeholder_scoped": "Posez une question aux études sur {name}…",
  "chat.new": "Nouveau",
  "chat.evidence": "Preuves",
  "chat.items": "éléments",
  "chat.datasets": "jeux de données",
  "chat.passages": "extraits",
  "chat.disclaimer": "Données de démonstration synthétiques. Citations : [D#] données du panel, [S#] extraits d'études.",
  "chat.error": "Impossible de joindre l'analyste. Le serveur tourne-t-il sur :8000 ?",
  "chat.empty_evidence": "Les preuves utilisées dans une réponse apparaissent ici : données du panel et extraits d'études, chacun avec son identifiant de citation.",
  "chat.trace": "Étapes de l'analyse",
  "chat.steps": "étapes",
  "chat.thinking": "Réflexion",
  "chat.hero": "Posez n'importe quelle question aux études",
  "chat.hero_sub": "L'analyste fouille la bibliothèque d'études, interroge le panel et cite chaque chiffre.",
  "chat.datasets_title": "Données du panel",
  "chat.passages_title": "Extraits d'études",
  "chat.open_report": "Ouvrir le rapport",
  "chat.close": "Fermer",
  "misc.loading_error": "Impossible de charger les données",
  "misc.start_api": "Lancez l'API avec make api puis rechargez.",
  "misc.credits_title": "Crédits photo",
  "misc.credits_sub": "Toutes les photos sont sous licence libre (CC0, domaine public, CC BY ou CC BY-SA) et hébergées dans ce dépôt.",
};

const DICTS: Record<Lang, Record<TKey, string>> = { en: EN, fr: FR };

type Ctx = {
  lang: Lang;
  setLang: (l: Lang) => void;
  t: (k: TKey, vars?: Record<string, string>) => string;
  /** Picks the French field of an API object when the UI is in French. */
  pick: <T extends Record<string, unknown>>(obj: T, field: string) => string;
};

const STORAGE_KEY = "zentrend-lang";

// Language preference as an external store: the server (and hydration) always render English,
// then React switches to the stored/browser language without a hydration mismatch.
const listeners = new Set<() => void>();
let current: Lang | null = null;

function readLang(): Lang {
  if (current) return current;
  let l: Lang = "en";
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved === "en" || saved === "fr") l = saved;
    else if (navigator.language?.toLowerCase().startsWith("fr")) l = "fr";
  } catch {
    /* storage unavailable */
  }
  current = l;
  return l;
}

function subscribe(cb: () => void) {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function setLang(l: Lang) {
  current = l;
  try {
    localStorage.setItem(STORAGE_KEY, l);
  } catch {
    /* ignore */
  }
  listeners.forEach((cb) => cb());
}

/** Keeps <html lang> in sync; components read the language themselves through useLang(). */
export function LangProvider({ children }: { children: ReactNode }) {
  const { lang } = useLang();
  useEffect(() => {
    document.documentElement.lang = lang;
  }, [lang]);
  return <>{children}</>;
}

/**
 * Each component subscribes to the store itself, so every hydration pass (including Suspense
 * boundaries that hydrate later) first renders the server snapshot ("en"), then updates.
 */
export function useLang(): Ctx {
  const lang = useSyncExternalStore(subscribe, readLang, () => "en" as Lang);
  return useMemo<Ctx>(
    () => ({
      lang,
      setLang,
      t: (k, vars) => {
        let s: string = DICTS[lang][k] ?? EN[k];
        if (vars) for (const [name, v] of Object.entries(vars)) s = s.replace(`{${name}}`, v);
        return s;
      },
      pick: (obj, field) => String((lang === "fr" ? obj[`${field}_fr`] : undefined) ?? obj[field] ?? ""),
    }),
    [lang],
  );
}

const SEGMENTS_FR: Record<string, string> = {
  France: "France", UK: "Royaume-Uni", Germany: "Allemagne", Spain: "Espagne", Italy: "Italie", US: "États-Unis",
  Female: "Femmes", Male: "Hommes", "Non-binary": "Non binaires", Low: "Faibles", Mid: "Moyens", High: "Élevés",
  Urban: "Urbains", "Non-urban": "Non urbains",
};
const OPTIONS_FR: Record<string, string> = {
  tiktok_shop: "TikTok Shop", instagram: "Instagram", marketplace: "Marketplaces en ligne", brand_dtc: "Site / appli de la marque",
  physical_store: "Magasin physique", resale: "Applis de revente", subscription: "Abonnement", tiktok: "TikTok",
  youtube: "YouTube", friends: "Amis & famille", search: "Moteurs de recherche", in_store: "En magasin",
  price: "Prix / rapport qualité-prix", quality: "Qualité & durabilité", creator: "Recommandation de créateur",
  aesthetic: "Esthétique & expression de soi", sustainability: "Durabilité", identity: "Identité de marque",
  convenience: "Praticité", novelty: "Nouveauté & tendances", performance: "Performance", health: "Bénéfices santé",
  community: "Communauté", exclusivity: "Exclusivité & drops",
};
const CHANNEL_LABEL_FR: Record<string, string> = {
  "TikTok Shop": "TikTok Shop", "Instagram Shopping": "Instagram", "Online marketplaces": "Marketplaces en ligne",
  "Brand website / app": "Site / appli de la marque", "Physical store": "Magasin physique",
  "Resale apps (Vinted, Depop...)": "Applis de revente", Subscription: "Abonnement",
};

/** Translates survey labels (segments, options, channels) for display. */
export function useLabels() {
  const { lang } = useLang();
  return {
    segment: (label: string) => (lang === "fr" ? (SEGMENTS_FR[label] ?? label) : label),
    option: (key: string | undefined, label: string) => (lang === "fr" && key ? (OPTIONS_FR[key] ?? label) : label),
    channel: (label: string) => (lang === "fr" ? (CHANNEL_LABEL_FR[label] ?? label) : label),
  };
}
