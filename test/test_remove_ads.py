import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from ad_begone.remove_ads import remove_ads


class TestRemoveAds(TestCase):

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_basic(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()

            mock_split.return_value = [str(tmpdir_path / "part_0_test.mp3")]
            mock_trimmer = Mock()
            mock_trimmer_class.return_value = mock_trimmer

            remove_ads(str(test_file))

            mock_split.assert_called_once_with(str(test_file))
            mock_trimmer_class.assert_called_once()
            mock_trimmer.remove_ads.assert_called_once()
            mock_join.assert_called_once_with(str(test_file))

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_creates_hit_file(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()
            hit_file = tmpdir_path / ".hit.test.mp3.txt"

            mock_split.return_value = [str(tmpdir_path / "part_0_test.mp3")]
            mock_trimmer_class.return_value = Mock()

            remove_ads(str(test_file))

            self.assertTrue(hit_file.exists())

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_skips_if_hit_file_exists(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()
            hit_file = tmpdir_path / ".hit.test.mp3.txt"
            hit_file.touch()

            remove_ads(str(test_file))

            # Should not call any processing functions
            mock_split.assert_not_called()
            mock_trimmer_class.assert_not_called()
            mock_join.assert_not_called()

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_overwrite_processes_again(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()
            hit_file = tmpdir_path / ".hit.test.mp3.txt"
            hit_file.touch()

            mock_split.return_value = [str(tmpdir_path / "part_0_test.mp3")]
            mock_trimmer_class.return_value = Mock()

            remove_ads(str(test_file), overwrite=True)

            # Should process even with hit file
            mock_split.assert_called_once()
            mock_trimmer_class.assert_called_once()
            mock_join.assert_called_once()

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_with_output_name(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            output_file = tmpdir_path / "output.mp3"
            test_file.touch()

            mock_split.return_value = [str(tmpdir_path / "part_0_test.mp3")]
            mock_trimmer_class.return_value = Mock()

            remove_ads(str(test_file), out_name=str(output_file))

            mock_split.assert_called_once_with(str(test_file))
            mock_join.assert_called_once_with(str(test_file))

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_multiple_parts(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()

            # Simulate splitting into 3 parts
            mock_split.return_value = [
                str(tmpdir_path / "part_0_test.mp3"),
                str(tmpdir_path / "part_1_test.mp3"),
                str(tmpdir_path / "part_2_test.mp3"),
            ]
            mock_trimmer = Mock()
            mock_trimmer_class.return_value = mock_trimmer

            remove_ads(str(test_file))

            # Should create a trimmer for each part
            self.assertEqual(mock_trimmer_class.call_count, 3)
            self.assertEqual(mock_trimmer.remove_ads.call_count, 3)

    @patch("ad_begone.remove_ads.join_files")
    @patch("ad_begone.remove_ads.AdTrimmer")
    @patch("ad_begone.remove_ads.split_file")
    def test_remove_ads_custom_notif(self, mock_split, mock_trimmer_class, mock_join):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            test_file = tmpdir_path / "test.mp3"
            test_file.touch()

            mock_split.return_value = [str(tmpdir_path / "part_0_test.mp3")]
            mock_trimmer = Mock()
            mock_trimmer_class.return_value = mock_trimmer

            custom_notif = "custom_notif.mp3"
            remove_ads(str(test_file), notif_name=custom_notif)

            mock_trimmer.remove_ads.assert_called_once_with(notif_name=custom_notif)
