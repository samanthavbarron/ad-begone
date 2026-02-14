from unittest import TestCase
from unittest.mock import Mock, patch

from ad_begone.ad_trimmer import AdTrimmer


class TestAdTrimmer(TestCase):

    def test_init_valid_mp3(self):
        trimmer = AdTrimmer("test.mp3")
        self.assertEqual(trimmer.file_name, "test.mp3")
        self.assertEqual(trimmer.transcription_cache_file, "test.mp3.transcription.json")
        self.assertEqual(trimmer.segments_cache_file, "test.mp3.segments.json")

    def test_init_invalid_extension(self):
        with self.assertRaises(ValueError) as context:
            AdTrimmer("test.wav")
        self.assertIn("must end with .mp3", str(context.exception))

    def test_init_no_extension(self):
        with self.assertRaises(ValueError) as context:
            AdTrimmer("test")
        self.assertIn("must end with .mp3", str(context.exception))

    @patch("ad_begone.ad_trimmer.cached_transcription")
    def test_transcription(self, mock_cached_transcription):
        mock_result = Mock()
        mock_cached_transcription.return_value = mock_result

        trimmer = AdTrimmer("test.mp3")
        result = trimmer.transcription()

        self.assertEqual(result, mock_result)
        mock_cached_transcription.assert_called_once_with(
            file_name="test.mp3",
            file_transcription="test.mp3.transcription.json"
        )

    @patch("ad_begone.ad_trimmer.cached_annotate_transcription")
    @patch("ad_begone.ad_trimmer.cached_transcription")
    def test_segments_completion(self, mock_cached_transcription, mock_cached_annotate):
        mock_transcription = Mock()
        mock_completion = Mock()
        mock_cached_transcription.return_value = mock_transcription
        mock_cached_annotate.return_value = mock_completion

        trimmer = AdTrimmer("test.mp3")
        result = trimmer.segments_completion()

        self.assertEqual(result, mock_completion)
        mock_cached_annotate.assert_called_once_with(
            transcription=mock_transcription,
            file_name="test.mp3.segments.json",
            model=None,
        )

    @patch("ad_begone.ad_trimmer.find_ad_time_windows")
    @patch("ad_begone.ad_trimmer.get_ordered_annotations")
    @patch("ad_begone.ad_trimmer.cached_annotate_transcription")
    @patch("ad_begone.ad_trimmer.cached_transcription")
    def test_get_time_windows(
        self,
        mock_cached_transcription,
        mock_cached_annotate,
        mock_get_annotations,
        mock_find_windows
    ):
        mock_transcription = Mock()
        mock_completion = Mock()
        mock_annotations = [Mock(), Mock()]
        mock_windows = [Mock(), Mock(), Mock()]

        mock_cached_transcription.return_value = mock_transcription
        mock_cached_annotate.return_value = mock_completion
        mock_get_annotations.return_value = mock_annotations
        mock_find_windows.return_value = mock_windows

        trimmer = AdTrimmer("test.mp3")
        result = trimmer.get_time_windows()

        self.assertEqual(result, mock_windows)
        mock_get_annotations.assert_called_once_with(mock_completion)
        mock_find_windows.assert_called_once_with(mock_transcription, mock_annotations)

    @patch("ad_begone.ad_trimmer._remove_ads")
    def test_remove_ads_default_params(self, mock_remove_ads):
        trimmer = AdTrimmer("test.mp3")
        trimmer.remove_ads()

        mock_remove_ads.assert_called_once()
        call_kwargs = mock_remove_ads.call_args[1]
        self.assertEqual(call_kwargs["file_name"], "test.mp3")
        self.assertEqual(call_kwargs["out_name"], None)
        self.assertEqual(call_kwargs["file_name_transcription_cache"], "test.mp3.transcription.json")

    @patch("ad_begone.ad_trimmer._remove_ads")
    def test_remove_ads_with_output_name(self, mock_remove_ads):
        trimmer = AdTrimmer("test.mp3")
        trimmer.remove_ads(out_name="output.mp3")

        mock_remove_ads.assert_called_once()
        call_kwargs = mock_remove_ads.call_args[1]
        self.assertEqual(call_kwargs["file_name"], "test.mp3")
        self.assertEqual(call_kwargs["out_name"], "output.mp3")

    @patch("ad_begone.ad_trimmer._remove_ads")
    def test_remove_ads_with_custom_notif(self, mock_remove_ads):
        trimmer = AdTrimmer("test.mp3")
        trimmer.remove_ads(notif_name="custom_notif.mp3")

        mock_remove_ads.assert_called_once()
        call_kwargs = mock_remove_ads.call_args[1]
        self.assertEqual(call_kwargs["notif_name"], "custom_notif.mp3")
