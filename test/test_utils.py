import os
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock, Mock, mock_open, patch

from openai.types.audio.transcription_verbose import TranscriptionVerbose

from ad_begone.models import SegmentAnnotation, Window
from ad_begone.utils import (
    cached_transcription,
    find_ad_time_windows,
    get_ordered_annotations,
    join_files,
    split_file,
    transcription_with_segment_indices,
)


class TestCachedTranscription(TestCase):

    def test_invalid_file_extension(self):
        with self.assertRaises(ValueError) as context:
            cached_transcription("test.wav")
        self.assertIn("Couldn't find valid file", str(context.exception))

    @patch("ad_begone.utils.os.path.isfile")
    @patch("builtins.open", new_callable=mock_open, read_data='{"text": "test"}')
    @patch("ad_begone.utils.TranscriptionVerbose.parse_raw")
    def test_loads_from_cache(self, mock_parse, mock_file, mock_isfile):
        mock_isfile.return_value = True
        mock_transcription = MagicMock(spec=TranscriptionVerbose)
        mock_parse.return_value = mock_transcription

        result = cached_transcription("test.mp3")

        self.assertEqual(result, mock_transcription)
        mock_isfile.assert_called_once_with("test.json")
        mock_parse.assert_called_once()


class TestTranscriptionWithSegmentIndices(TestCase):

    def test_empty_segments(self):
        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = []

        result = transcription_with_segment_indices(mock_transcription)
        self.assertEqual(result, "")

    def test_single_segment(self):
        mock_segment = Mock()
        mock_segment.text = "Hello world"

        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = [mock_segment]

        result = transcription_with_segment_indices(mock_transcription)
        self.assertIn("Segment 0:", result)
        self.assertIn("Hello world", result)

    def test_multiple_segments(self):
        mock_segment1 = Mock()
        mock_segment1.text = "First segment"
        mock_segment2 = Mock()
        mock_segment2.text = "Second segment"

        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = [mock_segment1, mock_segment2]

        result = transcription_with_segment_indices(mock_transcription)
        self.assertIn("Segment 0:", result)
        self.assertIn("Segment 1:", result)
        self.assertIn("First segment", result)
        self.assertIn("Second segment", result)


class TestGetOrderedAnnotations(TestCase):

    def test_empty_tool_calls(self):
        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.tool_calls = []

        result = get_ordered_annotations(mock_completion)
        self.assertEqual(result, [])

    def test_single_annotation(self):
        mock_tool_call = Mock()
        mock_tool_call.function.name = "SegmentAnnotation"
        mock_tool_call.function.parsed_arguments = {
            "segment_type": "ad",
            "segment_index": 5
        }

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.tool_calls = [mock_tool_call]

        result = get_ordered_annotations(mock_completion)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].segment_type, "ad")
        self.assertEqual(result[0].segment_index, 5)

    def test_annotations_sorted_by_index(self):
        mock_tool_call1 = Mock()
        mock_tool_call1.function.name = "SegmentAnnotation"
        mock_tool_call1.function.parsed_arguments = {
            "segment_type": "content",
            "segment_index": 10
        }

        mock_tool_call2 = Mock()
        mock_tool_call2.function.name = "SegmentAnnotation"
        mock_tool_call2.function.parsed_arguments = {
            "segment_type": "ad",
            "segment_index": 2
        }

        mock_tool_call3 = Mock()
        mock_tool_call3.function.name = "SegmentAnnotation"
        mock_tool_call3.function.parsed_arguments = {
            "segment_type": "content",
            "segment_index": 5
        }

        mock_completion = Mock()
        mock_completion.choices = [Mock()]
        mock_completion.choices[0].message.tool_calls = [
            mock_tool_call1, mock_tool_call2, mock_tool_call3
        ]

        result = get_ordered_annotations(mock_completion)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].segment_index, 2)
        self.assertEqual(result[1].segment_index, 5)
        self.assertEqual(result[2].segment_index, 10)


