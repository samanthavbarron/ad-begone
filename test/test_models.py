from unittest import TestCase

from ad_begone.models import SegmentAnnotation, SegmentAnnotations, Window


class TestSegmentAnnotation(TestCase):

    def test_create_ad_annotation(self):
        annotation = SegmentAnnotation(segment_type="ad", segment_index=0)
        self.assertEqual(annotation.segment_type, "ad")
        self.assertEqual(annotation.segment_index, 0)

    def test_create_content_annotation(self):
        annotation = SegmentAnnotation(segment_type="content", segment_index=5)
        self.assertEqual(annotation.segment_type, "content")
        self.assertEqual(annotation.segment_index, 5)

    def test_invalid_segment_type(self):
        with self.assertRaises(Exception):
            SegmentAnnotation(segment_type="invalid", segment_index=0)


class TestSegmentAnnotations(TestCase):

    def test_create_empty_annotations(self):
        annotations = SegmentAnnotations(annotations=[])
        self.assertEqual(len(annotations.annotations), 0)

    def test_create_with_multiple_annotations(self):
        ann1 = SegmentAnnotation(segment_type="content", segment_index=0)
        ann2 = SegmentAnnotation(segment_type="ad", segment_index=5)
        ann3 = SegmentAnnotation(segment_type="content", segment_index=10)

        annotations = SegmentAnnotations(annotations=[ann1, ann2, ann3])
        self.assertEqual(len(annotations.annotations), 3)
        self.assertEqual(annotations.annotations[0].segment_type, "content")
        self.assertEqual(annotations.annotations[1].segment_type, "ad")
        self.assertEqual(annotations.annotations[2].segment_type, "content")


class TestWindow(TestCase):

    def test_create_ad_window(self):
        window = Window(start=0.0, end=10.0, segment_type="ad")
        self.assertEqual(window.start, 0.0)
        self.assertEqual(window.end, 10.0)
        self.assertEqual(window.segment_type, "ad")

    def test_create_content_window(self):
        window = Window(start=10.0, end=50.0, segment_type="content")
        self.assertEqual(window.start, 10.0)
        self.assertEqual(window.end, 50.0)
        self.assertEqual(window.segment_type, "content")

    def test_duration_calculation(self):
        window = Window(start=5.5, end=15.5, segment_type="content")
        self.assertEqual(window.duration(), 10.0)

    def test_duration_zero(self):
        window = Window(start=10.0, end=10.0, segment_type="ad")
        self.assertEqual(window.duration(), 0.0)

    def test_duration_negative(self):
        window = Window(start=20.0, end=10.0, segment_type="content")
        self.assertEqual(window.duration(), -10.0)

    def test_repr(self):
        window = Window(start=5.0, end=15.0, segment_type="ad")
        expected = "Window(5.0-15.0, ad)"
        self.assertEqual(repr(window), expected)

    def test_repr_content(self):
        window = Window(start=100.5, end=200.75, segment_type="content")
        expected = "Window(100.5-200.75, content)"
        self.assertEqual(repr(window), expected)
