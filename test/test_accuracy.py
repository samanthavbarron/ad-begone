import unittest

from openai.types.audio.transcription_verbose import TranscriptionVerbose

from ad_begone.accuracy import (
    AccuracyReport,
    compute_accuracy,
    compute_time_iou,
    expand_annotations,
)
from ad_begone.models import SegmentAnnotation, Window


def _make_segment(id: int, start: float, end: float, text: str = "") -> dict:
    """Create a minimal segment dict for TranscriptionVerbose."""
    return {
        "id": id,
        "avg_logprob": -0.2,
        "compression_ratio": 1.5,
        "end": end,
        "no_speech_prob": 0.001,
        "seek": 0,
        "start": start,
        "temperature": 0.0,
        "text": text,
        "tokens": [1],
    }


def _make_transcription(segments: list[dict]) -> TranscriptionVerbose:
    """Build a TranscriptionVerbose from a list of segment dicts."""
    duration = segments[-1]["end"] if segments else 0.0
    return TranscriptionVerbose.model_validate({
        "duration": duration,
        "language": "english",
        "text": "",
        "segments": segments,
        "task": "transcribe",
    })


def _ann(segment_type: str, segment_index: int) -> SegmentAnnotation:
    return SegmentAnnotation(segment_type=segment_type, segment_index=segment_index)


class TestExpandAnnotations(unittest.TestCase):

    def test_basic_content_then_ad(self):
        anns = [_ann("content", 0), _ann("ad", 3)]
        result = expand_annotations(anns, 5)
        self.assertEqual(result, ["content", "content", "content", "ad", "ad"])

    def test_starts_with_ad(self):
        anns = [_ann("ad", 0), _ann("content", 2)]
        result = expand_annotations(anns, 4)
        self.assertEqual(result, ["ad", "ad", "content", "content"])

    def test_single_type_content(self):
        anns = [_ann("content", 0)]
        result = expand_annotations(anns, 5)
        self.assertEqual(result, ["content"] * 5)

    def test_single_type_ad(self):
        anns = [_ann("ad", 0)]
        result = expand_annotations(anns, 3)
        self.assertEqual(result, ["ad", "ad", "ad"])

    def test_empty_annotations(self):
        result = expand_annotations([], 5)
        self.assertEqual(result, ["content"] * 5)

    def test_zero_segments(self):
        result = expand_annotations([], 0)
        self.assertEqual(result, [])

    def test_multiple_transitions(self):
        anns = [_ann("content", 0), _ann("ad", 2), _ann("content", 4), _ann("ad", 6)]
        result = expand_annotations(anns, 8)
        self.assertEqual(
            result,
            ["content", "content", "ad", "ad", "content", "content", "ad", "ad"],
        )

    def test_unsorted_annotations(self):
        anns = [_ann("ad", 3), _ann("content", 0)]
        result = expand_annotations(anns, 5)
        self.assertEqual(result, ["content", "content", "content", "ad", "ad"])

    def test_annotation_not_at_zero(self):
        """If first annotation doesn't start at 0, segments before it default to content."""
        anns = [_ann("ad", 2)]
        result = expand_annotations(anns, 5)
        self.assertEqual(result, ["content", "content", "ad", "ad", "ad"])


