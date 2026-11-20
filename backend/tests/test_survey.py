import pytest

from app.corpus.spec import CATEGORIES
from app.survey import SurveyQueryError


def test_penetration_is_calibrated_to_spec(store):
    rows = store.query("penetration", [c.slug for c in CATEGORIES[:12]]).rows
    for c, r in zip(CATEGORIES[:12], rows, strict=True):
        assert abs(r["value"] - c.penetration * 100) < 3, c.slug


def test_mix_shares_sum_to_100(store):
    rows = store.query("channel_mix", ["sneakers"]).rows
    assert abs(sum(r["value"] for r in rows) - 100) < 0.6


def test_breakdown_and_filters(store):
    res = store.query("penetration", ["skincare"], breakdown="gender", filters={"country": ["FR"]})
    assert {r["segment"] for r in res.rows} == {"female", "male", "non-binary"}
    assert res.notes  # non-binary in one country is a low base


def test_gender_skew_matches_spec(store):
    rows = {r["segment"]: r["value"] for r in store.query("penetration", ["nail-care"], breakdown="gender").rows}
    assert rows["female"] > rows["male"] + 20


@pytest.mark.parametrize(
    "kwargs",
    [
        {"metric": "nope", "categories": ["skincare"]},
        {"metric": "penetration", "categories": ["unknown"]},
        {"metric": "penetration", "categories": ["skincare"], "breakdown": "shoe_size"},
        {"metric": "penetration", "categories": ["skincare"], "filters": {"country": ["XX"]}},
        {"metric": "penetration", "categories": ["skincare"], "filters": {"religion": "x"}},
    ],
)
def test_invalid_queries_raise(store, kwargs):
    with pytest.raises(SurveyQueryError):
        store.query(**kwargs)
