from unittest import TestCase


class TestImport(TestCase):

    def test_import(self):
        import ad_begone
        self.assertIsNotNone(ad_begone)

    def test_import_models(self):
        from ad_begone import models
        self.assertIsNotNone(models)
        self.assertTrue(hasattr(models, "Window"))
        self.assertTrue(hasattr(models, "SegmentAnnotation"))
        self.assertTrue(hasattr(models, "SegmentAnnotations"))

    def test_import_utils(self):
        from ad_begone import utils
        self.assertIsNotNone(utils)
        self.assertTrue(hasattr(utils, "cached_transcription"))
        self.assertTrue(hasattr(utils, "find_ad_time_windows"))

    def test_import_ad_trimmer(self):
        from ad_begone.ad_trimmer import AdTrimmer
        self.assertIsNotNone(AdTrimmer)

    def test_import_remove_ads(self):
        from ad_begone.remove_ads import remove_ads
        self.assertIsNotNone(remove_ads)