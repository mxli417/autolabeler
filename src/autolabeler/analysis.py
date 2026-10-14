from __future__ import annotations

from collections import Counter
from statistics import median

from .evaluation import _choice


def analyze_export(export: list[dict], control: str = "relevance") -> dict:
    labels, durations, annotators = Counter(), [], Counter()
    total_annotations = 0
    for task in export:
        for annotation in task.get("annotations", []):
            total_annotations += 1
            label = _choice(annotation, control)
            if label:
                labels[label] += 1
            who = annotation.get("completed_by", "unknown")
            if isinstance(who, dict):
                who = who.get("email") or who.get("id") or "unknown"
            annotators[str(who)] += 1
            if annotation.get("lead_time") is not None:
                durations.append(float(annotation["lead_time"]))
    completed = sum(bool(task.get("annotations")) for task in export)
    return {
        "tasks": len(export),
        "completed_tasks": completed,
        "completion_rate": completed / len(export) if export else 0.0,
        "annotations": total_annotations,
        "labels": dict(labels),
        "annotations_by_annotator": dict(annotators),
        "median_lead_time_seconds": median(durations) if durations else None,
        "multi_annotated_tasks": sum(len(task.get("annotations", [])) >= 2 for task in export),
    }
