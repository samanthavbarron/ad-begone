import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

from ad_begone.watch_directory import walk_directory


class TestWalkDirectory(TestCase):

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_empty(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            walk_directory(tmpdir)
            mock_remove_ads.assert_not_called()

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_with_mp3_files(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test MP3 files
            file1 = tmpdir_path / "podcast1.mp3"
            file2 = tmpdir_path / "podcast2.mp3"
            file1.touch()
            file2.touch()

            walk_directory(tmpdir)

            # Should be called twice, once for each MP3
            self.assertEqual(mock_remove_ads.call_count, 2)

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_skips_processed_files(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test MP3 file
            file1 = tmpdir_path / "podcast1.mp3"
            file1.touch()

            # Create hit marker file to indicate it's been processed
            hit_file = tmpdir_path / ".hit.podcast1.mp3.txt"
            hit_file.touch()

            walk_directory(tmpdir)

            # Should not be called since file was already processed
            mock_remove_ads.assert_not_called()

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_overwrite_processes_all(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create test MP3 file with hit marker
            file1 = tmpdir_path / "podcast1.mp3"
            file1.touch()
            hit_file = tmpdir_path / ".hit.podcast1.mp3.txt"
            hit_file.touch()

            # With overwrite=True, should process even with hit file
            walk_directory(tmpdir, overwrite=True)

            # Should be called even though hit file exists
            self.assertEqual(mock_remove_ads.call_count, 1)

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_recursive(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create nested directory structure
            subdir = tmpdir_path / "podcasts" / "series1"
            subdir.mkdir(parents=True)

            # Create MP3 files in different directories
            file1 = tmpdir_path / "podcast1.mp3"
            file2 = subdir / "podcast2.mp3"
            file1.touch()
            file2.touch()

            walk_directory(tmpdir)

            # Should find both files recursively
            self.assertEqual(mock_remove_ads.call_count, 2)

    @patch("ad_begone.watch_directory.remove_ads")
    def test_walk_directory_ignores_non_mp3(self, mock_remove_ads):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create various file types
            mp3_file = tmpdir_path / "podcast.mp3"
            wav_file = tmpdir_path / "audio.wav"
            txt_file = tmpdir_path / "notes.txt"
            mp3_file.touch()
            wav_file.touch()
            txt_file.touch()

            walk_directory(tmpdir)

            # Should only process the MP3 file
            self.assertEqual(mock_remove_ads.call_count, 1)
            call_args = mock_remove_ads.call_args[1]
            self.assertIn("podcast.mp3", call_args["file_name"])
