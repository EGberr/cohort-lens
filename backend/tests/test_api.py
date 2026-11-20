import json

from fastapi.testclient import TestClient

from app.main import app


def test_endpoints():
    with TestClient(app) as client:
        h = client.get("/api/health").json()
        assert h["analyst"] == "offline" and h["documents"] == 65
        ov = client.get("/api/overview").json()
        assert len(ov["categories"]) == 50 and len(ov["groups"]) == 9
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
