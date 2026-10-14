from autolabeler.analysis import analyze_export
from autolabeler.evaluation import label_studio_agreement


def annotation(person, label):
    return {
        "completed_by": person,
        "lead_time": 4.0,
        "result": [{"from_name": "relevance", "value": {"choices": [label]}}],
    }


def test_label_studio_export_analysis():
    export = [{"id": 1, "annotations": [annotation("a", "relevant"), annotation("b", "relevant")]}]
    assert analyze_export(export)["multi_annotated_tasks"] == 1
    report = label_studio_agreement(export)
    assert report["pairwise_cohen"]["a vs b"]["agreement"] == 1.0
