from dataclasses import dataclass, field

from openai.types.audio.transcription_verbose import TranscriptionVerbose

from .models import SegmentAnnotation, Window
from .utils import find_ad_time_windows


@dataclass
class AccuracyReport:
    segment_precision: float
    segment_recall: float
    segment_f1: float
    time_precision: float
    time_recall: float
    time_f1: float
    time_iou: float
    false_positive_segments: list[int] = field(default_factory=list)
    false_negative_segments: list[int] = field(default_factory=list)


def expand_annotations(
    annotations: list[SegmentAnnotation],
    total_segments: int,
) -> list[str]:
    """Expand sparse transition annotations into per-segment labels.

    Annotations mark only the *start* of each block (ad or content).
    This fills in every segment between transitions with the current label.
    """
    if not annotations or total_segments == 0:
        return ["content"] * total_segments

    labels: list[str] = []
    sorted_anns = sorted(annotations, key=lambda a: a.segment_index)

    ann_idx = 0
    # Default to "content" for segments before the first annotation
    current_type = "content"

    for seg_i in range(total_segments):
        if ann_idx < len(sorted_anns) and sorted_anns[ann_idx].segment_index == seg_i:
            current_type = sorted_anns[ann_idx].segment_type
            ann_idx += 1
        labels.append(current_type)

    return labels


def compute_time_iou(
    predicted_windows: list[Window],
    ground_truth_windows: list[Window],
) -> float:
    """Compute Intersection-over-Union of ad time windows."""
    pred_ad = [(w.start, w.end) for w in predicted_windows if w.segment_type == "ad"]
    gt_ad = [(w.start, w.end) for w in ground_truth_windows if w.segment_type == "ad"]

    if not pred_ad and not gt_ad:
        return 1.0
    if not pred_ad or not gt_ad:
        return 0.0

    intersection = 0.0
    for ps, pe in pred_ad:
        for gs, ge in gt_ad:
            overlap_start = max(ps, gs)
            overlap_end = min(pe, ge)
            if overlap_end > overlap_start:
                intersection += overlap_end - overlap_start

    pred_total = sum(e - s for s, e in pred_ad)
    gt_total = sum(e - s for s, e in gt_ad)
    union = pred_total + gt_total - intersection

    if union == 0.0:
        return 1.0

    return intersection / union


def _time_precision_recall(
    predicted_windows: list[Window],
    ground_truth_windows: list[Window],
) -> tuple[float, float]:
    """Compute time-weighted precision and recall for ad windows."""
    pred_ad = [(w.start, w.end) for w in predicted_windows if w.segment_type == "ad"]
    gt_ad = [(w.start, w.end) for w in ground_truth_windows if w.segment_type == "ad"]

    pred_total = sum(e - s for s, e in pred_ad)
    gt_total = sum(e - s for s, e in gt_ad)

    if pred_total == 0.0 and gt_total == 0.0:
        return 1.0, 1.0

    intersection = 0.0
    for ps, pe in pred_ad:
        for gs, ge in gt_ad:
            overlap_start = max(ps, gs)
            overlap_end = min(pe, ge)
            if overlap_end > overlap_start:
                intersection += overlap_end - overlap_start

    precision = intersection / pred_total if pred_total > 0 else 0.0
    recall = intersection / gt_total if gt_total > 0 else 0.0
    return precision, recall


def compute_accuracy(
    predicted: list[SegmentAnnotation],
    ground_truth: list[SegmentAnnotation],
    transcription: TranscriptionVerbose,
) -> AccuracyReport:
    """Compare predicted annotations against ground truth.

    Computes segment-level and time-level metrics.
    """
    total_segments = len(transcription.segments)
    pred_labels = expand_annotations(predicted, total_segments)
    gt_labels = expand_annotations(ground_truth, total_segments)

    # Segment-level metrics
    true_pos = 0
    false_pos = 0
    false_neg = 0
    fp_segments: list[int] = []
    fn_segments: list[int] = []

    for i in range(total_segments):
        pred_ad = pred_labels[i] == "ad"
        gt_ad = gt_labels[i] == "ad"

        if pred_ad and gt_ad:
            true_pos += 1
        elif pred_ad and not gt_ad:
            false_pos += 1
            fp_segments.append(i)
        elif not pred_ad and gt_ad:
            false_neg += 1
            fn_segments.append(i)

    seg_precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) > 0 else 1.0
    seg_recall = true_pos / (true_pos + false_neg) if (true_pos + false_neg) > 0 else 1.0
    seg_f1 = (
        2 * seg_precision * seg_recall / (seg_precision + seg_recall)
        if (seg_precision + seg_recall) > 0
        else 0.0
    )

    # Time-level metrics
    pred_windows = find_ad_time_windows(transcription, sorted(predicted, key=lambda a: a.segment_index))
    gt_windows = find_ad_time_windows(transcription, sorted(ground_truth, key=lambda a: a.segment_index))

    time_prec, time_rec = _time_precision_recall(pred_windows, gt_windows)
    time_f1 = (
        2 * time_prec * time_rec / (time_prec + time_rec)
        if (time_prec + time_rec) > 0
        else 0.0
    )
    time_iou = compute_time_iou(pred_windows, gt_windows)

    return AccuracyReport(
        segment_precision=seg_precision,
        segment_recall=seg_recall,
        segment_f1=seg_f1,
        time_precision=time_prec,
        time_recall=time_rec,
        time_f1=time_f1,
        time_iou=time_iou,
        false_positive_segments=fp_segments,
        false_negative_segments=fn_segments,
    )