class TestComputeTimeIou(unittest.TestCase):

    def test_exact_match(self):
        pred = [Window(10.0, 20.0, "ad")]
        gt = [Window(10.0, 20.0, "ad")]
        self.assertAlmostEqual(compute_time_iou(pred, gt), 1.0)

    def test_no_overlap(self):
        pred = [Window(0.0, 10.0, "ad")]
        gt = [Window(20.0, 30.0, "ad")]
        self.assertAlmostEqual(compute_time_iou(pred, gt), 0.0)

    def test_partial_overlap(self):
        pred = [Window(0.0, 15.0, "ad")]
        gt = [Window(10.0, 20.0, "ad")]
        # intersection = 5, union = 15 + 10 - 5 = 20
        self.assertAlmostEqual(compute_time_iou(pred, gt), 5.0 / 20.0)

    def test_no_ads_in_either(self):
        pred = [Window(0.0, 10.0, "content")]
        gt = [Window(0.0, 10.0, "content")]
        self.assertAlmostEqual(compute_time_iou(pred, gt), 1.0)

    def test_pred_has_ads_gt_has_none(self):
        pred = [Window(0.0, 10.0, "ad")]
        gt = [Window(0.0, 10.0, "content")]
        self.assertAlmostEqual(compute_time_iou(pred, gt), 0.0)

    def test_gt_has_ads_pred_has_none(self):
        pred = [Window(0.0, 10.0, "content")]
        gt = [Window(0.0, 10.0, "ad")]
        self.assertAlmostEqual(compute_time_iou(pred, gt), 0.0)

    def test_multiple_windows(self):
        pred = [Window(0.0, 10.0, "ad"), Window(20.0, 30.0, "ad")]
        gt = [Window(5.0, 15.0, "ad"), Window(25.0, 35.0, "ad")]
        # intersection = 5 + 5 = 10, union = 20 + 20 - 10 = 30
        self.assertAlmostEqual(compute_time_iou(pred, gt), 10.0 / 30.0)


class TestComputeAccuracy(unittest.TestCase):

    def _segments(self, n: int, duration_each: float = 5.0) -> list[dict]:
        return [
            _make_segment(i, i * duration_each, (i + 1) * duration_each, f"seg {i}")
            for i in range(n)
        ]

    def test_perfect_match(self):
        trans = _make_transcription(self._segments(10))
        anns = [_ann("content", 0), _ann("ad", 5)]
        report = compute_accuracy(anns, anns, trans)
        self.assertAlmostEqual(report.segment_f1, 1.0)
        self.assertAlmostEqual(report.time_iou, 1.0)
        self.assertEqual(report.false_positive_segments, [])
        self.assertEqual(report.false_negative_segments, [])

    def test_all_wrong(self):
        trans = _make_transcription(self._segments(10))
        pred = [_ann("ad", 0)]
        gt = [_ann("content", 0)]
        report = compute_accuracy(pred, gt, trans)
        # All segments predicted as ad, but all are content
        self.assertAlmostEqual(report.segment_precision, 0.0)
        self.assertAlmostEqual(report.segment_recall, 1.0)  # no actual ads, recall defaults to 1.0
        self.assertEqual(len(report.false_positive_segments), 10)
        self.assertEqual(report.false_negative_segments, [])

    def test_partial_overlap(self):
        trans = _make_transcription(self._segments(10))
        # Ground truth: segments 3-6 are ads
        gt = [_ann("content", 0), _ann("ad", 3), _ann("content", 7)]
        # Predicted: segments 4-7 are ads (shifted by 1)
        pred = [_ann("content", 0), _ann("ad", 4), _ann("content", 8)]
        report = compute_accuracy(pred, gt, trans)
        # TP=3 (4,5,6), FP=1 (7), FN=1 (3)
        self.assertAlmostEqual(report.segment_precision, 3.0 / 4.0)
        self.assertAlmostEqual(report.segment_recall, 3.0 / 4.0)
        self.assertEqual(report.false_positive_segments, [7])
        self.assertEqual(report.false_negative_segments, [3])

    def test_no_ads_in_either(self):
        trans = _make_transcription(self._segments(10))
        pred = [_ann("content", 0)]
        gt = [_ann("content", 0)]
        report = compute_accuracy(pred, gt, trans)
        # No ads predicted, no ads in ground truth
        self.assertAlmostEqual(report.segment_precision, 1.0)
        self.assertAlmostEqual(report.segment_recall, 1.0)
        self.assertAlmostEqual(report.segment_f1, 1.0)
        self.assertAlmostEqual(report.time_iou, 1.0)

    def test_false_positives_and_negatives_populated(self):
        trans = _make_transcription(self._segments(6))
        gt = [_ann("content", 0), _ann("ad", 2), _ann("content", 4)]
        pred = [_ann("content", 0), _ann("ad", 3), _ann("content", 5)]
        report = compute_accuracy(pred, gt, trans)
        # GT ads: [2,3], Pred ads: [3,4]
        # TP=1 (3), FP=1 (4), FN=1 (2)
        self.assertIn(4, report.false_positive_segments)
        self.assertIn(2, report.false_negative_segments)


if __name__ == "__main__":
    unittest.main()
