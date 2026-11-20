"""Simulates the Gen Z consumer panel (respondent-level microdata).

The simulation is deterministic (fixed seed) and calibrated so that the overall purchase
rate of each category matches `spec.Category.penetration`, while segments (age, gender,
country, income) differ in plausible, documented ways.

Run: `uv run python -m app.corpus.survey`
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import duckdb
import numpy as np

from app.config import settings
from app.corpus.spec import CATEGORIES, CHANNELS, DISCOVERY, DRIVERS, Category

SEED = 2026
N_RESPONDENTS = 6000

COUNTRIES = {"FR": 0.22, "UK": 0.18, "DE": 0.18, "ES": 0.14, "IT": 0.13, "US": 0.15}
COUNTRY_SPEND = {"US": 1.25, "UK": 1.10, "DE": 1.05, "FR": 1.00, "IT": 0.90, "ES": 0.88}
GENDERS = {"female": 0.49, "male": 0.47, "non-binary": 0.04}
INCOME_SPEND = {"low": 0.80, "mid": 1.00, "high": 1.35}

# Channels/discovery sources that skew younger (16-19) vs older (25-29).
YOUNG_CHANNELS = {"tiktok_shop": 1.35, "instagram": 1.2, "resale": 1.1}
OLD_CHANNELS = {"brand_dtc": 1.15, "marketplace": 1.15, "subscription": 1.1}
YOUNG_DISCOVERY = {"tiktok": 1.3, "instagram": 1.1}
OLD_DISCOVERY = {"search": 1.25, "youtube": 1.1, "in_store": 1.05}


def age_band(age: int) -> str:
    if age <= 19:
        return "16-19"
    if age <= 24:
        return "20-24"
    return "25-29"


def _logit(p: float) -> float:
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def _sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def _calibrate(base_effect: np.ndarray, target: float) -> float:
    """Find the intercept so that mean(sigmoid(intercept + effects)) == target."""
    lo, hi = -10.0, 10.0
    for _ in range(60):
        mid = (lo + hi) / 2
        if _sigmoid(mid + base_effect).mean() < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _weighted_choice(rng: np.random.Generator, keys: list[str], weights: np.ndarray) -> str:
    w = weights / weights.sum()
    return keys[int(rng.choice(len(keys), p=w))]


def simulate(out_dir: Path) -> tuple[Path, Path]:
    rng = np.random.default_rng(SEED)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ── Respondents ──────────────────────────────────────────────────────────
    n = N_RESPONDENTS
    countries = rng.choice(list(COUNTRIES), size=n, p=list(COUNTRIES.values()))
    genders = rng.choice(list(GENDERS), size=n, p=list(GENDERS.values()))
    ages = rng.integers(16, 30, size=n)
    age_z = (ages - 22.5) / 6.5  # roughly -1 (16) ... +1 (29)
    income_p_high = np.clip(0.08 + 0.02 * (ages - 16), 0.05, 0.38)
    income_p_low = np.clip(0.55 - 0.025 * (ages - 16), 0.18, 0.6)
    u = rng.random(n)
    incomes = np.where(u < income_p_low, "low", np.where(u > 1 - income_p_high, "high", "mid"))
    urban = rng.random(n) < 0.72
    gender_sign = np.where(genders == "female", 1.0, np.where(genders == "male", -1.0, 0.3))
    income_eff = np.where(incomes == "high", 0.25, np.where(incomes == "low", -0.2, 0.0))

    resp_path = out_dir / "respondents.csv"
    with resp_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["respondent_id", "country", "gender", "age", "age_band", "income_band", "urban"])
        for i in range(n):
            w.writerow(
                [i + 1, countries[i], genders[i], int(ages[i]), age_band(int(ages[i])), incomes[i], bool(urban[i])]
            )

    # ── Purchases ────────────────────────────────────────────────────────────
    purch_path = out_dir / "purchases.csv"
    channel_keys = list(CHANNELS)
    discovery_keys = list(DISCOVERY)
    driver_keys = list(DRIVERS)
    with purch_path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(
            [
                "respondent_id",
                "category",
                "monthly_spend_eur",
                "channel",
                "discovery",
                "top_driver",
                "pays_sustainable_premium",
                "bought_dupe",
                "brand_loyal",
                "price_decisive",
            ]
        )
        for cat in CATEGORIES:
            _simulate_category(
                rng,
                w,
                cat,
                countries,
                gender_sign,
                age_z,
                income_eff,
                incomes,
                channel_keys,
                discovery_keys,
                driver_keys,
            )
    return resp_path, purch_path


def _simulate_category(
    rng,
    writer,
    cat: Category,
    countries,
    gender_sign,
    age_z,
    income_eff,
    incomes,
    channel_keys,
    discovery_keys,
    driver_keys,
) -> None:
    n = len(countries)
    # Deterministic, category-specific country effects (small, so totals stay calibrated).
    country_eff = {c: float(rng.normal(0, 0.18)) for c in COUNTRIES}
    if cat.slug == "secondhand-fashion":
        country_eff["FR"] += 0.45  # resale apps are especially entrenched in France
    if cat.slug in {"fast-fashion", "food-delivery"}:
        country_eff["US"] += 0.25
    effects = (
        0.9 * cat.gender_skew * gender_sign
        + 0.6 * cat.age_skew * age_z
        + income_eff * (0.5 + cat.monthly_spend / 60)
        + np.array([country_eff[c] for c in countries])
    )
    intercept = _calibrate(effects, cat.penetration)
    bought = rng.random(n) < _sigmoid(intercept + effects)

    ch_w = np.array([cat.channels.get(k, 0.0) for k in channel_keys], dtype=float)
    ds_w = np.array([cat.discovery.get(k, 0.0) for k in discovery_keys], dtype=float)
    young_ch = np.array([YOUNG_CHANNELS.get(k, 1.0) for k in channel_keys])
    old_ch = np.array([OLD_CHANNELS.get(k, 1.0) for k in channel_keys])
    young_ds = np.array([YOUNG_DISCOVERY.get(k, 1.0) for k in discovery_keys])
    old_ds = np.array([OLD_DISCOVERY.get(k, 1.0) for k in discovery_keys])
    driver_w = {cat.drivers[0]: 0.40, cat.drivers[1]: 0.28, cat.drivers[2]: 0.18}
    sigma = 0.55

    for i in np.flatnonzero(bought):
        z = float(age_z[i])
        young = max(-z, 0.0)
        old = max(z, 0.0)
        ch = ch_w * (1 + (young_ch - 1) * young) * (1 + (old_ch - 1) * old)
        ds = ds_w * (1 + (young_ds - 1) * young) * (1 + (old_ds - 1) * old)
        mult = COUNTRY_SPEND[countries[i]] * INCOME_SPEND[incomes[i]] * (1 + 0.08 * z)
        mean = cat.monthly_spend * mult
        spend = float(rng.lognormal(math.log(mean) - sigma**2 / 2, sigma))

        if rng.random() < 0.86:
            keys = list(driver_w)
            driver = keys[int(rng.choice(3, p=np.array(list(driver_w.values())) / 0.86))]
        else:
            driver = driver_keys[int(rng.integers(len(driver_keys)))]

        g = gender_sign[i]
        p_sust = cat.sustainability * (1 + 0.12 * g) * (1.15 if incomes[i] == "high" else 1.0)
        p_dupe = cat.dupe_rate * (1 + 0.15 * young - 0.1 * old)
        p_price = cat.price_sensitivity * (1.15 if incomes[i] == "low" else 0.8 if incomes[i] == "high" else 1.0)
        writer.writerow(
            [
                i + 1,
                cat.slug,
                round(spend, 2),
                _weighted_choice(rng, channel_keys, ch),
                _weighted_choice(rng, discovery_keys, ds),
                driver,
                bool(rng.random() < min(p_sust, 0.97)),
                bool(rng.random() < min(p_dupe, 0.97)),
                bool(rng.random() < cat.loyalty),
                bool(rng.random() < min(p_price, 0.97)),
            ]
        )


def build_parquet(out_dir: Path) -> None:
    resp, purch = simulate(out_dir)
    con = duckdb.connect()
    for name, path in (("respondents", resp), ("purchases", purch)):
        con.execute(
            f"COPY (SELECT * FROM read_csv_auto('{path}')) TO '{out_dir / (name + '.parquet')}' "
            "(FORMAT PARQUET, COMPRESSION ZSTD)"
        )
        path.unlink()
    con.close()


if __name__ == "__main__":
    build_parquet(settings.data_dir / "survey")
    print(f"Survey written to {settings.data_dir / 'survey'}")
