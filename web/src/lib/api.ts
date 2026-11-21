// Typed client for the Cohort Lens FastAPI backend (proxied under /api by next.config.ts).

export type Health = {
  status: string;
  analyst: "claude" | "offline";
  model: string;
  retrieval_modes: string[];
  documents: number;
  chunks: number;
  respondents: number;
};

export type CategoryKpi = {
  slug: string;
  name: string;
  name_fr: string;
  group: string;
  group_name: string;
  group_name_fr: string;
  image: string;
  penetration: number;
  avg_monthly_spend: number;
  annual_spend_per_capita: number;
  yoy_growth: number;
  sustainable_premium_rate: number;
  dupe_rate: number;
  brand_loyalty_rate: number;
  price_decisive_rate: number;
  buyers: number;
};

export type Overview = {
  respondents: number;
  categories: CategoryKpi[];
  groups: { group: string; name: string; name_fr: string; categories: number; avg_penetration: number; annual_spend_per_capita: number; avg_growth: number }[];
  demographics: Record<string, { segment: string | boolean; n: number }[]>;
};

export type Row = {
  category: string;
  value: number;
  n: number;
  segment?: string | boolean;
  option?: string;
  option_key?: string;
};

export type CategoryDetail = {
  kpi: CategoryKpi;
  aliases: string[];
  insight: string;
  recommendation: string;
  trends: string[];
  barriers: string[];
  channel_mix: Row[];
  discovery_mix: Row[];
  driver_mix: Row[];
  penetration_by: Record<"gender" | "age_band" | "country" | "income_band", Row[]>;
  spend_by_country: Row[];
  discovery_by_age: Row[];
  documents: { doc_id: string; title: string; type: string }[];
  products: Product[];
  related: CategoryKpi[];
};

export type Product = {
  slug: string;
  category: string;
  category_name: string;
  category_name_fr: string;
  name: string;
  name_fr: string;
  image: string;
  price: number;
  per_month: boolean;
  trend: "rising" | "steady" | "cooling";
  buyers: number;
  share_of_category: number;
  reach: number;
  avg_monthly_spend: number;
  share_16_19: number;
  share_25_29: number;
  share_female: number;
  dupe_rate: number;
  brand_loyalty_rate: number;
  top_channel: string;
};

export type Home = {
  respondents: number;
  categories: number;
  products: number;
  documents: number;
  sectors: { group: string; name: string; name_fr: string; categories: number; image: string; top: string[]; avg_growth: number }[];
  trending_products: Product[];
  rising_categories: CategoryKpi[];
  popular_categories: CategoryKpi[];
  hero_categories: CategoryKpi[];
  spotlight: CategoryKpi[];
};

export type ProductDetail = {
  product: Product;
  category: CategoryKpi;
  siblings: Product[];
  share_by_age: Row[];
  share_by_country: Row[];
  passages: SearchHit[];
};

export type DocSummary = { doc_id: string; title: string; type: string; categories: string[]; group?: string };
export type DocFull = { doc_id: string; title: string; type: string; meta: Record<string, string>; body: string; chunks: string[] };

export type SearchHit = {
  chunk_id: string;
  doc_id: string;
  title: string;
  section: string;
  text: string;
  doc_type: string;
  categories: string[];
  score: number;
  ranks: Record<string, number>;
};

export type PassageSource = {
  id: string;
  kind: "passage";
  chunk_id: string;
  doc_id: string;
  title: string;
  section: string;
  text: string;
  doc_type: string;
  score: number;
};

export type Dataset = {
  id: string;
  metric: string;
  description: string;
  unit: string;
  breakdown: string | null;
  filters: Record<string, unknown>;
  rows: Row[];
  notes: string[];
  category_names: Record<string, string>;
};

export type ChartSpec = {
  id: string;
  title: string;
  chart_type: "bar" | "horizontal_bar" | "grouped_bar" | "donut";
  unit: string;
  data: { label: string; value: number; series?: string | null }[];
  source_ids: string[];
};

export type StreamEvent =
  | { type: "status"; text: string }
  | { type: "text"; delta: string }
  | { type: "tool_call"; id: string; name: string; input: Record<string, unknown>; is_error: boolean; summary: string }
  | { type: "source"; source: PassageSource }
  | { type: "dataset"; dataset: Dataset }
  | { type: "chart"; chart: ChartSpec }
  | { type: "done"; mode: string; model: string; usage: Record<string, number>; latency_ms: number }
  | { type: "error"; message: string };

export type EvalReport = {
  generated_at: string;
  corpus: { documents: number; chunks: number };
  retrieval: {
    n_queries: number;
    examples: string[];
    modes: Record<string, { "hit@1": number; "hit@5": number; "mrr@10": number; "section_hit@5": number; latency_p50_ms: number; latency_p95_ms: number; "hit@5_by_kind": Record<string, number> }>;
  };
  answers?: {
    analyst: string;
    model: string;
    n_questions: number;
    numeric_accuracy: number;
    dataset_citation_rate: number;
    citation_rate: number;
    error_rate: number;
    latency_p50_s: number;
    items: { question: string; gold: number; unit: string; correct: boolean; cited_dataset: boolean; answer: string; tools: string[] }[];
  };
};

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<Health>("/health"),
  home: () => get<Home>("/home"),
  product: (slug: string) => get<ProductDetail>(`/products/${slug}`),
  overview: () => get<Overview>("/overview"),
  category: (slug: string) => get<CategoryDetail>(`/categories/${slug}`),
  documents: () => get<DocSummary[]>("/documents"),
  document: (id: string) => get<DocFull>(`/documents/${encodeURIComponent(id)}`),
  search: (query: string, mode?: string, k = 8) => post<{ mode: string; latency_ms: number; hits: SearchHit[] }>("/search", { query, mode, k }),
  evalReport: () => get<EvalReport>("/eval"),
};

/** Streams the analyst's events over SSE (fetch + ReadableStream, so we can POST). */
export async function streamChat(
  messages: { role: "user" | "assistant"; content: string }[],
  onEvent: (e: StreamEvent) => void,
  opts: { signal?: AbortSignal; category?: string; lang?: "en" | "fr" } = {},
): Promise<void> {
  const { signal, category, lang } = opts;
  const base = process.env.NEXT_PUBLIC_API_URL ?? "";
  const res = await fetch(`${base}/api/chat`, {
    method: "POST",
    headers: { "content-type": "application/json", accept: "text/event-stream" },
    body: JSON.stringify({ messages, category, lang }),
    signal,
  });
  if (!res.ok || !res.body) throw new Error(`Chat request failed (${res.status})`);
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split(/\r?\n\r?\n/);
    buffer = frames.pop() ?? "";
    for (const frame of frames) {
      const data = frame
        .split(/\r?\n/)
        .filter((l) => l.startsWith("data:"))
        .map((l) => l.slice(5).trimStart())
        .join("\n");
      if (!data) continue;
      try {
        onEvent(JSON.parse(data) as StreamEvent);
      } catch {
        /* ignore keep-alive or malformed frames */
      }
    }
  }
}
