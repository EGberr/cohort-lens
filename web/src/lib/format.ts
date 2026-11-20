export const pct = (v: number, digits = 0) => `${v.toFixed(digits)}%`;
export const eur = (v: number, digits = 0) => `€${v.toLocaleString("en-GB", { maximumFractionDigits: digits, minimumFractionDigits: digits })}`;
export const signed = (v: number, digits = 1) => `${v > 0 ? "+" : ""}${v.toFixed(digits)}%`;

export const COUNTRY: Record<string, string> = { FR: "France", UK: "UK", DE: "Germany", ES: "Spain", IT: "Italy", US: "US" };
export const SEGMENT_LABEL = (s: string | boolean | undefined) => {
  if (s === true) return "Urban";
  if (s === false) return "Non-urban";
  if (s === undefined) return "";
  return COUNTRY[s] ?? s.charAt(0).toUpperCase() + s.slice(1);
};

export const CHART_COLORS = ["var(--chart-1)", "var(--chart-2)", "var(--chart-3)", "var(--chart-4)", "var(--chart-5)", "var(--chart-6)", "var(--chart-7)"];

export const GROUP_COLORS: Record<string, string> = {
  beauty: "var(--chart-4)",
  fashion: "var(--chart-1)",
  food: "var(--chart-3)",
  tech: "var(--chart-6)",
  entertainment: "var(--chart-7)",
  wellness: "var(--chart-2)",
  home: "var(--chart-5)",
  mobility: "#9aa3b2",
  services: "#c9a227",
};

export const METRIC_LABELS: Record<string, string> = {
  penetration: "Penetration",
  avg_monthly_spend: "Avg monthly spend",
  annual_spend_per_capita: "Annual spend / consumer",
  sustainable_premium_rate: "Pays sustainable premium",
  dupe_rate: "Bought a dupe",
  brand_loyalty_rate: "Brand loyal",
  price_decisive_rate: "Price decisive",
};

export function cx(...parts: (string | false | null | undefined)[]) {
  return parts.filter(Boolean).join(" ");
}
