"""Deterministic offline analyst, used when no Anthropic credentials are configured.

It follows the same tool path as the Claude agent (search + survey + chart) with rule-based
planning, and emits the same event stream, so the whole product can be demoed and tested
without an API key. It is intentionally simple and labelled as such in the UI.
"""

from __future__ import annotations

import asyncio
import re
import time
from collections.abc import AsyncIterator
from typing import Any

from app.corpus.catalog import BY_CATEGORY, CATEGORY_FR, PRODUCT_BY_SLUG
from app.corpus.spec import BY_SLUG, CATEGORIES, GROUPS
from app.tools import SourceRegistry, Toolbox

Event = dict[str, Any]

METRIC_RULES: list[tuple[str, str]] = [
    (
        r"\b(which products?|what products?|product types?|best.?sellers?|quels? produits?|types? de produits?)",
        "product_mix",
    ),
    (r"(contrefa|copie|imitation)", "dupe_rate"),
    (r"(durab|écolo|ecolo|environnement|éthique)", "sustainable_premium_rate"),
    (r"(fidél|fidel|même marque)", "brand_loyalty_rate"),
    (r"(découvr|decouvr|inspir)", "discovery_mix"),
    (r"(canal|canaux|où (achètent|achete|ach[eè]tent)|ou achetent|acheter sur)", "channel_mix"),
    (r"(pourquoi|motivation|raison|critère|critere)", "driver_mix"),
    (r"(dépens|depens|combien|budget|panier)", "avg_monthly_spend"),
    (r"\b(dupe|dupes|lookalike|copy|copies|knock-?off)", "dupe_rate"),
    (r"\b(sustainab|eco|green|ethical|environment)", "sustainable_premium_rate"),
    (r"\b(loyal|loyalty|switch|repurchase|same brand)", "brand_loyalty_rate"),
    (r"\b(discover|discovery|find out|hear about|awareness|inspiration)", "discovery_mix"),
    (r"\b(channel|where do|where does|buy from|shop on|purchase on|checkout|tiktok shop|online or)", "channel_mix"),
    (r"\b(why|driver|drivers|motivat|reason|choose|criteria)", "driver_mix"),
    (r"\b(per year|annual|wallet|share of wallet)", "annual_spend_per_capita"),
    (r"\b(spend|spending|how much|budget|basket|€|eur)", "avg_monthly_spend"),
    (r"\b(price.sensitiv|cheap|price matter|price-driven|deal)", "price_decisive_rate"),
]
BREAKDOWN_RULES: list[tuple[str, str]] = [
    (r"\b(hommes?|femmes?|genre|filles|garçons)\b", "gender"),
    (r"(âge|\bage\b|plus jeunes|plus âgés|ados|adolescents|étudiants)", "age_band"),
    (r"\b(pays|marchés?|allemagne|espagne|italie|royaume-uni|états-unis|etats-unis)", "country"),
    (r"\b(revenus?|aisés)\b", "income_band"),
    (r"\b(men|women|male|female|gender|girls|boys|non-binary)\b", "gender"),
    (r"\b(age|older|younger|teen|teens|16-19|20-24|25-29|students?)\b", "age_band"),
    (
        r"\b(countr|market|france|french|uk|britain|british|germany|german|spain|spanish|italy|italian|us|usa|america)",
        "country",
    ),
    (r"\b(income|affluent|wealthy|low-income|rich)\b", "income_band"),
    (r"\b(urban|rural|city|cities)\b", "urban"),
]
GROUP_WORDS = {
    "beauty": "beauty",
    "fashion": "fashion",
    "food": "food",
    "drinks": "food",
    "beverage": "food",
    "tech": "tech",
    "electronics": "tech",
    "entertainment": "entertainment",
    "media": "entertainment",
    "wellness": "wellness",
    "health": "wellness",
    "home": "home",
    "travel": "mobility",
    "mobility": "mobility",
    "finance": "services",
    "money": "services",
    "services": "services",
}


