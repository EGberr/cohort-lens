from app.offline import OfflineAnalyst, detect_categories


def test_detect_categories_uses_aliases():
    assert detect_categories("Do teens buy trainers or perfume?") == ["sneakers", "fragrance"]
    assert detect_categories("what about tech?")[:1] == ["smartphones"]


async def test_offline_answer_is_grounded(toolbox, store):
    events = [
        e
        async for e in OfflineAnalyst(toolbox).run(
            [{"role": "user", "content": "What share of Gen Z women bought skincare?"}]
        )
    ]
    text = "".join(e["delta"] for e in events if e["type"] == "text")
    assert events[-1]["type"] == "done"
    assert "[D1]" in text
    gold = next(
        r["value"]
        for r in store.query("penetration", ["skincare"], breakdown="gender").rows
        if r["segment"] == "female"
    )
    assert f"{gold:.0f}%" in text