class TestFindAdTimeWindows(TestCase):

    def test_single_content_segment(self):
        mock_segment = Mock()
        mock_segment.start = 0.0
        mock_segment.end = 10.0

        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = [mock_segment]

        annotations = [SegmentAnnotation(segment_type="content", segment_index=0)]

        result = find_ad_time_windows(mock_transcription, annotations)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].segment_type, "content")

    def test_content_then_ad(self):
        mock_segment1 = Mock()
        mock_segment1.start = 0.0
        mock_segment1.end = 10.0

        mock_segment2 = Mock()
        mock_segment2.start = 10.0
        mock_segment2.end = 15.0

        mock_segment3 = Mock()
        mock_segment3.start = 15.0
        mock_segment3.end = 20.0

        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = [mock_segment1, mock_segment2, mock_segment3]

        annotations = [
            SegmentAnnotation(segment_type="content", segment_index=0),
            SegmentAnnotation(segment_type="ad", segment_index=1),
        ]

        result = find_ad_time_windows(mock_transcription, annotations)
        self.assertEqual(len(result), 2)
        # The function creates windows based on transitions
        # After processing first annotation at index 0, current_time = seg[0].end = 10.0
        # When it sees second annotation at index 1 with different type, it creates window
        # from current_time (10.0) to seg[1].start (10.0)
        self.assertEqual(result[0].segment_type, "content")
        self.assertEqual(result[0].start, 10.0)
        self.assertEqual(result[0].end, 10.0)
        # Then updates current_time to seg[1].end = 15.0
        # At the end, creates final window from current_time to last segment end
        self.assertEqual(result[1].segment_type, "ad")
        self.assertEqual(result[1].start, 15.0)
        self.assertEqual(result[1].end, 20.0)

    def test_multiple_transitions(self):
        segments = []
        for i in range(6):
            mock_segment = Mock()
            mock_segment.start = i * 5.0
            mock_segment.end = (i + 1) * 5.0
            segments.append(mock_segment)

        mock_transcription = Mock(spec=TranscriptionVerbose)
        mock_transcription.segments = segments

        annotations = [
            SegmentAnnotation(segment_type="content", segment_index=0),
            SegmentAnnotation(segment_type="ad", segment_index=2),
            SegmentAnnotation(segment_type="content", segment_index=4),
        ]

        result = find_ad_time_windows(mock_transcription, annotations)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].segment_type, "content")
        self.assertEqual(result[1].segment_type, "ad")
        self.assertEqual(result[2].segment_type, "content")


class TestSplitFile(TestCase):

    @patch("ad_begone.utils.AudioSegment")
    @patch("ad_begone.utils.os.path.getsize")
    def test_split_small_file(self, mock_getsize, mock_audio_segment):
        # File smaller than 25MB should result in 1 split
        mock_getsize.return_value = 10 * 1024 * 1024  # 10MB in bytes
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=1000)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        mock_audio_segment.from_mp3.return_value = mock_audio

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.mp3"
            test_file.touch()

            result = split_file(str(test_file))

            self.assertEqual(len(result), 1)
            self.assertIn("part_0_test.mp3", result[0])

    @patch("ad_begone.utils.AudioSegment")
    @patch("ad_begone.utils.os.path.getsize")
    def test_split_large_file(self, mock_getsize, mock_audio_segment):
        # File larger than 25MB should result in multiple splits
        mock_getsize.return_value = 60 * 1024 * 1024  # 60MB in bytes
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=1000)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        mock_audio_segment.from_mp3.return_value = mock_audio

        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.mp3"
            test_file.touch()

            result = split_file(str(test_file))

            # 60MB / 25MB = 2.4, should ceil to 3 parts
            self.assertEqual(len(result), 3)


class TestJoinFiles(TestCase):

    @patch("ad_begone.utils.AudioSegment")
    @patch("ad_begone.utils.os.remove")
    def test_join_files(self, mock_remove, mock_audio_segment):
        mock_audio = Mock()
        mock_audio.__add__ = Mock(return_value=mock_audio)
        mock_audio_segment.silent.return_value = mock_audio
        mock_audio_segment.from_mp3.return_value = mock_audio

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_file = tmpdir_path / "test.mp3"
            original_file.touch()

            part1 = tmpdir_path / "part_0_test.mp3"
            part2 = tmpdir_path / "part_1_test.mp3"
            part1.touch()
            part2.touch()

            result = join_files(str(original_file))

            self.assertEqual(result, str(original_file))
            # Verify remove was called for the part files
            self.assertEqual(mock_remove.call_count, 2)

    @patch("ad_begone.utils.AudioSegment")
    @patch("ad_begone.utils.os.remove")
    def test_join_files_no_overwrite(self, mock_remove, mock_audio_segment):
        mock_audio = Mock()
        mock_audio.__add__ = Mock(return_value=mock_audio)
        mock_audio_segment.silent.return_value = mock_audio
        mock_audio_segment.from_mp3.return_value = mock_audio

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            original_file = tmpdir_path / "test.mp3"
            original_file.touch()

            part1 = tmpdir_path / "part_0_test.mp3"
            part1.touch()

            result = join_files(str(original_file), overwrite=False)

            self.assertIn("joined_test.mp3", result)
            self.assertNotEqual(result, str(original_file))