def _alias_index() -> list[tuple[str, str]]:
    pairs = []
    for c in CATEGORIES:
        names = {c.name.lower(), c.slug.replace("-", " "), *[a.lower() for a in c.aliases], CATEGORY_FR[c.slug].lower()}
        for prod in BY_CATEGORY[c.slug]:
            names |= {prod.name.lower(), prod.name_fr.lower()}
        for n in names:
            pairs.append((n, c.slug))
    return sorted(pairs, key=lambda p: -len(p[0]))


ALIASES = _alias_index()


def detect_categories(text: str) -> list[str]:
    t = " " + text.lower() + " "
    found: list[str] = []
    for alias, slug in ALIASES:
        if re.search(rf"(?<![a-z]){re.escape(alias)}(?:s|es)?(?![a-z])", t) and slug not in found:
            found.append(slug)
            t = t.replace(alias, " ")
    if not found:
        for word, group in GROUP_WORDS.items():
            if re.search(rf"\b{word}\b", t):
                found += [c.slug for c in CATEGORIES if c.group == group and c.slug not in found]
    return found[:12]


def detect(rules: list[tuple[str, str]], text: str, default: str | None) -> str | None:
    t = text.lower()
    for pattern, value in rules:
        if re.search(pattern, t):
            return value
    return default


def _fmt(v: float, unit: str) -> str:
    if unit.startswith("EUR"):
        return f"€{v:,.0f}"
    return f"{v:.0f}%"


SEGMENT_LABELS = {
    "FR": "France",
    "UK": "UK",
    "DE": "Germany",
    "ES": "Spain",
    "IT": "Italy",
    "US": "US",
    True: "Urban",
    False: "Non-urban",
}


