"""Renders the research corpus (Markdown reports) from the spec + simulated panel.

Produces 50 category reports, 9 sector reports, 5 thematic reports and a methodology note.
All figures are computed from the panel, so text and survey queries never disagree.

Run: `uv run python -m app.corpus.reports`
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from statistics import mean

from app.config import settings
from app.corpus.spec import BY_SLUG, CATEGORIES, DRIVERS, GROUPS, Category
from app.survey import SurveyStore

PUBLISHER = "Northwind Insights (fictional)"
WAVE = "Gen Z Consumer Panel, Wave 2026"
DATE = "2026-09-15"
DISCLAIMER = (
    "> **Synthetic data notice.** This report is part of a fictional demo corpus generated for "
    "Zentrend. Figures come from a simulated panel and must not be used for real decisions."
)
COUNTRY_NAMES = {"FR": "France", "UK": "the UK", "DE": "Germany", "ES": "Spain", "IT": "Italy", "US": "the US"}


def _pick(key: str, options: list[str]) -> str:
    h = int(hashlib.sha1(key.encode()).hexdigest(), 16)
    return options[h % len(options)]


def _pct(v: float) -> str:
    return f"{v:.0f}%" if v >= 10 else f"{v:.1f}%"


def _eur(v: float) -> str:
    return f"€{v:,.0f}"


def _front_matter(**kv) -> str:
    lines = ["---"]
    for k, v in kv.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines)


def _growth_phrase(g: float) -> str:
    if g >= 15:
        return f"one of the fastest-growing categories in the panel (+{g:.1f}% spend vs the 2025 wave)"
    if g >= 7:
        return f"growing solidly (+{g:.1f}% spend vs the 2025 wave)"
    if g >= 2:
        return f"growing modestly (+{g:.1f}% spend vs the 2025 wave)"
    if g > -2:
        return f"broadly flat ({g:+.1f}% spend vs the 2025 wave)"
    return f"in decline ({g:+.1f}% spend vs the 2025 wave)"


class CorpusBuilder:
    def __init__(self, store: SurveyStore) -> None:
        self.s = store
        self.kpis = {k["slug"]: k for k in store.category_kpis()}
        self.panel_avg = {
            m: mean(k[m] for k in self.kpis.values())
            for m in (
                "penetration",
                "sustainable_premium_rate",
                "dupe_rate",
                "brand_loyalty_rate",
                "price_decisive_rate",
                "avg_monthly_spend",
            )
        }

    # ── helpers ──────────────────────────────────────────────────────────────
    def _seg(self, metric: str, slug: str, dim: str) -> list[dict]:
        return self.s.query(metric, [slug], breakdown=dim).rows

    def _mix(self, metric: str, slug: str, **filters) -> list[dict]:
        return self.s.query(metric, [slug], filters=filters).rows

    def _vs_avg(self, value: float, metric: str) -> str:
        avg = self.panel_avg[metric]
        diff = value - avg
        if abs(diff) < 3:
            return f"in line with the panel average of {_pct(avg)}"
        word = "above" if diff > 0 else "below"
        return f"{abs(diff):.0f} points {word} the panel average of {_pct(avg)}"

    # ── category report ──────────────────────────────────────────────────────
    def category_report(self, cat: Category) -> str:
        k = self.kpis[cat.slug]
        gender = {r["segment"]: r["value"] for r in self._seg("penetration", cat.slug, "gender")}
        ages = {r["segment"]: r["value"] for r in self._seg("penetration", cat.slug, "age_band")}
        countries = sorted(self._seg("penetration", cat.slug, "country"), key=lambda r: -r["value"])
        spend_c = sorted(self._seg("avg_monthly_spend", cat.slug, "country"), key=lambda r: -r["value"])
        income = {r["segment"]: r["value"] for r in self._seg("penetration", cat.slug, "income_band")}
        disc = self._mix("discovery_mix", cat.slug)
        chan = self._mix("channel_mix", cat.slug)
        drivers = self._mix("driver_mix", cat.slug)
        disc_young = {r["option_key"]: r["value"] for r in self._mix("discovery_mix", cat.slug, age_band="16-19")}
        disc_old = {r["option_key"]: r["value"] for r in self._mix("discovery_mix", cat.slug, age_band="25-29")}
        chan_young = {r["option_key"]: r["value"] for r in self._mix("channel_mix", cat.slug, age_band="16-19")}
        chan_old = {r["option_key"]: r["value"] for r in self._mix("channel_mix", cat.slug, age_band="25-29")}

        title = f"{cat.name}: Gen Z Category Report 2026"
        aliases = ", ".join(cat.aliases)
        opener = _pick(
            cat.slug,
            [
                f"{_pct(k['penetration'])} of Gen Z consumers bought {cat.name.lower()} in the last twelve months",
                f"{cat.name} reached {_pct(k['penetration'])} of Gen Z consumers over the last twelve months",
                f"Over the past year, {_pct(k['penetration'])} of the Gen Z panel purchased {cat.name.lower()}",
            ],
        )
        f_gap = gender.get("female", 0) - gender.get("male", 0)
        if abs(f_gap) < 4:
            gender_line = (
                f"Purchase is balanced by gender (women {_pct(gender.get('female', 0))}, "
                f"men {_pct(gender.get('male', 0))})."
            )
        else:
            lead, lag = ("women", "men") if f_gap > 0 else ("men", "women")
            gender_line = (
                f"The category skews towards {lead}: {_pct(max(gender['female'], gender['male']))} "
                f"of {lead} bought versus {_pct(min(gender['female'], gender['male']))} of {lag}."
            )
        a_gap = ages.get("25-29", 0) - ages.get("16-19", 0)
        if abs(a_gap) < 4:
            age_line = (
                f"Penetration is similar across age bands (16-19: {_pct(ages['16-19'])}, 25-29: {_pct(ages['25-29'])})."
            )
        elif a_gap > 0:
            age_line = (
                f"It is an older-Gen Z category: penetration rises from {_pct(ages['16-19'])} among 16-19 "
                f"year-olds to {_pct(ages['25-29'])} among 25-29 year-olds."
            )
        else:
            age_line = (
                f"It is driven by younger Gen Z: {_pct(ages['16-19'])} of 16-19 year-olds bought, "
                f"against {_pct(ages['25-29'])} of 25-29 year-olds."
            )
        top_c, low_c = countries[0], countries[-1]
        top_sp = spend_c[0]

        lines = [
            _front_matter(
                id=f"cat-{cat.slug}",
                title=title,
                type="category_report",
                category=cat.slug,
                group=cat.group,
                publisher=PUBLISHER,
                wave=WAVE,
                date=DATE,
                synthetic="true",
            ),
            f"# {title}",
            DISCLAIMER,
            f"*Also covers: {aliases}. Sector: {GROUPS[cat.group]}.*",
            "## Executive summary",
            f"{opener}, spending an average of {_eur(k['avg_monthly_spend'])} per month. "
            f"The category is {_growth_phrase(cat.yoy_growth)}. {cat.insight}",
            "## Market snapshot",
            "\n".join(
                [
                    f"- Penetration (bought in last 12 months): {_pct(k['penetration'])}",
                    f"- Average monthly spend among buyers: {_eur(k['avg_monthly_spend'])}",
                    f"- Annualised spend per Gen Z consumer: {_eur(k['annual_spend_per_capita'])}",
                    f"- Spend growth vs 2025 wave: {cat.yoy_growth:+.1f}%",
                    f"- Buyers in panel: {k['buyers']:,} of {self.s.n_respondents:,} respondents",
                ]
            ),
            "## Who buys",
            f"{gender_line} {age_line} By market, penetration is highest in "
            f"{COUNTRY_NAMES[top_c['segment']]} ({_pct(top_c['value'])}) and lowest in "
            f"{COUNTRY_NAMES[low_c['segment']]} ({_pct(low_c['value'])}). Buyers in "
            f"{COUNTRY_NAMES[top_sp['segment']]} spend the most ({_eur(top_sp['value'])} per month). "
            f"Among high-income respondents penetration reaches {_pct(income.get('high', 0))}, "
            f"compared with {_pct(income.get('low', 0))} in the low-income band.",
            "## Path to purchase",
            f"Discovery is led by {disc[0]['option']} ({_pct(disc[0]['value'])} of buyers), followed by "
            f"{disc[1]['option']} ({_pct(disc[1]['value'])}) and {disc[2]['option']} ({_pct(disc[2]['value'])}). "
            f"TikTok accounts for {_pct(disc_young.get('tiktok', 0))} of first discoveries among 16-19 "
            f"year-olds versus {_pct(disc_old.get('tiktok', 0))} among 25-29 year-olds, while search engines "
            f"matter more for the older group ({_pct(disc_old.get('search', 0))} vs {_pct(disc_young.get('search', 0))}).",
            f"The main purchase channel is {chan[0]['option']} ({_pct(chan[0]['value'])}), then "
            f"{chan[1]['option']} ({_pct(chan[1]['value'])})"
            + (f" and {chan[2]['option']} ({_pct(chan[2]['value'])})." if len(chan) > 2 else ".")
            + (
                f" Social commerce through TikTok Shop reaches {_pct(chan_young.get('tiktok_shop', 0))} of "
                f"purchases among the youngest buyers, against {_pct(chan_old.get('tiktok_shop', 0))} among "
                f"25-29 year-olds."
                if chan_young.get("tiktok_shop", 0) >= 8
                else ""
            ),
            "## Purchase drivers and barriers",
            f"The top purchase driver is {drivers[0]['option'].lower()} ({_pct(drivers[0]['value'])} of buyers "
            f"cite it first), ahead of {drivers[1]['option'].lower()} ({_pct(drivers[1]['value'])}) and "
            f"{drivers[2]['option'].lower()} ({_pct(drivers[2]['value'])}). "
            f"Price is the decisive factor for {_pct(k['price_decisive_rate'])} of buyers, "
            f"{self._vs_avg(k['price_decisive_rate'], 'price_decisive_rate')}. "
            f"The main barriers reported in open answers are {cat.barriers[0]} and {cat.barriers[1]}.",
            "## Values: sustainability, dupes and loyalty",
            f"{_pct(k['sustainable_premium_rate'])} of buyers say they would pay more for a sustainable option "
            f"({self._vs_avg(k['sustainable_premium_rate'], 'sustainable_premium_rate')}). "
            f"{_pct(k['dupe_rate'])} bought a dupe or lookalike product in the last year "
            f"({self._vs_avg(k['dupe_rate'], 'dupe_rate')}), and {_pct(k['brand_loyalty_rate'])} usually "
            f"repurchase the same brand ({self._vs_avg(k['brand_loyalty_rate'], 'brand_loyalty_rate')}).",
            "## Products Gen Z buys",
            self._products_section(cat),
            "## Trends to watch",
            "\n".join(f"- **{t.capitalize()}**" for t in cat.trends) or "- No specific trend flagged.",
            "## Implications for marketers",
            cat.recommendation,
            "\n".join(
                [
                    f"- Prioritise {disc[0]['option']} for awareness: it is the first discovery source for "
                    f"{_pct(disc[0]['value'])} of buyers.",
                    f"- Build the offer around {drivers[0]['option'].lower()}, the most-cited driver.",
                    f"- Plan conversion on {chan[0]['option']}, which carries {_pct(chan[0]['value'])} of purchases.",
                ]
            ),
        ]
        return "\n\n".join(lines) + "\n"

    def _products_section(self, cat: Category) -> str:
        prods = sorted(self.s.product_stats(cat.slug), key=lambda p: -p["share_of_category"])
        trend_word = {"rising": "rising", "steady": "stable", "cooling": "cooling"}
        lead = prods[0]
        young = max(prods, key=lambda p: p["share_16_19"])
        old = max(prods, key=lambda p: p["share_25_29"])
        lines = [
            f"Among {cat.name.lower()} buyers, the most common product type is {lead['name']} "
            f"({_pct(lead['share_of_category'])} of buyers). {young['name']} over-indexes with 16-19 year-olds "
            f"({_pct(young['share_16_19'])} of its buyers), while {old['name']} skews older "
            f"({_pct(old['share_25_29'])} aged 25-29).",
        ]
        for p in prods:
            lines.append(
                f"- **{p['name']}**: {_pct(p['share_of_category'])} of category buyers, typical price "
                f"{_eur(p['price'])}{'/month' if p['per_month'] else ''}, interest {trend_word[p['trend']]}, mostly bought via {p['top_channel']}."
            )
        return "\n".join(lines[:1]) + "\n\n" + "\n".join(lines[1:])

    # ── sector report ────────────────────────────────────────────────────────
    def group_report(self, group: str) -> str:
        cats = [c for c in CATEGORIES if c.group == group]
        ks = sorted((self.kpis[c.slug] for c in cats), key=lambda k: -k["penetration"])
        growth = sorted(cats, key=lambda c: -c.yoy_growth)
        slugs = [c.slug for c in cats]
        chan = self.s.query("channel_mix", slugs).rows
        by_cat_top = {}
        for r in chan:
            by_cat_top.setdefault(r["category"], r)
        driver_counts: dict[str, int] = {}
        for c in cats:
            driver_counts[c.drivers[0]] = driver_counts.get(c.drivers[0], 0) + 1
        top_driver = max(driver_counts, key=driver_counts.get)
        name = GROUPS[group]
        title = f"{name}: Gen Z Sector Overview 2026"
        lines = [
            _front_matter(
                id=f"sector-{group}",
                title=title,
                type="sector_report",
                group=group,
                categories=slugs,
                publisher=PUBLISHER,
                wave=WAVE,
                date=DATE,
                synthetic="true",
            ),
            f"# {title}",
            DISCLAIMER,
            "## Overview",
            f"The {name} sector covers {len(cats)} categories in this panel: " + ", ".join(c.name for c in cats) + ". "
            f"The most widely bought is {ks[0]['name']} ({_pct(ks[0]['penetration'])} penetration), while "
            f"{ks[-1]['name']} is the most niche ({_pct(ks[-1]['penetration'])}). "
            f"The fastest-growing category is {growth[0].name} ({growth[0].yoy_growth:+.1f}% spend), and the "
            f"weakest is {growth[-1].name} ({growth[-1].yoy_growth:+.1f}%).",
            "## Category ranking by penetration",
            "\n".join(
                f"{i}. {k['name']}: {_pct(k['penetration'])} penetration, {_eur(k['avg_monthly_spend'])}/month, "
                f"{k['yoy_growth']:+.1f}% growth"
                for i, k in enumerate(ks, 1)
            ),
            "## Channels",
            "Main purchase channel per category: "
            + "; ".join(f"{BY_SLUG[s].name} — {r['option']} ({_pct(r['value'])})" for s, r in by_cat_top.items())
            + ".",
            "## What drives purchase",
            f"Across the sector, {DRIVERS[top_driver].lower()} is the most common lead driver "
            f"({driver_counts[top_driver]} of {len(cats)} categories). "
            + " ".join(f"{c.name}: {c.insight}" for c in growth[:2]),
        ]
        return "\n\n".join(lines) + "\n"

    # ── thematic reports ─────────────────────────────────────────────────────
    def _ranking(self, metric: str, n: int = 10, reverse: bool = True) -> list[dict]:
        return sorted(self.kpis.values(), key=lambda k: k[metric], reverse=reverse)[:n]

    def thematic_reports(self) -> dict[str, str]:
        docs: dict[str, str] = {}
        all_slugs = list(self.kpis)

        # Social commerce
        tt_rows = [r for r in self.s.query("channel_mix", all_slugs[:12]).rows]
        for i in range(12, 50, 12):
            tt_rows += self.s.query("channel_mix", all_slugs[i : i + 12]).rows
        tts = sorted((r for r in tt_rows if r["option_key"] == "tiktok_shop"), key=lambda r: -r["value"])
        disc_rows = []
        for i in range(0, 50, 12):
            disc_rows += self.s.query("discovery_mix", all_slugs[i : i + 12]).rows
        ttd = sorted((r for r in disc_rows if r["option_key"] == "tiktok"), key=lambda r: -r["value"])
        docs["theme-social-commerce"] = self._theme(
            "theme-social-commerce",
            "Social Commerce and the TikTok Effect",
            [
                (
                    "Summary",
                    f"TikTok is the single most important discovery source for Gen Z in this panel. It is the "
                    f"first discovery source for {_pct(ttd[0]['value'])} of {BY_SLUG[ttd[0]['category']].name.lower()} "
                    f"buyers, and TikTok Shop has become a meaningful checkout channel in beauty and accessories.",
                ),
                (
                    "Where TikTok drives discovery",
                    "\n".join(
                        f"- {BY_SLUG[r['category']].name}: {_pct(r['value'])} of buyers discovered via TikTok"
                        for r in ttd[:10]
                    ),
                ),
                (
                    "Where TikTok Shop converts",
                    "\n".join(
                        f"- {BY_SLUG[r['category']].name}: {_pct(r['value'])} of purchases on TikTok Shop"
                        for r in tts[:8]
                    ),
                ),
                (
                    "Implications",
                    "Discovery and checkout are collapsing into the same feed for low-ticket, visual categories. "
                    "Brands should plan creator content as a sales channel with its own merchandising, pricing and "
                    "stock planning, while high-consideration categories (tech, finance, travel) still rely on "
                    "YouTube reviews and search.",
                ),
            ],
        )
        # Sustainability
        sust = self._ranking("sustainable_premium_rate")
        low_sust = self._ranking("sustainable_premium_rate", 5, reverse=False)
        ff = self.kpis["fast-fashion"]
        docs["theme-sustainability"] = self._theme(
            "theme-sustainability",
            "The Sustainability Say-Do Gap",
            [
                (
                    "Summary",
                    f"On average {_pct(self.panel_avg['sustainable_premium_rate'])} of buyers say they would pay a "
                    f"premium for a sustainable option, but willingness varies strongly by category. Fast fashion "
                    f"illustrates the gap: it still reaches {_pct(ff['penetration'])} of Gen Z although only "
                    f"{_pct(ff['sustainable_premium_rate'])} of its buyers would pay more for sustainability.",
                ),
                (
                    "Highest willingness to pay for sustainability",
                    "\n".join(f"- {k['name']}: {_pct(k['sustainable_premium_rate'])}" for k in sust),
                ),
                (
                    "Lowest willingness to pay",
                    "\n".join(f"- {k['name']}: {_pct(k['sustainable_premium_rate'])}" for k in low_sust),
                ),
                (
                    "Implications",
                    "Sustainability converts when it is tangible and personal — resale, reusables, refills — and "
                    "rarely when it is an abstract claim. Circular models (trade-in, resale credit) let Gen Z act "
                    "on values without paying more.",
                ),
            ],
        )
        # Dupes
        dupes = self._ranking("dupe_rate")
        docs["theme-dupe-culture"] = self._theme(
            "theme-dupe-culture",
            "Dupe Culture: Lookalikes Go Mainstream",
            [
                (
                    "Summary",
                    f"Buying a 'dupe' — a cheaper lookalike of a popular product — is now normal. Across categories "
                    f"an average of {_pct(self.panel_avg['dupe_rate'])} of buyers bought one in the last year, rising "
                    f"to {_pct(dupes[0]['dupe_rate'])} in {dupes[0]['name'].lower()}.",
                ),
                (
                    "Categories with the highest dupe rates",
                    "\n".join(f"- {k['name']}: {_pct(k['dupe_rate'])} bought a dupe" for k in dupes),
                ),
                (
                    "Implications",
                    "Dupes are discovered in the same content as the originals. Prestige brands defend with "
                    "performance proof, refills and entry price points; mass brands that invest in original design "
                    "can escape comparison content.",
                ),
            ],
        )
        # Loyalty
        loyal = self._ranking("brand_loyalty_rate")
        fickle = self._ranking("brand_loyalty_rate", 8, reverse=False)
        docs["theme-loyalty"] = self._theme(
            "theme-loyalty",
            "Brand Loyalty and Switching",
            [
                (
                    "Summary",
                    f"Gen Z is often described as disloyal, but loyalty depends on the category. The average repurchase "
                    f"rate is {_pct(self.panel_avg['brand_loyalty_rate'])}; it peaks in ecosystem and habit categories "
                    f"such as {loyal[0]['name'].lower()} ({_pct(loyal[0]['brand_loyalty_rate'])}) and is lowest in "
                    f"trend-led categories like {fickle[0]['name'].lower()} ({_pct(fickle[0]['brand_loyalty_rate'])}).",
                ),
                ("Most loyal categories", "\n".join(f"- {k['name']}: {_pct(k['brand_loyalty_rate'])}" for k in loyal)),
                (
                    "Least loyal categories",
                    "\n".join(f"- {k['name']}: {_pct(k['brand_loyalty_rate'])}" for k in fickle),
                ),
                (
                    "Implications",
                    "In low-loyalty categories, win the next purchase through constant novelty and creator presence; "
                    "in high-loyalty categories, invest in onboarding the first purchase, because it locks in years.",
                ),
            ],
        )
        # Wallet
        wallet = self._ranking("annual_spend_per_capita", 12)
        growth = sorted(CATEGORIES, key=lambda c: -c.yoy_growth)
        docs["theme-wallet-share"] = self._theme(
            "theme-wallet-share",
            "Where the Gen Z Wallet Goes",
            [
                (
                    "Summary",
                    f"Ranked by annual spend per Gen Z consumer, {wallet[0]['name']} "
                    f"({_eur(wallet[0]['annual_spend_per_capita'])} a year) and {wallet[1]['name']} "
                    f"({_eur(wallet[1]['annual_spend_per_capita'])}) take the largest share of wallet. "
                    f"Growth is concentrated in experiences, resale and wellness.",
                ),
                (
                    "Largest share of wallet (annual spend per consumer)",
                    "\n".join(f"- {k['name']}: {_eur(k['annual_spend_per_capita'])}" for k in wallet),
                ),
                ("Fastest-growing categories", "\n".join(f"- {c.name}: {c.yoy_growth:+.1f}%" for c in growth[:10])),
                ("Declining categories", "\n".join(f"- {c.name}: {c.yoy_growth:+.1f}%" for c in growth[-5:])),
            ],
        )
        return docs

    def _theme(self, doc_id: str, title: str, sections: list[tuple[str, str]]) -> str:
        parts = [
            _front_matter(
                id=doc_id,
                title=title,
                type="thematic_report",
                publisher=PUBLISHER,
                wave=WAVE,
                date=DATE,
                synthetic="true",
            ),
            f"# {title}",
            DISCLAIMER,
        ]
        for heading, body in sections:
            parts += [f"## {heading}", body]
        return "\n\n".join(parts) + "\n"

    def methodology(self) -> str:
        demo = self.s.demographics()

        def fmt(dim):
            return ", ".join(f"{r['segment']} {r['n']:,}" for r in demo[dim])

        return (
            "\n\n".join(
                [
                    _front_matter(
                        id="methodology",
                        title="Panel Methodology",
                        type="methodology",
                        publisher=PUBLISHER,
                        wave=WAVE,
                        date=DATE,
                        synthetic="true",
                    ),
                    "# Panel Methodology",
                    DISCLAIMER,
                    "## Sample",
                    f"The panel covers {self.s.n_respondents:,} respondents aged 16 to 29 across six markets "
                    f"(France, the UK, Germany, Spain, Italy and the US). Country split: {fmt('country')}. "
                    f"Gender: {fmt('gender')}. Age bands: {fmt('age_band')}. Income bands: {fmt('income_band')}.",
                    "## Questions",
                    "For each of 50 product categories, respondents reported whether they bought in the last 12 months, "
                    "their average monthly spend, main purchase channel, where they first discovered the product, their "
                    "top purchase driver, and whether they would pay a premium for sustainability, bought a dupe, "
                    "usually repurchase the same brand, and whether price was decisive.",
                    "## Definitions",
                    "- Penetration: share of all respondents who bought in the category in the last 12 months.\n"
                    "- Average monthly spend: mean spend among buyers, in euros.\n"
                    "- Annualised spend per consumer: total annual spend divided by all respondents.\n"
                    "- Growth: change in spend versus the 2025 wave.\n"
                    "- Low base: segments with fewer than 80 respondents are directional only.",
                    "## Limitations",
                    "This panel is simulated. Distributions were calibrated by hand to be plausible, and segments differ "
                    "according to documented assumptions (age, gender, income and country effects). It demonstrates the "
                    "Zentrend platform and is not market evidence.",
                ]
            )
            + "\n"
        )

    # ── build ────────────────────────────────────────────────────────────────
    def build(self, out_dir: Path) -> int:
        if out_dir.exists():
            shutil.rmtree(out_dir)
        (out_dir / "categories").mkdir(parents=True)
        (out_dir / "sectors").mkdir()
        (out_dir / "themes").mkdir()
        count = 0
        for cat in CATEGORIES:
            (out_dir / "categories" / f"{cat.slug}.md").write_text(self.category_report(cat))
            count += 1
        for g in GROUPS:
            (out_dir / "sectors" / f"{g}.md").write_text(self.group_report(g))
            count += 1
        for doc_id, text in self.thematic_reports().items():
            (out_dir / "themes" / f"{doc_id.removeprefix('theme-')}.md").write_text(text)
            count += 1
        (out_dir / "methodology.md").write_text(self.methodology())
        return count + 1


if __name__ == "__main__":
    n = CorpusBuilder(SurveyStore()).build(settings.corpus_dir)
    print(f"Wrote {n} documents to {settings.corpus_dir}")
