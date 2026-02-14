import os

import pytest

from ad_begone.accuracy import compute_accuracy
from ad_begone.utils import cached_annotate_transcription, get_ordered_annotations

pytestmark = pytest.mark.skipif(
    os.environ.get("OPENAI_API_KEY", "dummy") == "dummy",
    reason="Requires real OPENAI_API_KEY",
)

MIN_F1 = 0.85
MIN_IOU = 0.80


def test_accuracy_eval(accuracy_fixture, tmp_path):
    transcription, ground_truth, name = accuracy_fixture

    cache_file = str(tmp_path / f"{name}_annotation.json")
    completion = cached_annotate_transcription(transcription, file_name=cache_file)
    predicted = get_ordered_annotations(completion)

    report = compute_accuracy(predicted, ground_truth, transcription)

    print(f"\n{'='*60}")
    print(f"Fixture: {name}")
    print(f"{'='*60}")
    print(f"Segment precision: {report.segment_precision:.3f}")
    print(f"Segment recall:    {report.segment_recall:.3f}")
    print(f"Segment F1:        {report.segment_f1:.3f}")
    print(f"Time precision:    {report.time_precision:.3f}")
    print(f"Time recall:       {report.time_recall:.3f}")
    print(f"Time F1:           {report.time_f1:.3f}")
    print(f"Time IoU:          {report.time_iou:.3f}")

    if report.false_positive_segments:
        print(f"False positives:   segments {report.false_positive_segments}")
    if report.false_negative_segments:
        print(f"False negatives:   segments {report.false_negative_segments}")

    assert report.segment_f1 >= MIN_F1, (
        f"[{name}] Segment F1 {report.segment_f1:.3f} < {MIN_F1}"
    )
    assert report.time_iou >= MIN_IOU, (
        f"[{name}] Time IoU {report.time_iou:.3f} < {MIN_IOU}"
    )
