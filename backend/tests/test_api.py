import json

from fastapi.testclient import TestClient

from app.main import app


def test_endpoints():
    with TestClient(app) as client:
        h = client.get("/api/health").json()
        assert h["analyst"] == "offline" and h["documents"] == 67
        ov = client.get("/api/overview").json()
        assert len(ov["categories"]) == 52 and len(ov["groups"]) == 9
        cat = client.get("/api/categories/skincare").json()
        assert cat["kpi"]["slug"] == "skincare" and cat["channel_mix"]
        assert client.get("/api/categories/nope").status_code == 404
        s = client.post("/api/search", json={"query": "dupes", "k": 3}).json()
        assert len(s["hits"]) == 3
        assert client.post("/api/survey", json={"metric": "x", "categories": ["skincare"]}).status_code == 400


def test_chat_streams_events():
    with (
        TestClient(app) as client,
        client.stream(
            "POST", "/api/chat", json={"messages": [{"role": "user", "content": "Why do Gen Z buy sneakers?"}]}
        ) as r,
    ):
        events = [json.loads(line[5:]) for line in r.iter_lines() if line.startswith("data:")]
    types = {e["type"] for e in events}
    assert {"tool_call", "source", "dataset", "text", "done"} <= types


def test_home_and_products():
    with TestClient(app) as client:
        home = client.get("/api/home").json()
        assert len(home["sectors"]) == 9 and home["products"] == 156
        assert all(p["trend"] == "rising" for p in home["trending_products"])
        assert len(home["hero_categories"]) == 4 and home["sectors"][0]["image"].startswith("/img/categories/")
        prods = client.get("/api/products", params={"category": "used-cars"}).json()
        assert len(prods) == 3
        assert abs(sum(p["share_of_category"] for p in prods) - 100) < 0.5
        detail = client.get(f"/api/products/{prods[0]['slug']}").json()
        assert detail["product"]["slug"] == prods[0]["slug"] and len(detail["siblings"]) == 2
        assert client.get("/api/products/nope").status_code == 404
        cat = client.get("/api/categories/electric-vehicles").json()
        assert len(cat["products"]) == 3 and cat["kpi"]["name_fr"] == "Voitures électriques"


def test_scoped_french_chat():
    payload = {
        "messages": [{"role": "user", "content": "Quels produits achètent les jeunes ?"}],
        "category": "electric-vehicles",
        "lang": "fr",
    }
    with TestClient(app) as client, client.stream("POST", "/api/chat", json=payload) as r:
        events = [json.loads(line[5:]) for line in r.iter_lines() if line.startswith("data:")]
    text = "".join(e["delta"] for e in events if e["type"] == "text")
    survey = next(e for e in events if e["type"] == "tool_call" and e["name"] == "query_survey")
    assert survey["input"]["categories"] == ["electric-vehicles"]
    assert survey["input"]["metric"] == "product_mix"
    assert "Citadine électrique" in text and "[D1]" in text
