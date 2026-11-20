import pytest

from app.tools import SourceRegistry, ToolError


def test_survey_tool_assigns_dataset_ids(toolbox):
    reg = SourceRegistry()
    r1, _ = toolbox.run("query_survey", {"metric": "penetration", "categories": ["skincare"]}, reg)
    r2, _ = toolbox.run("query_survey", {"metric": "dupe_rate", "categories": ["skincare"]}, reg)
    assert (r1["id"], r2["id"]) == ("D1", "D2")


def test_search_ids_are_stable_across_calls(toolbox):
    reg = SourceRegistry()
    a, _ = toolbox.run("search_research", {"query": "dupe culture", "k": 3}, reg)
    b, events = toolbox.run("search_research", {"query": "dupe culture", "k": 3}, reg)
    assert [p["id"] for p in a["passages"]] == [p["id"] for p in b["passages"]]
    assert not [e for e in events if e["type"] == "source"]  # no duplicate source events


def test_chart_must_reference_known_dataset(toolbox):
    with pytest.raises(ToolError):
        toolbox.run(
            "create_chart",
            {"title": "x", "chart_type": "bar", "data": [{"label": "a", "value": 1}], "source_ids": ["D9"]},
            SourceRegistry(),
        )


def test_invalid_input_is_a_tool_error(toolbox):
    with pytest.raises(ToolError):
        toolbox.run("query_survey", {"metric": "penetration", "categories": []}, SourceRegistry())