class OfflineAnalyst:
    def __init__(self, toolbox: Toolbox) -> None:
        self.toolbox = toolbox
        self.lang = "en"

    async def run(
        self, history: list[dict[str, str]], scope: str | None = None, lang: str = "en"
    ) -> AsyncIterator[Event]:
        self.lang = "fr" if lang == "fr" else "en"
        question = next((m["content"] for m in reversed(history) if m.get("role") == "user"), "").strip()
        if not question:
            yield {"type": "error", "message": "Ask a question to get started."}
            return
        t0 = time.perf_counter()
        reg = SourceRegistry()
        yield {"type": "status", "text": "Planning the analysis (offline analyst)"}

        cats = detect_categories(question)
        if not cats and scope:
            cats = [scope]
        metric = detect(METRIC_RULES, question, "penetration")
        breakdown = detect(BREAKDOWN_RULES, question, None)

        # 1. research search (always)
        yield {"type": "status", "text": "Searching the research library"}
        search_in = {"query": question, "k": 5, **({"categories": cats} if cats else {})}
        res, events = self.toolbox.run("search_research", search_in, reg)
        async for e in self._tool_events("search_research", search_in, events):
            yield e
        passages = res["passages"]
        if not cats and passages:
            top = self.toolbox.retriever.chunk_by_id[next(iter(reg.passages))].categories
            cats = top[:1]
        if not cats:
            async for e in self._stream(self._t("unmapped")):
                yield e
            yield {
                "type": "done",
                "mode": "offline",
                "model": "offline-analyst",
                "usage": {},
                "latency_ms": int((time.perf_counter() - t0) * 1000),
            }
            return

        # 2. survey query
        yield {"type": "status", "text": "Querying the survey panel"}
        if len(cats) > 1 and breakdown and metric.endswith("_mix"):
            breakdown = None  # keep mixes readable when comparing several categories
        survey_in = {"metric": metric, "categories": cats, **({"breakdown": breakdown} if breakdown else {})}
        data, events = self.toolbox.run("query_survey", survey_in, reg)
        async for e in self._tool_events("query_survey", survey_in, events):
            yield e

        # 3. recommendation passage for the lead category
        lead = cats[0]
        rec_in = {
            "query": f"implications for marketers {BY_SLUG[lead].name}",
            "categories": [lead],
            "k": 1,
            "doc_types": ["category_report"],
        }
        rec, events = self.toolbox.run("search_research", rec_in, reg)
        async for e in self._tool_events("search_research", rec_in, events):
            yield e

        # 4. chart
        chart_in = self._chart_input(data)
        if chart_in:
            _, events = self.toolbox.run("create_chart", chart_in, reg)
            async for e in self._tool_events("create_chart", chart_in, events):
                yield e

        yield {"type": "status", "text": "Writing the answer"}
        async for e in self._stream(self._compose(data, passages, rec["passages"], cats)):
            yield e
        yield {
            "type": "done",
            "mode": "offline",
            "model": "offline-analyst",
            "usage": {},
            "latency_ms": int((time.perf_counter() - t0) * 1000),
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    async def _tool_events(self, name, inp, events) -> AsyncIterator[Event]:
        await asyncio.sleep(0.05)
        summary = next((e["summary"] for e in events if e["type"] == "tool_summary"), "")
        yield {
            "type": "tool_call",
            "id": f"off_{name}_{id(inp)}",
            "name": name,
            "input": inp,
            "is_error": False,
            "summary": summary,
        }
        for e in events:
            if e["type"] != "tool_summary":
                yield e

    async def _stream(self, text: str) -> AsyncIterator[Event]:
        for piece in re.findall(r"\S+\s*|\n", text):
            yield {"type": "text", "delta": piece}
            await asyncio.sleep(0.006)

    def _label(self, row: dict) -> str:
        if "segment" in row:
            return self._seg(row["segment"])
        if "option" in row:
            return self._opt(row)
        return self._name(row["category"])

    def _chart_input(self, data: dict) -> dict | None:
        rows = data["rows"]
        cats = list(data["category_names"])
        if data["metric"].endswith("_mix") and data["breakdown"]:
            rows = [r for r in rows if r["category"] == cats[0]]
            overall = {}
            for r in rows:
                overall[r["option_key"]] = overall.get(r["option_key"], 0) + r["value"] * r["n"]
            key = max(overall, key=overall.get)
            sel = [r for r in rows if r["option_key"] == key]
            points = [{"label": self._label(r), "value": r["value"]} for r in sel]
            ctype = "bar"
            title = (
                f"{self._name(cats[0])} : part citant {self._opt(sel[0])}"
                if self.lang == "fr"
                else f"{self._name(cats[0])}: share citing {sel[0]['option']}, by {data['breakdown'].replace('_', ' ')}"
            )
        elif data["metric"].endswith("_mix"):
            rows = [r for r in rows if r["category"] == cats[0]][:6]
            points = [{"label": self._opt(r), "value": r["value"]} for r in rows]
            ctype = "donut" if data["metric"] not in ("driver_mix", "product_mix") else "horizontal_bar"
            title = f"{self._name(cats[0])} : {self._desc(data).lower()}"
        elif data["breakdown"] and len(cats) > 1:
            points = [{"label": self._label(r), "value": r["value"], "series": self._name(r["category"])} for r in rows]
            ctype, title = "grouped_bar", self._desc(data)
        else:
            ordered = rows if data["breakdown"] else sorted(rows, key=lambda r: -r["value"])
            points = [{"label": self._label(r), "value": r["value"]} for r in ordered]
            ctype = "bar" if len(points) <= 6 else "horizontal_bar"
            title = self._desc(data)
        if len(points) < 2:
            return None
        return {
            "title": title[:120],
            "chart_type": ctype,
            "unit": data["unit"],
            "data": points,
            "source_ids": [data["id"]],
        }

    def _desc(self, data: dict) -> str:
        return METRIC_FR[data["metric"]] if self.lang == "fr" else data["description"]

    def _t(self, key: str) -> str:
        return TEXT[self.lang][key]

    def _name(self, slug: str) -> str:
        return CATEGORY_FR[slug] if self.lang == "fr" else BY_SLUG[slug].name

    def _opt(self, row: dict) -> str:
        key = row.get("option_key", "")
        if self.lang == "fr":
            if key in PRODUCT_BY_SLUG:
                return PRODUCT_BY_SLUG[key].name_fr
            return OPTION_FR.get(key, row["option"])
        return row["option"]

    def _seg(self, seg) -> str:
        if self.lang == "fr":
            return SEGMENT_FR.get(seg, str(seg))
        return str(SEGMENT_LABELS.get(seg, seg))

    def _compose(self, data: dict, passages: list[dict], rec: list[dict], cats: list[str]) -> str:
        t = self._t
        d, unit, rows = data["id"], data["unit"], data["rows"]
        lead = self._name(cats[0])
        desc = METRIC_FR[data["metric"]] if self.lang == "fr" else data["description"]
        desc = desc[0].lower() + desc[1:]
        lines: list[str] = []
        if data["metric"].endswith("_mix"):
            top = [r for r in rows if r["category"] == cats[0]]
            if "segment" in top[0]:
                firsts: dict = {}
                for r in top:
                    firsts.setdefault(r["segment"], r)
                lines.append(t("by_segment").format(lead=lead, desc=desc, d=d))
                lines += [
                    f"- {self._seg(r['segment'])} : {self._opt(r)} ({_fmt(r['value'], unit)}, n={r['n']:,})"
                    if self.lang == "fr"
                    else f"- {self._seg(r['segment'])}: {self._opt(r)} ({_fmt(r['value'], unit)}, n={r['n']:,})"
                    for r in firsts.values()
                ]
            else:
                lines.append(t("leads").format(opt=self._opt(top[0]), lead=lead, v=_fmt(top[0]["value"], unit), d=d))
                lines += [f"- {self._opt(r)}: {_fmt(r['value'], unit)}" for r in top[:5]]
        elif data["breakdown"]:
            by_cat: dict[str, list[dict]] = {}
            for r in rows:
                by_cat.setdefault(r["category"], []).append(r)
            for cat, rs in by_cat.items():
                hi, lo = max(rs, key=lambda r: r["value"]), min(rs, key=lambda r: r["value"])
                lines.append(
                    t("hi_lo").format(
                        name=self._name(cat),
                        hi=self._seg(hi["segment"]),
                        hv=_fmt(hi["value"], unit),
                        lo=self._seg(lo["segment"]),
                        lv=_fmt(lo["value"], unit),
                        d=d,
                    )
                )
                lines += [f"- {self._seg(r['segment'])}: {_fmt(r['value'], unit)} (n={r['n']:,})" for r in rs]
        elif len(rows) == 1:
            lines.append(
                f"**{lead} : {_fmt(rows[0]['value'], unit)}** — {desc} [{d}]."
                if self.lang == "fr"
                else f"**{lead}: {_fmt(rows[0]['value'], unit)}** — {desc} [{d}]."
            )
        else:
            ranked = sorted(rows, key=lambda r: -r["value"])
            lines.append(
                t("ranks").format(
                    name=self._name(ranked[0]["category"]), v=_fmt(ranked[0]["value"], unit), desc=desc, d=d
                )
            )
            lines += [f"{i}. {self._name(r['category'])}: {_fmt(r['value'], unit)}" for i, r in enumerate(ranked, 1)]
        if data["notes"]:
            lines.append(f"*{t('note')}: {' '.join(data['notes'])}*")

        if passages:
            lines.append(f"\n### {t('research')}")
            prose = [p for p in passages if not p["text"].lstrip().startswith(("-", "*", "1."))]
            for p in prose[:3]:
                text = re.sub(r"\*Also covers:.*?\*\s*", "", p["text"]).replace("\n", " ")
                first = re.split(r"(?<=[.!?])\s", text.strip(), maxsplit=2)
                lines.append(f"- {' '.join(first[:2]).strip()} [{p['id']}]")
        if rec:
            text = rec[0]["text"].split("\n")[0]
            lines.append(f"\n### {t('so_what')}")
            lines.append(f"{text} [{rec[0]['id']}]")
        lines.append(f"\n*{t('footer')}*")
        return "\n".join(lines)


TEXT = {
    "en": {
        "by_segment": "**For {lead}, top answer by segment** — {desc} [{d}]:",
        "leads": "**{opt} leads for {lead}**, cited by {v} of buyers [{d}].",
        "hi_lo": "**{name}: highest among {hi} ({hv}), lowest among {lo} ({lv})** [{d}].",
        "ranks": "**{name} ranks first at {v}** — {desc} [{d}].",
        "note": "Note",
        "research": "What the research says",
        "so_what": "So what for marketers",
        "footer": "Offline analyst mode: answer assembled by rules from retrieved evidence. "
        "Configure `ANTHROPIC_API_KEY` for the full Claude agent.",
        "unmapped": "I could not map this question to one of the categories. Try naming one, e.g. "
        "*skincare*, *sneakers*, *electric vehicles* or *energy drinks*.",
    },
    "fr": {
        "by_segment": "**{lead} : réponse principale par segment** — {desc} [{d}] :",
        "leads": "**{opt} arrive en tête pour {lead}**, cité par {v} des acheteurs [{d}].",
        "hi_lo": "**{name} : le plus élevé chez {hi} ({hv}), le plus faible chez {lo} ({lv})** [{d}].",
        "ranks": "**{name} arrive en tête avec {v}** — {desc} [{d}].",
        "note": "Remarque",
        "research": "Ce que disent les études",
        "so_what": "Implications marketing",
        "footer": "Mode analyste hors ligne : réponse assemblée par règles à partir des preuves retrouvées "
        "(extraits d'études en anglais). Configurez `ANTHROPIC_API_KEY` pour l'agent Claude complet.",
        "unmapped": "Je n'ai pas pu relier cette question à une catégorie. Essayez d'en nommer une, par exemple "
        "*soins du visage*, *sneakers*, *voitures électriques* ou *boissons énergisantes*.",
    },
}
METRIC_FR = {
    "penetration": "Part des 16-29 ans ayant acheté dans la catégorie sur 12 mois",
    "avg_monthly_spend": "Dépense mensuelle moyenne (€) des acheteurs",
    "annual_spend_per_capita": "Dépense annuelle (€) par jeune de la génération Z",
    "channel_mix": "Répartition des acheteurs par canal d'achat principal",
    "discovery_mix": "Répartition des acheteurs selon le lieu de découverte",
    "driver_mix": "Répartition des acheteurs par motivation principale",
    "product_mix": "Répartition des acheteurs par type de produit",
    "sustainable_premium_rate": "Part des acheteurs prêts à payer plus pour une option durable",
    "dupe_rate": "Part des acheteurs ayant acheté un « dupe »",
    "brand_loyalty_rate": "Part des acheteurs fidèles à une marque",
    "price_decisive_rate": "Part des acheteurs pour qui le prix est décisif",
}
OPTION_FR = {
    "tiktok_shop": "TikTok Shop",
    "instagram": "Instagram",
    "marketplace": "Marketplaces en ligne",
    "brand_dtc": "Site / appli de la marque",
    "physical_store": "Magasin physique",
    "resale": "Applis de revente",
    "subscription": "Abonnement",
    "tiktok": "TikTok",
    "youtube": "YouTube",
    "friends": "Amis & famille",
    "search": "Moteurs de recherche",
    "in_store": "En magasin",
    "price": "Prix / rapport qualité-prix",
    "quality": "Qualité & durabilité",
    "creator": "Recommandation de créateur",
    "aesthetic": "Esthétique & expression de soi",
    "sustainability": "Durabilité",
    "identity": "Identité de marque",
    "convenience": "Praticité",
    "novelty": "Nouveauté & tendances",
    "performance": "Performance",
    "health": "Bénéfices santé",
    "community": "Communauté",
    "exclusivity": "Exclusivité & drops",
}
SEGMENT_FR = {
    "FR": "France",
    "UK": "Royaume-Uni",
    "DE": "Allemagne",
    "ES": "Espagne",
    "IT": "Italie",
    "US": "États-Unis",
    "female": "Femmes",
    "male": "Hommes",
    "non-binary": "Personnes non binaires",
    "low": "Revenus faibles",
    "mid": "Revenus moyens",
    "high": "Revenus élevés",
    True: "Urbains",
    False: "Non urbains",
    "16-19": "16-19 ans",
    "20-24": "20-24 ans",
    "25-29": "25-29 ans",
}


__all__ = ["OfflineAnalyst", "detect_categories", "GROUPS"]
