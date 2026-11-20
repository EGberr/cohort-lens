"""Safe, typed analytics over the Gen Z panel (DuckDB over Parquet).

The LLM never writes SQL. It picks a metric, categories, an optional breakdown and filters
from closed vocabularies; this module builds parameterised queries. Every result carries
its base size (n) and a low-base flag so the agent can caveat small samples.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

import duckdb

from app.config import settings
from app.corpus.spec import BY_SLUG, CHANNELS, DISCOVERY, DRIVERS, GROUPS

Metric = Literal[
    "penetration",
    "avg_monthly_spend",
    "annual_spend_per_capita",
    "channel_mix",
    "discovery_mix",
    "driver_mix",
    "sustainable_premium_rate",
    "dupe_rate",
    "brand_loyalty_rate",
    "price_decisive_rate",
]
Dimension = Literal["country", "gender", "age_band", "income_band", "urban"]

METRICS: dict[str, str] = {
    "penetration": "Share of Gen Z respondents who bought in the category in the last 12 months",
    "avg_monthly_spend": "Average monthly spend (EUR) among buyers",
    "annual_spend_per_capita": "Annualised spend (EUR) per Gen Z respondent, buyers and non-buyers",
    "channel_mix": "Share of buyers by main purchase channel",
    "discovery_mix": "Share of buyers by where they first discovered the product",
    "driver_mix": "Share of buyers by top purchase driver",
    "sustainable_premium_rate": "Share of buyers willing to pay more for a sustainable option",
    "dupe_rate": "Share of buyers who bought a dupe / lookalike product",
    "brand_loyalty_rate": "Share of buyers who repurchase the same brand",
    "price_decisive_rate": "Share of buyers for whom price was the decisive factor",
}
DIMENSIONS: tuple[str, ...] = ("country", "gender", "age_band", "income_band", "urban")
DIM_VALUES: dict[str, tuple[Any, ...]] = {
    "country": ("FR", "UK", "DE", "ES", "IT", "US"),
    "gender": ("female", "male", "non-binary"),
    "age_band": ("16-19", "20-24", "25-29"),
    "income_band": ("low", "mid", "high"),
    "urban": (True, False),
}
RATE_COLUMNS = {
    "sustainable_premium_rate": "pays_sustainable_premium",
    "dupe_rate": "bought_dupe",
    "brand_loyalty_rate": "brand_loyal",
    "price_decisive_rate": "price_decisive",
}
MIX_COLUMNS = {
    "channel_mix": ("channel", CHANNELS),
    "discovery_mix": ("discovery", DISCOVERY),
    "driver_mix": ("top_driver", DRIVERS),
}
LOW_BASE = 80


class SurveyQueryError(ValueError):
    """Raised for invalid metric/category/filter combinations (returned to the model)."""


@dataclass
class QueryResult:
    metric: str
    description: str
    unit: str
    rows: list[dict[str, Any]]
    filters: dict[str, Any]
    breakdown: str | None
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "description": self.description,
            "unit": self.unit,
            "breakdown": self.breakdown,
            "filters": self.filters,
            "rows": self.rows,
            "notes": self.notes,
        }


class SurveyStore:
    def __init__(self, survey_dir=None) -> None:
        survey_dir = survey_dir or settings.survey_dir
        self._con = duckdb.connect(database=":memory:")
        self._lock = threading.Lock()
        self._con.execute(f"CREATE TABLE respondents AS SELECT * FROM read_parquet('{survey_dir}/respondents.parquet')")
        self._con.execute(f"CREATE TABLE purchases AS SELECT * FROM read_parquet('{survey_dir}/purchases.parquet')")
        self._con.execute(
            "CREATE TABLE panel AS SELECT p.*, r.country, r.gender, r.age, r.age_band, "
            "r.income_band, r.urban FROM purchases p JOIN respondents r USING (respondent_id)"
        )
        self.n_respondents = self._scalar("SELECT count(*) FROM respondents")

    # ── low-level helpers ────────────────────────────────────────────────────
    def _rows(self, sql: str, params: list[Any] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            cur = self._con.execute(sql, params or [])
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, r, strict=True)) for r in cur.fetchall()]

    def _scalar(self, sql: str, params: list[Any] | None = None) -> Any:
        with self._lock:
            return self._con.execute(sql, params or []).fetchone()[0]

    @staticmethod
    def _where(filters: dict[str, Any], alias: str = "") -> tuple[str, list[Any]]:
        clauses, params = [], []
        prefix = f"{alias}." if alias else ""
        for dim, value in filters.items():
            if dim not in DIMENSIONS:
                raise SurveyQueryError(f"Unknown filter '{dim}'. Allowed: {', '.join(DIMENSIONS)}")
            values = value if isinstance(value, list) else [value]
            if dim == "urban":
                values = [v if isinstance(v, bool) else str(v).lower() == "true" for v in values]
            bad = [v for v in values if v not in DIM_VALUES[dim]]
            if bad:
                raise SurveyQueryError(f"Invalid value(s) {bad} for '{dim}'. Allowed: {list(DIM_VALUES[dim])}")
            clauses.append(f"{prefix}{dim} IN ({', '.join('?' for _ in values)})")
            params.extend(values)
        return (" AND ".join(clauses) or "TRUE"), params

    # ── public API ───────────────────────────────────────────────────────────
    def query(
        self,
        metric: str,
        categories: list[str],
        breakdown: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> QueryResult:
        filters = filters or {}
        if metric not in METRICS:
            raise SurveyQueryError(f"Unknown metric '{metric}'. Allowed: {', '.join(METRICS)}")
        if not categories:
            raise SurveyQueryError("Provide at least one category slug.")
        unknown = [c for c in categories if c not in BY_SLUG]
        if unknown:
            raise SurveyQueryError(f"Unknown category slug(s): {unknown}. Use list_categories.")
        if breakdown is not None and breakdown not in DIMENSIONS:
            raise SurveyQueryError(f"Unknown breakdown '{breakdown}'. Allowed: {DIMENSIONS}")
        if len(categories) > 12:
            raise SurveyQueryError("At most 12 categories per query.")

        where_r, params_r = self._where(filters)
        where_p, params_p = self._where(filters)
        cat_ph = ", ".join("?" for _ in categories)
        group_r = f", {breakdown}" if breakdown else ""
        sel_dim = f"{breakdown} AS segment, " if breakdown else ""
        notes: list[str] = []
        unit = "%"

        if metric in ("penetration", "annual_spend_per_capita"):
            # Base = all respondents in the segment (buyers and non-buyers).
            base_sql = (
                f"SELECT {sel_dim}count(*) AS base FROM respondents WHERE {where_r} "
                f"{'GROUP BY ' + breakdown if breakdown else ''}"
            )
            agg = "count(*)" if metric == "penetration" else "sum(monthly_spend_eur) * 12"
            num_sql = (
                f"SELECT category, {sel_dim}{agg} AS num FROM panel "
                f"WHERE category IN ({cat_ph}) AND {where_p} GROUP BY category{group_r}"
            )
            bases = {r.get("segment"): r["base"] for r in self._rows(base_sql, params_r)}
            nums = self._rows(num_sql, [*categories, *params_p])
            rows = []
            for cat in categories:
                for seg, base in sorted(bases.items(), key=lambda kv: str(kv[0])):
                    num = next((r["num"] for r in nums if r["category"] == cat and r.get("segment") == seg), 0) or 0
                    value = num / base * 100 if metric == "penetration" else num / base
                    row = {"category": cat, "value": round(value, 1), "n": int(base)}
                    if breakdown:
                        row["segment"] = seg
                    rows.append(row)
            unit = "%" if metric == "penetration" else "EUR / year"

        elif metric == "avg_monthly_spend" or metric in RATE_COLUMNS:
            expr = (
                "avg(monthly_spend_eur)"
                if metric == "avg_monthly_spend"
                else f"avg(CAST({RATE_COLUMNS[metric]} AS DOUBLE)) * 100"
            )
            sql = (
                f"SELECT category, {sel_dim}{expr} AS value, count(*) AS n FROM panel "
                f"WHERE category IN ({cat_ph}) AND {where_p} GROUP BY category{group_r} "
                f"ORDER BY category{group_r}"
            )
            rows = [
                {k: (round(v, 1) if k == "value" else v) for k, v in r.items()}
                for r in self._rows(sql, [*categories, *params_p])
            ]
            unit = "EUR / month" if metric == "avg_monthly_spend" else "%"

        else:  # mixes
            col, labels = MIX_COLUMNS[metric]
            sql = (
                f"SELECT category, {sel_dim}{col} AS option, count(*) AS cnt, "
                f"sum(count(*)) OVER (PARTITION BY category{group_r}) AS n FROM panel "
                f"WHERE category IN ({cat_ph}) AND {where_p} GROUP BY category{group_r}, {col} "
                f"ORDER BY category{group_r}, cnt DESC"
            )
            rows = []
            for r in self._rows(sql, [*categories, *params_p]):
                row = {
                    "category": r["category"],
                    "option": labels.get(r["option"], r["option"]),
                    "option_key": r["option"],
                    "value": round(r["cnt"] / r["n"] * 100, 1),
                    "n": int(r["n"]),
                }
                if breakdown:
                    row["segment"] = r["segment"]
                rows.append(row)

        low = sorted({str(r.get("segment", r["category"])) for r in rows if r["n"] < LOW_BASE})
        if low:
            notes.append(f"Low base (n < {LOW_BASE}) for: {', '.join(low)} — treat as directional.")
        if not rows:
            notes.append("No respondents match these filters.")
        return QueryResult(metric, METRICS[metric], unit, rows, filters, breakdown, notes)

    # ── convenience views used by the API and the report generator ───────────
    def category_kpis(self) -> list[dict[str, Any]]:
        sql = """
            SELECT category,
                   count(*) AS buyers,
                   avg(monthly_spend_eur) AS avg_spend,
                   avg(CAST(pays_sustainable_premium AS DOUBLE)) AS sustainable,
                   avg(CAST(bought_dupe AS DOUBLE)) AS dupe,
                   avg(CAST(brand_loyal AS DOUBLE)) AS loyalty,
                   avg(CAST(price_decisive AS DOUBLE)) AS price_decisive
            FROM panel GROUP BY category
        """
        out = []
        for r in self._rows(sql):
            spec = BY_SLUG[r["category"]]
            out.append(
                {
                    "slug": spec.slug,
                    "name": spec.name,
                    "group": spec.group,
                    "group_name": GROUPS[spec.group],
                    "penetration": round(r["buyers"] / self.n_respondents * 100, 1),
                    "avg_monthly_spend": round(r["avg_spend"], 1),
                    "annual_spend_per_capita": round(r["buyers"] * r["avg_spend"] * 12 / self.n_respondents, 1),
                    "yoy_growth": spec.yoy_growth,
                    "sustainable_premium_rate": round(r["sustainable"] * 100, 1),
                    "dupe_rate": round(r["dupe"] * 100, 1),
                    "brand_loyalty_rate": round(r["loyalty"] * 100, 1),
                    "price_decisive_rate": round(r["price_decisive"] * 100, 1),
                    "buyers": int(r["buyers"]),
                }
            )
        order = {c.slug: i for i, c in enumerate(BY_SLUG.values())}
        return sorted(out, key=lambda r: order[r["slug"]])

    def top_option(self, metric: str, category: str, **filters: Any) -> dict[str, Any]:
        rows = self.query(metric, [category], filters=filters).rows
        return rows[0] if rows else {}

    def demographics(self) -> dict[str, list[dict[str, Any]]]:
        out = {}
        for dim in DIMENSIONS:
            out[dim] = self._rows(
                f"SELECT {dim} AS segment, count(*) AS n FROM respondents GROUP BY {dim} ORDER BY {dim}"
            )
        return out


@lru_cache(maxsize=1)
def get_store() -> SurveyStore:
    return SurveyStore()
